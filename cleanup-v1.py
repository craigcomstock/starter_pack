#!/bin/python3
# Python script to purge hosts on a Federated Reporting feeder hub
# when other hubs in federation have had more recent contact with
# a host that has the same hostkey.
#
# Requirements:
# - self-signed certificates from both superhub and feeder
#   located at /var/cfengine/httpd/ssl/certs/$(hostname).cert
#  copy to the following location in your masterfiles
#  masterfiles/templates/federated/mrproper/$(hostname).cert
# - a mrproper account on superhub and feeders
#   encrypt password with the following command, entering the password then pressing Ctrl-D
#   /var/cfengine/bin/cf-secret --encrypt etc

import subprocess
import urllib3
import json
import platform
import os

FEDERATION_CONFIG_PATH = "/opt/cfengine/federation/cfapache/federation-config.json"
HUB_CERTS_PATH = "/var/cfengine/inputs/templates/mrproper/hub.certs"
# superhub credentials for mrproper username account
SUPERHUB_CREDS_PATH = "/var/cfengine/inputs/templates/mrproper/superhub.cfsecret"
# feeder credentials for mrpoper username account
FEEDER_CREDS_PATH = "/var/cfengine/inputs/templates/mrproper/(feeder-name?).cfsecret"

if os.path.exists(HUB_CERTS_PATH):
    http = urllib3.PoolManager(cert_reqs="CERT_REQUIRED", ca_certs=HUB_CERTS_PATH)
else:
    print("Could not find hub certs path at %s" % HUB_CERTS_PATH)
    return 1

try:
    feeder_hostkey = subprocess.check_output(
        ["/var/cfengine/bin/cf-key", "-p", "/var/cfengine/ppkeys/localhost.pub"],
        universal_newlines=True,
    ).strip()
    print(f"This feeder's hostkey is {feeder_hostkey}")
except CalledProcessError:
    print("Could not get this feeder's hostkey via cf-key command")
    return 1

if os.path.exists(FEDERATION_CONFIG_PATH):
    config = json.loads(f.read())
else:
    print("Federation config file could not be found at %s" % FEDERATION_CONFIG_PATH)
    return 1

remote_hubs = config["remote_hubs"]
for hub in remote_hubs:
    remote_hub = remote_hubs[hub]
    if remote_hub["role"] == "superhub" and remote_hub["target_state"] == "on":
        superhub_hostname = remote_hub["ui_name"]
        api_url = f"https://{superhub_hostname}"

print(f"superhub hostname is {superhub_hostname}")
if api_url == None:
    print("Sorry, couldn't figure out the superhub api url endpoint")
    return 1

url = f"{api_url}/api/query"

print(f"Using superhub API URL {api_url}")

feeder_secret = subprocess.check_output(
    [
        "/var/cfengine/bin/cf-secret",
        "decrypt",
        "/vagrant/superhub_credentials.cfsecret",
        "--output",
        "-",
    ],
    universal_newlines=True,
).strip()
# feeder_username = 'feeder_api'
feeder_username = "admin"  # TODO change me back to feeder_api
# auth = HTTPBasicAuth(feeder_username, feeder_secret)
headers = urllib3.make_headers(basic_auth=f"{feeder_username}:{feeder_secret}")
headers["Content-Type"] = "application/json"

sql = f"""
SELECT distinct ls.hostkey
FROM lastseenhosts ls
JOIN (
  SELECT hostkey,max(lastseentimestamp) as newesttimestamp
  FROM lastseenhosts
  WHERE lastseendirection = \'INCOMING\'
  GROUP BY hostkey
) AS newest
ON ls.hostkey = newest.hostkey
AND ls.lastseentimestamp = newest.newesttimestamp
AND ls.lastseendirection = \'INCOMING\'
JOIN (
  SELECT distinct(hub_id) FROM hosts
  WHERE hub_id = (
    SELECT hub_id
    FROM __hubs
    WHERE hostkey = \'{feeder_hostkey}\'
  )
) AS others
ON ls.hub_id != others.hub_id"""
f_sql = sql.replace("\n", " ").strip()
payload = f'{{ "query": "{f_sql}" }}'
# print(payload)

# TODO verify=True, and provide cert for verification :)
response = http.request("POST", url, headers=headers, body=payload)
data = json.loads(response.data.decode("utf-8"))["data"]
# print(data)
rows = data[0]["rows"]
# print(rows)
hosts_there = []
for entry in rows:
    [hostkey] = entry
    #  print(hostkey)
    hosts_there.append(hostkey)
exit

print("hosts_there:")
print(hosts_there)

# now get the list of local hosts, cull missing entries and process deletes
# TODO need both superhub credentials as well as local API credentials :)
response = http.request("GET", f"https://{platform.node()}/api/host", headers=headers)
data = json.loads(response.data.decode("utf-8"))["data"]
# print(data)
hosts_here = []
for entry in data:
    #  print(entry)
    hostkey = entry["id"]
    #  print(hostkey)
    hosts_here.append(hostkey)

print("hosts_here:")
print(hosts_here)

hosts_to_delete = [x for x in hosts_there if x in hosts_here]

print("hosts_to_delete:")
print(hosts_to_delete)

# and now really delete them! :)

for host_to_delete in hosts_to_delete:
    response = http.request(
        "DELETE",
        f"https://{platform.node()}/api/host/{host_to_delete}",
        headers=headers,
    )
    print(response)
