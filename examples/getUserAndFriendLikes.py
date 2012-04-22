from fqlpy import FqlApi

APP_ID='<YOUR APP_ID HERE>'
APP_SECRET='<YOUR APP_SECRET HERE>'
access_token='<A USER ACCESS TOKEN HERE>'
# NOTE: look at samplePhpToGetUserAccessToken.php on how to get a user access token
#       and note that you DON'T need to get the access token from the same server
fb=FqlApi(APP_ID,APP_SECRET)
fb.setAccessToken(access_token)
data=fb.runFQL('SELECT uid,user_likes,friends_likes FROM permissions WHERE uid=me()');
item=data[0]
uid=item['uid']
user_likes_perm=item['user_likes']
friends_likes_perm=item['friends_likes']
if not user_likes_perm:
	print 'Not allowed to get current user likes'
else:
	data=fb.runFQL('SELECT url FROM url_like WHERE user_id='+str(uid))
	for item in data: print 'Current user likes ',item['url']
	


####################################################
## BATCH REQUEST FOR FRIENDS
####################################################
def getUserNames(uids):
	# batch calls to 50 items per batch
	USER_LIMIT_PER_CALL=50
	if len(uids)>USER_LIMIT_PER_CALL:
		result=getUserNames(uids[USER_LIMIT_PER_CALL:])
		for (uid,name) in getUserNames(uids[:USER_LIMIT_PER_CALL]).items(): result[uid]=name
    		return result
	# do the batched query
	result={}
	fqls=['SELECT name FROM user WHERE uid='+str(uid) for uid in uids]
	datas=fb.runFQLs(fqls)
	for uid,data in zip(uids,datas):
		for item in data:
			result[uid]=item['name']
	return result

def printLikesOfUsers(uids,names={}):
	# batch calls to 50 items per batch
	USER_LIMIT_PER_CALL=5
	if len(uids)>USER_LIMIT_PER_CALL:
		printLikesOfUsers(uids[:USER_LIMIT_PER_CALL],names)
		printLikesOfUsers(uids[USER_LIMIT_PER_CALL:],names)
    		return
	# do the batched query
	fqls=['SELECT url FROM url_like WHERE user_id='+str(uid) for uid in uids]
	datas=fb.runFQLs(fqls)
	for uid,data in zip(uids,datas):
		for item in data:
			url=item['url']
			print names.get(uid,str(uid)).encode('utf8'),'likes',url.encode('utf8')


####################################################
## FRIENDS LIKES
####################################################
if friends_likes_perm:
	friend_uids=[]
	data=fb.runFQL('SELECT uid2 FROM friend WHERE uid1=me()');
	for item in data: friend_uids.append(item['uid2']) 
	friend_names=getUserNames(friend_uids)
	printLikesOfUsers(friend_uids,friend_names)
