import mnemonic
import account
from binascii import unhexlify,hexlify

class OfflineAuthMixin(object):
	pass

class Auth(object):
	def __init__(self,refname):
		self.refname=refname

	def authtx(self,account,txo): 	#txo is rw, adds whatever authorizations are possible to add to the txo, if any.   Returns the number added in this way.
		raise NotImplementedError
		
	def to_account(self,*args,**kwargs):
		raise NotImplementedError

class OnChainAddressSetAuth(Auth,OfflineAuthMixin):
	def __init__(self):
		pass
	def __iter__(privkeyiterator):
		pass

class PrivateKeySetAuth(OnChainAddressSetAuth):
	def __init__(self,keys=[]):
		self.keys=[PrivateKey(k) for k in keys]




