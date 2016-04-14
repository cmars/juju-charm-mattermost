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

This charm is Copyright 2016 Cmars Technologies, LLC. All rights reserved.

Mattermost is a trademark of Mattermost, Inc.

This charm automates installation, configuration and management of a Mattermost
server based on publicly documented best practices. This charm is not a part of
the Mattermost product, and does not represent Mattermost, or its trademark
owner, Mattermost, Inc., in any way.

See the [Mattermost](http://www.mattermost.org/) website for more information
about the licenses and trademarks applicable to the software installed by this
charm.

## Contact

Email: <charmed at cmars.tech>.
IRC: cmars on FreeNode.
