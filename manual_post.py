import http.client
import json
payload = json.dumps({'test': 'value'})
conn=http.client.HTTPSConnection('script.google.com',timeout=5)
conn.request('POST','/macros/s/AKfycbyev9ITDQksDX7p2BvbTMX-J6D4Jseq8dyjGwhiz50ugCHl0M2uzd_R_DZNLsNax7gM/dev?test=1', payload, headers={'Content-Type':'application/json'})
resp=conn.getresponse()
print(resp.status, resp.reason)
print(resp.read()[:120])

