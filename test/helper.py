import os
import docker
from time import sleep

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DOCKER_ROOT = os.path.join(ROOT_DIR, 'test', 'docker')


def _get_docker_client():
    return docker.from_env()


def build_containers():
    client = _get_docker_client()
    client.images.build(path=os.path.join(_DOCKER_ROOT, 'test_ftp'),
                        tag='test_ftp')


def start_ftp():
    client = _get_docker_client()
    stop_ftp()
    client.containers.run('test_ftp', name='test_ftp', detach=True,
                          ports={'21/tcp': 2021,
                                 '10090/tcp': 10090})


def stop_ftp():
    client = _get_docker_client()
    try:
        container = client.containers.get('test_ftp')
        container.remove(force=True)
    except docker.errors.NotFound:
        return
