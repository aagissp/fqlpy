import time

MAX_ERROR_HISTORY_SIZE=10

class FqlApiSyncer:
	def __init__(self,time_between_calls_in_secs=1):
		self.last_query_timestamp=0
		self.time_between_calls_in_secs=time_between_calls_in_secs	  
		self.error_timestamps=[]
	def logCall(self,fql):
		self.last_query_timestamp=time.time()
	def logError(self,error):
		self.error_timestamps=self.error_timestamps[-MAX_ERROR_HISTORY_SIZE:]
		self.error_timestamps.append(time.time())
	def shouldWaitToExecuteCall(self):
		# check time between calls
		time_between_calls_passed=time.time()>=self.last_query_timestamp+self.time_between_calls_in_secs
		# check time from last error
		if(len(self.error_timestamps)==0):
			error_pause_passed=1
		else:
			# an error will pause the calls 
			# for an time period that increments 
			# as errors accumulate
			error_pause_passed=time.time()>=self.error_timestamps[-1]+(self.error_timestamps[-1]-self.error_timestamps[0])
		return not time_between_calls_passed or not error_pause_passed 
		
