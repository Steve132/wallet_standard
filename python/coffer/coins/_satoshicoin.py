import struct
from _coin import *
from ..wallet import *
from cStringIO import StringIO
from binascii import hexlify,unhexlify
from _satoshiscript import *
from .. import _base

class SVarInt(object):
	@staticmethod
	def _sc_serialize(vi):
		vi=abs(vi)
		if(vi <= 252):
			return chr(vi)
		elif(vi <= 0xFFFF):
			return '\xfd'+struct.pack('<H',vi)
		elif(vi <= 0xFFFFFFFF):
			return '\xfe'+struct.pack('<L',vi)
		elif(vi <= 0xFFFFFFFFFFFFFFFF):
			return '\xff'+struct.pack('<Q',vi)
		raise Exception("Integer too large to store in a SVarInt")

	@staticmethod
	def _sc_deserialize(sio):
		first=sio.read(1)
		if(first == '\xff'):
			return struct.unpack('<Q',sio.read(8))[0]
		elif(first == '\xfe'):
			return struct.unpack('<L',sio.read(4))[0]
		elif(first == '\xfd'):
			return struct.unpack('<H',sio.read(2))[0]
		else:
			return ord(first)

#txid needs to be serialized backwards for strange reasons
class SOutpoint(object):
	def __init__(self,txid,index):
		self.txid=txid
		self.index=index

	@staticmethod
	def _sc_serialize(op):
		return struct.pack('<32sL',op.txid[::-1],op.index)
	@staticmethod
	def _sc_deserialize(sio):
		tid,dex=struct.unpack('<32sL',sio.read(36))
		tid=tid[::-1]
		return SOutpoint(tid,dex)

	def todict(self):
		return {"txid":hexlify(self.txid),"index":self.index}
	@staticmethod
	def fromdict(self,dct):
		return SOutpoint(unhexlify(dct["txid"]),dct["index"])


class SInput(object):
	def __init__(self,SOutpoint,scriptSig,sequence=0xFFFFFFFF):
		self.SOutpoint=SOutpoint
		self.scriptSig=scriptSig
		self.sequence=sequence

	@staticmethod
	def _sc_serialize(txin):
		out=b''
		out+=SOutpoint._sc_serialize(txin.SOutpoint)
		out+=SVarInt._sc_serialize(len(txin.scriptSig))
		out+=txin.scriptSig
		out+=struct.pack('<L',txin.sequence)
		return out

	@staticmethod
	def _sc_deserialize(sio):
		SOutpoint=SOutpoint._sc_deserialize(sio)
		scriptSig_size=SVarInt._sc_deserialize(sio)
		sSig=sio.read(scriptSig_size)
		seq=struct.unpack('<L',sio.read(4))[0]
		return SInput(SOutpoint,sSig,seq)

	def todict(self):
		return {"SOutpoint":self.SOutpoint.todict(),"scriptSig":hexlify(self.scriptSig),"sequence":self.sequence}
	@staticmethod
	def fromdict(self,dct):
		return SInput(SOutpoint.fromdct(dct["SOutpoint"]),unhexlify(dct["scriptSig"]),dct["sequence"])
			
class SOutput(object):
	def __init__(self,value,scriptPubKey):
		self.value=value
		self.scriptPubKey=scriptPubKey

	@staticmethod
	def _sc_serialize(outp):
		out=b''
		out+=struct.pack('<Q',outp.value)
		out+=SVarInt._sc_serialize(len(outp.scriptPubKey))
		out+=outp.scriptPubKey
	
	@staticmethod
	def _sc_deserialize(sio):
		v=struct.unpack('<Q',sio.read(8))[0]
		scriptPubKey_size=SVarInt._sc_deserialize(sio)
		scriptPubKey=sio.read(scriptPubKey_size)
		return SOutput(v,scriptPubKey)

	def todict(self):
		return {"value":self.value,"scriptPubKey":hexlify(self.scriptPubKey)}
	@staticmethod
	def fromdict(self,dct):
		return SOutput(dct["value"],unhexlify(dct["scriptPubKey"]))

