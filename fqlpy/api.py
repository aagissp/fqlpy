import urllib
import urllib2
import json
import re
import time
import errno
from fqlpy.error import *
from fqlpy.syncer import *


class FqlApi:
	FACEBOOK_ENDPOINT='https://graph.facebook.com'
	BATCH_QUERY_MAX_COUNT=50 # facebook limit on query batch
	def __init__(self,app_id,app_secret,syncer=None,retry_count=0,user_agent="fqlpy/1.0"):
		self.app_id=app_id
		self.app_secret=app_secret
		if syncer==None:
			self.syncer=FqlApiSyncer(0)
		else:
			self.syncer=syncer
		self.retry_count=retry_count
		self.opener = urllib2.build_opener( 
						urllib2.HTTPRedirectHandler(), 
						urllib2.HTTPHandler(debuglevel = 0), 
						urllib2.HTTPSHandler(debuglevel = 0) 
				)
		self.opener.addheaders = [('User-agent', user_agent)]
		self.access_token=None
	def setAppAccessToken(self):
		url=FqlApi.FACEBOOK_ENDPOINT+'/oauth/access_token?client_id='+self.app_id+'&client_secret='+self.app_secret+'&grant_type=client_credentials';
		response = self.opener.open(url)
		data = '\n'.join(response.readlines())
		g=re.match('^access_token=([^&]+).*',data)
		if not g: raise FqlApiError('Could not get app access token. Data returned:'+data)
		self.access_token=g.group(1)
		return self.access_token
	def setAccessToken(self,access_token):
		self.access_token=access_token 
	def refreshAccessToken(self):
		assert self.access_token
		url=FqlApi.FACEBOOK_ENDPOINT+'/oauth/access_token?client_id='+self.app_id+'&client_secret='+self.app_secret+'&grant_type=fb_exchange_token&fb_exchange_token='+self.access_token;
		response = self.opener.open(url)
		data = '\n'.join(response.readlines())
		g=re.match('^access_token=([^&]+).*',data)
		if not g: raise FqlApiError('Could not refresh the access token. Data returned:'+data)
		new_access_token=g.group(1)
		self.access_token=new_access_token
		return new_access_token
	def _callWithRetries(self,method,*args,**kwargs):
		# retry on errors that can only be considered of random nature
		# i.e. connections resets and unknown server errors
		try_count=max(1,self.retry_count+1)
		for try_i in range(try_count):
			last_retry=try_i==try_count-1
			try:	
				return method.__call__(*args,**kwargs)
			except urllib2.URLError,e:
				self.syncer.logError(e)
				if e.reason.errno == errno.ECONNRESET and not last_retry: continue
				raise 
			except FqlApiInternalUnknownServerError,e:
				self.syncer.logError(e)
				if not last_retry: continue
				raise 
			except Exception,e:
				self.syncer.logError(e)
				raise 
	def _runFQL(self,fql):
		while self.syncer.shouldWaitToExecuteCall(): time.sleep(1)
		self.syncer.logCall(fql)
		try:
			url=FqlApi.FACEBOOK_ENDPOINT+"/fql?"+urllib.urlencode({'q':fql})+'&access_token='+self.access_token
			response = self.opener.open(url)
			data = ''.join(response.readlines())
		except urllib2.HTTPError,error: raise fqlApiHttpErrorFactory(error)
		try:
			obj=json.loads(data)
		except Exception,e:
			raise FqlApiError(str(e)+' data:"%s"'%data)
		if not 'data' in obj:
			raise FqlApiError('Invalid json "no data" data:"%s"'%data)
		return obj['data']
	def runFQL(self,fql):
		return self._callWithRetries(self._runFQL,fql)
	def _makeFqlBatchPostData(self,fqls,multiquery_count):
		batch=[]
		q_count=0
		q_array={}
		for fql in fqls:
			q_count+=1
			q_array['q%d'%q_count]=fql
			if len(q_array)==multiquery_count or q_count==len(fqls):
				batch.append({"method":"GET","relative_url":"fql?"+urllib.urlencode({'q':json.dumps(q_array)})})
				q_array={}
		post_data=urllib.urlencode({'access_token':self.access_token,'batch':json.dumps(batch)})
		return post_data
	def _doBatchRequest(self,post_data):
		try:
			response = urllib2.urlopen(FqlApi.FACEBOOK_ENDPOINT,post_data,600)
			data = ''.join(response.readlines())
		except urllib2.HTTPError,error: raise fqlApiHttpErrorFactory(error)
		try:
			obj=json.loads(data)
		except Exception,e:
			raise FqlApiError(str(e)+' data:"%s"'%data)
		if obj==None: raise FqlApiError(str(e)+' data:"%s"'%data)
		return obj
	def _analyzeFqlBatchObject(self,batch_obj,multiquery_count):
		result_objs=[]
		q_count=0
		for reply in batch_obj: 
			if reply==None:
				result_objs.append(None)
				continue 
			if not 'body' in reply: raise FqlApiError('No "body" in response. Response:"%s"'%data)
			bodystr=reply['body']
			try:
				body=json.loads(bodystr)
			except Exception,e:
				raise FqlApiError(str(e)+' data:"%s"'%data[:50])
			if not 'data' in body: raise FqlApiError('No "data" in body. Response:"%s"'%bodystr)
			multiquery_objs={}
			for r in body['data']: multiquery_objs[r['name']]=r['fql_result_set']
			for i in range(len(multiquery_objs)):
				q_count+=1
				result_objs.append(multiquery_objs['q%d'%q_count])
		return result_objs
	def _runFQLs(self,fqls,multiquery_count):
		query_max_count=FqlApi.BATCH_QUERY_MAX_COUNT*multiquery_count 
		if len(fqls)>query_max_count: raise FqlApiError('up to %d requests can be batched'%(query_max_count))
		while self.syncer.shouldWaitToExecuteCall(): time.sleep(1)
		for fql in fqls:
			self.syncer.logCall(fql)
		post_data=self._makeFqlBatchPostData(fqls,multiquery_count)
		batch_obj=self._doBatchRequest(post_data)
		result_objs=self._analyzeFqlBatchObject(batch_obj,multiquery_count)
		return result_objs
	def runFQLs(self,fqls,multiquery_count=2):
		return self._callWithRetries(self._runFQLs,fqls,multiquery_count)
		
