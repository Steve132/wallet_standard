import hashlib,hmac
from binascii import hexlify,unhexlify
import struct
import _crypto
import _base


from key import *

def h(k):
	return (abs(k) | (0x80000000)) & (0xFFFFFFFF)

def _hparse(s):
	try:
		a=int(s,16)
		return unhexlify(s)
	except ValueError:
		return s

def checkvoidpath(p):
	return (p=="/" or p=="" or p.lower()=="m")

def splitpath(child):
	pall=child.strip().lstrip('/').rstrip('/').split("/")
	if(checkvoidpath(pall[0])):
		return pall[1:]
	return pall
def evalpath(components):
	finalcomp=[]
	for x in components:
		xistr=int(x.strip("'HhsS"))
		ival=int(xistr)
		if("'" in x or "h" in x.lower()):
			finalcomp.append(h(ival))
		else:
			finalcomp.append(ival)
	return finalcomp
	
#TODO: implement https://github.com/satoshilabs/slips/blob/master/slip-0032.md
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

class Bip32Settings(object):
	def __init__(self,prefix_private,prefix_public,seed_salt="Bitcoin seed",*pkargs,**pkkwargs):
		self.prefix_private=prefix_private
		self.prefix_public=prefix_public
		self.seed_salt=seed_salt
		self.pkargs=pkargs
		self.pkkwargs=pkkwargs
		
class Bip32(object):
	def seed2master(self,seed,bip32_settings):
		seed=_hparse(seed)
		digest=hmac.new(bip32_settings.seed_salt,seed,hashlib.sha512).digest()
		I_left,I_right=digest[:32],digest[32:]
		Ilp=PrivateKey(I_left,is_compressed=True) #errror check
		return ExtendedKey(bip32_settings.prefix_private,0,0,0,I_right,b'\x00'+I_left)

	def xpriv2xpub(self,xkey,bip32_settings):
		xkey=self.parse_xkey(xkey)
		return xkey._xpub(bip32_settings.prefix_public)

	def descend(self,xkey,child,ignore_tag=False):	#todo add settings load here to re-establish public private validity check
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

		xkey=self.parse_xkey(xkey)

		if(isinstance(child,basestring)):
			components=splitpath(child)	
			finalcomp=evalpath(components)
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
		
		if(private):
			if(isHardened):
				data=xkey.keydata
			else:
				data=PrivateKey(xkey.keydata,is_compressed=True).pub().pubkeydata
			return _descend_extend(xkey,True,data,child)
		else:
			if(isHardened):
				raise Exception("Cannot find the child of hardened public key %s" % (xkey))
			else:
				data=xkey.keydata
				return _descend_extend(xkey,False,data,child)

	def parse_xkey(self,xkey):
		if(isinstance(xkey,basestring)):
			xkey=ExtendedKey(xkey)
		return xkey

import re,itertools,collections
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
			yield '/'.join(a)



class XPubAddressSet(account.AddressSet):
	def __init__(self,coin,xkey,path="0/*",root=None,*bip32args,**bip32kwargs): #change is "1/*"
		super(XPubAddressSet,self).__init__(coin)
		xkey=coin.parse_xkey(xkey)
		if(xkey.is_private()):
			bip32_settings=coin.load_bip32_settings(prefix_private=xkey.version,*bip32args,**bip32kwargs)
		else:
			bip32_settings=coin.load_bip32_settings(prefix_public=xkey.version,*bip32args,**bip32kwargs)
		self.xpub=self.coin.xpriv2xpub(xkey,bip32_settings)
		self.coin=coin
		self.path=path
		self.root=root
		self.settings=bip32_settings

	def xpub_iter(self):
		for p in paths(self.path):
			yield self.coin.descend(self.xpub,p)

	def path2addr(self,p):
		return self.coin.pubkeys2addr([vpub.key()],*self.settings.pkargs,**self.settings.pkkwargs)

	def __iter__(self):
		for vpub in self.path_iter():
			yield self.path2addr(vpub)

class Bip32Account(account.OnChainAddressSetAccount):
	def __init__(self,coin,xkey,root,internal_path="1/*",external_path="0/*",authref=None,*bip32args,**bip32kwargs):
		self.coin=coin
		self.type='bip32'
		internal=XPubAddressSet(coin,xkey=xkey,path=internal_path,root=root,*bip32args,**bip32kwargs)
		external=XPubAddressSet(coin,xkey=xkey,path=external_path,root=root,*bip32args,**bip32kwargs)
		self.xpub=internal.xpub
		self.bip32args=bip32args
		self.bip32kwargs=bip32kwargs
		super(Bip32Account,self).__init__(internal=[internal],external=[external],authref=authref)

class Bip32SeedAuth(Auth):
	def __init__(self,seed):
		self.seed=seed

	def _genmaster(self,coin,*bip32args,**bip32kwargs):
		bip32_settings=coin.load_bip32_settings(*bip32args,**bip32kwargs)
		master=coin.seed2master(self.seed,bip32_settings)
		master,bip32_settings
	
	def to_b32auth(self,coin,root,internal_path="1/*",external_path="0/*",*bip32args,**bip32kwargs):
		#bip32_settings=coin.load_bip32_settings(*bip32args,**bip32kwargs)

	@staticmethod
	def from_mnemonic(words,passphrase=None):
		seed=mnemonic.words_to_seed(words,passphrase)
		return Bip32SeedAuth(seed)
	
	#def childauth(self,account):
	#masterxpriv=account.coin.seed2master(self.seed)
	#xpriv=coin.descend(account.root)
	#return Bip32Auth(account,xpriv,account.root)
	
class Bip32Auth(Auth):
	def __init__(self,xpriv,root):
		self.coin=coin
		self.xpriv=xpriv
		self.root=root

	def childauth(self,account):
		return self
		
	def toaccount(self,coin,root,internal_path="1/*",external_path="0/*",*bip32args,**bip32kwargs):
		#bip32_settings=coin.load_bip32_settings(*bip32args,**bip32kwargs)
		master=coin.seed2master(self.seed,bip32_settings)
		xpriv=coin.descend(master,root)
		return account.Bip32Account(coin,xpriv,root=root,authref=authref,*bip32args,**bip32kwargs)





