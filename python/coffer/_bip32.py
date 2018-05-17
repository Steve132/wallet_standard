import hashlib,hmac
from binascii import hexlify,unhexlify
import struct
import _crypto
import _base
from key import *

import re,itertools,collections

def h(k):
	return (abs(k) | (0x80000000)) & (0xFFFFFFFF)

def _hparse(s):
	try:
		a=int(s,16)
		return unhexlify(s)
	except ValueError:
		return s

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

	def _xpub(self,pubversion):
		if(not self.is_private()):
			return self
		else:
			return ExtendedKey(pubversion,self.depth,self.fingerprint,self.child,self.chaincode,PrivateKey(self.keydata[1:],is_compressed=True).pub().pubkeydata)

	def key(self):
		if(self.is_private()):
			return PrivateKey(self.keydata[1:],is_compressed=True)
		else:
			return PublicKey(self.keydata,is_compressed=True)
	def __repr__(self):
		return str(self)

class _Bip32(object):
	def __init__(self,bip32_prefix_private,bip32_prefix_public):
		self.bip32_prefix_private=bip32_prefix_private
		self.bip32_prefix_public=bip32_prefix_public
		self.bip32_seed_salt=b'Bitcoin seed' #Mandatory for bip32

	def seed2master(self,seed):
		seed=_hparse(seed)
		digest=hmac.new(self.bip32_seed_salt,seed,hashlib.sha512).digest()
		I_left,I_right=digest[:32],digest[32:]
		Ilp=PrivateKey(I_left,is_compressed=True) #errror check
		return ExtendedKey(self.bip32_prefix_private,0,0,0,I_right,b'\x00'+I_left)

	def descend(self,xkey,child,ignore_tag=False):
		def _descend_extend(xkeyparent,isprivate,data,childindex):
			data+=unhexlify("%08X" % (childindex))
			digest=hmac.new(xkey.chaincode,data,hashlib.sha512).digest()
			I_left,I_right=digest[:32],digest[32:]
			Ilp=PrivateKey(I_left,is_compressed=True) #errror check
			if(isprivate):
				Irp=PrivateKey(xkey.keydata[1:],is_compressed=True)
				child_key=b'\x00'+(Ilp+Irp).privkeydata
				parent_pubkey=xkey.key().pub().pubkeydata
			else:
				pk=Ilp.pub()+xkey.key()
				child_key=pk.pubkeydata
				parent_pubkey=xkey.keydata
				
			child_chain=I_right
			fg=int(hexlify(_base.hash160(parent_pubkey)[:4]),16)
			return ExtendedKey(xkey.version,xkey.depth+1,fg,childindex,child_chain,child_key)

		if(isinstance(xkey,basestring)):
			xkey=ExtendedKey(xkey)

		if(isinstance(child,basestring)):
			def _checkvoidpath(p):
				return (p=="/" or p=="" or p.lower()=="m")
			
			child=child.strip()
			if(_checkvoidpath(child)):
				return xkey
			components=child.strip().lstrip('/mM').rstrip('/').split("/")	
			finalcomp=[]
			for x in components:
				xistr=int(x.strip("'HhsS"))
				ival=int(xistr)
				if("'" in x or "h" in x.lower()):
					finalcomp.append(h(ival))
				else:
					finalcomp.append(ival)

			return reduce(lambda xk,c: self.descend(xk,c),finalcomp,xkey)
		try:
			children=list(child)
			return reduce(lambda xk,c: self.descend(xk,c),children,xkey)
		except TypeError:
			pass

		try:
			child=int(child)
		except TypeError:
			raise Exception("Could not descend")

		isHardened=(child >= 0x80000000)
		
		private=xkey.is_private()
		
		if(private and (ignore_tag or xkey.version==self.bip32_prefix_private)):
			if(isHardened):
				data=xkey.keydata
			else:
				data=PrivateKey(xkey.keydata,is_compressed=True).pub().pubkeydata
			return _descend_extend(xkey,True,data,child)
		elif(ignore_tag or xkey.version==self.bip32_prefix_public):
			if(isHardened):
				raise Exception("Cannot find the child of hardened key %s" % (xkey))
			else:
				data=xkey.keydata
				return _descend_extend(xkey,False,data,child)
		else:
			raise Exception("The key type disagrees with the tag type")

	def xpriv2xpub(self,xpriv,version=None):
		if(version is None):
			version=self.bip32_prefix_public
		if(isinstance(xpriv,basestring)):
			xpriv=ExtendedKey(xpriv)

		return xpriv._xpub(version)











