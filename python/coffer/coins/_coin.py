from ..wallet import *
from .. import _base
import _slip44
import hashlib

def h(k):
	return (abs(k) | (0x80000000)) & (0xFFFFFFFF)

def _hparse(s):
	try:
		a=int(s,16)
		return unhexlify(s)
	except ValueError:
		return s

class Coin(object):
	def __init__(self,ticker,is_testnet,bip32_prefix_private,bip32_prefix_public,bip32_seed_salt):
		self.ticker=ticker
		self.is_testnet=is_testnet
		#https://github.com/satoshilabs/slips/blob/master/slip-0044.md
		self.childid=_slip44.lookups[self.ticker]

		self.bip32_prefix_private=bip32_prefix_private
		self.bip32_prefix_public=bip32_prefix_public
		self.bip32_seed_salt=b'Bitcoin seed'	#non-negotiable

	
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
				parent_pubkey=PrivateKey(xkey.keydata[1:],is_compressed=True).pub().pubkeydata
			else:
				pk=Ilp.pub()+PublicKey(xkey.keydata,is_compressed=True)
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

		isHardened=(child >= 0x80000000)
		
		private=(xkey.keydata[0]==b'\x00')
		
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

	def pubkeys2addr_bytes(self,pubkeys,*args,**kwargs):
		raise NotImplementedError

	def pubkeys2addr(self,pubkeys,*args,**kwargs):
		raise NotImplementedError

	def parse_privkey(self,pkstring):
		raise NotImplementedError

	def parse_pubkey(self,pkstring):
		raise NotImplementedError

	def parse_addr(self,addrstring):
		raise NotImplementedError

	def xpriv2xpub(self,xpriv,version=None):
		if(version is None):
			version=self.bip32_prefix_public
		if(isinstance(xpriv,basestring)):
			xpriv=ExtendedKey(xpriv)

		return xpriv.xpub(version)

	def serializetx(self,txo):
		raise NotImplementedError
	def unserializetx(self,txb):
		raise NotImplementedError

	def denomination_float2whole(self,x):
		raise NotImplementedError
	
	def denomination_whole2float(self,x):
		raise NotImplementedError


def _amountcheck(x):
	if(not isinstance(x, (int, long))):
		raise Exception("Amount must be an integer not %r" % (type(x)))
	return x

class Output(object):
	def __init__(self,address,amount,meta={}):
		self.address=address
		self._amount=_amountcheck(amount)
		self.meta=meta
	@property
	def amount(self):
		return self._amount
	@amount.setter
	def amount(self,x):
		self._amount=_amountcheck(amount)

class Previous(Output):
	def __init__(self,unspentid,height,confirmations,amount,address,meta={}):
		super(Previous,self).__init__(address,amount,meta)
		self.unspentid=unspentid
		self.height=height
		self.confirmations=confirmations
		
	def __repr__(self):
		fmt='%s(unspentid=%s,address=%s,amount=%d,confirmations=%d,meta=%r'
		tpl=(
			type(self).__name__,
			self.unspentid[:8]+'...:'+self.unspentid.split(':')[-1],
			self.address,
			self._amount,
			self.confirmations,
			self.meta
			)
		return fmt % tpl

class Transaction(object):
	def __init__(self,unspents,dsts,spent=False,confirmations=0,time=None,meta={}):
		self.prevs=prevs
		self.dsts=dsts
		self.spent=False
		self.meta=meta
		self.confirmations=confirmations
		self.time=None
	
