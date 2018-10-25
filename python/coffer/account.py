import hashlib
import itertools
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
		
	def authtx(self,txo,auth):
		raise NotImplementedError

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
			
	def sync(self,retries=10,targets=[]): #TODO: sync unspents_only goes here...bci.unspents(iter(aset))
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

	def authtx(self,txo,auth,maxsearch=1000):
		raise NotImplementedError	
