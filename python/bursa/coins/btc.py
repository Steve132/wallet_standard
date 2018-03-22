from ...wallet import *

class BTC(SegwitCoin):
	def __init__(self,is_testnet=False):
		super(BTC,self).__init__('BTC',is_testnet)
		if(not is_testnet):
			self.bip32_prefix_private=0x0488ADE4
			self.bip32_prefix_public=0x0488B21E
			self.pk_prefix=0x00
			self.sh_prefix=0x05
			self.wif_prefix=0x80
		else:
			self.bip32_prefix_private=0x04358394
			self.bip32_prefix_public=0x043587CF
			self.pk_prefix=0x6F
			self.sh_prefix=0xC4
			self.wif_prefix=0xEF

		self.bip32_default_prefix_private=self.bip32_prefix_private
		self.bip32_default_prefix_public=self.bip32_prefix_public

		self.sig_prefix=b'\x18Bitcoin Signed Message:\n'
	#TODO: SEGWIT has different bip32_prefixes

