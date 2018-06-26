from .btc import BTC
from .bch import BCH
#from .ltc import LTC

classes={'btc':BTC,
	 'bch':BCH}
tickers=classes.keys()

def fromticker(ticker):
	if(ticker[-5:].lower()=='-test'):
		ticker=ticker[:-5]
	return classes[ticker.lower()]
