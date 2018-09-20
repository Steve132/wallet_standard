import hashlib
import itertools
from _bip32 import paths
import random

try:
	from itertools import izip_longest as zlong
except:
	from itertools import zip_longest as zlong
	

class AddressSet(object):
	def __init__(self,coin):
		self.coin=coin

	def address_iter(self):
		not ImplementedError

class SetAddressSet(AddressSet):
	def __init__(self,coin,addresses):
		super(SingleAddress,self).__init__(coin)
		self.addrset=addrset

	def address_iter(self):
		return itertools.cycle(self.addrset)

class XPubAddressSet(AddressSet):
	def __init__(self,coin,xpub,path="0/*",root=None,pkargs=[],pkkwargs={}): #change is "1/*"
		super(XPubAddressSet,self).__init__(coin)
		self.xpub=coin.xpriv2xpub(xpub)
		self.path=path
		self.root=root
		self.pkargs=pkargs
		self.pkkwargs=pkkwargs

	def path_iter(self):
		for p in paths(self.path):
			yield self.coin.descend(self.xpub,p)

	def address_iter(self):
		for vpub in self.path_iter():
			yield self.coin.pubkeys2addr([vpub.key()],*self.pkargs,**self.pkkwargs)

class Account(object):
	def __init__(self,coin,authref=None):
		self.coin=coin
		self.authref=authref
		self.meta={}

	def id(self):
		raise NotImplementedError

	def next_internal_iter(self):
		raise NotImplementedError
	def next_external_iter(self):
		raise NotImplementedError

	def next_internal(self,count=1):
		return list(itertools.islice(self.next_internal_iter(),count))
	def next_external(self,count=1):
		return list(itertools.islice(self.next_external_iter(),count))

	def used_internal(self):
		raise NotImplementedError
	def used_external(self):
		raise NotImplementedError

	def balance(self):
		raise NotImplementedError
	def sync(self):
		raise NotImplementedError
	

class AddressSetAccount(Account):
	def __init__(self,external,internal=[],authref=None):
		coincmps=set([x.coin for x in internal+external])
		if(len(coincmps) != 1):
			raise Exception("Account requires change addresses blockchain and all public address blockchains to be the same")

		super(AddressSetAccount,self).__init__(external[0].coin,authref)
		
		self.external=external
		self.internal=internal if len(internal) > 0 else external

		idt=tuple([(ass.xpub,ass.coin.ticker,ass.path) for ass in self.internal+self.external])
		
		self._id=hashlib.sha256(str(idt)).hexdigest()

	def id(self):
		return self._id
	
	def sync(self,bci=None):
		if(bci is None):
			bci=self.coin.blockchain()
		for v in self.internal+self.external:
			m=self.meta.setdefault("txs",{})
			txs=bci.transactions(v.address_iter())
			for k,v in txs.items():
				m[k]=v

	def balance(self):
		amount=0
		for aset in self.internal+self.external:
			unspents=bci.unspents(aset.address_iter())
			amount+=sum([p.amount for p in unspents])
		return amount

	def _referenced_addr(self):
		for k,v in self.meta.get('txs',{}).items():
			for dst in v.dsts:
				yield dst.address

	def _next_addr(self,lst):
		referenced=frozenset(self._referenced_addr())
		iters=[addrset.address_iter() for addrset in lst]
		for addr in zlong(*iters):
			if(addr is not None and addr[0] not in referenced):
				yield addr[0]

	def next_internal_iter(self):
		return self._next_addr(self.internal)
	def next_external_iter(self):
		return self._next_addr(self.external)

	

class Bip32Account(AddressSetAccount):
	def __init__(self,coin,xpub,internal_path="1/*",external_path="0/*",index=None,root=None,authref=None,**kwargs):
		self.xpub=coin.xpriv2xpub(xpub)
		if(root == None):
			root=[h(44),h(coin.childid),h(self.xpub.child)]
		self.type='bip32'
		pkargs=[]
		pkkwargs={}
		internal=XPubAddressSet(coin,xpub=xpub,path=internal_path,root=root,pkargs=pkargs,pkkwargs=pkkwargs)
		external=XPubAddressSet(coin,xpub=xpub,path=external_path,root=root,pkargs=pkargs,pkkwargs=pkkwargs)
		super(Bip32Account,self).__init__(internal=[internal],external=[external],authref=authref)
