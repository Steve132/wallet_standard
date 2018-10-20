from ..wallet import *
from _coin import *
from _segwitcoin import *
from ..bip32 import Bip32,Bip32Settings
from blockchain._insight import InsightBlockchainInterface
from blockchain._interface import MultiBlockchainInterface



_settings_table=[
	(False,False,0x0488ADE4,0x0488B21E),
	(False,True,0x019d9cfe,0x019da462),
	(True,False,0x04358394,0x043587CF),
	(True,True,0x0436ef7d,0x0436f6e1)
]
_priv_table={v[2]:v for v in _settings_table}
_pub_table={v[3]:v for v in _settings_table}
_s_table={(v[0],v[1]):v for v in _settings_table}

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
		
		sig_prefix=b'\x19Litecoin Signed Message:\n'

		super(LTC,self).__init__('LTC',is_testnet=is_testnet,
			pkh_prefix=pkh_prefix,
			sh_prefix=sh_prefix,
			wif_prefix=wif_prefix,
			sig_prefix=sig_prefix,
			bech32_prefix=bech32_prefix)

	def _load_bip32_settings(self,prefix_private=None,prefix_public=None,use_ltpub=True):
		if(prefix_private is not None):
			priv_e=_priv_table.get(prefix_private,None)
			if(priv_e is None or priv_e[0] != self.is_testnet):
				raise Exception("Private Prefix %X does not match any expected prefix for coin %s" % (prefix_private,self.ticker))
			return Bip32Settings(priv_e[2],priv_e[3],use_ltpub=priv_e[1])
		if(prefix_public is not None):
			pub_e=_pub_table.get(prefix_public,None)
			if(pub_e is None or pub_e[0] != self.is_testnet):
				raise Exception("Private Prefix %X does not match any expected prefix for coin %s" % (prefix_private,self.ticker))
			return Bip32Settings(pub_e[2],pub_e[3],use_ltpub=pub_e[1])
		s_e=_s_table[(self.is_testnet,self.use_ltpub)]
		return Bip32Settings(s_e[2],s_e[3],use_ltpub=s_e[1])
		

		#TODO ALL SEGWIT STUFF: segwit=False,embed_in_legacy=True,bech32=False,use_ltpub=False

	


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
