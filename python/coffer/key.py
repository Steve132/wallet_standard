import hashlib,hmac
from binascii import hexlify,unhexlify
import struct
import _crypto
import _base
		
class PublicKey(object):
	def __init__(self,pubkeydata,is_compressed=None):
		self.pubkeydata=pubkeydata
		self.is_compressed=is_compressed
		if(is_compressed==None):
			self.is_compressed = len(self.pubkeydata) <= 33
		if(not self.is_compressed):
			raise Exception("Uncompressed public keys not implemented!")
	def decompressed(self):
		return _crypto._decode_pub(self.pubkeydata)

	def __add__(self,o):
		return PublicKey(_crypto.pubkey_add(self.pubkeydata,o.pubkeydata),is_compressed=self.is_compressed)

	def __cmp__(self,other):
		return cmp(self.pubkeydata,other.pubkeydata)
		
	def __hash__(self):
		return hash(self.pubkeydata)

#TODO CANNOT HANDLE UNCOMPRESSED

class PrivateKey(object):
	def __init__(self,privkeydata,is_compressed=True):
		if(isinstance(privkeydata,PrivateKey)):
			pko=privkeydata
			privkeydata=pko.privkeydata
			is_compressed=pko.is_compressed

		self.privkeydata=privkeydata
		self.is_compressed=is_compressed
		if(not self.is_compressed):
			raise Exception("Uncompressed private keys not implemented!")
		if(not _crypto.privkey_verify(self.privkeydata)):
			raise Exception("Invalid private key")

	def pub(self):
		pkd=_crypto.privkey_to_compressed_pubkey(self.privkeydata)
		return PublicKey(pkd,is_compressed=True)

	def __add__(self,o):
		return PrivateKey(_crypto.privkey_add(self.privkeydata,o.privkeydata),is_compressed=self.is_compressed)
	
	def __cmp__(self,other):
		return cmp(self.privkeydata,other.privkeydata)
		
	def __hash__(self):
		return hash(self.privkeydata)

class Address(object):
	def __init__(self,addrdata,coin,format_args=[],format_kwargs={}):
		self.addrdata=addrdata
		self.coin=coin
		self.afargs=format_args
		self.afkwargs=format_kwargs

	def __cmp__(self,other):
		return cmp((self.addrdata,self.coin),(other.addrdata,other.coin))
		
	def __hash__(self):
		return hash((self.addrdata,self.coin))
		
	def __str__(self):
		if(self.coin is None):
			return "genericaddrdata:%s" % (hexlify(self.addrdata))

		return self.coin.format_addr(self,*self.afargs,**self.afkwargs)

	def __repr__(self):
		return 'Address(%s)' % (str(self))
