from ..wallet import *
from _coin import *
from _segwitcoin import *
from ..bip32 import Bip32,Bip32Settings
from blockchain._insight import InsightBlockchainInterface
from blockchain._interface import MultiBlockchainInterface


class LTC(SegwitCoin):
	def __init__(self,is_testnet=False):
		#https://github.com/litecoin-project/litecoin/blob/master/src/chainparams.cpp#L238
		if(not is_testnet):
			pkh_prefix=0x30
			sh_prefix=0x32
			wif_prefix=0xb0
			bech32_prefix='ltc'
		else:
			pkh_prefix=111
			sh_prefix=58
			wif_prefix=239
			bech32_prefix='tltc'
		
		sig_prefix=b'Litecoin Signed Message:\n'

		super(LTC,self).__init__('LTC',is_testnet=is_testnet,
			pkh_prefix=pkh_prefix,
			sh_prefix=sh_prefix,
			wif_prefix=wif_prefix,
			sig_prefix=sig_prefix,
			bech32_prefix=bech32_prefix)

	def load_bip32_settings(self,prefix_private=None,prefix_public=None,use_ltpub=True,segwit=False,p2wsh=False,bech32=False,embed_in_legacy=False,*args,**kwargs):
		entry=None
		if(not use_ltpub):
			return super(LTC,self).load_bip32_settings(prefix_private,prefix_public,p2wsh=p2wsh,*args,**kwargs)

		if(p2wsh):
			raise Exception("There is no ltpub version prefix defined for p2wsh prefixes in litecoin")

		if(self.is_testnet):
			if(segwit):
				raise Exception("There is no ltpub version prefix defined for segwit prefixes in litecoin testnet")
			elif(prefix_private==0x0436ef7d or prefix_public==0x0436f6e1 or (prefix_private,prefix_public)==(None,None)):
				return Bip32Settings(prefix_private=0x0436ef7d,prefix_public=0x0436f6e1,use_ltpub=True,segwit=False,p2wsh=p2wsh,*args,**kwargs)
		else:
			if(not segwit):
				if(prefix_private==0x019d9cfe or prefix_public==0x019da462 or (prefix_private,prefix_public)==(None,None)):
					return Bip32Settings(prefix_private=0x019d9cfe,prefix_public=0x019da462,use_ltpub=True,segwit=False,embed_in_legacy=False,bech32=False,*args,**kwargs)
			elif(bech32):
				raise Exception("There is no ltpub version prefix defined for bech32 segwit prefixes in litecoin")
			elif(prefix_private==0x01b26792 or prefix_public==0x01b26ef6 or (prefix_private,prefix_public)==(None,None)):
				return Bip32Settings(prefix_private=0x01b26792,prefix_public=0x01b26ef6,use_ltpub=True,segwit=False,bech32=False,embed_in_legacy=True,p2wsh=p2wsh,*args,**kwargs)
		
		return super(LTC,self).load_bip32_settings(prefix_private,prefix_public,p2wsh=p2wsh,*args,**kwargs)
				
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
