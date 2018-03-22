from _satoshicoin import *

#TODO switch all properties to true property implementations.
class SegwitCoin(SatoshiCoin):
	def __init__(self,ticker,is_testnet):
		super(SegwitCoin,self).__init__(ticker,is_testnet)
	
	#https://github.com/bitcoin/bips/blob/master/bip-0141.mediawiki#p2wpkh
	def pubkeys2addr_bytes(self,pubkeys,*args,**kwargs):
		segwit=kwargs.get('segwit',False)
		embed_in_legacy=kwargs.get('embed_in_legacy',True)
		bech32=kwargs.get('bech32',False)

		if(isinstance(pubkeys,basestring)):
			pubkeys=[pubkeys] #assume that if it's a single argument, then it's one pubkey

		pubkeys=[PublicKey(pub) for pub in pubkeys]
		multisig=len(pubkeys) > 1
		if(not segwit):
			return super(SegwitCoin,self).pubkeys2addr_bytes(pubkeys,*args,**kwargs)
		else:
			#if(multisig) probably goes out front for embedding or not embedding case
			if(embed_in_legacy):
				if(multisig): #P2WSH-P2SH
					pass	#TODO IMPLEMENT THIS
				else:		#P2WPKH-P2SH
					pass #TODO IMPLEMENT THIS
			else:
				if(multisig): #P2WSH
					pass #TODO IMPLEMENT THIS
				else:#P2WPKH
					pass #TODO IMPLEMENT THIS
