import mnemonic
import account
from binascii import unhexlify,hexlify


class IncompatibleAuthError(Exception):
	pass

class OfflineAuthMixin(object):
	pass

#TODO: Refactor this to be 'Authorizer' or 'Credentials'
class Auth(object):
	def __init__(self,refname):
		self.refname=refname
	
	def to_account(self,*args,**kwargs):
		raise NotImplementedError

class OnChainAddressSetAuth(Auth,OfflineAuthMixin):
	def __init__(self):
		pass
	def __iter__(self):
		pass

class PrivateKeySetAuth(OnChainAddressSetAuth):
	def __init__(self,keys=[]):
		self.keys=[PrivateKey(k) for k in keys]




