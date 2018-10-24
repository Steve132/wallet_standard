from ..key import *
from .. import _base
from ..transaction import *
from .. import bip32
from binascii import hexlify,unhexlify
from ..lib.index import IndexBase
from _slip44 import lookups as slip44table
#todo change this to own bip32 as an object
from collections import namedtuple
from ..chain import Chain

class ForkMixin(object):
	ForkInfo=namedtuple('ForkInfo',['ticker','timestamp','height','forkUSD'])
	def fork_info(self):
		raise NotImplementedError

class Denomination(IndexBase):
	@property
	def denomination_scale(self):
		raise NotImplementedError

	def denomination_float2whole(self,x):
		return int(x*self.denomination_scale)
	
	def denomination_whole2float(self,x):
		ipart,fpart=divmod(int(x),int(self.denomination_scale))
		return ipart+float(fpart)/self.denomination_scale;
	
	@property
	def ticker(self):
		raise NotImplementedError
	
	def _reftuple(self):
		return (self.ticker)

class Coin(bip32.Bip32,Chain,Denomination,IndexBase):
	def __init__(self,ticker,is_testnet):
		super(Coin,self).__init__()

		self._ticker=ticker
		self.is_testnet=is_testnet

		if('-TEST' in self._ticker):
			self.is_testnet=True
		elif(self.is_testnet):
			self._ticker+='-TEST'

		if(self.is_testnet):
			self.bip44_id=0x80000001
		else:
			#https://github.com/satoshilabs/slips/blob/master/slip-0044.md
			self.bip44_id=slip44table[ticker]

		
	@property
	def ticker(self):
		return self._ticker

	@property
	def chainid(self):
		return self.ticker

	def __repr__(self):
		return self.ticker

	def load_bip32_settings(self,prefix_private=None,prefix_public=None,*args,**kwargs):
		if(not self.is_testnet):
				bip32_prefix_private=0x0488ADE4
				bip32_prefix_public=0x0488B21E
		else:
				bip32_prefix_private=0x04358394
				bip32_prefix_public=0x043587CF

		if(prefix_private is not None and prefix_private not in [bip32_prefix_private]):
			 raise Exception("Private Prefix %X does not match expected prefix %X for coin %s" % (prefix_private,bip32_prefix_private,self.ticker))
		if(prefix_public is not None and prefix_public not in [bip32_prefix_public]):
			 raise Exception("Public Prefix %X does not match expected prefix %X for coin %s" % (prefix_public,bip32_prefix_public,self.ticker))
			
		return bip32.Bip32Settings(prefix_private=bip32_prefix_private,prefix_public=bip32_prefix_public,*args,**kwargs)

	def _reftuple(self):
		return (self.ticker,self.is_testnet)

	def pubkeys2addr(self,pubkeys,xpub=None,*args,**kwargs):
		raise NotImplementedError

	def parse_addr(self,addrstring):
		raise NotImplementedError

	def format_addr(self,addr,*args,**kwargs):
		raise NotImplementedError

	def parse_privkey(self,pkstring):
		pkshex=pkstring
		if(pkshex[:2].lower()=='0x'):
			pkshex=pkshex[2:]
		if(len(pkshex)!=64):
			raise Exception("'%s' is not the right size to be interpreted as a hex private key" % (pkshex))
		byts=unhexlify(pkshex)
		return PrivateKey(byts[:32])

	def format_privkey(self,privkey):
		return hexlify(privkey.privkeydata)

	def parse_pubkey(self,pkstring):
		pkshex=pkstring
		if(pkshex[:2].lower()=='0x'):
			pkshex=pkshex[2:]
		if(len(pkshex)!=66):
			raise Exception("'%s' is not the right size to be interpreted as a hex compressed public key" % (pkshex))
		byts=unhexlify(pkshex)	
		return PublicKey(byts)

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
		if(isinstance(obj,bip32.ExtendedKey)):
			return str(obj)
		raise Exception("I don't know how to format %r" % (obj))

	#privkeys is a mapping from an address to a list of privkeys for signing an on-chain transaction
	def signtx(self,tx,privkeys):
		raise NotImplementedError

	def blockchain(self,*args,**kwargs):
		raise Exception("Could not find a suitable block-explorer interface instance for '%s'" % (self.ticker))

	


