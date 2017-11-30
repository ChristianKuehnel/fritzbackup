import os
import docker


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
    client.container.run('test_ftp', name='test_ftp', detatch=True)


def stop_ftp():
    client = _get_docker_client()
    client.container.stop('test_ftp')
