from ..key import *
from .. import _base
import _slip44
from .. import _bip32
from binascii import hexlify,unhexlify

class Coin(_bip32._Bip32):
	def __init__(self,ticker,is_testnet,bip32_prefix_private,bip32_prefix_public):
		super(Coin,self).__init__(bip32_prefix_private=bip32_prefix_private,
					bip32_prefix_public=bip32_prefix_public) 
		self.ticker=ticker
		self.is_testnet=is_testnet
		#https://github.com/satoshilabs/slips/blob/master/slip-0044.md
		self.childid=_slip44.lookups[self.ticker]

	def __cmp__(self,other):
		cv=cmp(self.ticker.lower(),other.ticker.lower())
		if(cv==0):
			return cmp(self.is_testnet,other.is_testnet)
		return cv
	def __hash__(self):
		return hash(self.ticker.lower()+str(self.is_testnet))
		

	def pubkeys2addr(self,pubkeys,*args,**kwargs):
		raise NotImplementedError


	def parse_addr(self,addrstring):
		raise NotImplementedError

	def format_addr(self,addr,*args,**kwargs):
		raise NotImplementedError


	def parse_privkey(self,pkstring):
		raise NotImplementedError

	def format_privkey(self,privkey):
		raise NotImplementedError


	def parse_pubkey(self,pkstring):
		return PublicKey(unhexlify(pkstring))

	def format_pubkey(self,pubkey):
		return hexlify(pubkey.pubkeydata)


	def parse_tx(self,txstring):
		raise NotImplementedError

	def format_tx(self,txo):
		raise NotImplementedError

	def format(self,obj,*args,**kwargs):
		if(isinstance(obj,PrivateKey)):
			return self.format_privkey(obj,*args,**kwargs)
		if(isinstance(obj,PublicKey)):
			return self.format_pubkey(obj,*args,**kwargs)
		if(isinstance(obj,Address)):
			return self.format_addr(obj,*args,**kwargs)
		if(isinstance(obj,Transaction)):
			return self.format_tx(obj,*args,**kwargs)
		if(isinstance(obj,_bip32.ExtendedKey)):
			return str(obj)
		raise Exception("I don't know how to format %r" % (obj))


	def denomination_float2whole(self,x):
		raise NotImplementedError
	
	def denomination_whole2float(self,x):
		raise NotImplementedError


	def txpreimage(self,tx):
		raise NotImplementedError

	def signtx(self,tx,privkeys):
		raise NotImplementedError

	def blockchain(self,*args,**kwargs):
		raise Exception("Could not find a suitable block-explorer interface instance for '%s'" % (self.ticker))
			
			
class Output(object):
	@staticmethod	
	def _amountcheck(x):
		if(not isinstance(x, (int, long))):
			raise Exception("Amount must be an integer not %r" % (type(x)))
		return x

	def __init__(self,address,amount,meta={}):
		self.address=address
		self._amount=Output._amountcheck(amount)
		self.meta=meta
	@property
	def amount(self):
		return self._amount
	@amount.setter
	def amount(self,x):
		self._amount=Output._amountcheck(amount)

class Previous(Output):
	def __init__(self,previd,amount,address,meta={},spentpid=None):
		super(Previous,self).__init__(address,amount,meta)
		self.previd=previd
		self.spentpid=spentpid

	def __repr__(self):
		fmt='%s(previd=%s,address=%s,amount=%d,meta=%r,spentpid=%s)'
		tpl=(
			type(self).__name__,
			self.previd,
			self.address,
			self._amount,
			self.meta,
			self.spentpid
			)
		return fmt % tpl


#class SubmittedPrevious(Previous):
#	def __init__(self,previd,amount,address,height,confirmations=0,meta={}):
#		super(Previous,self).__init__(previd,amount,address,meta)
#		self.height=height
#		self.confirmations=confirmations

class Transaction(object):
	def __init__(self,prevs,dsts,meta={},txid=None):
		self.prevs=prevs
		self.dsts=dsts
		self.meta=meta
		self.signatures=None
		self.txid=None
		#self.confirmations=confirmations
		#self.time=None

	def __repr__(self):
		fmt='Transaction(txid=%r,prevs=%r,dsts=%r,meta=%r)'
		tpl=(
			self.txid,
			self.prevs,
			self.dsts,	
			self.meta
			)
		return fmt % tpl
	
