#!/usr/bin/env python3
#
# Copyright 2016 Casey Marshall
# Copyright 2017 Ghent University
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import json
import os
import shutil
from subprocess import check_call

from charmhelpers.core.hookenv import (
    status_set,
    close_port,
    open_port,
    resource_get,
    config,
)
from charmhelpers.core.host import (
    add_group,
    adduser,
    user_exists,
    group_exists,
    service_running,
    service_start,
    service_stop,
    service_restart,
)

from charmhelpers.core.templating import render
from charmhelpers.payload.archive import extract_tarfile
from charmhelpers.core.unitdata import kv

from charms.reactive import (
    hook,
    when,
    when_not,
    set_state,
    remove_state,
)

from charms.layer.nginx import configure_site  # pylint:disable=E0611,E0401
from charms.layer import lets_encrypt  # pylint:disable=E0611,E0401


@hook('upgrade-charm')
def upgrade_charm():
    if service_running("mattermost"):
        service_stop("mattermost")
    remove_state('mattermost.installed')


@when_not('mattermost.installed')
def install_mattermost():
    """Grab the mattermost binary, unpack, install
    to /srv.
    """

    status_set('maintenance', "Installing Mattermost")

    # Create mattermost user & group if not exists
    if not group_exists('mattermost'):
        add_group("mattermost")
    if not user_exists('mattermost'):
        adduser("mattermost", system_user=True)

    # Get and uppack resource
    if os.path.exists('/opt/mattermost'):
        shutil.rmtree('/opt/mattermost')

    mattermost_bdist = resource_get('bdist')
    extract_tarfile(mattermost_bdist, destpath="/srv")

    # Create data + log + config dirs
    for folder in ("data", "logs", "config"):
        os.makedirs(os.path.join("/opt/mattermost", folder), mode=0o700,
                    exist_ok=True)
        shutil.chown(os.path.join("/opt/mattermost", folder), user="mattermost",
                     group="mattermost")

    # Render systemd template
    render(source="mattermost.service.tmpl",
           target="/etc/systemd/system/mattermost.service",
           perms=0o644,
           owner="root",
           context={})
    check_call(['systemctl', 'daemon-reload'])
    set_state('mattermost.installed')
    status_set('active', 'Mattermost installation complete')


@hook('config-changed')
def config_changed():
    conf = config()
    setup()

    # If fqdn has changed, need to rewrite the nginx config as well.
    if conf.changed('fqdn'):
        remove_state('mattermost.web.configured')
    # If fqdn is configured, enable LE
    if conf.get('fqdn'):
        remove_state('lets-encrypt.disabled')


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
    with open("/opt/mattermost/config/config.json", "r") as f:
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

    with open("/opt/mattermost/config/config.json", "w") as f:
        json.dump(config_file, f)

    restart_service()
    status_set('active', 'Mattermost configured')


@when('nginx.available', 'lets-encrypt.registered',
      'mattermost.initialized')
@when_not('mattermost.web.configured')
def configure_webserver_le():
    """Configure nginx
    """

    status_set('maintenance', 'Configuring website')
    fqdn = config().get('fqdn')
    live = lets_encrypt.live()
    configure_site('mattermost', 'mattermost.nginx.tmpl',
                   key_path=live['privkey'],
                   crt_path=live['fullchain'], fqdn=fqdn)
    open_port(80)
    open_port(443)
    close_port(8065)
    restart_service('nginx')
    status_set('active', 'Mattermost available: https://%s' % fqdn)
    set_state('mattermost.web.configured')


def restart_service(name='mattermost'):
    if service_running(name):
        service_restart(name)
    else:
        service_start(name)


@when('website.available')
def setup_website(website):
    set_state('lets-encrypt.disable')
    close_port(80)
    close_port(443)
    open_port(8065)
    website.configure(8065)
