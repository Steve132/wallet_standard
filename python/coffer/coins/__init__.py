from .btc import BTC
from .bch import BCH
#from .ltc import LTC

classes={'btc':BTC,
	 'bch':BCH}
tickers=classes.keys()

def fromticker(ticker):
	return classes[ticker.lower()]
