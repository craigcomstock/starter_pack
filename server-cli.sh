hosts=${@:-superhub feeder1 feeder2}
echo "hosts: $hosts"
while true
do
  echo "*: \c"
  read cmd
#  parallel --tagstring {}: ssh {} "$cmd" ::: superhub feeder1 feeder2
  parallel --tagstring {}: ssh {} "$cmd" ::: ${hosts}
  # TODO ^^^ figure out how to specify the list in a variable or from cmd line
done
# TODO, input list of servers/ips
# TODO, suppress errors and make it easy to back-track to examine errors
# TODO, capture all output for later perusal :)
# TODO, build-in rlwrap somehow?

# TODO, switch between GROUPS of servers defined in a json file or something and single hosts :) list hosts/groups
# TODO, make prompt be the group or list of hosts operating on
# TODO fix globs?

# *: sudo ls /var/cfengine/inputs/templates/federated_reporting/*.py
#feeder1:        ls: cannot access '/var/cfengine/inputs/templates/federated_reporting/*.py': No such file or directory
#feeder2:        ls: cannot access '/var/cfengine/inputs/templates/federated_reporting/*.py': No such file or directory
#*: sudo ls /var/cfengine/inputs/templates/federated_reporting/mrproper.py
#feeder1:        /var/cfengine/inputs/templates/federated_reporting/mrproper.py
#feeder2:        /var/cfengine/inputs/templates/federated_reporting/mrproper.py
