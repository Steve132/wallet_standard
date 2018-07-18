from _bip32 import *
from itertools import islice,count
from transaction import Transaction

try:
	from collections import MutableMapping
except:
	from collections.abc import MutableMapping

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
	def __init__(self,coin,xpub,path="0/*",root=None): #change is "1/*"
		super(XPubAddressSet,self).__init__(coin)
		self.xpub=coin.xpriv2xpub(xpub)
		self.path=path
		self.root=root

	def __iter__(self):
		for p in paths(self.path):
			yield self.coin.descend(self.xpub,p)

	def addresses(self,*pkargs,**pkkwargs):
		for vpub in iter(self):
			yield self.coin.pubkeys2addr([vpub.key()],*pkargs,**pkkwargs)

class Account(object):
	def __init__(self,coin,authref=None):
		self.coin=coin
		self.authref=authref
		self.meta={}

	def id(self):
		raise NotImplementedError
	

class AddressSetAccount(Account):
	def __init__(self,external,internal=[],authref=None):
		coincmps=set([x.coin for x in internal+external])
		if(len(coincmps) != 1):
			raise Exception("Account requires change addresses blockchain and all public address blockchains to be the same")

		super(AddressSetAccount,self).__init__(external[0].coin,authref)
		
		self.external=external
		self.internal=internal if len(internal) > 0 else external

		self._id=str(hash(tuple([(ass.xpub,ass.coin.ticker,ass.path,ass.root) for ass in self.internal+self.external])))

	def id(self):
		return _id
	
	def sync(self,bci):
		for v in self.internal+self.external:
			m=self.meta.setdefault("txs",{})
			txs=bci.transactions(v.addresses())
			for k,v in txs.items():
				m[k]=v

#AccountGroup = dict
class Wallet(object):
	def __init__(self):
		self.groups={}


class Bip32Account(AddressSetAccount):
	def __init__(self,coin,xpub,ipath="1/*",epath="0/*",index=None,root=None,authref=None,**kwargs):
		self.xpub=coin.xpriv2xpub(xpub)
		
		if(root == None):
			root=[h(44),h(coin.childid),h(self.xpub.child)]
		
		internal=XPubAddressSet(coin,xpub=xpub,path=ipath,root=root)
		external=XPubAddressSet(coin,xpub=xpub,path=epath,root=root)
		super(Bip32Account,self).__init__(internal=[internal],external=[external],authref=authref)



