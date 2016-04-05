import os
import shutil

from charms.reactive import hook, when, when_not, set_state, remove_state, is_state
from charmhelpers.core import hookenv
from charmhelpers.core.host import add_group, adduser, service_running, service_start, service_restart
from charmhelpers.core.templating import render
from charmhelpers.fetch import archiveurl, apt_install, apt_update
from charmhelpers.payload.archive import extract_tarfile


INSTALL_URL="https://github.com/mattermost/platform/releases/download/v2.1.0/mattermost.tar.gz"


@hook('install')
def install():
    handler = archiveurl.ArchiveUrlFetchHandler()
    handler.download(INSTALL_URL, dest='/opt/mattermost.tar.gz')

    extract_tarfile('/opt/mattermost.tar.gz', destpath="/opt")
 
    # Create mattermost user & group
    add_group("mattermost")
    adduser("mattermost", system_user=True)
    
    os.makedirs("/opt/mattermost/data", mode=0o700, exist_ok=True)
    shutil.chown("/opt/mattermost/data", user="mattermost", group="mattermost")
    os.makedirs("/opt/mattermost/logs", mode=0o700, exist_ok=True)
    shutil.chown("/opt/mattermost/logs", user="mattermost", group="mattermost")

    render(source='upstart',
        target="/etc/init/mattermost.conf",
        perms=0o644,
        context={})

    hookenv.open_port(8065)


@when("db.database.available")
def setup(db):
    conf = hookenv.config()
    render(source='config.json',
        target="/opt/mattermost/config/config.json",
        perms=0o644,
        context={
            'conf': conf,
            'db': db,
        })
    remove_state("db.database.available")
    restart_service()


def restart_service():
    if service_running("mattermost"):
        service_restart("mattermost")
    else:
        service_start("mattermost")
