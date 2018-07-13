#!/bin/bash

PERIOD=$1
if [ -z "$PERIOD" ]; then
	PERIOD=$(date +%Y-%m)
fi

set -eux

bhttp https://api.staging.jujucharms.com/omnibus/v4/multipass/rating/${PERIOD}
