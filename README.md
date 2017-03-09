# How to use

## Basic unsecured mattermost instance

Deploy and connect Mattermost and PorsgreSQL for a basic Mattermost setup.

```bash
# Deploy mattermost and postgres
juju deploy cs:~tengu-team/mattermost
juju deploy cs:postgres
# Connect the two
juju add-realtion mattermost postgres:db
# Make mattermost publicly available
juju expose mattermost
```

Check the deployment status (press <kbd>ctrl</kbd>-<kbd>c</kbd> to exit)

    watch -c juju status --color

```
Unit                  Workload  Agent  Machine  Public address  Ports                     Message
mattermost/2*         active    idle    0       172.28.0.50     80/tcp,443/tcp,8065/tcp   Ready (http://172.28.0.50:8065 [Insecure! Please set fqdn!])
postgresql/2*         active    idle    1       172.28.0.31     5432/tcp                  Live master (9.5.6)
```
This is a basic insecure mattermost setup ideal for testing. All your traffic can be sniffed so **never use this in production**. Surf to the url from the message to get started. The first thing you'll need to do is to create an account. This account will be the admin user of mattermost. After installation, Mattermost runs in "Preview mode". Email and push notifications will be disabled. Add email settings in the admin console to get mattermost out of preview mode.

## Secure mattermost using a Let's Encrypt certificate

You need to have a DNS entry pointing to the mattermost unit to make it secure. The mattermost instance will request a Let's Encrypt https certificate to secure itself. Tell the mattermost instance its DNS name using the fqdn config option.

```bash
# Expose mattermost (this is needed for certificate request)
juju expose mattermost
# Tell mattermost what DNS name points to it.
juju config mattermost fqdn=mattermost.example.com
```

This will give you a secure mattermost instance that is publicly available by surfing to `https://mattermost.example.com`. If registration fails, check:

- That you've exposed mattermost. Let's Encrypt needs to connect to ports 80 and 443 as part of the registration process.
- That the DNS name has had time to propagate and cached entries have expired.
- That the DNS name is allowed by Let's Encrypt. Some names, like the dynamic ones given to EC2 instances, may not be allowed.

## How to upgrade Mattermost

Upgrade mattermost by giving it the tarball of the new Mattermost release. You can find these tarballs here: https://about.mattermost.com/download/. Download the file to your laptop and send it to the Mattermost instance using `juju attach`.

```bash
juju attach charm-name bdist=/path/to/mattermost.tar.gz
```

The Mattermost config and userdata will not be overwritten during an upgrade. Previous mattermost versions will be saved on the Mattermost instance. You can revert to the previous version using `juju run-action mattermost/0 revert-mattermost`. Check the status of the revert using `juju show-action-output <uid>`.

## How to rever

## Advanced: Mattermost behind a reverse proxy

Mattermost exposes the `http` interface that can be used to connect other Charms to mattermost. Other Charms will always connect using the insecure http interface since the reverse proxy will also be the https endpoint in a typical deployment.

```bash
# Deploy Mattermost, Postgres and the HAProxy reverse proxy.
juju deploy cs:~tengu-team/mattermost
juju deploy postgresql
juju deploy haproxy
# Connect Mattermost to Postgres
juju add-relation postgresql:db mattermost:db
# Connect Mattermost to the reverse proxy.
juju add-relation haproxy mattermost
# Add ssl config to haproxy
# ...
```



# License

Copyright 2016 Casey Marshall.
Copyright 2017 Ghent University.

The [copyright](copyright) file contains the software license for this charm.

Mattermost is a trademark of Mattermost, Inc.

## Disclaimer

This charm automates installation, configuration and management of a Mattermost server based on publicly documented best practices. This charm is not a part of the Mattermost product, is not endorsed by, and does not represent Mattermost, Inc. in any way.

See the [Mattermost](http://www.mattermost.org/) website for more information
about the licenses and trademarks applicable to the software installed by this
charm.

# Contact Information

This software was created in the [IDLab research group](https://www.ugent.be/ea/idlab) of [Ghent University](https://www.ugent.be) in Belgium. This software is used in [Tengu](https://tengu.io), a project that aims to make experimenting with data frameworks and tools as easy as possible.

 - Merlijn Sebrechts <merlijn.sebrechts@gmail.com>
