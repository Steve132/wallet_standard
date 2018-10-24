import hashlib,hmac
from binascii import hexlify,unhexlify
import struct
import _crypto
import _base
		
class PublicKey(object):
	def __init__(self,pubkeydata,is_compressed=None):
		self.pubkeydata=pubkeydata
		self.P,detected_is_compressed=_crypto._decode_pub(pubkeydata)
		
		if(is_compressed==None):
			self.is_compressed=detected_is_compressed
		else:
			self.pubkeydata=_crypto._encode_pub(self.P,is_compressed)

	def decompressed(self):
		return self.P

	def __add__(self,o):
		return PublicKey(_crypto.pubkey_add(self.pubkeydata,o.pubkeydata,compressed=self.is_compressed),compressed=self.is_compressed)

	def __cmp__(self,other):
		return cmp(self.pubkeydata,other.pubkeydata)
		
	def __hash__(self):
		return hash(self.pubkeydata)

#TODO CANNOT HANDLE UNCOMPRESSED
#TODO compressed private keys are 33 bytes long
class PrivateKey(object):
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
		return PublicKey(pkd,is_compressed=True)

	def __add__(self,o):
		return PrivateKey(_crypto.privkey_add(self.privkeydata,o.privkeydata),is_compressed=self.is_compressed)
	
	def __cmp__(self,other):
		return cmp(self.privkeydata,other.privkeydata)
		
	def __hash__(self):
		return hash(self.privkeydata)

	def sign(self,msghash_bytes,use_der=False):
		return _crypto.sign(msghash_bytes,self.privkeydata,compressed=self.is_compressed,use_der=use_der)


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
