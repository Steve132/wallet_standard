import hashlib,hmac
from binascii import hexlify,unhexlify
import struct
import _crypto
import _base	
from lib.index import IndexBase	

class PublicKey(IndexBase):
	def __init__(self,pubkeydata,is_compressed=None):
		self.pubkeydata=pubkeydata
		self.P,detected_is_compressed=_crypto._decode_pub(pubkeydata)
		
		if(is_compressed is None):
			self.is_compressed=detected_is_compressed
		else:
			self.pubkeydata=_crypto._encode_pub(self.P,is_compressed)
			self.is_compressed=is_compressed

	def decoded(self):
		return self.P

	def __add__(self,o):
		return PublicKey(_crypto.pubkey_add(self.pubkeydata,o.pubkeydata,compressed=self.is_compressed),is_compressed=self.is_compressed)

	def _reftuple(self):
		return (self.P,self.is_compressed)

#TODO compressed private keys are 32 bytes long.always
class PrivateKey(IndexBase):
	def __init__(self,privkeydata,is_compressed=True):
		if(isinstance(privkeydata,PrivateKey)):
			pko=privkeydata
			privkeydata=pko.privkeydata
			is_compressed=pko.is_compressed

		self.privkeydata=privkeydata
		self.is_compressed=is_compressed
		if(not _crypto.privkey_verify(self.privkeydata)):
			raise Exception("Invalid private key")

	def pub(self):
		pkd=_crypto.privkey_to_pubkey(self.privkeydata,compressed=self.is_compressed)
		return PublicKey(pkd,is_compressed=self.is_compressed)

	def __add__(self,o):
		return PrivateKey(_crypto.privkey_add(self.privkeydata,o.privkeydata),is_compressed=self.is_compressed)
	
	def sign(self,msghash_bytes,use_der=False):
		return _crypto.sign(msghash_bytes,self.privkeydata,compressed=self.is_compressed,use_der=use_der)

	def _reftuple(self):
		return (self.privkeydata,self.is_compressed)

class Address(IndexBase):
	def __init__(self,addrdata,coin,addrtype,format_args=[],format_kwargs={}):
		self.addrdata=addrdata
		self.coin=coin
		self.afargs=format_args
		self.afkwargs=format_kwargs
		#self.addrtype=addrtype			#TODO: remove addrtype from Address, it's not used anywhere except as an annotation 

	def _reftuple(self):
		return (self.addrdata) #TODO should include coin and addrdata?
		
	def __str__(self):
		if(self.coin is None):
			return "genericaddrdata:%s" % (hexlify(self.addrdata))

		return self.coin.format_addr(self,*self.afargs,**self.afkwargs)

	def __repr__(self):
		return 'Address(%s)' % (str(self))
