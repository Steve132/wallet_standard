#https://www.myetherapi.com/
#curl -H "Content-Type: application/json" -X POST --data '{"jsonrpc":"2.0","method":"eth_getBalance","params":["0x7cB57B5A97eAbe94205C07890BE4c1aD31E486A8", "latest"],"id":1}' https://api.myetherapi.com/eth
#curl -X POST --data '{"jsonrpc":"2.0","method":"eth_getTransactionCount","params":["0xc94770007dda54cF92009BFF0dE90c06F603a09f","latest"],"id":1}'

from ..key import *
from .. import _base
from ..transaction import *
import _coin
from binascii import hexlify,unhexlify
import impl._keccak as _keccak

class ETH(_coin.Coin):
	def __init__(self,is_testnet=False):
		super(ETH,self).__init__(ticker='ETH',is_testnet=is_testnet) 
	
	def pubkeys2addr(self,pubkeys,*args,**kwargs):
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
		return Address(unhexlify(addr),self,format_kwargs={'checksum_case':True})

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
		return Address(byts,self,format_kwargs={'checksum_case':True})

	def format_addr(self,addr,checksum_case=True,*args,**kwargs):
		return _keccak.checksum_encode(addr.addrdata)

	def parse_privkey(self,pkstring):
		return super(ETH,self).parse_privkey(pkstring)

	def format_privkey(self,privkey):
		return super(ETH,self).format_privkey(privkey)

	def parse_tx(self,txstring):
		raise NotImplementedError

	def format_tx(self,txo):
		raise NotImplementedError

	@property
	def denomination_scale(self):
		return 1000000000000000000.0

	def signtx(self,tx,privkeys):
		raise NotImplementedError

	def blockchain(self,*args,**kwargs):
		raise Exception("Could not find a suitable block-explorer interface instance for '%s'" % (self.ticker))
		
