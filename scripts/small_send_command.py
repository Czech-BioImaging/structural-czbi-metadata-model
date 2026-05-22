import requests
import json

token = "jd2tX8I4evotMo3jjdJxU2pHM0ZTCMn0JuqkIVU6qzF5rlElG5ACMRV8Wh0o"

url = "https://127.0.0.1:5000"
h = {"Accept": "application/json", "Content-Type": "application/json", "Authorization": f"Bearer {token}"}
datapath = "/home/ulman/devel/EOSC/czbirepo/model/example_payload/example_small.json"

with open(datapath) as fp:
    data = json.load(fp)
print(data)

r = requests.post(f"{url}/api/records", data=json.dumps(data), headers=h, verify=False)
print(r.status_code)
print(json.dumps(r.json(), indent=4))
