import os
import json

aenea_json="c:\\Natlink\Natlink\\MacroSystem\\aenea.json"
server_json="c:\\Natlink\Natlink\\MacroSystem\\server_state.json"
server_ip="e:\\aenea-grammars\\tools\\server_ip"

with open(aenea_json, 'r') as f:
    config = json.load(f)

try:
    os.remove(server_json)
    os.remove(aenea_json)
except:
    print("file not found")

with open(server_ip, 'r') as f:
    config['host'] = f.readline()[:-1]

print("new config is: {}".format(config))

with open(aenea_json, 'w') as f:
    json.dump(config,f)

