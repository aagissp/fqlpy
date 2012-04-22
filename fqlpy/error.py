
class FqlApiError(Exception): pass

class FqlApiHttpError(FqlApiError):
	def __init__(self,http_error,fql_response=None):
		 self.http_error=http_error
		 if fql_response==None:
		   self.fql_response=http.error.read()
		 else:
		   self.fql_response=fql_response
	def __str__(self):
		 return 'HTTP Error '+str(self.http_error.code)+'\n'+self.fql_response+'\n'+str(self.http_error)

class FqlApiInternalUnknownServerError(FqlApiHttpError): pass

def fqlApiHttpErrorFactory(http_error):
	fql_response=http_error.read()
	if http_error.code==500 and fql_response=='{"error_code":1,"error_msg":"An unknown error occurred"}':
		return FqlApiInternalUnknownServerError(http_error,fql_response)
	else:
		return FqlApiHttpError(http_error,fql_response) 

