#https://www.myetherapi.com/
#curl -H "Content-Type: application/json" -X POST --data '{"jsonrpc":"2.0","method":"eth_getBalance","params":["0x7cB57B5A97eAbe94205C07890BE4c1aD31E486A8", "latest"],"id":1}' https://api.myetherapi.com/eth
#curl -X POST --data '{"jsonrpc":"2.0","method":"eth_getTransactionCount","params":["0xc94770007dda54cF92009BFF0dE90c06F603a09f","latest"],"id":1}'

from coffer.key import *
import coffer._base as _base
from coffer.transaction import *
import _coin
from binascii import hexlify,unhexlify
import impl._keccak as _keccak
import impl._ethtx as _ethtx

class ETH(_coin.Coin):
	def __init__(self,is_testnet=False):
		super(ETH,self).__init__(ticker='ETH',is_testnet=is_testnet) 
	
	def pubkeys2address(self,pubkeys,*args,**kwargs):
		if(len(pubkeys) > 1):
			raise NotImplementedError("TODO: ETH implementation doesn't support multiple pubkeys")
		khash=_keccak.Keccak256()
		key=pubkeys[0]
		pki=key.decoded()
		tv="%064X%064X" % (pki[0],pki[1])
		tv=unhexlify(tv)
		khash.update(tv)
		hx=khash.hexdigest()
		addr=hx[-40:]
		return Address(unhexlify(addr),self,'ethaddr',format_kwargs={'checksum_case':True})

	def parse_addr(self,addrstring,ignore_checksum=False):
		pkshex=addrstring
		if(pkshex[:2].lower()!='0x'):
			raise Exception("%s is not an ETH address because it does not start with 0x" % (addrstring))
		pkshex=pkshex[2:]
		if(len(pkshex)!=40):
			raise Exception("'%s' is not the right size to be interpreted as an ETH address" % (addrstring))
		byts=unhexlify(pkshex)
		if(not ignore_checksum):
			o='0x'+pkshex
			if(o != _keccak.checksum_encode(byts)):
				raise Exception("'%s' did not pass the ETH case-based checksum" % (o))
		return Address(byts,self,'ethaddr',format_kwargs={'checksum_case':True})

	def format_addr(self,addr,checksum_case=True,*args,**kwargs):
		return _keccak.checksum_encode(addr.addrdata)

	def parse_tx(self,txstring):
		raise NotImplementedError

	def format_tx(self,txo):
		raise NotImplementedError

	@property
	def denomination_scale(self):
		return 1000000000000000000.0

	########### BUILD AND SIGN

	#privkeys is a mapping from an address to a list of privkeys for signing an on-chain transaction
	#returns a dictionary mapping to an authorization (can be directly stored later)
	#this is a part of a coin, NOT a chain
	def sign_tx(self,tx,privkeys):
		raise NotImplementedError

	def build_tx(self,unspents,outputs,changeaddr,fee=None,feerate=None):
		raise NotImplementedError

	def is_src_fully_authorized(self,tx,index):
		raise NotImplementedError

	##########  BLOCKCHAIN STUFF
	def blockchain(self,*args,**kwargs):
		raise Exception("Could not find a suitable block-explorer interface instance for '%s'" % (self.ticker))

	def estimate_fee(self,txo,fee_amount_per_byte=None):
		raise NotImplementedError




		
