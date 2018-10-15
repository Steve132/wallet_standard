from coffer.lib.make_request import make_json_request
import baseprice
import time
import logging
import price_packcache
import sys

_coincap_ids={}
def _coincap_id(ticker):
	global _coincap_ids
	if(ticker in _coincap_ids):
		return _coincap_ids[ticker]

	data=make_json_request("GET", "https://api.coincap.io/v2","/assets",{"search":ticker})
	fid=None

	for entry in data['data']:
		if(entry['symbol']==ticker):
			fid=entry['id']
	if(fid is not None):
		_coincap_ids[ticker]=fid
		return fid
	else:
		approxtickers=[e['symbol'] for e in data['data']]
		raise Exception("CoinCap.io does not seem to support a coin with the exact ticker %s.  This is a list of similar tickers that are supported: %r" % (ticker,approxtickers)) 

def _currate(cid):
	data=make_json_request("GET", "https://api.coincap.io/v2","/rates/"+cid)
	if('data' not in data):
		raise Exception("No data found for coin %s" % (cid))
	ts=float(data['timestamp'])
	data=data['data']
	return float(data['rateUsd']),ts/1000.0

def _fetch_closest_data(cid,timestamp,spread=20000.0):
	timestamp=float(timestamp)
	pre=timestamp-spread
	if(pre > time.time()):
		price,ts=_currate(cid)
		raise PriceLookupFutureError(timestamp,ts,price)
	post=timestamp+spread
	print("POST IS",post)
	reqparams={'interval':'m1','start':int(pre*1000.0),'end':int(post*1000)}
	data=make_json_request("GET","https://api.coincap.io/v2","/assets/%s/history" % (cid),reqparams)
	data=data['data']
	if(len(data) > 0):
		return {float(d['time'])/1000.0 : float(d['priceUsd']) for d in data}
	else:
		return {}

_earliest_cache={}
def bsearch_to_find_earliest(ticker,bottom=time.time(),top=1493596800): #01.05.2017
	cid=_coincap_id(ticker)
	if(cid in _earliest_cache):
		return _earliest_cache[cid]

	while(bottom-top > (2*60)):
		middlets=(bottom+top)/2.0
		middledata=_fetch_closest_data(cid,middlets)
		if(len(middledata) > 0):
			bottom=middlets
		else:
			top=middlets
		logging.info("Searching coincap ts range %d-%d for earliest data point" % (top,bottom)) #this is inverted on purpose


	_earliest_cache[cid]=min(_fetch_closest_data(cid,bottom).items(),key=lambda v: v[0])
	return _earliest_cache[cid]
	
def backend(ticker,timestamp=None):
	cid=_coincap_id(ticker)
	if timestamp is None:
		price,ts=_currate(cid)
		return price
	else:
		hdct=_fetch_closest_data(cid,timestamp)
		try:
			if(len(hdct) > 0):
				cach=baseprice.LerpCache(ticker,hdct)
				print("TIMESTAMP IS",timestamp)
				return cach.lookup(timestamp)
			else:
				raise Exception("No history found for that ticker at that timestamp")
		except Exception as e:
			v=sys.exc_info()
			try:
				return price_packcache.backend(ticker,timestamp)
			except Exception as e2:
				print("Exception in fallback price in packcache: %r" % (e2))
				raise v[0],v[1],v[2]
		
			
			#bsearch to find earliest and cache it.  Then raise PriceLookupPastError if(timestamp < self.history_timestamps[0]):
			#	raise PriceLookupPastError(timestamp,self.history_timestamps[0],self.history_prices[0])


if __name__=="__main__":
	logging.basicConfig(level=logging.INFO)
	print(bsearch_to_find_earliest('BCH'))
