from typing import Dict, Optional
import warnings

class ParsingError(Exception):
    """Exception raised for errors in parsing container information."""
    pass

# Attempt to import the docker SDK
try:
    import docker
    DockerSDKBaseClass = docker.models.containers.Container
    docker_client = docker.from_env()
except ImportError:
    DockerSDKBaseClass = (
        object  # Fallback to a basic object if docker-py is not available
    )
    docker_client = None
    warnings.warn("The Docker SDK for Python is not installed. Install with pip3 install docker")
except docker.errors.DockerException:
    DockerSDKBaseClass = (
        object  # Fallback to a basic object if docker-py is not available
    )
    docker_client = None
    warnings.warn("We were unable to instantiate a client instance to a running Docker instance.")    

class DockerContainer(DockerSDKBaseClass):
    """
    Represents a Docker container and provides functionalities for extracting
    and handling information related to the container.

    Attributes:
        container_name (str): The full name of the Docker container.
        info (Optional[Dict[str, str]]): Extracted information about the container, including hostname, path, name, and tag.

    Args:
        container_name (str): The full name of the Docker container, typically in the format 'hostname/path/name:tag'.

    """

    DEFAULT_HOSTNAME = "docker.io"

    def __init__(self, raw_container_name_string: str, enable_client: bool = False):
        # Initialize base class if Docker SDK is available
        if DockerSDKBaseClass is not object and enable_client:
            super().__init__(client=docker_client, attrs={"Image": raw_container_name_string})

        # Your custom initialization
        self.raw_container_name_string = raw_container_name_string
        self.info = self.extract_container_info()
        if self.info:
            self.hostname = self.info["hostname"]
            self.path = self.info["path"]
            self.container_name = self.info["container_name"]
            self.tag = self.info["tag"]
        else:
            raise ValueError("Invalid docker image path")

    def extract_container_info(self) -> Optional[Dict[str, str]]:
        """
        Extracts and returns information about the Docker container.

        Splits the container name into its constituent parts - hostname, path, name, and tag.
        If the container name is invalid, this method returns None.

        Returns:
            Optional[Dict[str, str]]: A dictionary containing the extracted container information,
            or None if the container name is invalid.

        Raises:
            ValueError: If the container name format is invalid.

        """
        try:
            components = self.raw_container_name_string.split("/")
            hostname, path = self._parse_hostname_and_path(components)
            container_name, tag = self._parse_name_and_tag(components[-1])
            return {
                "hostname": hostname,
                "path": path,
                "container_name": container_name,
                "tag": tag,
            }
        except ValueError as e:
            raise ParsingError(f"Failed to parse container info: {e}")

    @staticmethod
    def _parse_hostname_and_path(components: list[str]) -> tuple[str, str]:
        """
        Parses and returns the hostname and path from the components of the container name.

        Args:
            components (list[str]): The components of the container name, split by '/'.

        Returns:
            tuple[str, str]: A tuple containing the hostname and path.

        """
        if "." in components[0]:
            return components[0], "/".join(components[1:-1])
        return DockerContainer.DEFAULT_HOSTNAME, "/".join(components[:-1])

    @staticmethod
    def _parse_name_and_tag(container_name_with_tag: str) -> tuple[str, str]:
        """
        Parses and returns the name and tag from the last component of the container name.

        Args:
            container_name_with_tag (str): The last component of the container name, typically in the format 'name:tag'.

        Returns:
            tuple[str, str]: A tuple containing the name and tag.

        Raises:
            ValueError: If the format of the name and tag component is invalid.

        """
        name_array = container_name_with_tag.split(":")
        if len(name_array) != 2:
            raise ValueError("Invalid docker image path")
        return tuple(name_array)

    @property
    def full_name(self) -> str:
        if self.path == "":
            return f"{self.hostname}/{self.container_name}:{self.tag}"
        else:
            return f"{self.hostname}/{self.path}/{self.container_name}:{self.tag}"

    def __repr__(self) -> str:
        """
        Returns a string representation of the DockerContainer instance.

        If the container information is valid, it returns the formatted string with all details.
        If the container information is invalid, it returns a string indicating an invalid container.

        Returns:
            str: A string representation of the DockerContainer instance.

        """
        if self.info:
            return f"DockerContainer(hostname='{self.hostname}', path='{self.path}', name='{self.container_name}', tag='{self.tag}')"
        return "DockerContainer(invalid)"
