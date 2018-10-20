from _satoshicoin import *


def parsebech32(addrstring):
	raise NotImplementedError
	
#https://github.com/satoshilabs/slips/blob/master/slip-0132.md

#TODO switch all properties to true property implementations.

#TODO: add ypub and slip132 implementations here
#TODO: add bech32 implementations and polymod refactoring

class SegwitCoin(SatoshiCoin):
	def __init__(self,ticker,is_testnet,wif_prefix,pkh_prefix,sh_prefix,sig_prefix,bech32_prefix=None):

		super(SegwitCoin,self).__init__(ticker=ticker,is_testnet=is_testnet,
			wif_prefix=wif_prefix,
			pkh_prefix=pkh_prefix,
			sh_prefix=sh_prefix,
			sig_prefix=sig_prefix)
		
		self.bech32_prefix=bech32_prefix
		
		#BIP142 is relevant here but not directly.  That would be the case where you don't embed in p2sh but you also don't want segwit.   IS DEPRECATED.
														#embed and bech32 should be considered to be one variable exclusive in that context

	#https://github.com/bitcoin/bips/blob/master/bip-0141.mediawiki#p2wpkh
	def pubkeys2addr(self,pubkeys,segwit=False,bech32=False,embed_in_legacy=True):
		multisig=len(pubkeys) > 1
		if(multisig):
			raise NotImplementedError
		if(not segwit):
			return super(SegwitCoin,self).pubkeys2addr(pubkeys)

		if(not embed_in_legacy and not bech32):
			raise Exception("if embed_in_legacy is false and bech32 is false, that implies BIP142 mode, which is deprecated")
		
		if(self.embed_in_legacy):
			pass
		else:
			if(self.bech32_prefix is None):
				raise Exception("This coin does not support bech32 addresses")

			if(multisig): #P2WSH
				pass #TODO IMPLEMENT THIS
			else:#P2WPKH
				pass #TODO IMPLEMENT THIS"""
	#def pubkeys2addr(self,pubkeys,*args,**kwargs):
	#	if(bech32):
	#		raise NotImplementedError
	#	return super(SegwitCoin,self).pubkeys2addr(pubkeys,*args,**kwargs)

	def parse_addr(self,addrstring):
		#handle bech32 addresses...detect either one
		try:
			return Address(parsebech32(addrstring),self,format_kwargs={'bech32':True})
		except:
			return super(SegwitCoin,self).parse_addr(addrstring)

	def signature2witness(self,signature):
		raise NotImplementedError
