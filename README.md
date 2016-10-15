# Juju reactive charm layer for Mattermost

# Build

In this directory:

    charm build

# Deploy

## TLS Options

Deployment requires agreement to ISRG terms of service, because Let's Encrypt
is the primary and recommended method for setting up TLS.

### Secured with Let's Encrypt in public clouds

Deploy to a public cloud and expose it.

    juju deploy cs:~cmars/mattermost
    juju deploy postgresql
    juju add-relation mattermost postgresql:db
    juju expose mattermost

Acquire a DNS name for the instance. Then set `fqdn` to the DNS name.

    juju config mattermost fqdn=chat.cmars.tech

Let's Encrypt will do the rest. When the workload state becomes active, your
Mattermost instance is ready to set up.

If registration fails, check:

- That you've exposed mattermost. Let's Encrypt needs to connect to ports 80
  and 443 as part of the registration process.
- That the DNS name has had time to propagate and cached entries have expired.
- That the DNS name is allowed by Let's Encrypt. Some names, like the dynamic
  ones given to EC2 instances, may not be allowed.

### Reverse-proxied by a front-end

With `fqdn` unset, relate mattermost to a reverse proxy.

    juju deploy cs:~cmars/mattermost
    juju deploy postgresql
    juju deploy haproxy
    juju add-relation postgresql:db mattermost:db
    juju add-relation haproxy mattermost

## Alternative binary distributions

To deploy with your own Mattermost binary distribution:

    juju deploy cs:~cmars/mattermost --resource bdist=/path/to/mattermost.tar.gz

Note that Mattermost releases prior to 2.1.0 have not been tested.

# License

Copyright 2016 Casey Marshall.

The [copyright](copyright) file contains the software license for this charm.

Mattermost is a trademark of Mattermost, Inc.

## Disclaimer

This charm automates installation, configuration and management of a Mattermost
server based on publicly documented best practices. This charm is not a part of
the Mattermost product, is not endorsed by, and does not represent Mattermost,
Inc. in any way.

See the [Mattermost](http://www.mattermost.org/) website for more information
about the licenses and trademarks applicable to the software installed by this
charm.

# Contact

Email: charmed at cmars.tech

IRC: cmars on FreeNode

Mattermost: Join the [Juju team on live.cmars.tech](https://live.cmars.tech/signup_user_complete/?id=wccpdu6dqp88mjkqbngnws6ohc)

