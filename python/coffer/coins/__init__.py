_all_classes=None
_ticker_listings={}
def register(ticker,cls,listing):
	global _all_classes
	if(ticker not in _all_classes):
		_all_classes[ticker]=cls
		_ticker_listings.setdefault(listing,set()).add(ticker)
	
def register_standard():
	from .btc import BTC
	register('BTC',BTC,'standard')
	from .bch import BCH
	register('BCH',BCH,'standard')
	from .ltc import LTC
	register('LTC',LTC,'standard')
	from .eth import ETH
	register('ETH',ETH,'standard')

def classes(listing=None):
	global _all_classes
	if(_all_classes is None):
		_all_classes={}
		register_standard()
	if(listing is None):
		return _all_classes
	tickers=set(_ticker_listings[listing])
	return {tic:_all_classes[tic] for tic in tickers}

def tickers(listings=None):
	tickers=classes(listings).keys()

def classfromticker(ticker):
	if(ticker[-5:].upper()=='-TEST'):
		ticker=ticker[:-5]
	lclasses=classes(None)
	return lclasses[ticker.upper()]

def fromticker(ticker,*args,**kwargs):
	is_testnet=False
	if(ticker[-5:].upper()=='-TEST'):
		is_testnet=True
		
	coincls=classfromticker(ticker)
	return coincls(is_testnet=is_testnet,*args,**kwargs)
