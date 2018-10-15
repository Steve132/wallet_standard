import json
import logging
import time
import random
import bisect
import time
from coffer.lib.make_request import make_json_request
import hashlib
import os,os.path
import coffer.lib.appdirs as appdirs

#cache is needed for coins that existed prior to 2013 (coincap.io provides only data prior to 2013)
_packcache={
'XPM':'05c853b891b89057f6b947163d3acc0f9cd819acb7eec4b6de90c71ac931fcd3',
'GRC':'855c4d274945cedc6efb7aacc132472397997f6a9bde4a0ec5a0699eda7e961e',
'FTC':'cb529507dd0d68fa62f12bf5d74c543c48365ebe10307fd3bff8f7de9ceb3fce',
'PPC':'588d35804feb0c0632c0bfe6a5cc7bdcd3ce44bbf1e06da22824bd3a40c8126a',
'BCN':'f6fb6f5144e8bc5df7011c96f8d71eb5f0ee7aa086e0b0a3d73c176282ace2d7',
'STC':'44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a',
'XRP':'437c96984352ac149fb1c65b15d5fdfd2bc124a583419de1af5bafad38e1ccec',
'NXT':'08a416ce2d6468af6e1094e1009b0f7f9f0ba4fe3e9f88d75be5f84a4812fd51',
'DOGE':'c435100175cae4d69730a2494e579cb6b0353a17e43750081bcfae7b8f0b339b',
'NMC':'cad9ea117057f1633f7e1984787bfd1ea88bb4e73550c02f00d6c1bd9b20e10c',
'LTC':'e5b3cb48b9d79a646ba6a4daead1616a47b95ec697071d09fb7bde7490ebb1db',
'BTC':'ee1969931376c1fd59cf8dca04415fd8e6c2d7df6b46377be3390131a0c21582',
'ETH':'4bac35db83301d877385cb6f108e08d665ba8ff34a7c7bfcfa3a601f28b6ae1a',
}

disk_cache_expiration=3600 #TODO: until the cache is encrypted this represents a security risk
cache_expiration=300
def _locate_disk_cache(ticker):
	user_cache=appdirs.user_data_dir("CofferPrice","Coffer")
	try:
		os.makedirs(user_cache,0755)
	except OSError:
		pass

	return os.path.join(appdirs.user_cache_dir("CofferPrice","Coffer"),'priceUSD_cache_%s.json' % (ticker))

def _load_disk_cache(filename):
	try:
		if(os.path.getmtime(filename)+disk_cache_expiration < time.time()):
			logging.info("Could not load price cache %s from disk, expired" % (filename))
			return None
		logging.info("Loading price cache %s" % (filename))
		cfo=open(filename,'r')
		jso=json.load(cfo)
		cfo.close()
		return jso
	except OSError as e:
		logging.info("Could not load price cache %s from disk, file exception: %r" % (filename,e))
		return None

def _save_disk_cache(filename,historydict):
	try:
		logging.info("Saving price cache %s" % (filename))
		cfo=open(filename,'w')
		json.dump(historydict,cfo)
		cfo.close()
	except Exception as e:
		logging.info("Could not save price cache %s to disk, file exception: %r" % (filename,e))



	

class CoinCapCache(object):
	def __init__(self,ticker):
		self.ticker=ticker
		self.history_timestamps=None  #history is stored in {us:priceusd}
		self.history_prices=None
		self.time_of_last_sync=0

	def _initcache(self):
		if(self.ticker.upper() in _packcache):
			pclocation=os.path.join(os.path.realpath(__file__),'caches',self.ticker.upper()+'-usd.json')
			try:
				data=json.load(open(pclocation,'r'))
				dstring=json.dumps(dstring)
				h=hashlib.sha256(dstring).hexdigest()
				if(h!=_packcache[self.ticker.upper()]):
					return {}
				return {float(ts)*1000.0:price for ts,price in data.items()}
				
			except:
				return {}
		return {}

	def fetch(self):
		#TODO: only fetch the recent history from the last update.  So if you've gone 300 seconds to 1 day since you last updated, only get the 1day endpoint.
		dcache_fn=_locate_disk_cache(self.ticker)
		historydict=_load_disk_cache(dcache_fn)
		if(historydict is None or len(historydict)==0):
			historydict=self._initcache()
			historyurls=['/1day','/7day','/30day','/90day','/180day','/365day','']
			success=False
			try:
				for hurl in historyurls:
					logging.info("Downloading %s price info from chart database" % (hurl))
					hist = make_json_request("GET", "http://coincap.io/history"+hurl+'/'+self.ticker.upper())
					hist["price"]
					historydict.update(hist["price"])
				_save_disk_cache(dcache_fn,historydict)
			except Exception as e:
				logging.warning("Could not download price data from coincap.io")
	

		if(len(historydict) == 0):
			logging.warning("No price data found anywhere")
		data=sorted(historydict.items(),key=lambda x:int(x[0]))
		self.history_timestamps,self.history_prices=zip(*data)
		#print self.history_timestamps
		#print self.history_prices

	def lookup_current(self):
		current_price=get_current_price(self.ticker,'USD')
		ts=time.time()*1000.0
		self.history_timestamps.append(ts)
		self.history_prices.append(current_price)
		return ts,current_price

	def lookup(self,timestamp):
		timestamp=float(timestamp)
		if(self.history_timestamps is None or self.history_prices is None or timestamp > (self.time_of_last_sync+cache_expiration)): #500 seconds is the expiration date on the cache
			self.fetch()

		if(timestamp < self.history_timestamps[0]):
			raise PriceLookupPastError(timestamp,self.history_timestamps[0],self.history_prices[0])

		self.time_of_last_sync=self.history_timestamps[-1]
		#print "sorted:", all(self.history_timestamps[i] <= self.history_timestamps[i+1] for i in xrange(len(self.history_timestamps)-1))
		timestamp_index = bisect.bisect_left(self.history_timestamps, timestamp)

		# bisect_left error?
		#if(self.history_timestamps[timestamp_index] > timestamp):
		#	timestamp_index-=1

		if(timestamp_index == len(self.history_timestamps)):
			left_x,left_y=self.history_timestamps[-1],self.history_prices[-1]
			current_ts,current_price=self.lookup_current()
			
			if(timestamp > current_ts):
				raise PriceLookupHistoryError(timestamp,current_ts,current_price)
			right_x,right_y=current_ts,current_price
		else:
			left_x,left_y=self.history_timestamps[timestamp_index],self.history_prices[timestamp_index]
			right_x,right_y=self.history_timestamps[timestamp_index+1],self.history_prices[timestamp_index+1]

		left_x,right_x=float(left_x),float(right_x)
		t=(timestamp-left_x)/(right_x-left_x)
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
		return fhc.lookup(float(timestamp)*1000.0)
		

if __name__ == "__main__":
	print get_price("BTC", "USD", 1367347501995)
