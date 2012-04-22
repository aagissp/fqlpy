from fqlpy import FqlApi

APP_ID='<YOUR APP_ID HERE>'
APP_SECRET='<YOUR APP_SECRET HERE>'
fb=FqlApi(APP_ID,APP_SECRET)
# app access token needed to read public data
fb.setAppAccessToken()
# get id of page http://www.facebook.com/pythonlang
data=fb.runFQL('SELECT page_id FROM page WHERE username="pythonlang"')
page_id=data[0]['page_id']
# print messages
data=fb.runFQL('SELECT message FROM stream WHERE source_id='+str(page_id))
for item in data:
	print item['message'].encode('utf8')
