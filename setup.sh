#!/usr/bin/env bash
set -e
set -x
cd $HOME/cfe/starter_pack
hubs="superhub feeder1 feeder2"
clients="bob"
all="${hubs} ${clients}"
echo "all servers are ${all}"
parallel vagrant destroy --force {} ::: ${all}
parallel vagrant up {} ::: ${all}
parallel sed -i '/{}/,/^$/d' ~/.ssh/config ::: ${all}
parallel vagrant ssh-config {} >> ~/.ssh/config ::: ${all}
cf-remote --version master download --edition enterprise ubuntu20
parallel ssh {} sudo apt remove -y postgres* ::: ${hubs}
parallel cf-remote --version master install --hub {} ::: ${hubs}
parallel cf-remote --version master install --clients {} ::: ${clients}
# then do api to setup FR dude! :p
rm hubs.cert
parallel ssh {} sudo cat /var/cfengine/httpd/ssl/certs/{}.cert ::: ${hubs} >> hubs.cert
# TODO fix up this next step, with sudo, as a promise not an action
sudo echo "192.168.100.90 superhub" >> /etc/hosts
sudo echo "192.168.100.91 feeder1" >> /etc/hosts
sudo echo "192.168.100.92 feeder2" >> /etc/hosts
# or rather sed promise to include that line :p
parallel --link ssh {1} sudo cf-agent -IB {2} ::: superhub feeder1 feeder2 ::: 192.168.100.90 192.168.100.91 192.168.100.92
