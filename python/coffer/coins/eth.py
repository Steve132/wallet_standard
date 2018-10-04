#https://www.myetherapi.com/
#curl -H "Content-Type: application/json" -X POST --data '{"jsonrpc":"2.0","method":"eth_getBalance","params":["0x7cB57B5A97eAbe94205C07890BE4c1aD31E486A8", "latest"],"id":1}' https://api.myetherapi.com/eth
#curl -X POST --data '{"jsonrpc":"2.0","method":"eth_getTransactionCount","params":["0xc94770007dda54cF92009BFF0dE90c06F603a09f","latest"],"id":1}'

from ..key import *
from .. import _base
from ..transaction import *
import _coin
from .. import bip32
from binascii import hexlify,unhexlify
import _keccak


class ETH(_coin.Coin):
	def __init__(self,ticker,is_testnet=False):
		super(ETH,self).__init__(ticker=ticker,is_testnet=is_testnet) 

	def bip32(self,*args,**kwargs):
		if(not self.is_testnet):
			bip32_prefix_private=0x0488ADE4
			bip32_prefix_public=0x0488B21E
		else:
			bip32_prefix_private=0x04358394
			bip32_prefix_public=0x043587CF
		return bip32.Bip32(self,bip32_prefix_private,bip32_prefix_public)
			
		
	def pubkeys2addr(self,pubkeys,*args,**kwargs):
		if(len(pubkeys) > 1):
			raise NotImplementedError("TODO: ETH implementation doesn't support multiple pubkeys")
		khash=_keccak.Keccak256()
		key=pubkeys[0]
		pki=key.decompressed()
		tv="%064X%064X" % (pki[0],pki[1])
		tv=unhexlify(tv)
		khash.update(tv)
		hx=khash.hexdigest()
		addr=hx[-40:]
		return _keccak.checksum_encode(addr)

	def parse_addr(self,addrstring):
		raise NotImplementedError

	def format_addr(self,addr,*args,**kwargs):
		raise NotImplementedError

	def parse_privkey(self,pkstring):
		raise NotImplementedError

	def format_privkey(self,privkey):
		raise NotImplementedError


	def parse_tx(self,txstring):
		raise NotImplementedError

	def format_tx(self,txo):
		raise NotImplementedError

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
			return [bip32.h(44),bip32.h(self.bip44_id),bip32.h(account)]
		return default_gen

