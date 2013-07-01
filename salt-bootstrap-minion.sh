#!/bin/bash

# Install saltstack
add-apt-repository ppa:saltstack/salt -y
apt-get update -y

#set custom hostname
NEWHOSTNAME=${hostname}
echo $NEWHOSTNAME > /etc/hostname
hostname $NEWHOSTNAME

# For minion
apt-get install salt-minion -y
apt-get upgrade -y


# Set salt master location and start minion
sed -i 's/#master: salt/master: ${salt_master_fqdn_1}/' /etc/salt/minion
salt-minion -d