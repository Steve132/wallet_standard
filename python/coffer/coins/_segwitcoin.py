from _satoshicoin import *


def parsebech32(addrstring):
	raise NotImplementedError
	
#TODO switch all properties to true property implementations.
class SegwitCoin(SatoshiCoin):
	def __init__(self,ticker,is_testnet,
		bip32_prefix_private,bip32_prefix_public,bip32_seed_salt,wif_prefix,pkh_prefix,sh_prefix,sig_prefix,
		segwit,embed_in_legacy,bech32):

		super(SegwitCoin,self).__init__(ticker,is_testnet,bip32_prefix_private,bip32_prefix_public,bip32_seed_salt,wif_prefix,pkh_prefix,sh_prefix,sig_prefix)
		self.segwit=segwit
		self.embed_in_legacy=embed_in_legacy
		self.bech32=bech32
	
	#https://github.com/bitcoin/bips/blob/master/bip-0141.mediawiki#p2wpkh
	def pubkeys2addr_bytes(self,pubkeys):
		
		if(isinstance(pubkeys,basestring)):
			pubkeys=[pubkeys] #assume that if it's a single argument, then it's one pubkey

		pubkeys=[PublicKey(pub) for pub in pubkeys]
		multisig=len(pubkeys) > 1
		if(not self.segwit):
			return super(SegwitCoin,self).pubkeys2addr_bytes(pubkeys) 
		else:
			#if(multisig) probably goes out front for embedding or not embedding case
			if(self.embed_in_legacy):
				if(multisig): #P2WSH-P2SH
					pass	#TODO IMPLEMENT THIS
				else:		#P2WPKH-P2SH
					pass #TODO IMPLEMENT THIS
			else:
				if(multisig): #P2WSH
					pass #TODO IMPLEMENT THIS
				else:#P2WPKH
					pass #TODO IMPLEMENT THIS
	def pubkeys2addr(self,pubkeys):
		if(self.bech32):
			raise NotImplementedError
		return super(SegwitCoin,self).pubkeys2addr(pubkeys)
	def parse_addr(self,addrstring):
		#handle bech32 addresses...detect either one
		try:
			return parsebeck32(addrstring)
		except:
			return super(SegwitCoin,self).parse_addr(addrstring)

	def address2scriptPubKey(self,addrstring):
		addrbytes=self.parse_addr(addrstring)
		#parse p2wpkh p2wsh