#TODO: this really only applies to a satoshicoin.				
class STransaction(object):
	def __init__(self,version,ins,outs,locktime):
		self.version=version
		self.ins=ins
		self.outs=outs
		self.locktime=locktime

	@staticmethod
	def _sc_serialize(txo):
		out=b''
		out+=struct.pack('<L',txo.version)
		out+=SVarInt._sc_serialize(len(txo.ins))
		for inv in txo.ins:
			out+=SInput._sc_serialize(inv)
		out+=SVarInt._sc_serialize(len(txo.outs))
		for ot in txo.outs:
			out+=SOutput._sc_serialize(ot)
		out+=struct.pack('<L',txo.locktime)
		return out

	@staticmethod
	def _sc_deserialize(sio):
		version=struct.unpack('<L',sio.read(4))[0]
		num_ins=SVarInt._sc_deserialize(sio)
		ins=[SInput._sc_deserialize(sio) for k in range(num_ins)]
		num_outs=SVarInt._sc_deserialize(sio)
		outs=[SOutput._sc_deserialize(sio) for k in range(num_outs)]
		locktime=struct.unpack('<L',sio.read(4))[0]

		return STransaction(version,ins,outs,locktime)

	def todict(self):
		ins=[t.todict() for t in self.ins]
		outs=[t.todict() for t in self.outs]
		return {"version":self.version,"ins":ins,"outs":outs,"locktime":self.locktime}

	@staticmethod
	def fromdict(self,dct):
		lt=dct.get("locktime",0)
		v=dct.get("version",1)
		ins=dct.get("ins",[])
		outs=dct.get("outs",[])

		ins=[SInput.fromdict(t) for t in ins]
		outs=[SOutput.fromdict(t) for t in outs]
		return STransaction(version=version,ins=ins,outs=outs,locktime=lt)

class SatoshiCoin(Coin): #a coin with code based on satoshi's codebase
	def __init__(self,ticker,is_testnet,bip32_prefix_private,bip32_prefix_public,wif_prefix,pkh_prefix,sh_prefix,sig_prefix):
		super(SatoshiCoin,self).__init__(
			ticker=ticker,
			is_testnet=is_testnet,
			bip32_prefix_private=bip32_prefix_private,
			bip32_prefix_public=bip32_prefix_public)

		self.wif_prefix=wif_prefix
		self.pkh_prefix=pkh_prefix
		self.sh_prefix=sh_prefix
		self.sig_prefix=sig_prefix
		
	#https://en.bitcoin.it/wiki/List_of_address_prefixes
	def pubkeys2addr_bytes(self,pubkeys,*args,**kwargs):
		#if(isinstance(pubkeys,basestring)):
		#	pubkeys=[pubkeys] #assume that if it's a single argument, then it's one pubkey
		#pubkeys=[(PublicKey(pub) if isinstance(pub,basestr) else pub) for pub in pubkeys] #if there's a string test
		
		multisig=len(pubkeys) > 1
		if(multisig):#P2SH multisig
			raise NotImplementedError #TODO implement this #self.sh_version()
		else:  #P2PKH
			h160=_base.hash160(pubkeys[0].pubkeydata)
			return chr(self.pkh_prefix)+h160

	def pubkeys2addr(self,pubkeys,*args,**kwargs):
		abytes=self.pubkeys2addr_bytes(pubkeys,*args,**kwargs)
		return _base.bytes2base58c(abytes)

	#https://github.com/bitcoinjs/bitcoinjs-lib/blob/master/src/networks.js
	#https://github.com/iancoleman/bip39/blob/master/src/js/bitcoinjs-extensions.js
	#https://www.cryptocompare.com/coins/guides/what-are-the-bitcoin-STransaction-types/
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

	def parse_addr(self,addrstring):
		return _base.base58c2bytes(addrstring)

	def address2scriptPubKey(self,addrstring):
		addrbytes=parse_addr(addrstring)
		version=addrbytes[0]
		if(version==self.pkh_prefix):
			return sum([OP_DUP,OP_HASH160,chr(len(addrbytes)),addrbytes[1:],OP_EQUALVERIFY,OP_CHECKSIG],b'')
		elif(version==self.sh_prefix):
			return sum([OP_HASH160,chr(len(addrbytes)),addrbytes[1:],OP_EQUAL],b'')
		else:
			raise Exception("Invalid Address Version %h for address" % (ord(version),addrstring))
		raise NotImplementedError

	def denomination_float2whole(self,x):
		return int(x*100000000.0)
	
	def denomination_whole2float(self,x):
		raise float(x)/100000000.0


	def serializetx(self,txo):
		stxo=STransaction.fromtxo(txo)
		return STransaction._sc_serialize(stxo)

	#def deserializetx(self,sio):
	#	if(isinstance(sio,basestring)):
	#		sio=StringIO(sio)
	#	return STransaction._sc_deserialize(sio)

	def txtodict(self,tx):
		return tx.todict()

	def txfromdict(self,dct):
		return STransaction.fromdict(dct)

	"""

	
	#todo: obviously broken
	"""

	
