# Juju reactive charm layer for Mattermost

## Build

In this directory:

    $ charm build

## Deploy

To deploy the locally-built charm:

    $ juju deploy cs:~cmars/mattermost
    $ juju deploy postgresql
    $ juju add-relation postgresql:db mattermost:db

## License

Copyright 2016 Cmars Technologies, LLC.

Mattermost is a trademark of Mattermost, Inc.

### Disclaimer

This charm automates installation, configuration and management of a Mattermost
server based on publicly documented best practices. This charm is not a part of
the Mattermost product, is not endorsed by, and does not represent Mattermost,
Inc. in any way.

See the [Mattermost](http://www.mattermost.org/) website for more information
about the licenses and trademarks applicable to the software installed by this
charm.

## Contact

Email: charmed at cmars.tech
IRC: cmars on FreeNode
Mattermost: Coming soon...
