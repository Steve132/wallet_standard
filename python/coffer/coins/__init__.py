

def classes():
	from .btc import BTC
	from .bch import BCH
	from .ltc import LTC

	lclasses={'BTC':BTC,
		 'BCH':BCH,
		 'LTC':LTC}
	return lclasses


def tickers():
	tickers=classes.keys()

def classfromticker(ticker):
	if(ticker[-5:].lower()=='-test'):
		ticker=ticker[:-5]
	return classes[ticker.lower()]

def fromticker(ticker,*args,**kwargs):
	is_testnet=False
	if(ticker[-5:].lower()=='-test'):
		is_testnet=True
		
	coincls=classfromticker(ticker)
	return coincls(is_testnet=is_testnet,*args,**kwargs)
