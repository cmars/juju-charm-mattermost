# Juju reactive charm layer for Mattermost

## Build

In this directory:

    $ charm build

## Deploy

To deploy the locally-built charm:

    $ juju deploy local:trusty/mattermost
    $ juju deploy postgresql
    $ juju add-relation postgresql:db mattermost:db

## TODO

- Randomly generate encryption keys and salts during install hook.
- `website` relation to support reverse-proxying.

## Contact

Casey Marshall <charmed at cmars.tech>

