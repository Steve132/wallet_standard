from _bip32 import *
from itertools import islice,count
import xurl

class Account(object):
	def __init__(self,coin):
		self.coin=coin

	def addresses(self):
		not ImplementedError

class SingleAddressAccount(Account):
	def __init__(self,coin,address):
		super(SingleAddressAccount,self).__init__(coin)
		self.address=address
	def addresses(self):
		lst=[self.address]
		return lst

class XPubAccount(Account):
	def __init__(self,coin,xpub,path="0/*"):
		super(XPubAccount,self).__init__(coin)
		self.xpub=coin.xpriv2xpub(xpub)
		self.path=path

	def __iter__(self):
		for p in xurl.paths(self.path):
			print(p)
			yield self.coin.descend(self.xpub,p)

	def addresses(self,*pkargs,**pkkwargs):
		for vpub in iter(self):
			yield self.coin.pubkeys2addr([vpub.key()],*pkargs,**pkkwargs)


#multichain address set:  itertools.zip_longest(*iterables, fillvalue=None)
		
#hierarchical wallet
#sign
#class Wallet(object):
#	def addresses(): #return a series of address,tickers
#		pass
#	def add(self,keyobject,coin,meta=None): #..must be a (xpub or xpriv) or (priv or pub) OBJECT or string
#		pass
	
