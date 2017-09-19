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
import re
import shutil
from subprocess import check_call, check_output
import datetime

from charmhelpers.core.hookenv import (
    status_set,
    close_port,
    open_port,
    resource_get,
    config,
    unit_public_ip,
    application_version_set,
)
from charmhelpers.core.host import (
    add_group,
    adduser,
    user_exists,
    group_exists,
    service_running,
    service_stop,
    service_restart,
    chownr,
)

from charmhelpers.core.templating import render
from charmhelpers.payload.archive import extract_tarfile

from charms.reactive import (
    hook,
    when,
    when_not,
    set_state,
    remove_state,
    when_file_changed,
)

from charms.layer.nginx import configure_site  # pylint:disable=E0611,E0401
from charms.layer import lets_encrypt  # pylint:disable=E0611,E0401


# HANDLERS FOR INSTALLATION

@hook(
    'upgrade-charm',
    'resource-changed')
def upgrade_charm():
    print("Upgrading mattermost setup.")
    if service_running("mattermost"):
        service_stop("mattermost")
    remove_state('mattermost.installed')
    remove_state('mattermost.backend.started')


@when_not('mattermost.installed')
def install():
    print("[re]installing mattermost.")
    status_set('maintenance', "Installing Mattermost")
    _install_mattermost()
    set_state('mattermost.installed')


# HANDLERS FOR BACKEND & POSTGRES


@when('mattermost.installed')
@when_not('postgres.master.available')
def set_blocked():
    print("No postgres. Signalling this.")
    service_stop('mattermost')
    remove_state('mattermost.backend.started')
    close_port(8065)
    close_port(config().get('port'))
    close_port(443)
    status_set('blocked', 'Need relation to postgres')


@when(
    'mattermost.installed',
    'postgres.master.available', )
@when_not('mattermost.backend.started')
def setup_mattermost_backend(postgres_relation):
    print("Configuring and starting backend service.")
    _configure_mattermost_postgres(postgres_relation.master.uri)
    service_restart('mattermost')
    # Set build number for Juju status
    output = check_output(['/opt/mattermost/bin/platform', 'version'],
                          cwd='/opt/mattermost/bin/',
                          universal_newlines=True)
    build_number = re.search(r'Build Number: ([0-9]+.[0-9]+.[0-9])+\n', output).group(1)
    application_version_set(build_number)
    open_port(8065)
    # The next two aren't really open. This is a fix for the following issue:
    #    no expose possible before `open-port`.
    #    no `open-port` of 80 and 443 before ssl.
    #    no ssl certificate before `expose`.
    open_port(config().get('port'))
    open_port(443)
    status_set(
        'active',
        'Ready (http://{}:8065 [Insecure! Please set fqdn!])'.format(unit_public_ip()))
    set_state('mattermost.backend.started')


@when('mattermost.backend.started')
@when_file_changed('/opt/mattermost/config/config.json')
def restart_mattermost():
    print("Mattermost config changed. Restarting.")
    service_restart('mattermost')


@when(
    'website.available',
    'mattermost.backend.started', )
def setup_website_relation(website):
    print("Connection to reverse proxy established. Sending information.")
    website.configure(8065)


# HANDLERS FOR REVERSE PROXY + HTTPS SETUP


@when('config.changed.fqdn')
def signal_reverseproxy_update():
    print("FQDN changed.")
    conf = config()
    if conf.get('fqdn') and conf.get('fqdn') != "":
        print("FQDN set, signaling that we need a [new] cert")
        remove_state('lets-encrypt.disabled')
        remove_state('lets-encrypt.registered')
        remove_state('mattermost.nginx.configured')


@when(
    'nginx.available',
    'lets-encrypt.registered')
@when_not(
    'mattermost.nginx.configured')
def configure_nginx():
    print("Configuring NGINX reverse proxy and https endpoint.")
    fqdn = config().get('fqdn')
    live = lets_encrypt.live()
    configure_site('mattermost', 'mattermost.nginx.tmpl',
                   key_path=live['privkey'],
                   crt_path=live['fullchain'], fqdn=fqdn)
    set_state('mattermost.nginx.configured')


@when(
    'mattermost.backend.started',
    'mattermost.nginx.configured', )
@when_not('mattermost.nginx.started')
def start_mattermost_nginx():
    print("Starting NGINX reverseproxy and https endpoint.")
    service_restart('nginx')
    open_port(config().get('port'))
    open_port(443)
    status_set('active', 'Ready (https://{})'.format(config().get('fqdn')))
    set_state('mattermost.nginx.started')


# HELPER FUNCTIONS FOR MATTERMOST


def _install_mattermost():
    # Backup existing installation if it exists
    backup_path = None
    if os.path.isdir('/opt/mattermost'):
        backup_path = "/opt/mattermost.back{}".format(str(datetime.datetime.now()))
        shutil.move('/opt/mattermost', backup_path)
    # Create mattermost user & group if not exists
    if not group_exists('mattermost'):
        add_group("mattermost")
    if not user_exists('mattermost'):
        adduser("mattermost", system_user=True)
    # Get and uppack resource
    mattermost_bdist = resource_get('bdist')
    extract_tarfile(mattermost_bdist, destpath="/opt")
    # Create data + log + config dirs
    for folder in ("data", "logs", "config"):
        os.makedirs("/opt/mattermost/{}".format(folder),
                    mode=0o700,
                    exist_ok=True)
    # Render systemd template
    render(source="mattermost.service.tmpl",
           target="/etc/systemd/system/mattermost.service",
           perms=0o644,
           owner="root",
           context={})
    check_call(['systemctl', 'daemon-reload'])
    if backup_path:
        shutil.move(
            '{}/config/config.json'.format(backup_path),
            '/opt/mattermost/config/config.json')
        shutil.move(
            '{}/data'.format(backup_path),
            '/opt/mattermost/')
    chownr("/opt/mattermost", "mattermost", "mattermost")


def _update_config(site_name):
    """Gather and write out mattermost configs
    """
    with open("/opt/mattermost/config/config.json", "r") as f:
        config_file = json.load(f)
    # Config options
    svcconf = config_file.setdefault("ServiceSettings", {})
    svcconf['ListenAddress'] = ':8065'
    teamconf = config_file.setdefault("TeamSettings", {})
    teamconf['SiteName'] = site_name
    with open("/opt/mattermost/config/config.json", "w") as f:
        json.dump(config_file, f)


def _configure_mattermost_postgres(postgres_uri):
    with open("/opt/mattermost/config/config.json", "r") as f:
        config_file = json.load(f)
    sqlconf = config_file.setdefault("SqlSettings", {})
    sqlconf['DriverName'] = 'postgres'
    sqlconf['DataSource'] = '{}?sslmode=disable&connect_timeout=10'.format(postgres_uri)
    with open("/opt/mattermost/config/config.json", "w") as f:
        json.dump(config_file, f, sort_keys=True, indent=4, separators=(',', ': '))
