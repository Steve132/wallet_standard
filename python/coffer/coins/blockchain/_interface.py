import json
import logging
import random
import time
import itertools

try:
	from urllib.request import urlopen,Request
	from urllib.error import URLError
	from urllib.parse import urlencode
except:
	from urllib2 import urlopen,Request,URLError
	from urllib import urlencode




def break_into_blocks(iterat,gap):
	lst=[]
	for obj in iterat:
		lst.append(obj)
		if(len(lst)>=gap):
			yield lst
			lst=[]
	if(len(lst)):
		yield lst 




class BlockchainInaccessibleError(Exception):
	def __init__(self,url,err):
		super(BlockchainInaccessibleError,self).__init__("Blockchain %s was inaccessable due to %r:%r" % (url,err,err.reason))

class BlockchainInterface(object):
	def __init__(self,coin):
		self.coin=coin

	def unspents(self,addressiter,*args,**kwargs):
		raise NotImplementedError

	def transactions(self,addressiter,*args,**kwargs):
		raise NotImplementedError

	def pushtx_bytes(self,txbytes):
		raise NotImplementedError

	def pushtx(self,txo):
		raise NotImplementedError

	def used_addresses(self,addressiter,*args,**kwargs): #this accepts an xpub too
		iter1,iter2=itertools.tee(addressiter, n=2)
		txos=self.transactions(iter1,*args,**kwargs)
		#addressset={k,i; for i,k in enumerate(addressiter
		usedaddr={}
		for tx in txos:
			paddr=[o.address for o in tx.prevs]
			daddr=[o.address for o in tx.dsts]
			for addr in paddr+daddr:
				usedaddr[addr]=True

		output=[]
		for k,addr in enumerate(itertools.islice(iter2,len(usedaddr))):
			output.append((addr,usedaddr.get(addr,False)))
		return output
		

	
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
	def __init__(self,coin,endpoint):
		super(HttpBlockchainInterface,self).__init__(coin)
		self.endpoint=endpoint

	#https://stackoverflow.com/questions/19396696/415-unsupported-media-type-post-json-to-odata-service-in-lightswitch-2012
	def make_request(self,request_type,call,callargs=None,retry_counter=0,delay=0.1,*args,**kwargs):
		if(callargs):
			encodeargs=urlencode(callargs)

		headers={'User-Agent': 'Mozilla/5.0%d'%(random.randrange(1000000))}
		
		if(request_type is 'GET'):
			url=self.endpoint+call+('?'+encodeargs) if encodeargs else ''
			data=None
		elif(request_type is 'POST'):
			url=self.endpoint+call
			data=encodeargs
		else:
			raise Exception("Unhandled request type")

		req=Request(url,data,headers)
		
		for k in range(retry_counter+1):
			try:
				response=urlopen(req,*args,**kwargs)
				response=response.read().strip()
				return response
			except URLError as u:
				try:
					p = u.read().strip()
				except:
					p = u
				logging.warning('Error loading URL url %s.  "%s". Try number %d',url,u,k)
				if(k==retry_counter):
					raise BlockchainInaccessibleError(self.endpoint,u)
			time.sleep(delay)

	def make_json_request(self,request_type,call,callargs=None,retry_counter=0,*args,**kwargs):
		return json.loads(self.make_request(request_type,call,callargs,retry_counter,*args,**kwargs))
		


			
