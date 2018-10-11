import mnemonic
from bip32 import h
import account

class Auth(object):
	def __init__(self):
		pass

	def toaccount(self,coin):
		raise NotImplementedError

	def privkey(self,coin,account,address):
		pass

class Bip32SeedAuth(Auth):
	def __init__(self,seed):
		self.seed=seed

	def toaccount(self,coin,root,authref=None,*bip32args,**bip32kwargs):
		bip32_settings=coin.load_bip32_settings(*bip32args,**bip32kwargs)
		master=coin.seed2master(self.seed,bip32_settings)
		xpriv=coin.descend(master,root)
		return account.Bip32Account(coin,xpriv,root=root,authref=authref,*bip32args,**bip32kwargs)

	@staticmethod
	def from_mnemonic(words,passphrase=None):
		seed=mnemonic.words_to_seed(words,passphrase)
		return Bip32SeedAuth(seed)
	
	#def childauth(self,account):
	#masterxpriv=account.coin.seed2master(self.seed)
	#xpriv=coin.descend(account.root)
	#return Bip32Auth(account,xpriv,account.root)
	
class Bip32Auth(Auth):
	def __init__(self,xpriv,root):
		self.coin=coin
		self.xpriv=xpriv
		self.root=root

	def childauth(self,account):
		return self

class HexPrivKeyAuth(Auth):
	def __init__(self,key):
		pass


