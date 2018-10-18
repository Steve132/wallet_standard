import struct
from binascii import hexlify,unhexlify
from cStringIO import StringIO
#https://github.com/bitcoinjs/bitcoinjs-lib/blob/master/src/networks.js
#https://github.com/iancoleman/bip39/blob/master/src/js/bitcoinjs-extensions.js

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

	def to_dict(self):
		return {"txid":hexlify(self.txid),"index":self.index}
	@staticmethod
	def from_dict(self,dct):
		return SOutpoint(unhexlify(dct["txid"]),dct["index"])

	@staticmethod
	def from_outref(ref):
		txid=unhexlify(ref.ownertx.refid)[::-1]
		index=ref.index
		return SOutpoint(txid=txid,index=index)

class SInput(object):
	def __init__(self,outpoint,scriptSig,sequence=0xFFFFFFFF):
		self.outpoint=outpoint
		self.scriptSig=scriptSig
		self.sequence=sequence

	@staticmethod
	def _sc_serialize(txin):
		out=b''
		out+=SOutpoint._sc_serialize(txin.outpoint)
		out+=SVarInt._sc_serialize(len(txin.scriptSig))
		out+=txin.scriptSig
		out+=struct.pack('<L',txin.sequence)
		return out

	@staticmethod
	def _sc_deserialize(sio):
		outpoint=SOutpoint._sc_deserialize(sio)
		scriptSig_size=SVarInt._sc_deserialize(sio)
		sSig=sio.read(scriptSig_size)
		seq=struct.unpack('<L',sio.read(4))[0]
		return SInput(outpoint,sSig,seq)

	def to_dict(self):
		return {"outpoint":self.outpoint.to_dict(),"scriptSig":hexlify(self.scriptSig),"sequence":self.sequence}
	@staticmethod
	def from_dict(self,dct):
		return SInput(SOutpoint.from_dict(dct["outpoint"]),unhexlify(dct["scriptSig"]),dct["sequence"])

	@staticmethod
	def from_src(src,sig):
		if(sig is None):
			sig=''
		sequence=src.meta.get('sequence',0xffffffff)
		scriptSig=src.meta.get('scriptSig',sig)
		return SInput(SOutpoint.from_outref(src.ref),scriptSig,sequence)
			
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
		return out
	
	@staticmethod
	def _sc_deserialize(sio):
		v=struct.unpack('<Q',sio.read(8))[0]
		scriptPubKey_size=SVarInt._sc_deserialize(sio)
		scriptPubKey=sio.read(scriptPubKey_size)
		return SOutput(v,scriptPubKey)

	def to_dict(self):
		return {"value":self.value,"scriptPubKey":hexlify(self.scriptPubKey)}
	@staticmethod
	def from_dict(self,dct):
		return SOutput(dct["value"],unhexlify(dct["scriptPubKey"]))

	@staticmethod
	def from_dst(dst):
		value=int(dst.iamount)
		if('scriptPubKey' in dst.meta):
			scriptPubKey=unhexlify(dst.meta['scriptPubKey'])
		else:
			scriptPubKey=dst.coin.address2scriptPubKey(dst.address)
		return SOutput(value,scriptPubKey)

#https://en.bitcoin.it/wiki/Protocol_documentation#tx
#TODO: Segwit has a different transaction value
#TODO: this really only applies to a satoshicoin.				
class STransaction(object):
	def __init__(self,version,ins,outs,locktime):
		self.version=version
		self.ins=ins
		self.outs=outs
		self.locktime=locktime

	@staticmethod
	def _sc_serialize(txo):
		if(isinstance(txo,SWitnessTransaction)):
			return SWitnessTransaction._sc_serialize(txo)
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
		if(num_ins==0):	#this is a witness transaction
			return SWitnessTransaction._sc_deserialize(StringIO(sio.getvalue()))
		ins=[SInput._sc_deserialize(sio) for k in range(num_ins)]
		num_outs=SVarInt._sc_deserialize(sio)
		outs=[SOutput._sc_deserialize(sio) for k in range(num_outs)]
		locktime=struct.unpack('<L',sio.read(4))[0]

		return STransaction(version,ins,outs,locktime)

	def to_dict(self):
		ins=[t.to_dict() for t in self.ins]
		outs=[t.to_dict() for t in self.outs]
		return {"version":self.version,"ins":ins,"outs":outs,"locktime":self.locktime}

	@staticmethod
	def from_dict(dct):
		lt=dct.get("locktime",0)
		v=dct.get("version",1)
		ins=dct.get("ins",[])
		outs=dct.get("outs",[])

		ins=[SInput.from_dict(t) for t in ins]
		outs=[SOutput.from_dict(t) for t in outs]
		return STransaction(version=version,ins=ins,outs=outs,locktime=lt)

	#@staticmethod
	#def from_txo(txo):
	#	version=txo.meta.get('version',1)
	#	locktime=txo.meta.get('locktime',0xffffffff)
	#	ins=[SInput.from_src(o,txo.signatures.get(o.ref,None)) for o in txo.srcs]
	#	outs=[SOutput.from_dst(o) for o in txo.dsts]
	#	return STransaction(version,ins,outs,locktime)


#https://bitcoincore.org/en/segwit_wallet_dev/
class SWitnessTransaction(STransaction):
	def __init__(version,flag,ins,outs,witness,locktime):
		super(SWitnessTransaction,self).__init__(version,ins,outs,locktime)
		self.flag=flag
		self.witness=witness

	@staticmethod
	def _sc_serialize(txo):
		if(not isinstance(txo,SWitnessTransaction) and isinstance(txo,STransaction)):
			return STransaction._sc_serialize(txo)
		out=b''
		out+=struct.pack('<L',txo.version)
		out+=b'\x00'
		out+=struct.pack('B',txo.flag)

		out+=SVarInt._sc_serialize(len(txo.ins))
		for inv in txo.ins:
			out+=SInput._sc_serialize(inv)

		out+=SVarInt._sc_serialize(len(txo.outs))
		for ot in txo.outs:
			out+=SOutput._sc_serialize(ot)

		if(len(txo.witness) != len(txo.ins)):
			raise Exception("Witness data not the same length as number of inputs")
		for wit in txo.witness:		#load witness data
			out+=SVarInt._sc_serialize(len(wit))
			for wititem in wit:
				out+=SVarInt._sc_serialize(len(wititem))
				out+=wititem
				
		out+=struct.pack('<L',txo.locktime)
		return out

	@staticmethod
	def _sc_deserialize(sio):
		version=struct.unpack('<L',sio.read(4))[0]
		num_ins=SVarInt._sc_deserialize(sio)
		if(num_ins!=0):	#this is not a witness transaction
			return STransaction._sc_deserialize(StringIO(sio.getvalue()))
		flag=ord(sio.read(1))
	
		num_ins=SVarInt._sc_deserialize(sio)
		ins=[SInput._sc_deserialize(sio) for k in range(num_ins)]
		num_outs=SVarInt._sc_deserialize(sio)
		outs=[SOutput._sc_deserialize(sio) for k in range(num_outs)]
		
		witness=[]
		for _ in range(num_ins):
			num_wititems=SVarInt._sc_deserialize(sio)
			wititems=[]
			for _ in range(num_wititems):
				witsize=SVarInt._sc_deserialize(sio)
				wititmes.append(sio.read(witsize))
			witness.append(wititems)

		locktime=struct.unpack('<L',sio.read(4))[0]

		return SWitnessTransaction(version,flag,ins,outs,witness,locktime)
	
