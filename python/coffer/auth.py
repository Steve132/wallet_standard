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
	def __init__(self,words=None,seed=None):
		if(words):
			self.seed=mnemonic.words_to_seed(words)
		if(seed):
			self.seed=seed
		if(not self.seed):
			raise Exception("either seed or seedwords must be given")

	def toaccount(self,coin,authref=None,root=None,accountnum=0,*args,**kwargs):
		master=coin.seed2master(self.seed)
		if(root is None):
			root="44h/%dh/%dh" % (coin.bip44_id-h(0),accountnum)
		xpriv=coin.descend(master,root)
		return account.Bip32Account(coin,xpriv,root=root,authref=authref)
	
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


