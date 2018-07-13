#!/bin/bash

set -eux

RELEASE=$1

bhttp POST https://api.staging.jujucharms.com/omnibus/v4/p/cmars/mattermost-labeled-plan/${RELEASE}/release

