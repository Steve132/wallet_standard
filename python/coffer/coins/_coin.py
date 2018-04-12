from ..key import *
from .. import _base
import _slip44
from .. import _bip32

class Coin(_bip32._Bip32):
	def __init__(self,ticker,is_testnet,bip32_prefix_private,bip32_prefix_public):
		super(Coin,self).__init__(bip32_prefix_private=bip32_prefix_private,
					bip32_prefix_public=bip32_prefix_public) 
		self.ticker=ticker
		self.is_testnet=is_testnet
		#https://github.com/satoshilabs/slips/blob/master/slip-0044.md
		self.childid=_slip44.lookups[self.ticker]


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

	def serializetx(self,txo):
		raise NotImplementedError

	def unserializetx(self,txb):
		raise NotImplementedError

	def denomination_float2whole(self,x):
		raise NotImplementedError
	
	def denomination_whole2float(self,x):
		raise NotImplementedError



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
	def __init__(self,previd,amount,address,meta={}):
		super(Previous,self).__init__(address,amount,meta)
		self.previd=previd
		
	def __repr__(self):
		fmt='%s(previd=%s,address=%s,amount=%d,meta=%r'
		tpl=(
			type(self).__name__,
			self.previd,
			self.address,
			self._amount,
			self.meta
			)
		return fmt % tpl


#class SubmittedPrevious(Previous):
#	def __init__(self,previd,amount,address,height,confirmations=0,meta={}):
#		super(Previous,self).__init__(previd,amount,address,meta)
#		self.height=height
#		self.confirmations=confirmations

class Transaction(object):
	def __init__(self,unspents,dsts,meta={}):
		self.prevs=prevs
		self.dsts=dsts
		self.meta=meta

		#self.confirmations=confirmations
		#self.time=None
	
