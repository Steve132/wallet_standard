from ..wallet import *
from _coin import *
from _segwitcoin import *
from ..bip32 import Bip32
from blockchain._insight import InsightBlockchainInterface
from blockchain._interface import MultiBlockchainInterface

class LTC(SegwitCoin):
	def __init__(self,is_testnet=False):
		#https://github.com/litecoin-project/litecoin/blob/master/src/chainparams.cpp#L238
		if(not is_testnet):
			pkh_prefix=0x30
			sh_prefix=0x32
			wif_prefix=0xb0
		else:
			pkh_prefix=111
			sh_prefix=58
			wif_prefix=239
		
		
		sig_prefix=b'\x19Litecoin Signed Message:\n'

		super(LTC,self).__init__('LTC',is_testnet=is_testnet,
			pkh_prefix=pkh_prefix,
			sh_prefix=sh_prefix,
			wif_prefix=wif_prefix,
			sig_prefix=sig_prefix)

		#self.use_ltpub(use=use_ltpub)
		#TODO: segwit=False,embed_in_legacy=True,bech32=False,use_ltpub=False

	def bip32(self,use_ltpub=True):
		if(not self.is_testnet):
			if(use):
				bip32_prefix_private=0x019d9cfe
				bip32_prefix_public=0x019da462
			else:
				bip32_prefix_private=0x0488ADE4
				bip32_prefix_public=0x0488B21E
		else:
			if(use):
				bip32_prefix_private=0x0436ef7d
				bip32_prefix_public=0x0436f6e1
			else:
				bip32_prefix_private=0x04358394
				bip32_prefix_public=0x043587CF
		return Bip32(self,bip32_prefix_private,bip32_prefix_public)


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
