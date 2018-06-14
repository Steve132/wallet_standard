from ..wallet import *
from _coin import *
from _satoshicoin import *
from .. import _base
import _cashaddr
from blockchain._insight import InsightBlockchainInterface
from blockchain._interface import MultiBlockchainInterface


class BCH(SatoshiCoin):
	def __init__(self,is_testnet=False,cashaddr=False):
		
		if(not is_testnet):
			bip32_prefix_private=0x0488ADE4
			bip32_prefix_public=0x0488B21E
			pkh_prefix=0x00
			sh_prefix=0x05
			wif_prefix=0x80
		else:
			bip32_prefix_private=0x04358394
			bip32_prefix_public=0x043587CF
			pkh_prefix=0x6F
			sh_prefix=0xC4
			wif_prefix=0xEF

		sig_prefix=b'\x18Bitcoin Signed Message:\n'
		
		super(BCH,self).__init__('BCH',is_testnet=is_testnet,
			bip32_prefix_private=bip32_prefix_private,
			bip32_prefix_public=bip32_prefix_public,
			pkh_prefix=pkh_prefix,
			sh_prefix=sh_prefix,
			wif_prefix=wif_prefix,
			sig_prefix=sig_prefix)

	
	
	#https://github.com/bitcoincashorg/spec/blob/master/cashaddr.md
	def parse_cashaddr(self,addrstring):
		prefix,version_int,payload=cashaddr.decode(addrstring)
		addrversions=[self.pkh_prefix,self.sh_prefix]
		addrversion=addrversions[version_int]
	
		return Address(bytes(chr(addrversion))+payload)
	
	def _write_cashaddr(self,abytes,prefix=None):
		tprefix=prefix
		if(prefix==None or prefix==True or prefix==False):
			if(self.is_testnet):
				tprefix='bchtest'
			else:
				tprefix='bitcoincash'
	
			
		addrpayload=abytes[1:]
		addrversion=abytes[0]
		vint=[self.pkh_prefix,self.sh_prefix].index(ord(addrversion))
		out=_cashaddr.encode(tprefix,vint,addrpayload)
		if(prefix==None or prefix==False):
			return out.split(':')[1]
		
		return out

	def format_addr(self,addr,cashaddr=True,prefix=None,*args,**kwargs):
		if(cashaddr):
			return self._write_cashaddr(addr.addrdata,prefix)
		else:
			return _base.bytes2base58c(addr.addrdata)

	def parse_addr(self,addrstring):
		if(':' in addrstring):
			return self.parse_cashaddr(addrstring)
		try:
			return self.parse_cashaddr(addrstring)
		except Exception as caerr:
			try:
				return Address(_base.base58c2bytes(addrstring))
			except Exception as err:
				raise Exception("Could not parse BCH address: %r,%r" % (err.msg,caerr.msg))

	def blockchain(self):
		subcoins=[]

		if(not self.is_testnet):
			insighturls=[
				"https://insight.yours.org/insight-api",
				"https://bitcoincash.blockexplorer.com/api",
				"https://bch-bitcore2.trezor.io/api",
				"https://blockdozer.com/insight-api",
				"https://bch-insight.bitpay.com/api"
			]
		else:
			insighturls=[
				"https://tbch.blockdozer.com/insight-api",
				"https://test-bch-insight.bitpay.com/api"
			]

		insights=[InsightBlockchainInterface(self,insighturls)]
		subcoins.extend(insights)
		return MultiBlockchainInterface(self,subcoins).select()


	
