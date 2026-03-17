import urllib.request, json
req = urllib.request.Request("http://localhost:8000/api/v1/auth/login", data=b'{"email":"test@test.com","password":"password"}', headers={"Content-Type": "application/json"})
print(json.loads(urllib.request.urlopen(req).read())["access_token"])
