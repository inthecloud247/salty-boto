#!/bin/bash

## Sample Saltmaster startup script

cd /srv
git clone https://github.com/ydavid365/saltmine.git
cd /srv/saltmine
git checkout develop

mkdir -p /srv/salt/pillar/base
mkdir -p /srv/salt/pillar/common

cat > /srv/salt/pillar/top.sls << "EOF"
base:
  '*':
    - base
EOF

cat > /srv/salt/pillar/base/init.sls << "EOF"
include:
  - saltmine.pillar.env_globals
  - common.env_globals
EOF

cat >> /etc/salt/master << "EOF"
file_roots:
  base:
    - /srv/saltmine
    - /srv/salt

pillar_roots:
  base:
    - /srv/saltmine
    - /srv/salt/pillar

renderer: mako|yaml
log_level: debug
EOF

cat > /srv/salt/pillar/common/env_globals.sls << "EOF"
# put custom globals here
EOF
