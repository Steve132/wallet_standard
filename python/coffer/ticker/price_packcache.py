import baseprice
import logging
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

def load(ticker):
	if(ticker in _packcache):
		pclocation=os.path.join(os.path.realpath(__file__),'caches',self.ticker.upper()+'-usd.json')
		try:
			data=json.load(open(pclocation,'r'))
			dstring=json.dumps(dstring)
			h=hashlib.sha256(dstring).hexdigest()
			if(h!=_packcache[self.ticker.upper()]):
				logging.warning("Failure loading package cache price data from file %s: mismatched sha2sums" % (pclocation))
				return {}
			return {float(ts):float(price) for ts,price in data.items()}
		except Exception as e:
			logging.warning("Exception loading package cache price data from file %s" % (pclocation))
			return {}

_pcdata={}
def backend(ticker,timestamp):
	global _pcdata
		
	if(timestamp is None):
		raise Exception("Package cache prices cannot be used to get current price information")
		
	if(ticker in _pcdata):
		return _pcdata[ticker].lookup(timestamp)

	if(ticker in _packcache):
		pdata=load(ticker)
		if(len(pdata) > 0):
			_pcdata[ticker]=baseprice.LerpCache(ticker,pdata)
			return _pcdata[ticker].lookup(timestamp)
	raise Exception("No package price data found for coin %s" % (ticker))
