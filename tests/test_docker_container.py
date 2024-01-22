import pytest
from docker_container_utils.docker_container import DockerContainer, ParsingError

def test_extract_container_info_valid():
    # Test a valid container name
    containers = [
            ('docker.io', 'library', 'nginx', 'latest', 'docker.io/library/nginx:latest'),
            ('quay.io', 'my-project', 'webserver', 'v1.0', 'quay.io/my-project/webserver:v1.0'),
            ('registry.example.com', 'my-org', 'app', 'v2.0', 'registry.example.com/my-org/app:v2.0'),
            ('docker.io', 'stable', 'mysql', 'latest', 'docker.io/stable/mysql:latest'),
            ('gitlab.com', 'group/repo', 'image', 'v3.0', 'gitlab.com/group/repo/image:v3.0'),
            ('github.com', 'username', 'project', 'v4.0', 'github.com/username/project:v4.0'),
            ('docker.io', 'community', 'database', 'latest', 'docker.io/community/database:latest'),
            ('cloud.example', '', 'my-app', 'latest', 'cloud.example/my-app:latest'),
            ('registry.example.com', 'my-group', 'web', 'v5.0', 'registry.example.com/my-group/web:v5.0'),
            ('docker.io', 'third-party', 'proxy', 'latest', 'docker.io/third-party/proxy:latest'),
            ('docker.io', 'third-party', 'proxy', 'latest', 'docker.io/third-party/proxy:latest')
    ]

    for container_name_array in containers:
        hostname, path, container_name, tag, full = container_name_array
        c = DockerContainer(full)
        assert c.hostname == hostname
        assert c.path == path
        assert c.container_name == container_name
        assert c.tag == tag

def test_extract_container_info_invalid():
    # Test an invalid container name
    container_name = "invalid-format"
    with pytest.raises(ParsingError):
        DockerContainer(container_name)


def test_full_name():
    # Test the full_name property
    container_name = "docker.io/library/nginx:latest"
    container = DockerContainer(container_name)
    # Note that this will fail if it's a container name 
    # without a hostname because our class will fill in 
    # the hostname with docker.io (docker assumes this 
    # as the hostname if one isn't given).
    assert container.full_name == container_name

