from _bip32 import *
from itertools import islice,count

class AddressSet(object):
	def __init__(self,coin):
		self.coin=coin

	def addresses(self):
		not ImplementedError

class SingleAddress(AddressSet):
	def __init__(self,coin,address):
		super(SingleAddressAccount,self).__init__(coin)
		self.address=address
	def addresses(self):
		lst=[self.address]
		return lst

class XPubAddressSet(AddressSet):
	def __init__(self,coin,xpub,path="0/*"): #change is "1/*"
		super(XPubAddressSet,self).__init__(coin)
		self.xpub=coin.xpriv2xpub(xpub)
		self.path=path

	def __iter__(self):
		for p in paths(self.path):
			yield self.coin.descend(self.xpub,p)

	def addresses(self,*pkargs,**pkkwargs):
		for vpub in iter(self):
			yield self.coin.pubkeys2addr([vpub.key()],*pkargs,**pkkwargs)

class Account(object):
	def __init__(self,external,internal=[]):
		coincmps=set([x.coin for x in internal+external])
		if(len(coincmps) != 1):
			raise Exception("Account requires change addresses blockchain and all public address blockchains to be the same")

		self.external=external
		self.internal=internal if len(internal) > 0 else external
		
		
