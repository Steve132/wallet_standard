from baseprice import *
from baseprice import get_price as bgp

import price_coincap2

default_backend=price_coincap2.backend

def get_current_price(asset_ticker,currency_ticker,backend=default_backend):
	return get_price(asset_ticker,currency_ticker,timestamp=None,backend=backend)

def get_price(asset_ticker,currency_ticker,timestamp,backend=default_backend):
	return bgp(asset_ticker,currency_ticker,backend=backend,timestamp=timestamp)
