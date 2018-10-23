import mnemonic
from bip32 import h
import account
from binascii import unhexlify,hexlify


class OfflineAuthMixin(object):
	pass

class Auth(object):
	def __init__(self):
		pass

	def authtx(self,account,txo): 	#txo is rw, adds whatever authorizations are possible to add to the txo, if any.   Returns the number added in this way.
		raise NotImplementedError
		
	def to_account(self,*args,**kwargs):
		raise NotImplementedError

class OnChainAddressSetAuth(Auth,OfflineAuthMixin):
	def __init__(self,external,internal=[],authref=None,gap=20):
		

class PrivateKeySetAuth(OnChainAddressSetAuth):
	def __init__(self,keys=[]):
		self.keys=[PrivateKey(k) for k in keys]




