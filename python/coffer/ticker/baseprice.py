import logging
import time
import bisect

class PriceLookupBoundsError(Exception):
    def __init__(self,requested_timestamp,nearest_timestamp,nearest_price):
		super(PriceLookupBoundsError, self).__init__("Requested price lookup at time %s is out of bounds of the available data" % (requested_timestamp))
		self.requested_timestamp=requested_timestamp
		self.nearest_timestamp=nearest_timestamp
		self.nearest_price=nearest_price

class PriceLookupFutureError(PriceLookupBoundsError):
    pass

class PriceLookupPastError(PriceLookupBoundsError):
	pass

class LerpCache(object):
	def __init__(self,ticker,historydict={},timestamp=time.time()):
		self.ticker=ticker
		self.history_timestamps=None  #history is stored in {us:priceusd}
		self.history_prices=None
		self.time_of_last_sync=0
		self.cache_expiration=300
		if(len(historydict) > 0):
			self.update(historydict,timestamp)

	def update(self,historydict,timestamp=time.time()):
		newdata=list([(float(ts),float(price)) for ts,price in historydict.items()])
		if(self.history_timestamps is not None and self.history_prices is not None):
			newdata.extend(zip(self.history_timestamps,self.history_prices))
		
		data=sorted(newdata,key=lambda x:float(x[0]))
		self.history_timestamps,self.history_prices=zip(*data)
		self.time_of_last_sync=timestamp

	def is_expired(self,timestamp=time.time()):
		timestamp=float(timestamp)
		return (self.time_of_last_sync+self.cache_expiration) < timestamp

	def lookup(self,timestamp):
		timestamp=float(timestamp)
		if(self.history_timestamps is None or self.history_prices is None):
			raise Exception("No history data is loaded.")

		print(timestamp,self.history_timestamps)

		if(timestamp < self.history_timestamps[0]):
			raise PriceLookupPastError(timestamp,self.history_timestamps[0],self.history_prices[0])

		timestamp_index = bisect.bisect_right(self.history_timestamps, timestamp)

		if(timestamp_index == len(self.history_timestamps)):
			raise PriceLookupFutureError(timestamp,self.history_timestamps[-1],self.history_prices[-1])
		
		left_x,left_y=self.history_timestamps[timestamp_index],self.history_prices[timestamp_index]
		right_x,right_y=self.history_timestamps[timestamp_index+1],self.history_prices[timestamp_index+1]

		left_x,right_x=float(left_x),float(right_x)
		t=(timestamp-left_x)/(right_x-left_x)
		return left_y+(right_y-left_y)*t
		
def filter_ticker(tc):
	return tc.upper().replace('-TEST','')

def get_price(asset_ticker,currency_ticker,backend,timestamp=None):
	asset_ticker=filter_ticker(asset_ticker)
	currency_ticker=filter_ticker(currency_ticker)
	if(currency_ticker != "USD"):
		return get_price(asset_ticker,'USD',timestamp)/get_price(currency_ticker,'USD',timestamp)

	return backend(asset_ticker,timestamp)
	

