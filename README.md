# Description

This Charm installs and manages Mattermost, an Open source, private cloud Slack-alternative.

* Workplace messaging for web, PCs and phones.
* MIT-licensed. Hundreds of contributors. 11 languages.
* Secure, configurable, and scalable from teams to enterprise.

![Mattermost screenshot](https://raw.githubusercontent.com/tengu-team/layer-mattermost/master/files/mattermost-screenshot.png)

# How to use

## Basic insecure mattermost instance

Deploy and connect Mattermost and PostgreSQL for a basic Mattermost testing setup.

```bash
# Deploy mattermost and postgres
juju deploy cs:~tengu-team/mattermost
juju deploy postgresql
# Connect the two
juju add-relation mattermost postgresql:db
# Make mattermost publicly available
juju expose mattermost
```

Check the deployment status with `watch -c juju status --color` (press <kbd>ctrl</kbd>-<kbd>c</kbd> to exit).

```text
Unit                  Workload  Agent  Machine  Public address  Ports                     Message
mattermost/2*         active    idle    0       172.28.0.50     80/tcp,443/tcp,8065/tcp   Ready (http://172.28.0.50:8065 [Insecure! Please set fqdn!])
postgresql/2*         active    idle    1       172.28.0.31     5432/tcp                  Live master (9.5.6)
```

This is a basic insecure mattermost setup ideal for testing. All your traffic can be sniffed so **never use this in production**. Surf to the url from the message to get started. The first thing you'll need to do is to create an account. This account will be the admin user of mattermost. After installation, Mattermost runs in "Preview mode". Email and push notifications will be disabled. Add email settings in the admin console to get mattermost out of preview mode.

## Secure mattermost using Let's Encrypt

You need to have a DNS entry pointing to the mattermost unit to make it secure. The mattermost instance will request a Let's Encrypt https certificate to secure itself. Tell the mattermost instance its DNS name using the fqdn config option.

```bash
# Expose mattermost (this is needed for certificate request)
juju expose mattermost
# Tell mattermost what DNS name points to it.
juju config mattermost fqdn=mattermost.example.com
```

This will give you a secure mattermost instance that is publicly available by surfing to `https://mattermost.example.com`. If registration fails, check:

* That you've exposed mattermost. Let's Encrypt needs to connect to ports 80 and 443 as part of the registration process.
* That the DNS name has had time to propagate and cached entries have expired.
* That the DNS name is allowed by Let's Encrypt. Some names, like the dynamic ones given to EC2 instances, may not be allowed.

## Upgrade Mattermost

Upgrade mattermost by giving it the tarball of the new Mattermost release. You can find these tarballs here: https://about.mattermost.com/download/. Download the file to your laptop and send it to the Mattermost instance using `juju attach`.

```bash
juju attach charm-name bdist=/path/to/mattermost.tar.gz
```

The Mattermost config and userdata will not be overwritten during an upgrade. Previous mattermost versions will be saved on the Mattermost instance. You can revert to the previous version using `juju run-action mattermost/0 revert-mattermost`. Check the status of the revert using `juju show-action-output <uid>`.

## How to import Slack History

Mattermost allows you to import your complete Slack history. You get your complete Slack history even if you are on a free plan. More information: https://docs.mattermost.com/administration/migrating.html#migrating-from-slack

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

<!--

## How to create a backup

To have a full back-up of mattermost instance, you need to back-up the following things.

 - `/opt/mattermost/config/config.json`
 - `/opt/mattermost/data/`
 - A backup of the postgres database.

sudo tar -zcvf mattermost-data-backup.tar.gz /opt/mattermost/data/

```bash
sudo cp -r /opt/mattermost/data/ .
sudo cp /opt/mattermost/config/config.json .
# Now get the files with
# juju scp mattermost/0:~/config.json .
# juju scp -- -r mattermost/0:~/data/ .
```


I'll explain two ways to backup the postgres database: An SQL dump and a Write Ahaid Log for Point In Time Recovery.

**SQL Dump**

An SQL dump is the most portable dumping mechanism. Restoring an SQL dump to a Postgres instance with a higher version or a different processor architecture should work without any isues. An SQL dump is internally consistent. The dump represents a snapshot of the database at the time the dump starts. A dump doesn't block other operations on the database while dumping, but these operations won't be included in the dump.

```bash
juju ssh postgresql/0
sudo su - postgres
psql
```

You see the following output.

```
postgres@juju-c23533-0-lxd-0:~$ psql
psql (9.5.6)
Type "help" for help.

postgres=#
```

```
postgres=# \du
                                      List of roles
    Role name    |                         Attributes                         | Member of
-----------------+------------------------------------------------------------+-----------
 _juju_repl      | Replication                                                | {}
 juju_mattermost |                                                            | {}
 postgres        | Superuser, Create role, Create DB, Replication, Bypass RLS | {}

postgres=# \dt
No relations found.
postgres=# \l
                                 List of databases
    Name    |  Owner   | Encoding | Collate | Ctype |      Access privileges
------------+----------+----------+---------+-------+------------------------------
 mattermost | postgres | UTF8     | C       | C     | =Tc/postgres                +
            |          |          |         |       | postgres=CTc/postgres       +
            |          |          |         |       | juju_mattermost=CTc/postgres
 postgres   | postgres | UTF8     | C       | C     |
 template0  | postgres | UTF8     | C       | C     | =c/postgres                 +
            |          |          |         |       | postgres=CTc/postgres
 template1  | postgres | UTF8     | C       | C     | =c/postgres                 +
            |          |          |         |       | postgres=CTc/postgres
(4 rows)
```

Exit the psql client by typing `\q` and dump the database.

```bash
sudo su - postgres
DUMP=mattermost-dump-$(date +%Y-%m-%d:%H:%M:%S).sql
echo "$DUMP"
pg_dump --clean mattermost > "/var/lib/postgresql/backups/$DUMP"
ln -sf "$DUMP" /var/lib/postgresql/backups/mattermost-dump-latest.sql
exit
# As Ubuntu
sudo cp "/var/lib/postgresql/backups/mattermost-dump-latest.sql" /home/ubuntu/mattermost-dump-latest.sql
sudo chown ubuntu:ubuntu /home/ubuntu/mattermost-dump-latest.sql
# now you can download this dump from your laptop with
# juju scp postgresql/0:~/mattermost-dump-latest.sql .
```

## How to restore a backup

```bash
juju scp -- -r data matter2/0:~/
juju scp -- -r config.json matter2/0:~/
juju scp -- -r mattermost-dump-latest.sql postgres2/0:~/
#
juju ssh matter2/0
sudo systemctl stop mattermost
sudo cp config.json /opt/mattermost/config/config.json
sudo cp -r data/ /opt/mattermost/
sudo chown -R mattermost:mattermost /opt/mattermost/data/ /opt/mattermost/config/config.json
exit
#
juju ssh postgres2/0
sudo cp mattermost-dump-latest.sql /var/lib/postgresql/
sudo su - postgres
psql matter2 < mattermost-dump-latest.sql
```
```
SET
ERROR:  relation "audits" already exists
ERROR:  role "juju_mattermost" does not exist
ERROR:  relation "channelmembers" already exists
ERROR:  role "juju_mattermost" does not exist
...
ERROR:  relation "idx_users_names_no_full_name_txt" already exists
ERROR:  relation "idx_users_names_txt" already exists
ERROR:  relation "idx_users_update_at" already exists
REVOKE
REVOKE
GRANT
GRANT

```

[Source](https://www.postgresql.org/docs/9.1/static/backup-dump.html)

-->

# License

* Copyright 2016 Casey Marshall.
* Copyright 2018 Ghent University.

The [copyright](copyright) file contains the software license for this charm (ALv2).

Mattermost is a trademark of Mattermost, Inc.

## Disclaimer

This charm automates installation, configuration and management of a Mattermost server based on publicly documented best practices. This charm is not a part of the Mattermost product, is not endorsed by, and does not represent Mattermost, Inc. in any way.

See the [Mattermost](http://www.mattermost.org/) website for more information about the licenses and trademarks applicable to the software installed by this charm.

# Contact Information

This software was created in the [IDLab research group](https://www.ugent.be/ea/idlab) of [Ghent University](https://www.ugent.be) in Belgium. This software is used in [Tengu](https://tengu.io), a project that aims to make experimenting with data frameworks and tools as easy as possible.

* Merlijn Sebrechts <merlijn.sebrechts@gmail.com>
