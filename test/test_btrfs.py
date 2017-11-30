import os
import shutil
import unittest
from datetime import datetime
from subprocess import check_call

from fritzbackup import FritzBackup


class TestBtrfs(unittest.TestCase):

    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    TEMP_DIR = os.path.join(ROOT_DIR, 'tmp')
    MOUNT_POINT = os.path.join(TEMP_DIR, 'mnt')
    IMG_FILE = os.path.join(TEMP_DIR, 'btrfs.img')
    TEST_FILE = os.path.join(MOUNT_POINT, 'test_file')
    CONFIG_ROOT = os.path.join(ROOT_DIR, 'test', 'config')

    @classmethod
    def setUpClass(cls):
        if os.path.ismount(cls.MOUNT_POINT):
            check_call('umount {}'.format(cls.MOUNT_POINT), shell=True)
        if os.path.exists(cls.TEMP_DIR):
            shutil.rmtree(cls.TEMP_DIR)
        os.makedirs(os.path.join(cls.TEMP_DIR, cls.MOUNT_POINT))
        check_call('dd if=/dev/zero of={} bs=1M count=100'.format(cls.IMG_FILE), shell=True)
        check_call('mkfs.btrfs {}'.format(cls.IMG_FILE), shell=True)
        check_call('mount -o loop {} {}'.format(cls.IMG_FILE, cls.MOUNT_POINT), shell=True)
        cls.update_testfile()

    @classmethod
    def update_testfile(cls):
        with open(cls.TEST_FILE, 'w') as test_file:
            test_file.write(datetime.now().isoformat()+"\n")

    def test_1(self):
        config_dir = os.path.join(self.CONFIG_ROOT, 'btrfs1')
        fb = FritzBackup(config_dir)
        fb.run()