import json
import logging
import random
import time


try:
	from urllib.request import urlopen,Request
	from urllib.error import URLError
	from urllib.parse import urlencode
except:
	from urllib2 import urlopen,Request,URLError
	from urllib import urlencode

def _break_into_blocks(iterat,gap):
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

	def unspents_block(self,addressblock):
		raise NotImplementedError

	def transactions_block(self,addressblock):
		raise NotImplementedError

	def _addrfunc(self,func,addressiter,gap=20,*args,**kwargs):
		outs=[]
		for addrblock in _break_into_blocks(addressiter,gap):
			done=True
			for addr in addrblock:
				self.coin.parse_addr(addr)

			for sp in func(addrblock,*args,**kwargs):
				done=False
				outs.append(sp)
			if(done):
				break
		return outs

	def unspents(self,addressiter,*args,**kwargs):
		return self._addrfunc(self.unspents_block,addressiter,*args,**kwargs)

	def transactions(self,addressiter,*args,**kwargs):
		return self._addrfunc(self.transactions_block,addressiter,*args,**kwargs)
	
	def pushtx_bytes(self,txbytes):
		raise NotImplementedError

	def pushtx(self,txo):
		raise NotImplementedError
	
_exempt_members=['subchains','coin','unspents','_addrfunc','transactions']
class MultiBlockchainInterface(BlockchainInterface):
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
			if(last):
				raise last
			else:
				raise Exception("%r never found as a method" % (name))

		return _multicaller
			

class HttpBlockchainInterface(BlockchainInterface):
	def __init__(self,coin,endpoint):
		super(HttpBlockchainInterface,self).__init__(coin)
		self.endpoint=endpoint

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
					p = e.read().strip()
				except:
					p = e
				logging.warning('Error loading URL url %s.  "%s". Try number %d',url,u,k)
				if(k==retry_counter):
					raise BlockchainInaccessibleError(self.endpoint,u)
			time.sleep(delay)

	def make_json_request(self,request_type,call,callargs=None,retry_counter=0,*args,**kwargs):
		return json.loads(self.make_request(request_type,call,callargs,retry_counter,*args,**kwargs))
		

	def unspents_block(self,addressblock):
		raise NotImplementedError

	def pushtx(self,txo):
		raise NotImplementedError


			
