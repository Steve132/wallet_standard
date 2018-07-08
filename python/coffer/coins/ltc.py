from ..wallet import *
from _coin import *
from _segwitcoin import *
from blockchain._insight import InsightBlockchainInterface
from blockchain._interface import MultiBlockchainInterface

class LTC(SegwitCoin):
	def __init__(self,is_testnet=False,segwit=False,embed_in_legacy=True,bech32=False,use_ltpub=False):
		#https://github.com/litecoin-project/litecoin/blob/master/src/chainparams.cpp#L238
		if(not is_testnet):
			if(use_ltpub):
				bip32_prefix_private=0x019d9cfe
				bip32_prefix_public=0x019da462
			else:
				bip32_prefix_private=0x0488ADE4
				bip32_prefix_public=0x0488B21E
			pkh_prefix=0x30
			sh_prefix=0x32
			wif_prefix=0xb0
		else:
			if(use_ltpub):
				bip32_prefix_private=0x0436ef7d
				bip32_prefix_public=0x0436f6e1
			else:
				bip32_prefix_private=0x04358394
				bip32_prefix_public=0x043587CF
			pkh_prefix=111
			sh_prefix=58
			wif_prefix=239

		sig_prefix=b'\x19Litecoin Signed Message:\n'
		
		super(BTC,self).__init__('LTC',is_testnet=is_testnet,
			bip32_prefix_private=bip32_prefix_private,
			bip32_prefix_public=bip32_prefix_public,
			pkh_prefix=pkh_prefix,
			sh_prefix=sh_prefix,
			wif_prefix=wif_prefix,
			sig_prefix=sig_prefix,
			segwit=segwit,embed_in_legacy=embed_in_legacy,bech32=bech32)


	def blockchain(self,*args,**kwargs):
		subcoins=[]
	
		if(not self.is_testnet):
			insighturls=[
				"https://insight.litecore.io/api"
			]
		else:
			insighturls=[
				"https://testnet.litecore.io/api"
			]

		insights=[InsightBlockchainInterface(self,insighturls)]
		subcoins.extend(insights)
		return MultiBlockchainInterface(self,subcoins).select()
