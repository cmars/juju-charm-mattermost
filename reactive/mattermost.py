import json
import os
import shutil

from charms.reactive import hook, when, when_not, set_state, remove_state, is_state
from charmhelpers.core import hookenv
from charmhelpers.core.host import add_group, adduser, service_running, service_start, service_restart
from charmhelpers.core.templating import render
from charmhelpers.fetch import archiveurl, apt_install, apt_update
from charmhelpers.payload.archive import extract_tarfile
from charmhelpers.core.unitdata import kv


@hook('install')
def install():
    conf = hookenv.config()
    version = conf['version']
    install_url = conf['install_url']

    handler = archiveurl.ArchiveUrlFetchHandler()
    handler.download(install_url % conf, dest='/opt/mattermost.tar.gz')

    extract_tarfile('/opt/mattermost.tar.gz', destpath="/opt")

    # Create mattermost user & group
    add_group("mattermost")
    adduser("mattermost", system_user=True)

    for dir in ("data", "logs", "config"):
        os.makedirs(os.path.join("/opt/mattermost", dir), mode=0o700, exist_ok=True)
        shutil.chown(os.path.join("/opt/mattermost", dir), user="mattermost", group="mattermost")

    render(source='upstart',
        target="/etc/init/mattermost.conf",
        perms=0o644,
        context={})
    hookenv.status_set('maintenance', 'installation complete')


@hook('config-changed')
def config_changed():
    conf = hookenv.config()
    if conf.changed('port') and conf.previous('port'):
        hookenv.close_port(conf.previous('port'))
    if conf.get('port'):
        hookenv.open_port(conf['port'])
    setup()


@when("db.database.available")
def db_available(db):
    unit_data = kv()
    unit_data.set('db', {
        'host': db.host(),
        'port': db.port(),
        'user': db.user(),
        'password': db.password(),
        'database': db.database(),
    })
    setup()
    remove_state("db.database.available")


def setup():
    unit_data = kv()
    db = unit_data.get('db')
    if not db:
        hookenv.status_set('blocked', 'need relation to postgresql')
        return

    conf = hookenv.config()
    with open("/opt/mattermost/config/config.json", "r") as f:
        config = json.load(f)

    # Config options
    svcconf = config.setdefault("ServiceSettings", {})
    svcconf['ListenAddress'] = ':%d' % (conf['port'])

    teamconf = config.setdefault("TeamSettings", {})
    teamconf['SiteName'] = conf['site_name']
    
    # Database
    sqlconf = config.setdefault("SqlSettings", {})
    sqlconf['DriverName'] = 'postgres'
    sqlconf['DataSource'] = 'postgres://%(user)s:%(password)s@%(host)s:%(port)s/%(database)s?sslmode=disable&connect_timeout=10' % db

    with open("/opt/mattermost/config/config.json", "w") as f:
        json.dump(config, f)
    remove_state("db.database.available")

    restart_service()
    hookenv.status_set('active', 'ready')


def restart_service():
    if service_running("mattermost"):
        service_restart("mattermost")
    else:
        service_start("mattermost")


@when('website.available')
def setup_website(website):
    conf = hookenv.config()
    website.configure(conf['port'])
