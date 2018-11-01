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

	#https://github.com/bitcoin/bips/blob/master/bip-0141.mediawiki#p2wpkh
	def pubkeys2addr(self,pubkeys,segwit=False,bech32=False,embed_in_legacy=True):
		multisig=len(pubkeys) > 1
		if(multisig):
			raise NotImplementedError
		if(not segwit):
			return super(SegwitCoin,self).pubkeys2addr(pubkeys)

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

	def scriptPubKey2address(self,scriptPubKey):
		spk=scriptPubKey
		if(spk[0]==OP_0 or (spk[0]>=OP_1 and spk[0] <= OP_16)):
			wversion=0 if spk[0]==OP_0 else (1+(spk[0]-OP_1))
			wdatalen=scriptPubKey[1]
			wdata=scriptPubKey[2:(2+wdatalen)]
			return self._address_from_wdata(wversion,wdata)

		return super(SegwitCoin,self).scriptPubKey2address(scriptPubKey)

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

