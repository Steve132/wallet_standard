from ..wallet import *
from _coin import *
from _segwitcoin import *
from ..bip32 import Bip32
from blockchain._insight import InsightBlockchainInterface
from blockchain._interface import MultiBlockchainInterface

class BTC(SegwitCoin):
	def __init__(self,is_testnet=False):
		
		#TODO: SEGWIT has different bip32_prefixes

		if(not is_testnet):
			pkh_prefix=0x00
			sh_prefix=0x05
			wif_prefix=0x80
		else:
			pkh_prefix=0x6F
			sh_prefix=0xC4
			wif_prefix=0xEF

		sig_prefix=b'\x18Bitcoin Signed Message:\n'
		
		super(BTC,self).__init__('BTC',is_testnet=is_testnet,
			pkh_prefix=pkh_prefix,
			sh_prefix=sh_prefix,
			wif_prefix=wif_prefix,
			sig_prefix=sig_prefix)
		
		#TODO:segwit=False,embed_in_legacy=True,bech32=False

	def blockchain(self,*args,**kwargs):
		subcoins=[]
	
		if(not self.is_testnet):
			insighturls=[
				"https://insight.bitpay.com/api",
				"https://blockexplorer.com/api",
				"https://localbitcoinschain.com/api",
				"https://bitcore2.trezor.io/api",
				"https://btc.blockdozer.com/insight-api"
			]
		else:
			insighturls=[
				"https://tbtc.blockdozer.com/insight-api",
				"https://test-insight.bitpay.com/api"
			]

		insights=[InsightBlockchainInterface(self,insighturls)]
		subcoins.extend(insights)
		return MultiBlockchainInterface(self,subcoins).select()
