from ..key import *
from .. import _base
from ..transaction import *
import _slip44
from .. import _bip32
from binascii import hexlify,unhexlify
from ..lib.index import IndexBase
#todo change this to own bip32 as an object
class Coin(_bip32._Bip32,IndexBase):
	def __init__(self,ticker,is_testnet,bip32_prefix_private,bip32_prefix_public):
		super(Coin,self).__init__(bip32_prefix_private=bip32_prefix_private,
					bip32_prefix_public=bip32_prefix_public) 
		self.ticker=ticker.upper()
		self.is_testnet=is_testnet

		if('-TEST' in self.ticker):
			self.is_testnet=True
		elif(self.is_testnet):
			self.ticker+='-TEST'
		if(self.is_testnet):
			self.childid=0x80000001
		else:
			#https://github.com/satoshilabs/slips/blob/master/slip-0044.md
			self.childid=_slip44.lookups[self.ticker]

	def __cmp__(self,other):
		return cmp(self.ticker.upper(),other.ticker.upper())
	
	def __hash__(self):
		return hash(self.ticker.upper())
		

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
	
	def hdpath_generator(self):
		def default_gen(self,account=0):
			return [_bip32.h(44),_bip32.h(self.childid),_bip32.h(account)]
		return default_gen
