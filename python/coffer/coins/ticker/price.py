import json
import logging
import time
import random
import bisect
import time
from coffer.lib.make_request import make_json_request


class CoinCapCache(object):
	def __init__(self,ticker):
		self.ticker=ticker
		self.history_timestamps=None
		self.history_prices=None
		self.time_of_last_sync=0

	def fetch(self):
		current_time=None
		#TODO: only fetch the recent history from the last update.  So if you've gone 300 seconds to 1 day since you last updated, only get the 1day endpoint.
		historyurls=['/1day','/7day','/30day','/90day','/180day','/365day','']
		historydict={}
		for hurl in historyurls:
			hist = make_json_request("GET", "http://coincap.io/history"+hurl+'/'+self.ticker.upper())
			historydict.update(hist["price"])
		data=sorted(historydict.items(),key=lambda x:x[0])
		self.history_timestamps,self.history_prices=zip(*data)
		print self.history_timestamps
		print self.history_prices

	def lookup_current(self):
		current_price=get_current_price(self.ticker,'USD')
		ts=time.time()*1000.0
		self.history_timestamps.append(ts)
		self.history_prices.append(current_price)
		return current_price,ts

	def lookup(self,timestamp):
		timestamp=float(timestamp)
		if(self.history_timestamps is None or self.history_prices is None or timestamp > (self.time_of_last_sync+300)): #300 seconds is the expiration date on the cache 
			self.fetch()

		if(timestamp < self.history_timestamps[0]):
			raise Exception("Timestamp %d is earlier than the best known data" % (timestamp))

		self.time_of_last_sync=self.history_timestamps[-1]
		timestamp_index = bisect.bisect_left(self.history_timestamps, timestamp)
		
		
		if(timestamp_index == len(self.history_timestamps)):
			left_x,left_y=self.history_timestamps[-1],self.history_prices[-1]
			current_price,current_ts=self.lookup_current()
			
			if(timestamps > current_ts):
				raise Exception("Timestamp %d is in the future" % (timestamp))
			right_x,right_y=current_ts,current_price
		else:
			left_x,left_y=self.history_timestamps[timestamp_index],self.history_prices[timestamp_index]
			right_x,right_y=self.history_timestamps[timestamp_index+1],self.history_prices[timestamp_index+1]

		left_x,right_x=float(left_x),float(right_x)

		t=(right_x-left_x)/(timestamp-left_x)
		return left_y+(right_y-left_y)*t
		
		
		
			
_coincap_history_cache={}

_available_coins_cache=None
def available_price_coins():
	global _available_coins_cache
	if(_available_coins_cache is None):
		_available_coins_cache=set(make_json_request("GET","http://coincap.io","/coins"))
	return _available_coins_cache


def filter_ticker(tc):
	return tc.upper().replace('-TEST','')


def _fetch_history_cache(ticker):
	global _coincap_history_cache
	avcoins=available_price_coins()
	if(ticker.upper() not in avcoins):
		raise Exception("CoinCap.io does not support price data for coin '%s'" % (ticker))
	return _coincap_history_cache.setdefault(ticker,CoinCapCache(ticker))

def get_current_price(asset_ticker,currency_ticker):
	asset_ticker=filter_ticker(asset_ticker)
	currency_ticker=filter_ticker(currency_ticker)
	asset_data = make_json_request("GET", "http://coincap.io","/page/" + asset_ticker.upper(),"")
	price_label = "price_" + currency_ticker.lower()
	if price_label in asset_data:
		return asset_data[price_label]
	else:
		return get_current_price(asset_ticker,'USD') / get_current_price(currency_ticker,'USD')

def get_price(asset_ticker,currency_ticker,timestamp=None):
	asset_ticker=filter_ticker(asset_ticker)
	currency_ticker=filter_ticker(currency_ticker)

	if(currency_ticker != "USD"):
		return get_price(asset_ticker,'USD',timestamp)/get_price(currency_ticker,'USD',timestamp)

	if timestamp is None:
		return get_current_price(asset_ticker,currency_ticker)
	else: #must be USD at this point
		fhc=_fetch_history_cache(asset_ticker)
		return fhc.lookup(timestamp)
		

if __name__ == "__main__":
	print get_price("BTC", "USD", 1367347501995)
