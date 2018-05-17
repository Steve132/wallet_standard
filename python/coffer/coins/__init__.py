from .btc import BTC
from .bch import BCH

classes={'btc':BTC,
	 'bch':BCH}
tickers=classes.keys()

def fromticker(ticker):
	return classes[ticker.lower()]
