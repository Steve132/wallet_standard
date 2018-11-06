from _satoshicoin import *
from _satoshiscript import *
import coffer._base as _base

def parsebech32(addrstring):
	raise NotImplementedError
	
#https://github.com/satoshilabs/slips/blob/master/slip-0132.md

#TODO switch all properties to true property implementations.
#TODO: add ypub and slip132 implementations here
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
		#we will still use bip142 support and use it as an internal representation to go in line with the serialized format from other address forms 
		#this should be fine according to https://github.com/libbitcoin/libbitcoin/wiki/Altcoin-Version-Mappings
		if(not is_testnet):
			self._b142p2wpkh_prefix=0x06
			self._b142p2wsh_prefix=0x0A
		else:
			self._b142p2wpkh_prefix=0x03
			self._b142p2wsh_prefix=0x28
		self._p2uw_prefix=0xF1 #pay to unknown segwit witness program in case of non b142 address

		if(len(frozenset([sh_prefix,pkh_prefix]) & frozenset([self._b142p2wpkh_prefix,self._b142p2wsh_prefix])) > 0):
			raise Exception("The chosen prefix %X for this coin conflicts with internal bip142 representation")

	###########################addresses and prefixes
	_segwit_b32_table_main={
			0x049d7cb2:(0x049d7878,True,False),				  #Pub:(Priv,Embed_in_legacy,WSH (multisig?))
			0x04b24746:(0x04b2430c,False,False),
			0x0295b43f:(0x0295b005,True,True),
			0x02aa7ed3:(0x02aa7a99,False,True)}
	_segwit_b32_table_test={
			0x043587cf:(0x044a4e28,True,False),				  #Pub:(Priv,Embed_in_legacy,WSH (multisig?))
			0x044a5262:(0x024285b5,False,False),
			0x024289ef:(0x045f18bc,True,True),
			0x02575483:(0x02575048,False,True)}
	#https://github.com/satoshilabs/slips/blob/master/slip-0132.md
	def load_bip32_settings(self,prefix_private=None,prefix_public=None,*args,segwit=False,embed_in_legacy=False,p2wsh=False,bech32=False,**kwargs):
		if(not segwit):
			return super(SegwitCoin,self).load_bip32_settings(prefix_private,prefix_public,*args,segwit=segwit,embed_in_legacy=embed_in_legacy,p2wsh=p2wsh,bech32=bech32,**kwargs)

		table=_segwit_b32_table_main if not self.is_testnet else _segwit_b32_table_test
		entry=None
		if(prefix_public is not None):
			if(prefix_public in table):
				entry=table[prefix_public]
		else:
			if(prefix_private is not None):
				for k,v in table.items():
					if(v[0]==prefix_private):
						entry=e
			else:
				if(embed_in_legacy == bech32):
					logging.warning("bech32 and embed_in_legacy are mutually exclusive unless you are incorrectly seeking bip142 support.  If segwit is enabled the correct value has been selected based on the bech32 setting")
					if(not bech32):
						bech32=True
					else:
						embed_in_legacy=False

				for k,v in table.items():
					if(v[1]==embed_in_legacy and v[2]==p2wsh):	#if both relevant flags are true
						entry=e
				
		if(entry is None):
			return super(SegwitCoin,self).load_bip32_settings(prefix_private,prefix_public,*args,segwit=segwit,embed_in_legacy=embed_in_legacy,p2wsh=p2wsh,bech32=bech32,**kwargs)
		else:
			return Bip32Settings(*args,prefix_private=entry[1],prefix_public=entry[0],segwit=True,embed_in_legacy=entry[2],bech32=bech32,p2wsh=entry[3],**kwargs)


	#https://github.com/bitcoin/bips/blob/master/bip-0141.mediawiki#p2wpkh
	def pubkeys2address(self,pubkeys,segwit=False,bech32=False,embed_in_legacy=True):
		multisig=len(pubkeys) > 1
		if(multisig):
			raise NotImplementedError
		if(not segwit):
			return super(SegwitCoin,self).pubkeys2address(pubkeys)

		if(not embed_in_legacy and not bech32):
			raise Exception("if embed_in_legacy is false and bech32 is false, that implies you are trying to activate BIP142 mode, which is deprecated")
		

		if(self.embed_in_legacy):
			raise NotImplementedError
		else:
			if(self.bech32_prefix is None):
				raise Exception("This coin does not support bech32 addresses")
			if(multisig): #P2WSH
				pass #TODO IMPLEMENT THIS
			else:#P2WPKH
				pass #TODO IMPLEMENT THIS"""

	def address2scriptPubKey(self,addr):
		version=ord(addr.addrdata[0])
		addrbytes=bytearray()
		addrbytes+=addr.addrdata[1:]
		
		if(version in [self._b142p2wpkh_prefix,self._b142p2wsh_prefix,self._p2uw_prefix]):
			wversion=ord(addr.addrdata[1])
			if(wversion > 16):
				raise Exception("Invalid witness version. Must be in range 0-16")
			opcode_wversion=OP_0 if wversion==0 else OP_1+(wversion-1)
		
			witnessprogram=addr.addrdata[3:]	#Bip142 internal representation, witness program is on byte 3.  
			if(len(witnessprogram) > 40):
				raise Exception("Witness program cannot be more than 40 bytes")
			return bytearray([opcode_wversion,len(witnessprogram)])+witnessprogram
		else:
			return super(SegwitCoin,self).address2scriptPubKey(addr)

	def _address_from_wdata(self,witversion,witprogram):
		if(wdatalen > 40):
				raise Exception("Witness program cannot be more than 40 bytes")
		if(witversion==0):
			if(len(witprogram)==20):						#store the witness version into an address using bip142 serialization ONLY INTERNAL REPRESENTATION!
				wvb142=self._b142p2wpkh_prefix
				wtype='p2wpkh'
			elif(len(witprogram)==32):
				wvb142=self._b142p2wsh_prefix
				wtype='p2wsh'
			else:
				raise Exception("Unexpected witness program length for version")
		else:
			wvb142=self._p2uw_prefix
			wtype='p2uw'

		return Address(bytearay([wvb142,witversion,0])+witprogram,wtype,self,format_kwargs={'bech32':True})

	def scriptPubKey2addressess(self,scriptPubKey):
		spk=scriptPubKey
		if(spk[0]==OP_0 or (spk[0]>=OP_1 and spk[0] <= OP_16)):
			wversion=0 if spk[0]==OP_0 else (1+(spk[0]-OP_1))
			wdatalen=scriptPubKey[1]
			wdata=scriptPubKey[2:(2+wdatalen)]
			return self._address_from_wdata(wversion,wdata)

		return super(SegwitCoin,self).scriptPubKey2addressess(scriptPubKey)

	#############parsing and formatting
	def format_addr(self,addr,*args,**kwargs):
		v=ord(addr.addrdata[0])
		if(v in [self._b142p2wpkh_prefix,self._b142p2pkh_prefix,self._p2uw_prefix]):
			if(not addr.get('bech32',False)):
				logging.warning("Youve requested to format a segwit address without bech32.  This is specified in bip142, which is DEPRECATED!")
				return _base.bytes2base58c(addr.addrdata)
			else:
				return _segwitaddr.encode(self.bech32_prefix,ord(addr.addrdata[1]),addr.addrdata[2:])
		
		return super(SegwitCoin,self).format_addr(addr,*args,**kwargs)

	def parse_addr(self,addrstring):
		bech32_result=_segwitaddr.decode(self.bech32_prefix, addrstring)
		if(bech32_result==(None,None)):
			return super(SegwitCoin,self).parse_addr(addrstring)	#this technically allows bip142
	
		witversion,witprogram=bech32_result
		if(ord(witversion)!=0):
			logging.warning("Unsupported witness version in address %s!" % (addrstring))
		return self._address_from_wdata(witversion,witprogram)
		

	def parse_tx(self,sio):
		if(isinstance(sio,basestring)):
			sio=StringIO(unhexlify(sio))
		return SWitnessTransaction._sc_deserialize(hexlify(sio))

	def txo2internal(self,txo):
		return SWitnessTransaction.from_txo(txo)

	def signature2witness(self,signature):
		raise NotImplementedError
	########SIGNING AND BUILDING

	def _sighash(self,stxo,index,nhashtype):
		if(hasattr(stxo,'witness')):
			return _segwittx.segwit_sighash(stxo,index,nhashtype)
		return _satoshitx.legacy_sighash(stxo,index,nhashtype)

	self._authorize_index(satoshitxo,index,addr,redeem_param) #TODO multiple address authorizations?  That's weird/wrong
		if(hasattr(satoshitxo,'witness')):
			raise Exception("Segwit signing not implemented yet")
		return super(SegwitCoin,self)._authorize_index(satoshitxo,index,addr,redeem_param)

