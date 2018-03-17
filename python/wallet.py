import hashlib,hmac
from binascii import hexlify,unhexlify
import struct
import _crypto
import _slip44

#https://github.com/iancoleman/bip39/issues/58#issuecomment-281905574
def _hparse(s):
	try:
		a=int(s,16)
		return unhexlify(s)
	except ValueError:
		return s

def _parse256(I):
	pass #todo: verify if valid key

def _dblsha256(byts):
	return hashlib.sha256(hashlib.sha256(byts).digest()).digest()
def _hash160(byts):
	rmd=hashlib.new('ripemd160')
	rmd.update(hashlib.sha256(byts).digest())
	return rmd.digest()

def _bytes2int(byts):
	return int(hexlify(byts),16)
def _int2bytes(bint,mxlen=None):
	fmt=("\%0%dX" % mxlen) if mxlen else "%X"
	sv=fmt % bint
	sv = '0'+sv if len(sv) & 1 else sv
	return unhexlify(sv)

def _bytes2checksum(byts):
	return _dblsha256(byts)[:4]

def _bytes2baseX(byts,basechars):
	maxint=(1 << (8*len(byts)))-1
	bint=_bytes2int(byts)
	base=len(basechars)
	out=[]
	while(maxint):
		cur=bint % base
		bint //=base
		maxint //=base
		out.append(basechars[cur])
	return "".join(out[::-1][1:]) #todo is this correct?
def _baseX2bytes(bXstr,basechars):
	base=len(basechars)
	bint=0
	maxint=1
	for c in bXstr:
		try:
			dex=basechars.index(c)
			bint=bint*base+dex
			maxint*=base
		except ValueError:
			raise Exception("Error, cannot convert %s to base %d." % (c,base))
	bsize=len(_int2bytes(maxint-1))
	byts=_int2bytes(bint)
	return byts


_b58cs="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
def _bytes2base58c(byts):
	csb=_bytes2checksum(byts)
	bytscs=byts+csb
	return _bytes2baseX(bytscs,_b58cs)

def _base58c2bytes(b58str):
	bytscs=_baseX2bytes(b58str,_b58cs)
	byts,cs=bytscs[:-4],bytscs[-4:]
	csvalidated=_bytes2checksum(byts)
	if(csvalidated!=cs):
		raise Exception("Base58check checksum for %s did not validate" % (b58str))
	return byts

_xkeydatastruct=struct.Struct("!LBLL32s33s")
class ExtendedKey(object):
	def __init__(self,version,depth=None,fingerprint=None,child=None,chaincode=None,keydata=None):
		if(depth is None and fingerprint is None and child is None and chaincode is None and keydata is None):
			data=_base58c2bytes(b58str)
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
		return _bytes2base58c(data)

	def toxpub(self):
		if(not self.is_private()):
			return self
		
			
	def is_private(self):
		return (xkey.keydata[0]==b'\x00')
		

_xkeydatastruct=struct.Struct("!LBLL32s33s")
class PrivateKey(object):
	def __init__(self,serialdata):
		data=_base58c2bytes(b58str)

def h(k):
	return (abs(k) | (1 << 31)) & (0xFFFFFFFF)


class Coin(object):
	def __init__(self,ticker,network='main'):
		self.ticker=ticker
		self.network=network
	
	def seed2master(self,seed):
		seed=_hparse(seed)
		digest=hmac.new(b"Bitcoin seed",seed,hashlib.sha512).digest()
		I_left,I_right=digest[:32],digest[32:]
		Ilp=_parse256(I_left) #errror check
		version=self.masterversion(private=True)
		return ExtendedKey(version,0,0,0,I_right,b'\x00'+I_left)

	def descend(self,xkey,child,ignore_tag=False):
		def _descend_extend(xkeyparent,isprivate,data,childindex):
			data+=unhexlify("%08X" % (childindex))
			digest=hmac.new(xkey.chaincode,data,hashlib.sha512).digest()
			I_left,I_right=digest[:32],digest[32:]
			Ilp=_parse256(I_left) #errror check
			if(isprivate):
				child_key=b'\x00'+_crypto.privkey_add(I_left,xkey.keydata[1:])
				parent_pubkey=_crypto.privkey_to_compressed_pubkey(xkey.keydata[1:])
			else:
				pk=privkey_to_compressed_pubkey(I_left)
				child_key=_crypto.pubkey_add(pk,xkey.keydata)
				parent_pubkey=xkey.keydata
				
			child_chain=I_right
			fg=int(hexlify(_hash160(parent_pubkey)[:4]),16)
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
		
		if(private and (ignore_tag or xkey.version==self.masterversion(private==True))):
			if(isHardened):
				data=xkey.keydata
			else:
				data=_crypto.privkey_to_compressed_pubkey(xkey.keydata)
			return _descend_extend(xkey,True,data,child)
		elif(ignore_tag or xkey.version==self.masterversion(private==False)):
			if(isHardened):
				raise Exception("Cannot find the child of hardened key %s" % (xkey))
			else:
				data=xkey.keydata
				return _descend_extend(xkey,False,data,child)
		else:
			raise Exception("The key type disagrees with the tag type")
	
	#https://github.com/satoshilabs/slips/blob/master/slip-0044.md
	def cointypeid(self):
		return _slip44.lookups[self.ticker]

#segwitcoin
class BTC(Coin):
	def __init__(self,network='main'):
		super(BTC,self).__init__('BTC',network)
	def masterversion(self,private):
		if(self.network=='main'):
			return 0x0488ADE4 if private else 0x0488B21E
		else:
			return 0x04358394 if private else 0x043587CF
	

