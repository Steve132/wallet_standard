import hashlib
import itertools
from bip32 import paths
import random
from lib.index import UuidBase

try:
	from itertools import izip_longest as zlong
except:
	from itertools import zip_longest as zlong

try:
	from collections import Iterable
except:
	from collections.abc import Iterable


class AddressSet(Iterable):
	def __init__(self,coin):
		self.coin=coin

	def __iter__(self):
		not ImplementedError

class SetAddressSet(AddressSet):
	def __init__(self,coin,addresses):
		super(SingleAddress,self).__init__(coin)
		self.addrset=addrset

	def __iter__(self):
		return itertools.cycle(self.addrset)

class XPubAddressSet(AddressSet):
	def __init__(self,coin,xkey,path="0/*",root=None,*bip32args,**bip32kwargs): #change is "1/*"
		super(XPubAddressSet,self).__init__(coin)
		xkey=coin.parse_xkey(xkey)
		if(xkey.is_private()):
			bip32_settings=coin.load_bip32_settings(prefix_private=xkey.version,*bip32args,**bip32kwargs)
		else:
			bip32_settings=coin.load_bip32_settings(prefix_public=xkey.version,*bip32args,**bip32kwargs)
		self.xpub=self.coin.xpriv2xpub(xkey,bip32_settings)
		self.coin=coin
		self.path=path
		self.root=root
		self.settings=bip32_settings

	def path_iter(self):
		for p in paths(self.path):
			yield self.coin.descend(self.xpub,p)

	def __iter__(self):
		for vpub in self.path_iter():
			yield self.coin.pubkeys2addr([vpub.key()],*self.settings.pkargs,**self.settings.pkkwargs)

class Account(UuidBase):
	def __init__(self,coin,authref=None):
		self.coin=coin
		self.authref=authref
		self.meta={}
		self.transactions={}

	def _reftuple(self):
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

	def sync(self):
		raise NotImplementedError

	def sources_iter(self):
		for tref,txo in self.transactions.items():
			for subin in txo.srcs:
				yield subin

	def destinations_iter(self):
		for tref,txo in self.transactions.items():
			for subout in txo.dsts:
				yield subout

	def intowallet_iter(self):
		used=frozenset(self.used_internal() | self.used_external())
		for dst in self.destinations_iter():
			if(dst.address in used):
				yield dst

	def unspents_iter(self):
		allsrcs=frozenset(self.sources_iter())
		for dst in self.intowallet_iter():
			if(dst not in allsrcs and dst.spenttx is None):
				yield dst

	def balance(self):
		amount=0.0
		for o in self.unspents_iter():
			amount+=o.amount
		return amount

#stop if you fail the predicate gap times in a row
def gaptakewhile(it,predicate,gap):
	for x in it:
		if(predicate(x)):
			yield x
		else:
			gap-=1
			if(gap <= 0):
				break

class OnChainAddressSetAccount(Account):
	def __init__(self,external,internal=[],authref=None,gap=20):
		coincmps=set([x.coin for x in internal+external])
		if(len(coincmps) != 1):
			raise Exception("Account requires change addresses blockchain and all public address blockchains to be the same")

		super(OnChainAddressSetAccount,self).__init__(external[0].coin,authref)
		
		self.external=external
		self.internal=internal if len(internal) > 0 else external

		self.gap=gap
		
	def _reftuple(self):
		idt=tuple([(ass.xpub,ass.coin.ticker,ass.path) for ass in self.internal+self.external])
		return idt
	
	def sync_transactions(self,retries=10,unspents_only=False): #TODO: sync unspents_only goes here...bci.unspents(iter(aset))
		bci=self.coin.blockchain()
		bci.retries=retries
		for v in self.internal+self.external:
			m=self.transactions
			txs=bci.transactions(iter(v),gap=self.gap)
			for k,v in txs.items():
				m[k]=v

	def _referenced_addr(self):
		for k,v in self.transactions.items():
			for dst in v.dsts:
				yield dst.address

	def _used_addr_iter(self,lst):
		referenced=frozenset(self._referenced_addr())
		def pred(addr):
			return addr is not None and addr in referenced 

		iters=[gaptakewhile(iter(addrset),pred,gap=self.gap) for addrset in lst]
		return itertools.chain.from_iterable(zlong(*iters))

	def _next_addr_iter(self,lst):
		referenced=frozenset(self._referenced_addr())
		def pred(addr):
			return addr is None or addr in referenced

		iters=[itertools.dropwhile(pred,iter(addrset)) for addrset in lst]
		for addr in itertools.chain.from_iterable(zlong(*iters)):
				yield addr

	def next_internal_iter(self):
		return self._next_addr_iter(self.internal)
	def next_external_iter(self):
		return self._next_addr_iter(self.external)
	def used_internal(self):
		return frozenset(self._used_addr_iter(self.internal))
	def used_external(self):
		return frozenset(self._used_addr_iter(self.external))

class Bip32Account(OnChainAddressSetAccount):
	def __init__(self,coin,xkey,root,internal_path="1/*",external_path="0/*",authref=None,*bip32args,**bip32kwargs):
		self.coin=coin
		self.type='bip32'
		internal=XPubAddressSet(coin,xkey=xkey,path=internal_path,root=root,*bip32args,**bip32kwargs)
		external=XPubAddressSet(coin,xkey=xkey,path=external_path,root=root,*bip32args,**bip32kwargs)
		self.xpub=internal.xpub
		self.bip32args=bip32args
		self.bip32kwargs=bip32kwargs
		super(Bip32Account,self).__init__(internal=[internal],external=[external],authref=authref)
