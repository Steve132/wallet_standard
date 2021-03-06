from ..wallet import *
from _coin import *
from ..bip32 import Bip32
from blockchain._insight import InsightBlockchainInterface
from blockchain._interface import MultiBlockchainInterface

from impl._segwitcoin import *

class BTC(SegwitCoin):
	def __init__(self,is_testnet=False):
		#self.supported=True
		if(not is_testnet):
			pkh_prefix=0x00
			sh_prefix=0x05
			wif_prefix=0x80
			bech32_prefix="bc"
		else:
			pkh_prefix=0x6F
			sh_prefix=0xC4
			wif_prefix=0xEF
			bech32_prefix="tb"

		sig_prefix=b'Bitcoin Signed Message:\n'
		
		super(BTC,self).__init__('BTC',is_testnet=is_testnet,
			pkh_prefix=pkh_prefix,
			sh_prefix=sh_prefix,
			wif_prefix=wif_prefix,
			sig_prefix=sig_prefix,bech32_prefix=bech32_prefix)
		
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
				"https://testnet.blockexplorer.com/api"
				#"https://test-insight.bitpay.com/api"  This is testnetv1, doesn't work
			]

		insights=[InsightBlockchainInterface(self,insighturls)]
		subcoins.extend(insights)
		return MultiBlockchainInterface(self,subcoins).select()
