#!/usr/bin/env bash
set -e
set -x
cd $HOME/cfe/starter_pack
hubs="superhub feeder1 feeder2"
clients="bob"
all="${hubs} ${clients}"
echo "all servers are ${all}"
parallel vagrant up {} ::: ${all}
parallel sed -i '/{}/,/^$/d' ~/.ssh/config ::: ${all}
parallel vagrant ssh-config {} >> ~/.ssh/config ::: ${all}
# next line is like a double-check, a promise, to make sure the previous steps actually accomplished their goal :)
parallel ssh {} hostname ::: ${all}
cf-remote --version master download --edition enterprise ubuntu20
parallel ssh {} sudo apt remove -y postgres* ::: ${hubs}
parallel cf-remote --version master install --hub {} ::: ${hubs}
parallel cf-remote --version master install --clients {} ::: ${clients}
# then do api to setup FR dude! :p
rm -f hubs.cert
parallel ssh {} sudo cat /var/cfengine/httpd/ssl/certs/{}.cert ::: ${hubs} >> hubs.cert
# TODO fix up this next step, with sudo, as a promise not an action
grep superhub /etc/hosts || \
echo "192.168.100.90 superhub" | sudo tee -a /etc/hosts
grep feeder1 /etc/hosts || \
echo "192.168.100.91 feeder1" | sudo tee -a /etc/hosts
grep feeder2 /etc/hosts || \
echo "192.168.100.92 feeder2" | sudo tee -a /etc/hosts
# or rather sed promise to include that line :p
parallel --link ssh {1} sudo cf-agent -IB {2} ::: superhub feeder1 feeder2 ::: 192.168.100.90 192.168.100.91 192.168.100.92
echo "192.168.100.91 feeder1" | ssh superhub sudo tee -a /etc/hosts
echo "192.168.100.92 feeder2" | ssh superhub sudo tee -a /etc/hosts
