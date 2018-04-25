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
			components=[(h(int(x.strip("'HhsS"))) if ("'" in x or "H" in x.lower()) else int(x)) for x in components]
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

	def xkey_iterate(self,xkey,paths):
		for p in paths:
			yield p,self.descend(xkey,p)



#this represents a security bug of a sort.  It has to.  Because you can pass 0-20320301h to a path.  And 0-200202321h to a path.
#you could stop it with a warning error message but it's some kind of security problem without a threshold.  Even low thresholds would be a target for multiple paths.
#(therefore must premultiply)

starpath=0x7FFFFFFF
PathNum=collections.namedtuple('PathNum', ['value','is_hardened'])
PathRange=collections.namedtuple('PathRange', ['lower','upper','is_hardened'])
solidvalre=re.compile(r"(?:(\d+)|\*)([shSH']?)",re.UNICODE)
#split groups too. also inclusion
def paths(pathstring,maxaddrs=1000000):
	def parse_pathnum(x):
		mo=solidvalre.match(x)
		if(not mo):
			raise Exception("Failed to match %r to a path integer" % (x))
		ival=mo.group(1)
		if(ival is not None):
			ival=int(ival)
		is_hardened=len(mo.group(2)) > 0 and mo.group(2).lower()!='s'
		return PathNum(value=ival,is_hardened=is_hardened)
	def parse_range(x):
		asbs=x.split('-')
		if(len(asbs) > 2):
			raise Exception("Too many elements in range %r" % (x))
		a=parse_pathnum(asbs[0])
		if(len(asbs) == 2):				 
			b=parse_pathnum(asbs[1])
		elif(len(asbs) == 1):
			b=a
		else:
			raise Exception("Not enough elements in range %r" % (x))

		newa=0 if a.value is None else a.value
		newb=starpath if b.value is None else b.value

		is_hardened=a.is_hardened or b.is_hardened
		a=PathNum(newa,is_hardened)
		b=PathNum(newb,is_hardened)
		
		a,b=sorted([a,b],key=lambda p: p.value)
		
		return PathRange(lower=a,upper=b,is_hardened=is_hardened)

	def parse_subpath(x):
		subranges=[parse_range(r) for r in x.split(',')]
		def fold_subranges(sri):
			 #this should be an optimization.   It can be done efficiently by sorting the beginning of each start range and seeing if any begin at the current end and then folding until none do then popping.
			sro=[]
			ssri=sorted(sri,key=lambda r: r.lower.value,reverse=True)
			crange=None
			while(len(ssri)):
				if(crange is None):
					crange=ssri.pop()
					continue
				nx=ssri.pop()
				if(nx.lower.value <= crange.upper.value):
					crange.upper.value=max(nx.upper.value,crange.upper.value)
				else:
					sro.append(crange)
					crange=nx
			if(crange is not None):
				sro.append(crange)
			return sro
		hardened_subranges=[r for r in subranges if r.is_hardened]
		hardened_subranges=fold_subranges(hardened_subranges)
		softened_subranges=[r for r in subranges if not r.is_hardened]
		softened_subranges=fold_subranges(softened_subranges)
		#print(softened_subranges)
		return hardened_subranges+softened_subranges

	def subpath_iterable(subpath):
		def subrange_iterable(subrange):
			return itertools.imap(lambda p: str(p)+('h' if subrange.is_hardened else ''),xrange(subrange.lower.value,subrange.upper.value+1))
		return itertools.chain.from_iterable([subrange_iterable(sr) for sr in subpath])
	def subpath_size(subpath):
		return sum([sr.upper.value-sr.lower.value for sr in subpath])
	
	
	
	subpaths=pathstring.strip('/').split('/')
	subpaths=[parse_subpath(sp) for sp in subpaths]
	infinite_subpathi=None
	for spi,sp in enumerate(subpaths):
		for sr in sp:
			if(sr.upper.value==starpath):
				if(infinite_subpathi is not None):
					raise Exception("There can only be one wildcard in a path expression")
				else:
					infinite_subpathi=spi
	infiter=["XXh"]
	if(infinite_subpathi is not None):
		isubpath=subpaths[infinite_subpathi]
		subpaths=subpaths[:infinite_subpathi]+subpaths[infinite_subpathi+1:]
		infiter=subpath_iterable(isubpath)

	totalsize=1
	for sp in subpaths:
		totalsize*=subpath_size(sp)

	if(totalsize > maxaddrs):
		raise Exception('The path "%s" generates more keys than the supplied limit of %d' % (pathstring,maxaddrs))

	for ispvalue in infiter:
		spiters=[subpath_iterable(sp) for sp in subpaths]
		for pout in itertools.product(*spiters):
			a=list(pout)
			if(infinite_subpathi is not None):
				a.insert(infinite_subpathi,ispvalue)
			yield str(ispvalue)+'/'+'/'.join(pout)
		

