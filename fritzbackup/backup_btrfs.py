import os
from subprocess import check_call, PIPE, Popen
from datetime import datetime
import logging
from collections import deque
import io
import ftplib

_LOGGER = logging.getLogger(__name__)
DATEFORMAT = '%Y-%m-%d_%H-%M-%S'
SNAPSHOT_PREFIX = 'fritzbackup'
SIZE_1_MB = 1024*1024
SIZE_25_MB = 25*SIZE_1_MB
BTRFS_DIR = 'btrfs'


class BackupBtrfs(object):

    def __init__(self, config):
        self.config = config
        # TODO: check if we are root

    def backup(self, name, mount_point, keep_snapshots=3):
        mount_point = os.path.abspath(mount_point)
        if not os.path.exists(mount_point):
            raise ValueError('mount point does not exist: {}'.format(mount_point))
        snapshot_name = '{}_{}'.format(SNAPSHOT_PREFIX, datetime.now().strftime(DATEFORMAT))
        last_snapshot = self.get_last_snapshot(mount_point)
        _LOGGER.debug('last snapshot was: %s', last_snapshot)
        self.create_snapshot(mount_point, snapshot_name)
        self.backup_snapshot(name, mount_point, last_snapshot, snapshot_name)
        self.delete_old_snapshots(mount_point, keep_snapshots)

    def create_snapshot(self, mount_point, snapshot_name):
        snapshot_root = self._get_snapshot_root(mount_point)
        os.makedirs(snapshot_root, exist_ok=True)
        snapshot_path = os.path.join(snapshot_root, snapshot_name)
        _LOGGER.info('Creating snapshot of %s in %s', mount_point, snapshot_path)
        cmd = 'btrfs subvolume snapshot -r {} {}'.format(mount_point, snapshot_path)
        _LOGGER.debug('running command: %s', cmd)
        check_call(cmd, shell=True)

    def _get_snapshot_root(self, mount_point):
        return os.path.join(mount_point, 'snapshots')

    def get_last_snapshot(self, mount_point):
        snapshots = self.get_snapshots(mount_point)
        if len(snapshots) == 0:
            return None
        return snapshots[-1]

    def get_snapshots(self, mount_point):
        try:
            snapshots = os.listdir(self._get_snapshot_root(mount_point))
        except FileNotFoundError:
            return []
        snapshots = [s for s in snapshots if s.startswith(SNAPSHOT_PREFIX)]
        return sorted(snapshots)

    def backup_snapshot(self, name, mount_point, last_snapshot, current_snapshot, max_file_size=SIZE_25_MB):
        current_path = os.path.join(self._get_snapshot_root(mount_point), current_snapshot)
        if last_snapshot is not None:
            _LOGGER.info('backing up diff between %s and %s', last_snapshot, current_snapshot)
            last_path = os.path.join(self._get_snapshot_root(mount_point), last_snapshot)
            cmd = 'btrfs send -p {} {}'.format(last_path, current_path)  # TODO: add gzip and gpg
            backup_type ='incremental'
        else:
            cmd = 'btrfs send {}'.format(current_path)  # TODO: add gzip and gpg
            backup_type = 'full'
        _LOGGER.debug('running command: %s', cmd)
        ftp = ftplib.FTP()
        ftp.connect(self.config.fritzbox_url, self.config.fritzbox_port)
        ftp.login(self.config.username, self.config.password)
        self._make_ch_dirs(ftp, deque([self.config.target_path, BTRFS_DIR, name]))

        proc = Popen(cmd, shell=True, stdout=PIPE)
        file_size = 0
        total_size = 0
        file_count = 0
        while True:
            io_buffer = io.BytesIO()
            while True:
                next_buffer_size = min(SIZE_1_MB, max_file_size - file_size)
                buffer = proc.stdout.read(next_buffer_size)
                if buffer is None or proc.poll() is not None or file_size >= max_file_size:
                    break
                io_buffer.write(buffer)
                file_size += len(buffer)
                total_size += len(buffer)
            io_buffer.seek(0)
            filename = '{}_{}_{:03d}'.format(current_snapshot, backup_type, file_count)
            ftp.storbinary('STOR {}'.format(filename), io_buffer)
            file_size = 0
            file_count += 1
            io_buffer.close()
            if proc.poll() is not None:
                break
        _LOGGER.info("Transfered %d bytes", total_size)

    def delete_old_snapshots(self, mount_point, num_keep_snapshots):
        snapshots = deque(self.get_snapshots(mount_point))
        while len(snapshots) > num_keep_snapshots:
            snapshot = snapshots.popleft()
            snapshot_path = os.path.join(self._get_snapshot_root(mount_point), snapshot)
            _LOGGER.info('Deleting old snapshot %s', snapshot_path)
            cmd = 'btrfs property set -ts {} ro false'.format(snapshot_path)
            _LOGGER.debug('running command: %s', cmd)
            check_call(cmd, shell=True)

            cmd = 'btrfs subvolume delete {}'.format(snapshot_path)
            _LOGGER.debug('running command: %s', cmd)
            check_call(cmd, shell=True)

    @staticmethod
    def _make_ch_dirs(ftp, dir_list):
        """Changedir on ftp server, create missing directories on the go."""
        if len(dir_list) == 0:
            return
        next_dir = dir_list.popleft()
        try:
            files = ftp.nlst()
        except ftplib.error_perm as e:
            if str(e).startswith("550 "):
                files = []
            else:
                raise
        if next_dir not in files:
            ftp.mkd(next_dir)
        ftp.cwd(next_dir)
        BackupBtrfs._make_ch_dirs(ftp, dir_list)

    def list_backups(self):
        # TODO
        pass

    def restore_backup(self):
        # TODO
        pass