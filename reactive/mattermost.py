import json
import os
import shutil
import socket

from charms.reactive import (
    hook,
    when,
    when_not,
    set_state,
    remove_state
)

from charmhelpers.core.hookenv import (
    status_set,
    close_port,
    open_port,
    unit_public_ip,
    unit_private_ip,
    resource_get,
    config,
    local_unit
)

from charmhelpers.core.host import (
    add_group,
    adduser,
    user_exists,
    group_exists,
    service_running,
    service_start,
    service_stop,
    service_restart
)

from charmhelpers.core.templating import render
from charmhelpers.payload.archive import extract_tarfile
from charmhelpers.core.unitdata import kv

from charms.layer.nginx import configure_site
from charms import layer


@hook('upgrade-charm')
def upgrade_charm():
    if service_running("mattermost"):
        service_stop("mattermost")
        remove_state('mattermost.installed')


@when_not('mattermost.installed')
def install_mattermost():
    """Grab the mattermost binary, unpack, install
    to /opt.
    """

    status_set('maintenance', "Installing Mattermost")

    # Create mattermost user & group if not exists
    if not group_exists('mattermost'):
        add_group("mattermost")
    if not user_exists('mattermost'):
        adduser("mattermost", system_user=True)

    # Get and uppack resource
    if os.path.exists('/srv/mattermost'):
        shutil.rmtree('/srv/mattermost')

    mattermost_bdist = resource_get('bdist')
    extract_tarfile(mattermost_bdist, destpath="/srv")

    # Create data + log + config dirs
    for dir in ("data", "logs", "config"):
        os.makedirs(os.path.join("/srv/mattermost", dir), mode=0o700,
                    exist_ok=True)
        shutil.chown(os.path.join("/srv/mattermost", dir), user="mattermost",
                     group="mattermost")

    # Render systemd template
    render(source="mattermost.service.tmpl",
           target="/etc/systemd/system/mattermost.service",
           perms=0o644,
           owner="root",
           context={})
    set_state('mattermost.installed')
    status_set('active', 'Mattermost installation complete')


@hook('config-changed')
def config_changed():
    conf = config()
    if conf.changed('port') and conf.previous('port'):
        close_port(conf.previous('port'))
    if conf.get('port'):
        open_port(conf['port'])
    setup()


@when_not('mattermost.db.available')
@when('db.master.available')
def get_set_db_data(db):
    unit_data = kv()
    unit_data.set('db', db.master.uri)
    set_state('mattermost.db.available')


@when('mattermost.db.available', 'mattermost.installed')
@when_not('mattermost.initialized')
def configure_mattermost():
    """Call setup
    """
    setup()
    set_state("mattermost.initialized")


def setup():
    """Gather and write out mattermost configs
    """

    unit_data = kv()
    db = unit_data.get('db')
    if not db:
        status_set('blocked', 'need relation to postgresql')
        return

    conf = config()
    with open("/srv/mattermost/config/config.json", "r") as f:
        config_file = json.load(f)

    # Config options
    svcconf = config_file.setdefault("ServiceSettings", {})
    svcconf['ListenAddress'] = ':8065'

    teamconf = config_file.setdefault("TeamSettings", {})
    teamconf['SiteName'] = conf['site_name']

    # Database
    sqlconf = config_file.setdefault("SqlSettings", {})
    sqlconf['DriverName'] = 'postgres'
    sqlconf['DataSource'] = '%s?sslmode=disable&connect_timeout=10' % db

    with open("/srv/mattermost/config/config.json", "w") as f:
        json.dump(config_file, f)

    restart_service()
    status_set('active', 'Mattermost configured')


@when('certificates.available')
def send_data(tls):
    # Use the public ip of this unit as the Common Name for the certificate.
    common_name = unit_public_ip()
    # Get a list of Subject Alt Names for the certificate.
    sans = []
    sans.append(unit_public_ip())
    sans.append(unit_private_ip())
    sans.append(socket.gethostname())
    # Create a path safe name by removing path characters from the unit name.
    certificate_name = local_unit().replace('/', '_')
    # Send the information on the relation object.
    tls.request_server_cert(common_name, sans, certificate_name)


@when('certificates.server.cert.available')
@when_not('mattermost.ssl.available')
def save_crt_key(tls):
    '''Read the server crt/key from the relation object and
    write to /etc/ssl/certs'''

    opts = layer.options('tls-client')
    crt = opts.get('server_certificate_path')
    key = opts.get('server_key_path')
    # Set location of crt/key in unitdata
    unit_data = kv()
    unit_data.set('crt_path', crt)
    unit_data.set('key_path', key)
    # Remove the crt/key if they pre-exist
    if os.path.exists(crt):
        os.remove(crt)
    if os.path.exists(key):
        os.remove(key)
    # Get and write out crt/key
    server_cert, server_key = tls.get_server_cert()
    with open(crt, 'w') as crt_file:
        crt_file.write(server_cert)
    with open(key, 'w') as key_file:
        key_file.write(server_key)

    status_set('active', 'TLS crt/key ready')
    set_state('mattermost.ssl.available')


@when('nginx.available', 'mattermost.ssl.available',
      'mattermost.initialized')
@when_not('mattermost.web.configured')
def configure_webserver():
    """Configure nginx
    """

    unit_data = kv()

    status_set('maintenance', 'Configuring website')
    configure_site('mattermost', 'mattermost.nginx.tmpl',
                   key_path=unit_data.get('key_path'),
                   crt_path=unit_data.get('crt_path'), fqdn=config('fqdn'))
    open_port(443)
    restart_service()
    status_set('active', 'Mattermost available: %s' % unit_public_ip())
    set_state('mattermost.web.configured')


def restart_service():
    if service_running("mattermost"):
        service_restart("mattermost")
    else:
        service_start("mattermost")


@when('website.available')
def setup_website(website):
    conf = config()
    website.configure(conf['port'])
