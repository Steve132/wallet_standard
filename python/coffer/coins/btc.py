from ..wallet import *
from _coin import *
from _segwitcoin import *

class BTC(SegwitCoin):
	def __init__(self,is_testnet=False,segwit=False,embed_in_legacy=True,bech32=False):
		
		#TODO: SEGWIT has different bip32_prefixes

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
		
		super(BTC,self).__init__('BTC',is_testnet=is_testnet,
			bip32_prefix_private=bip32_prefix_private,
			bip32_prefix_public=bip32_prefix_public,
			pkh_prefix=pkh_prefix,
			sh_prefix=sh_prefix,
			wif_prefix=wif_prefix,
			sig_prefix=sig_prefix,
			segwit=segwit,embed_in_legacy=embed_in_legacy,bech32=bech32)
