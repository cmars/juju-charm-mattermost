#!/bin/bash

set -eux

go run mkplanjson.go >plan.json
bhttp POST --stdin https://api.staging.jujucharms.com/omnibus/v4/p Content-Type:application/json <plan.json
