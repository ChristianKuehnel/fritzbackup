# fritzbackup
scripts to backup data to a USB drive attached to a Fritz!Box

## Config file example
```yaml
# configuration of your fritz box to backup to
# this can also be a Fritz!Box your connected to via VPN
fritzbox:
  url: <url of your fritz box>
  target_path: <root dir on Fritz!NAS, where to store the files>

gpg_passphrase: <your gpg passphrase>

# create backup of local directories
directories:
  - name: some_folder
    path: /home/myuser/some_folder

# create backups of the files stored in a nextcloud account
nextcloud:
  - name: my_nextcloud_account
    url: <nextcloud url>
    username: <nextcloud user name>
    password: <nextcloud password
    # optional: set directory where nextfloud files shall be cached locally
    #local_cache_dir: ~/tmp/nextcloud

# enable more log output on console
# debug:

```