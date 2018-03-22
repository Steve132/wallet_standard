import struct
from _coin import *
from ...wallet import *

class SatoshiCoin(Coin): #a coin with code based on satoshi's codebase
	def __init__(self,ticker,is_testnet):
		super(SatoshiCoin,self).__init__(ticker,is_testnet)


	#https://en.bitcoin.it/wiki/List_of_address_prefixes
	def pubkeys2addr_bytes(self,pubkeys,*args,**kwargs):
		if(isinstance(pubkeys,basestring)):
			pubkeys=[pubkeys] #assume that if it's a single argument, then it's one pubkey
		pubkeys=[PublicKey(pub) for pub in pubkeys]
		multisig=len(pubkeys) > 1
		if(multisig):#P2SH multisig
			pass #TODO implement this #self.sh_version()
		else:  #P2PKH
			h160=_base.hash160(pubkeys[0].keydata)
			return chr(self.pkh_prefix)+h160

	def pubkeys2addr(self,pubkeys,*args,**kwargs):
		abytes=self.pubkeys2addr_bytes(pubkeys,*args,**kwargs)
		return _base.bytes2base58c(abytes)

	#https://github.com/bitcoinjs/bitcoinjs-lib/blob/master/src/networks.js
	#https://github.com/iancoleman/bip39/blob/master/src/js/bitcoinjs-extensions.js
	
	def parse_privkey(self,pkstring):
		try:
			ak=int(pkstring,16)
			pkshex=pkstring
			if(pkshex[:2].lower()=='0x'):
				pkshex=pkshex[2:]
			if(len(pkshex)!=64 and len(pkshex)!=66):
				raise Exception("'%s' is not the right size to be interpreted as a hex private key" % (pkshex))
			byts=unhexlify(pkshex)
			return PrivateKey(pkbytes[:32],is_compressed=(len(pkshex)==66))
		except ValueError:
			pass
				
		pkbytes=_base.base58c2bytes(pkstring)
		if(pkbytes[0] != chr(self.wif_prefix)):
			raise Exception("WIF private key %s could not validate for coin %s.  Expected %d got %d." % (pkstring,self.ticker,ord(pkbytes[0]),self.wif_prefix))
		if(len(pkbytes)==34):
			return PrivateKey(pkbytes[1:-1],is_compressed=True)
		else:
			return PrivateKey(pkbytes[1:],is_compressed=False)

	def parse_pubkey(self,pkstring):
		raise NotImplementedError


	def serializetx(self,txo):
		raise NotImplementedError

	def deserializetx(self,txo):
		raise NotImplementedError


class VarInt(object):
	@classmethod:
	def _sc_serialize(vi):
		vi=abs(vi)
		if(vi <= 252):
			return chr(vi)
		elif(vi <= 0xFFFF):
			return '\xfd'+struct.pack('>H',vi)
		elif(vi <= 0xFFFFFFFF):
			return '\xfe'+struct.pack('>L',vi)
		elif(vi <= 0xFFFFFFFFFFFFFFFF):
			return '\xff'+struct.pack('>Q',vi)
		raise Exception("Integer too large to store in a varint")

class Outpoint(object):
	def __init__(self,txid,index):
		self.txid=txid
		self.index=index

	@classmethod
	def _sc_serialize(op):
		return struct.pack('>32sL',op.txid,op.index)


class Input(object):
	def __init__(self,outpoint,scriptSig,sequence=0xFFFFFFFF):
		self.outpoint=outpoint
		self.scriptSig=scriptSig
		self.sequence=sequence

	@classmethod
	def _sc_serialize(txin):
		out=b''
		out+=Outpoint._sc_serialize(txin.outpoint)
		out+=VarInt._sc_serialize(len(txin.scriptSig))
		out+=txin.scriptSig
		out+=struct.pack('>L',txin.sequence)
		return out

class Output(object):
	def __init__(self,value,scriptPubKey):
		self.value=value
		self.scriptPubKey=scriptPubKey

#TODO: this really only applies to a satoshicoin.				
class Transaction(object):
	def __init__(self,version,ins,outs,locktime):
		self.version=version
		self.ins=ins
		self.outs=outs
		self.locktime=locktime

	@classmethod
	def _sc_serialize(txo):
		out=b''
		out+=struct.pack('>L',txo.version)
		out+=VarInt._sc_serialize(len(txo.ins))
		for inv in txo.ins:
			out+=Input._sc_serialize(inv)
		out+=VarInt._sc_serialize(len(txo.outs))
		for ot in txo.outs:
			out+=Output._sc_serialize(ot)
		out+=struct.pack('>L',txo.locktime)
		return out








	
