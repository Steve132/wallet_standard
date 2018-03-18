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
		
def h(k):
	return (abs(k) | (1 << 31)) & (0xFFFFFFFF)


class Coin(object):
	def __init__(self,ticker,is_testnet):
		self.ticker=ticker
		self.is_testnet=is_testnet
	
	def seed2master(self,seed):
		seed=_hparse(seed)
		digest=hmac.new(b"Bitcoin seed",seed,hashlib.sha512).digest()
		I_left,I_right=digest[:32],digest[32:]
		Ilp=_parse256(I_left) #errror check
		version=self.bip32_prefix_private if private else self.bip32_prefix_public
		return ExtendedKey(version,0,0,0,I_right,b'\x00'+I_left)

	def descend(self,xkey,child,ignore_tag=False):
		def _descend_extend(xkeyparent,isprivate,data,childindex):
			data+=unhexlify("%08X" % (childindex))
			digest=hmac.new(xkey.chaincode,data,hashlib.sha512).digest()
			I_left,I_right=digest[:32],digest[32:]
			Ilp=PrivateKey(I_left,is_compressed=True) #errror check
			if(isprivate):
				child_key=b'\x00'+_crypto.privkey_add(I_left,xkey.keydata[1:])
				parent_pubkey=PrivateKey(xkey.keydata[1:],is_compressed=True).pub().pubkeydata
			else:
				pk=Ilp.pub().pubkeydata
				child_key=_crypto.pubkey_add(pk,xkey.keydata)
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
			components=child.strip().split("/")
			if(_checkvoidpath(components[0])):
				components=components[1:]
			if(components[-1]==''):
				components=components[:-1]
			components=[(h(int(x.strip("'H"))) if ("'" in x or "H" in x) else int(x)) for x in components]
			return reduce(lambda xk,c: self.descend(xk,c),components,xkey)
		try:
			children=list(child)
			return reduce(lambda xk,c: self.descend(xk,c),children,xkey)
		except TypeError:
			pass

		try:
			child=int(child)
		except TypeError:
			raise Exception("Could not descend")

		isHardened=(child >= 0x70000000)
		
		private=(xkey.keydata[0]==b'\x00')
		
		if(private and (ignore_tag or xkey.version==self.bip32_prefix_private)):
			if(isHardened):
				data=xkey.keydata
			else:
				data=_crypto.privkey_to_compressed_pubkey(xkey.keydata)
			return _descend_extend(xkey,True,data,child)
		elif(ignore_tag or xkey.version==self.bip32_prefix_public):
			if(isHardened):
				raise Exception("Cannot find the child of hardened key %s" % (xkey))
			else:
				data=xkey.keydata
				return _descend_extend(xkey,False,data,child)
		else:
			raise Exception("The key type disagrees with the tag type")
	
	#https://github.com/satoshilabs/slips/blob/master/slip-0044.md
	def chainid(self):
		return _slip44.lookups[self.ticker]

	def pubkeys2addr_bytes(self,pubkeys,*args,**kwargs):
		raise NotImplementedError

	def pubkeys2addr(self,pubkeys,*args,**kwargs):
		raise NotImplementedError

	def parse_privkey(self,pkstring):
		raise NotImplementedError

	def parse_pubkey(self,pkstring):
		raise NotImplementedError
	
	
	
class SatoshiCoin(Coin): #a coin with code based on satoshi's codebase
	def __init__(self,ticker,is_testnet):
		super(SatoshiCoin,self).__init__(ticker,is_testnet)

	#https://en.bitcoin.it/wiki/List_of_address_prefixes
	def pubkeys2addr_bytes(self,pubkeys,*args,**kwargs):
		if(isinstance(pubkeys,basestring)):
			pubkeys=[pubkeys] #assume that if it's a single argument, then it's one pubkey
		multisig=len(pubkeys) > 1
		if(multisig):#P2SH multisig
			pass #TODO implement this #self.sh_version()
		else:  #P2PKH
			h160=_base.hash160(pubkeys[0].keydata)
			return chr(self.pkh_prefix)+h160

	def pubkeys2addr(self,pubkeys,*args,**kwargs):
		abytes=self.pubkeys2addr_bytes(pubkeys,*args,**kwargs)
		return _base.bytes2base58c(abytes)

	#https://github.com/bitcoinjs/bitcoinjs-lib/blob/master/src/networks.js
	#https://github.com/iancoleman/bip39/blob/master/src/js/bitcoinjs-extensions.js
	
	def parse_privkey(self,pkstring):
		try:
			ak=int(pkstring,16)
			pkshex=pkstring
			if(pkshex[:2].lower()=='0x'):
				pkshex=pkshex[2:]
			if(len(pkshex)!=64 and len(pkshex)!=66):
				raise Exception("'%s' is not the right size to be interpreted as a hex private key" % (pkshex))
			byts=unhexlify(pkshex)
			return PrivateKey(pkbytes[:32],is_compressed=(len(pkshex)==66))
		except ValueError:
			pass
				
		pkbytes=_base.base58c2bytes(pkstring)
		if(pkbytes[0] != chr(self.wif_prefix)):
			raise Exception("WIF private key %s could not validate for coin %s.  Expected %d got %d." % (pkstring,self.ticker,ord(pkbytes[0]),self.wif_prefix))
		if(len(pkbytes)==34):
			return PrivateKey(pkbytes[1:-1],is_compressed=True)
		else:
			return PrivateKey(pkbytes[1:],is_compressed=False)

	def parse_pubkey(self,pkstring):
		raise NotImplementedError


#TODO switch all properties to true property implementations.
class SegwitCoin(object):
	def __init__(self,ticker,is_testnet):
		super(SegwitCoin,self).__init__(ticker,is_testnet)
	
	#https://github.com/bitcoin/bips/blob/master/bip-0141.mediawiki#p2wpkh
	def pubkeys2addr_bytes(self,pubkeys,*args,**kwargs):
		segwit=kwargs.get('segwit',False)
		embed_in_legacy=kwargs.get('embed_in_legacy',True)
		bech32=kwargs.get('bech32',False)

		if(isinstance(pubkeys,basestring)):
			pubkeys=[pubkeys] #assume that if it's a single argument, then it's one pubkey
		multisig=len(pubkeys) > 1
		if(not segwit):
			return super(SegwitCoin,self).pubkeys2addr_bytes(pubkeys,*args,**kwargs)
		else:
			#if(multisig) probably goes out front for embedding or not embedding case
			if(embed_in_legacy):
				if(multisig): #P2WSH-P2SH
					pass	#TODO IMPLEMENT THIS
				else:		#P2WPKH-P2SH
					pass #TODO IMPLEMENT THIS
			else:
				if(multisig): #P2WSH
					pass #TODO IMPLEMENT THIS
				else:#P2WPKH
					pass #TODO IMPLEMENT THIS

				
			
