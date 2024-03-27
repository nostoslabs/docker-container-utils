import argparse
import subprocess
import threading
import queue
from pathlib import Path
from typing import List
from docker_container import DockerContainer, extract_container_info_from_image_file


def load_docker_image(image_queue: queue.Queue, tag_queue: queue.Queue):
    while True:
        image_path = image_queue.get()
        if image_path is None:  # Poison pill means shutdown
            tag_queue.put(None)  # Pass shutdown signal to the next stage
            break
        try:
            result = subprocess.run(["docker", "load", "-i", image_path], capture_output=True, text=True, check=True)
            image_details = extract_container_info_from_image_file(image_path)
            tag_queue.put((image_path, image_details))
        except subprocess.CalledProcessError as e:
            print(f"Failed to load image {image_path}: {e}")
        finally:
            image_queue.task_done()


def tag_docker_image(tag_queue: queue.Queue, push_queue: queue.Queue, new_tag: str, destination_path: str):
    while True:
        item = tag_queue.get()
        if item is None:  # Poison pill means shutdown
            push_queue.put(None)  # Pass shutdown signal to the next stage
            break
        image_path, image_details = item
        try:
            imageObj = DockerContainer(image_details)
            new_image_tag = f"{destination_path}/{imageObj.container_name}:{new_tag}"
            subprocess.run(["docker", "tag", image_details, new_image_tag], check=True)
            print(f"Tagged {image_details} as {new_image_tag}")
            push_queue.put(new_image_tag)
        except subprocess.CalledProcessError as e:
            print(f"Failed to tag image {image_details}: {e}")
        finally:
            tag_queue.task_done()


def push_docker_image(push_queue: queue.Queue):
    while True:
        image_tag = push_queue.get()
        if image_tag is None:  # Poison pill means shutdown
            break
        try:
            subprocess.run(["docker", "push", image_tag], check=True)
            print(f"Pushed {image_tag} successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to push image {image_tag}: {e}")
        finally:
            push_queue.task_done()


def process_images(images: List[str], new_tag: str, destination_path: str):
    image_queue = queue.Queue()
    tag_queue = queue.Queue()
    push_queue = queue.Queue()

    threads = [
        threading.Thread(target=load_docker_image, args=(image_queue, tag_queue)),
        threading.Thread(target=tag_docker_image, args=(tag_queue, push_queue, new_tag, destination_path)),
        threading.Thread(target=push_docker_image, args=(push_queue,))
    ]

    for thread in threads:
        thread.start()

    for image in images:
        image_queue.put(image)

    image_queue.put(None)  # Send shutdown signal to load stage

    for thread in threads:
        thread.join()


def main():
    parser = argparse.ArgumentParser(description="Concurrently load, tag, and push Docker images.")
    parser.add_argument("--new_tag", required=True, help="New tag for the Docker images.")
    parser.add_argument("--destination_path", required=True, help="Destination path for tagged images.")
    parser.add_argument("--image_dir", required=True, help="Directory containing Docker image files.")
    args = parser.parse_args()

    image_dir = Path(args.image_dir)
    if not image_dir.exists() or not image_dir.is_dir():
        print("Specified image directory does not exist or is not a directory.")
        return

    images = [str(f) for f in image_dir.glob("*.tar.gz")]  # Adjust glob pattern as necessary
    process_images(images, args.new_tag, args.destination_path)


if __name__ == "__main__":
    main()
