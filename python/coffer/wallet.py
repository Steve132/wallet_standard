from _bip32 import *
from itertools import islice,count
#itertools.chain(*iterables)

class AddressSet(object):
	def __init__(self,coin):
		self.coin=coin

	def addresses(self,start=0,stop=-1,step=1):
		not ImplementedError

#multichain address set:  itertools.zip_longest(*iterables, fillvalue=None)
		
#hierarchical wallet
#sign
#class Wallet(object):
#	def addresses(): #return a series of address,tickers
#		pass
#	def add(self,keyobject,coin,meta=None): #..must be a (xpub or xpriv) or (priv or pub) OBJECT or string
#		pass
	
