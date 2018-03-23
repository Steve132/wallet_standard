from _satoshicoin import *

#TODO switch all properties to true property implementations.
class SegwitCoin(SatoshiCoin):
	def __init__(self,ticker,is_testnet,segwit=False,embed_in_legacy=True,bech32=False):
		super(SegwitCoin,self).__init__(ticker,is_testnet)
		self.segwit=segwit
		self.embed_in_legacy=embed_in_legacy
		self.bech32=False
	
	#https://github.com/bitcoin/bips/blob/master/bip-0141.mediawiki#p2wpkh
	def pubkeys2addr_bytes(self,pubkeys,*args,**kwargs):
		segwit=kwargs.get('segwit',None)
		embed_in_legacy=kwargs.get('embed_in_legacy',None)
		bech32=kwargs.get('bech32',None)
		segwit=segwit if segwit is not None else self.segwit
		embed_in_legacy=embed_in_legacy if embed_in_legacy is not None else self.embed_in_legacy
		bech32=bech32 if bech32 is not None else self.embed_in_legacy
		
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
