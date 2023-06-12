#!/usr/bin/env bash
source $(cd /opt/using_guidance/ && pdm env info -p)/bin/activate
exec "$@"
