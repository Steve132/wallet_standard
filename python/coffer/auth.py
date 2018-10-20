import mnemonic
from bip32 import h
import account

class Auth(object):
	def __init__(self):
		pass

	def privkey(self,coin,account,address):
		pass

	def authtx(self,txo,account,offline=False): #returns an authorization object appropriate for the transaction.
		raise NotImplementedError
		

class HexPrivKeyAuth(Auth):
	def __init__(self,key):
		pass


