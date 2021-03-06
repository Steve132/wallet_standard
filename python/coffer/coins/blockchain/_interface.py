import json
import logging
import random
import time
import itertools
from coffer.lib.make_request import make_json_request as mjr

def break_into_blocks(iterat,gap):
	lst=[]
	for obj in iterat:
		lst.append(obj)
		if(len(lst)>=gap):
			yield lst
			lst=[]
	if(len(lst)):
		yield lst 


def retryable(f):
	def wrapper(*args,**kwargs):
		for k in range(args[0].retries):
			try:
				return f(*args,**kwargs)
			except Exception as u:
				logging.warning('Exception detected in try %d/%d: %r,%r',k,args[0].retries,str(u),u.args)
				last=u
		else:
			raise last
	return wrapper

class BlockchainInaccessibleError(Exception):
	def __init__(self,url,err):
		super(BlockchainInaccessibleError,self).__init__("Blockchain %s was inaccessable due to %r:%r" % (url,err,err.reason))

class BlockchainInterface(object):
	def __init__(self,coin,retries=10):
		self.coin=coin
		self.retries=retries

	def sendraw(self,rawtx):
		raise NotImplementedError

	def transactions(self,addressiter,*args,**kwargs):
		raise NotImplementedError

	def pushtx_bytes(self,txbytes):
		raise NotImplementedError

	def pushtx(self,txo):
		raise NotImplementedError

	def _transactions_used(self,addressiter,*args,**kwargs):
		iter1,iter2=itertools.tee(addressiter)
		txos=self.transactions(iter1,*args,**kwargs)
		#addressset={k,i; for i,k in enumerate(addressiter
		usedaddr={}
		for txid,tx in txos.items():
			paddr=[o.address for o in tx.prevs]
			daddr=[o.address for o in tx.dsts]
			for addr in paddr+daddr:
				usedaddr[addr]=True

		output=[]
		for k,addr in enumerate(itertools.islice(iter2,len(usedaddr))):
			output.append((addr,usedaddr.get(addr,False)))
		return txos,output

	def used_addresses(self,addressiter,*args,**kwargs): #there should be an xpub version
		txso,used=self._transactions_used(addressiter,*args,**kwargs)
		return used

#	def unspents(self,addressiter,*args,**kwargs): #there should be an xpub version here
#		txso,used=self._transactions_used(addressiter,*args,**kwargs)
#		used=dict(used)
#		return self.coin.filter_unspents(txso,set([k for k,v in used.items() if v]))
"""	def filter_unspents(self,txs,addrused,*args,**kwargs):
		utxos={}

		for txid,tx in txs.items():
			for p in tx.dsts:
				if(not p.spentpid and (p.address in addrused)):
					utxos[p.previd]=p
		return utxos"""

	
_exempt_members=['subchains','coin'] #'unspents','_addrfunc','transactions']
multi_blockchain_dispatch=False
class MultiBlockchainInterface(BlockchainInterface):

	def select(self):
		if(not multi_blockchain_dispatch):
			return random.choice(self.subchains)
		else:
			return self
		
	def __init__(self,coin,subchains):
		super(MultiBlockchainInterface,self).__init__(coin)
		self.subchains=subchains
		
	def __getattribute__(self,name):
		if(name in _exempt_members):
			return BlockchainInterface.__getattribute__(self,name)

		valid_subchains=[]
		valid_subvalues=[]
		for s in self.subchains:
			try:
				func=s.__getattribute__(name)
				if(not callable(func)):
					valid_subvalues.append(func)
				else:
					valid_subchains.append(s)
			except AttributeError:
				pass
		if(len(valid_subvalues) > 0):
			return random.choice(valid_subvalues)

		if(len(valid_subchains) == 0):
			return BlockchainInterface.__getattribute__(self,name)

		#do a thing 
		def _multicaller(*args,**kwargs):
			random.shuffle(valid_subchains)
			last=None
			for s in valid_subchains:
				try:
					cb=s.__getattribute__(name)
					return cb(*args,**kwargs)
				except Exception as e:
					logging.warning("Exception found trying %r on %r" % (name,s))
					last=e
			else:
				if(last):
					raise last
				else:
					raise Exception("%r never found as a method" % (name))

		def _multicaller_addressiter(addressiter,*args,**kwargs):
			random.shuffle(valid_subchains)
			last=None
 
			for addrblock in break_into_blocks(addressiter,32):
				for s in valid_subchains:
					try:
						cb=s.__getattribute__(name)
						return cb(addrblock,*args,**kwargs)
					except Exception as e:
						logging.warning("Exception found trying %r on %r" % (name,s))
						last=e
				else:
					if(last):
						raise last
					else:
						raise Exception("%r never found as a method" % (name))
		#if(name in _addressblock):
		#	return _multicaller_addressiter
		#else:
		return _multicaller
			

class HttpBlockchainInterface(BlockchainInterface):
	def __init__(self,coin):
		super(HttpBlockchainInterface,self).__init__(coin)
		
	def get_endpoint():
		raise NotImplementedError

	#https://stackoverflow.com/questions/19396696/415-unsupported-media-type-post-json-to-odata-service-in-lightswitch-2012
	def make_json_request(self,request_type,call,callargs=None,retry_counter=10,delay=0.25,*args,**kwargs):
		return mjr(request_type,self.get_endpoint(),call,callargs,retry_counter,delay,*args,**kwargs)

	#def make_json_request(self,request_type,call,callargs=None,retry_counter=0,*args,**kwargs):
		
	#	return json.loads(self.make_request(request_type,call,callargs,retry_counter,*args,**kwargs))
		


			
