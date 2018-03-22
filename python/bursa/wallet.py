import hashlib,hmac
from binascii import hexlify,unhexlify
import struct
import _crypto
import _slip44
import _base

def _hparse(s):
	try:
		a=int(s,16)
		return unhexlify(s)
	except ValueError:
		return s

_xkeydatastruct=struct.Struct("!LBLL32s33s")
class ExtendedKey(object):
	def __init__(self,version,depth=None,fingerprint=None,child=None,chaincode=None,keydata=None):
		if(depth is None and fingerprint is None and child is None and chaincode is None and keydata is None):
			data=_base.base58c2bytes(b58str)
			self.version,self.depth,self.fingerprint,self.child,self.chaincode,self.keydata=_xkeydatastruct.unpack(data)
		else:
			self.version=version
			self.depth=depth
			self.fingerprint=fingerprint
			self.child=child
			self.chaincode=chaincode
			self.keydata=keydata
		
	def __str__(self):
		data=_xkeydatastruct.pack(self.version,self.depth,self.fingerprint,self.child,self.chaincode,self.keydata)
		return _base.bytes2base58c(data)

	def toxpub(self):
		if(not self.is_private()):
			return self
		
			
	def is_private(self):
		return (xkey.keydata[0]==b'\x00')
		
class PublicKey(object):
	def __init__(self,pubkeydata,is_compressed=None):
		self.pubkeydata=pubkeydata
		self.is_compressed=is_compressed

#TODO CANNOT HANDLE UNCOMPRESSED

class PrivateKey(object):
	def __init__(self,privkeydata,is_compressed=True):
		self.privkeydata=privkeydata
		self.is_compressed=is_compressed
		if(not self.is_compressed):
			raise Exception("Uncompressed private keys not implemented!")
		if(not _crypto.verify_privkey(self.privkeydata)):
			raise Exception("Invalid private key")

	def pub(self):
		pkd=_crypto.privkey_to_compressed_pubkey(self.privkeydata)
		return PublicKey(pkd,is_compressed=True)
		

#hierarchical wallet
#sign
class Wallet(object):
	def addresses(): #return a series of address,tickers
		pass
	def add(self,keyobject,coin,meta=None): #..must be a (xpub or xpriv) or (priv or pub) OBJECT or string
		pass
	
