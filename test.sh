#!/usr/bin/env bash
cd `dirname $0`
set -eux

# Be sure to use `exec` so that termination signals reach the python process,
# or handle forwarding termination signals manually
exec python3 src/main.py $@