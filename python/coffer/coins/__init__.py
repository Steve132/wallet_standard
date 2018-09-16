
_all_classes=None
def classes():
	global _all_classes
	if(_all_classes is None):
		from .btc import BTC
		from .bch import BCH
		from .ltc import LTC

		lclasses={'BTC':BTC,
			 'BCH':BCH,
			 'LTC':LTC}
		_all_classes=lclasses

	return _all_classes

def tickers():
	tickers=classes().keys()

def classfromticker(ticker):
	if(ticker[-5:].lower()=='-test'):
		ticker=ticker[:-5]
	lclasses=classes()
	return lclasses[ticker.upper()]

def fromticker(ticker,*args,**kwargs):
	is_testnet=False
	if(ticker[-5:].lower()=='-test'):
		is_testnet=True
		
	coincls=classfromticker(ticker)
	return coincls(is_testnet=is_testnet,*args,**kwargs)
