import urllib,urllib2
import json
import logging
import random
import time


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
		super(BlockchainInaccessibleError,self).__init__("Blockchain %s was inacessable due to %r" % (url,err))

class BlockchainInterface(object):
	def __init__(self,coin):
		self.coin=coin

	def unspent_block(self,addressblock):
		raise NotImplementedError

	def unspent(self,addressiter,gap=20):
		for addrblock in _break_into_blocks(addressiter,gap):
			done=True
			for addr in addrblock:
				self.coin.parse_addr(addr)

			for sp in self.unspent_block(addrblock):
				done=False
				yield sp
			if(done):
				break

	def pushtx_bytes(self,txbytes):
		raise NotImplementedError

	def pushtx(self,txo):
		raise NotImplementedError
	

class MultiBlockchainInterface(BlockchainInterface):
	def __init__(self,coin,subchains):
		super(MultiBlockchainInterface,self).__init__(coin)
		self.subchains=subchains
		
	def __getattribute__(self,name):
		valid_subchains=[]
		valid_subvalues=[]
		for s in subchains:
			try:
				s.__getattribute__(name)
				if(not callable(s)):
					valid_subvalues.append(s)
				else:
					valid_subchains.append(s)
			except AttributeError:
				pass

		if(len(valid_subvalues) > 0):
			return random.choice(valid_subvalues)

		if(len(valid_subchains) == 0):
			return BlockchainInterface.__getattribute__(self,name)

		def _multicaller(*args,**kwargs):
			random.shuffle(valid_subvalues)
			last=None
			for s in subc:
				try:
					cb=s.__getattribute__(name)
					return cb(s,*args,**kwargs)
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
			encodeargs=urllib.urlencode(callargs)
		
		if(request_type is 'GET'):
			url=self.endpoint+call+('?'+encodeargs) if encodeargs else ''
			data=None
		elif(request_type is 'POST'):
			url=self.endpoint+call
			data=encodeargs
		else:
			raise Exception("Unhandled request type")
		
		for k in range(retry_counter+1):
			try:
				if(data is not None):
					response=urllib2.urlopen(url,data,*args,**kwargs)
				else:
					response=urllib2.urlopen(url,*args,**kwargs)
				response=response.read()
				return response
			except urllib2.URLError as u:
				logging.warning('Error loading URL url %s.  "%s". Try number %d',url,u,k)
				if(k==retry_counter):
					raise BlockchainInaccessibleError(self.endpoint,u)
			time.sleep(delay)

	def make_json_request(self,request_type,call,callargs=None,retry_counter=0,*args,**kwargs):
		return json.loads(self.make_request(request_type,call,callargs,retry_counter,*args,**kwargs))
		

	def unspent_block(self,addressblock):
		raise NotImplementedError

	def pushtx(self,txo):
		raise NotImplementedError


			
