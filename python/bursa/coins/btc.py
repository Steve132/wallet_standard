from ...wallet import *

class BTC(SegwitCoin):
	def __init__(self,is_testnet=False):
		super(BTC,self).__init__('BTC',is_testnet)
		if(not is_testnet):
			self.bip32_prefix_private=0x0488ADE4
			self.bip32_prefix_public=0x04358394

	def bip32_version(self,private):
		if(not self.is_testnet):
			return 0x0488ADE4 if private else 0x0488B21E
		else:
			return 0x04358394 if private else 0x043587CF
	def pk_version(self):
		return 0x00 if not self.is_testnet else 0x6F
	
	def sh_version(self):
		return 0x05 if not self.is_testnet else 0x6F

	def sig_prefix(self):
		return b'\x18Bitcoin Signed Message:\n'

	def wif(self):
		return 0x80 if not self.is_testnet else 0xEF


def pk_version(self):
		raise NotImplementedError

	def sh_version(self):
		raise NotImplementedError

	def sig_prefix(self):
		raise NotImplementedError

	def wif(self):
		raise NotImplementedError

