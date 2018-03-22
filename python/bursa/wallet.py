import hashlib,hmac
from binascii import hexlify,unhexlify
import struct
import _crypto
import _slip44
import _base
		
class PublicKey(object):
	def __init__(self,pubkeydata,is_compressed=None):
		self.pubkeydata=pubkeydata
		self.is_compressed=is_compressed
	def __add__(self,o):
		return PublicKey(_crypto.pubkey_add(self.pubkeydata,o.pubkeydata),is_compressed=self.is_compressed)

#TODO CANNOT HANDLE UNCOMPRESSED

class PrivateKey(object):
	def __init__(self,privkeydata,is_compressed=True):
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
	

_xkeydatastruct=struct.Struct("!LBLL32s33s")
class ExtendedKey(object):
	def __init__(self,version,depth=None,fingerprint=None,child=None,chaincode=None,keydata=None):
		if(isinstance(version,basestring) and depth is None and fingerprint is None and child is None and chaincode is None and keydata is None):
			data=_base.base58c2bytes(version)
			version,depth,fingerprint,child,chaincode,keydata=_xkeydatastruct.unpack(data)
				
		self.version=version
		self.depth=depth
		self.fingerprint=fingerprint
		self.child=child
		self.chaincode=chaincode
		self.keydata=keydata
		
		
	def __str__(self):
		data=_xkeydatastruct.pack(self.version,self.depth,self.fingerprint,self.child,self.chaincode,self.keydata)
		return _base.bytes2base58c(data)
			
	def is_private(self):
		return (self.keydata[0]==b'\x00')

	def xpub(self,pubversion):
		if(not self.is_private()):
			return self
		else:
			return ExtendedKey(pubversion,self.depth,self.fingerprint,self.child,self.chaincode,PrivateKey(self.keydata[1:],is_compressed=True).pub().pubkeydata)

		

#hierarchical wallet
#sign
class Wallet(object):
	def addresses(): #return a series of address,tickers
		pass
	def add(self,keyobject,coin,meta=None): #..must be a (xpub or xpriv) or (priv or pub) OBJECT or string
		pass
	
