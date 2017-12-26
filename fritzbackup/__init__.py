import os
import subprocess
import yaml
import netrc
import shutil
import logging

from fritzbackup.backup_btrfs import BackupBtrfs

_LOGGER = logging.getLogger(__name__)

DIRECTORIES_FOLDER = 'directories'
NEXTCLOUD_FOLDER = 'nextcloud'


class Configuration(object):
    CONFIG_FILE_NAME = 'config.yaml'

    def __init__(self, config_root):
        config_file_path = os.path.join(config_root, self.CONFIG_FILE_NAME)
        self.cache_dir = os.path.join(config_root, 'cache')
        with open(config_file_path, 'r') as config_file:
            yconfig = yaml.load(config_file)
        self.fritzbox_url = yconfig['fritzbox']['host']
        self.fritzbox_port = 21
        if 'port' in yconfig['fritzbox']:
            self.fritzbox_port = yconfig['fritzbox']['port']
        self.ca_cert = None
        if 'ca-cert' in yconfig['fritzbox']:
            self.ca_cert = yconfig['fritzbox']['ca-cert']
        self.target_path = yconfig['fritzbox']['target_path']
        self.username = yconfig['fritzbox']['username']
        self.password = yconfig['fritzbox']['password']
        self.gpg_passphrase = yconfig['gpg_passphrase']
        self.directories = yconfig.get('directories', [])
        self.nextcloud = yconfig.get('nextcloud', [])
        self.btrfs = yconfig.get('btrfs', [])

        self.debug = 'debug' in yconfig
        self._config_logging()

    def _config_logging(self):
        level = logging.INFO
        timeform = '%a, %d %b %Y %H:%M:%S'
        logform = '%(asctime)s %(levelname)-8s %(message)s'
        if self.debug:
            level = logging.DEBUG
        logging.basicConfig(level=level, datefmt=timeform, format=logform)


class FritzBackup(object):

    def __init__(self, config_root=os.path.expanduser('~/.fritzbackup')):
        self.config = Configuration(config_root)
        self._check_executable('duplicity')
        self._check_executable('lftp')

    @staticmethod
    def _check_executable(name):
        if shutil.which(name) is None:
            raise ValueError('Command {} not found. you need to install it first!'.format(name))

    def backup_directory(self, name, source_path, subdir=DIRECTORIES_FOLDER):
        print('backing up directory {}: {}'.format(name, source_path))
        ftp_url = 'ftp://{}@{}:{}/{}/{}/{}'.format(self.config.username,
                                                   self.config.fritzbox_url,
                                                   self.config.fritzbox_port,
                                                   self.config.target_path,
                                                   subdir, name)
        new_env = os.environ.copy()
        new_env['FTP_PASSWORD'] = self.config.password
        new_env['PASSPHRASE'] = self.config.gpg_passphrase
        cmd = ['duplicity', source_path, ftp_url]
        if self.config.ca_cert is not None:
            cmd.append('--ssl-cacert-file {}'.format(self.config.ca_cert))
        _LOGGER.debug('executing command: %s', ' '.join(cmd))
        subprocess.check_call(cmd, env=new_env)

    def backup_nextcloud(self, name, url, username, password, local_cache_dir=None):
        self._check_executable('owncloudcmd')
        if local_cache_dir is None:
            local_cache_dir = os.path.join(self.config.cache_dir, NEXTCLOUD_FOLDER, name)
        else:
            local_cache_dir = os.path.expanduser(local_cache_dir)
        os.makedirs(local_cache_dir, exist_ok=True)
        _LOGGER.info('backup up nextcloud folder %s: %s', name, url)
        nextcloud_cmd = 'owncloudcmd -u {} -p {} {} {}'.format(username, password, local_cache_dir, url)
        _LOGGER.debug('running command %s', nextcloud_cmd.replace(password, "<passwd>"))
        subprocess.check_call(nextcloud_cmd, shell=True)
        self.backup_directory(name, local_cache_dir, subdir=NEXTCLOUD_FOLDER)

    @staticmethod
    def _remove_dir(mount_dir):
        if not os.path.exists(mount_dir):
            return
        _LOGGER.debug('removing temp dir: %s', mount_dir)
        umount_cmd = ['fusermount', '-u "{}"'.format(mount_dir)]
        subprocess.check_call(umount_cmd)
        os.remove(mount_dir)

    def run(self):
        for directory in self.config.directories:
            self.backup_directory(directory['name'], directory['path'])
        for nextcloud in self.config.nextcloud:
            self.backup_nextcloud(nextcloud['name'], nextcloud['url'], nextcloud['username'],
                                  nextcloud['password'], nextcloud.get('local_cache_dir'))
        for btrfs in self.config.btrfs:
            bb = BackupBtrfs(self.config)
            bb.backup(btrfs['name'], btrfs['mount_point'])

    def list_backups(self):
        # TODO: directories and nextcloud
        backups = []
        for btrfs in self.config.btrfs:
            bb = BackupBtrfs(self.config)
            backups.extend(bb.list_backups(btrfs['name']))
        return backups

    def restore_btrfs(self, name, snapshot, mount_point):
        bb = BackupBtrfs(self.config)
        bb.restore(name, snapshot, mount_point)

