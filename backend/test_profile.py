import urllib.request
import json
import urllib.error

def req(url, method="GET", data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token: headers["Authorization"] = f"Bearer {token}"
    bdata = json.dumps(data).encode("utf-8") if data else b""
    req = urllib.request.Request(f"http://localhost:8000/api/v1{url}", data=bdata, headers=headers, method=method)
    try:
        return json.loads(urllib.request.urlopen(req).read())
    except urllib.error.HTTPError as e:
        print(f"Error {e.code}: {e.read().decode()}")
        return None

# 1. Login
token = req("/auth/login", method="POST", data={"email":"test2@test.com","password":"password"})["access_token"]

# 2. Add profile data
profile_data = {
    "user_id": "will_be_overwritten",
    "name": "Test User",
    "email": "test@test.com",
    "phone": "123",
    "experiences": [{
        "id": "e1", "company": "Goldman Sachs", "role": "Analyst", "location": "NY", "start": "Jan", "end": "Feb",
        "tags": [], "bullets": [{"id": "b1", "text": "Did work", "tags": [], "order": 0}]
    }],
    "projects": [], "education": [], "skill_categories": []
}
print("UPDATE PROFILE:", req("/profile", method="PUT", token=token, data=profile_data))

# 3. Create Variant
var_data = {"name": "Test", "template_id": "jake_classic"}
v = req("/variants", method="POST", token=token, data=var_data)

# 4. Fetch Variant
v2 = req(f"/variants/{v['id']}", method="GET", token=token)
if v2:
    for s in v2.get("sections", []):
         print(f"SECTION {s.get('type')}:")
         print(json.dumps(s.get("items", []), indent=2))