if __name__=='__main__':
	for p in paths('0h/0h-10h,15/0-*'):
		print(p)

#http://www.ietf.org/rfc/rfc1738.txt
#$-_.+!*'(),
#standard path uri for 
#base58c
#pre='\x22\x56\x53'+64 bits of hash160 which makes (xidXXXXXXX) in base58c (TODO: use () or just raw xid?
#path is (xid) OR rangeset, where rangeset is range(,range)* and range is int(h|'|H)?(-'*' OR int(h|'|H))
#That's the path component.  URI component is
#bip32://[slip44string][:network (main/test.  default main)]/path
#try to get this to be a bip?

#- means range mix inclusive, _means range donotmix
#comma means include1 inclusive, +means seperate exclusive

#bip32://btc:main/m/44h/60h+0h+145h/0h-15h,5h/45-65,100/0-1
#bip32://btc:main/m/44h/60h,0h,145h/0h-15h,5h/45-65,100/0-1
#bip32://btc:main/m/44h/60h,0h,145h/0h-15h,5h/45-65,100/0-1
#bip32://btc:main/m/44h/60h,0h,145h/0h-15h,5h/45-65,100/0-1
#bip32://btc:main/m/44h/60h,0h,145h/0h-15h,5h/45-65,100/0-1
#xpub://btc:main/m/44h/60h
#two subbips.  One for path and one for URI
#path
#there can only be one '*' in the whole URI ??

#	uri='bip32://' authority '/' path
#	authority=chain   #['+' chain]?
#	chain=\a+ [':' \a+]?
#	path:= root [label]? ['/' subpath]*
#	root:='m' | xpubstmt  #| xsi		#xsi (id master seed)
#	xpubstmt:= xpubstr ['!' solidroot ]? 
#	solidroot:=solidval ['.' solidval]*
#	solidval1:= \d+('h'|'H'|'\''|'s'|'S')?
#	solidval1:= \d+('h'|'H'|'\''|'s'|'S')?
#	subpath=subrange [(','|'+') subrange]*
#	subrange=solidval [('-','_') (solidval | '*')]? [label]?
#	label='(' urlencodedstring ')'

#topub(key(m/0'/0'))/0/0 #ALLOWED
#topub(key(m/0'/0'))/0'  #NOT ALLOWED
#P(m/0'/0')/0/0
#K=P(m/44'/24'/6)
#k/b = ckd(k,b)
#key/b'/c' = ckd_hard(ckd_hard(key,b),c) 
#m/419'/575'/11'/99'/*/13
#m/44'/0'/0'/*/0 for i in 0 to infinity
#m/*/0
#m/44'/0'/0'/*/1
#m/0'/0'/0'/*/0
#m/0'/*
#J=P(m/44'/0'/0')
#J/*/0    m/44'/0'/0'/*/0
#J/*
#J,childpathsregex  <-iterate all addresses
#private(J),childpathsregex <-  get all private keys from privJ
#m,44'/0'/0' <--get privJ from seed entropy.
#44'/145'/0'/0/0
#bip32://btc:main/m/44h/60h,0h,145h/0h-15h,5h/45-*,100/0-1
#bip32://btc:main/m/44h/50/23/xpub6BepLctGphRm3trCJcYEx5mWNysBBz8AaTsMbkoyJ6QTUnxcu82bm47gycmjjT3TzYBqkHwfH4JkCXwyKvXTFiStcnUJXmqqnaKEbNzrAr7/45-*,100/0-1
#m/44'/

#44h_60h,0h,145h_0h-15h,5h_45-*,100_0-1

#purpose: communicate 

def parse_xurl_path(x):
	items=filter(None,'/'.split(x))
	items=[parse_b201_subpath(r) for r in items]
	#todo error
	return items

def parse_xurl_root(x):
	if(x.lower() == 'm'):
		return 'm'
	xp=ExtendedKey(x)
	if(xp.is_private()):
		raise Exception("parsed xpub root cannot be private")

def parse_xurl_subrange(x):
	items=filter(None,','.split(x))
	items=[parse_b201_subrange(r) for r in items]
	return items

def parse_xurl_subpath(x):
	items=filter(None,','.split(x))
	root=parse_b201_root(x[0])
	items=[parse_b201_subrange(r) for r in items[:1]]
	return [root]+items

class PathIterator(object):
	def __init__(self,pathstr):
		pass

#hierarchical wallet
#sign
#class Wallet(object):
#	def addresses(): #return a series of address,tickers
#		pass
#	def add(self,keyobject,coin,meta=None): #..must be a (xpub or xpriv) or (priv or pub) OBJECT or string
#		pass
	
