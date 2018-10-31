import struct
from binascii import hexlify,unhexlify
from cStringIO import StringIO
import _satoshiscript
import coffer._crypto
from .._base import dblsha256
import coffer.transaction as transaction

#https://github.com/bitcoinjs/bitcoinjs-lib/blob/master/src/networks.js
#https://github.com/iancoleman/bip39/blob/master/src/js/bitcoinjs-extensions.js

#https://bitcoin.stackexchange.com/questions/3374/how-to-redeem-a-basic-tx
#https://medium.com/coinmonks/how-to-create-a-raw-bitcoin-transaction-step-by-step-239b888e87f2


SIGHASH_ANYONECANPAY=0x00000080
SIGHASH_ALL=0x00000001
SIGHASH_NONE=0x00000002
SIGHASH_SINGLE=0x00000003
SIGHASH_FORKID=0x00000040

sighash_null_value=0xFFFFFFFFFFFFFFFF
class SigHashOptions(object):
	def __init__(self,nHashTypeInt):
		nHashTypeInt=int(nHashTypeInt)
		if(nHashTypeInt < 0):
			nHashTypeInt+=1 << 32
		
		self.mode=(nHashTypeInt & 0x1f)
		self.anyonecanpay=(nHashTypeInt & SIGHASH_ANYONECANPAY) > 0
		self.forkid=(nHashTypeInt & SIGHASH_FORKID) > 0
		self.nhashtype=nHashTypeInt

	def to_byte(self):
		"""byt=int(self.mode)
		byt|=SIGHASH_ANYONECANPAY if self.anyonecanpay else 0
		byt|=SIGHASH_FORKID if self.forkid else 0
		return chr(byt)"""
		return self.nhashtype & 0xFF

class SVarInt(object):
	def __init__(self,ival=0):
		self.ival=ival

	def serialize(self):
		vi=abs(self.ival)
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

	def serialize(self):
		op=self
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
		txid=unhexlify(ref.ownertx.refid)
		index=ref.index
		return SOutpoint(txid=txid,index=index)

	def to_outref(self,chainid):
		txref=transaction.TransactionReference(chainid,hexlify(self.txid))
		return transaction.OutputReference(txref,self.index)

#TODO: add segwit inputs and outputs?
class SInput(object):
	def __init__(self,outpoint,scriptSig,sequence=0xFFFFFFFF,prevout=None):
		self.outpoint=outpoint
		self.scriptSig=scriptSig
		self.sequence=sequence
		self.prevout=prevout

	def serialize(self):
		txin=self
		out=bytearray()
		out+=txin.outpoint.serialize()
		out+=SVarInt(len(txin.scriptSig)).serialize()
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
	def from_src(src,scriptSig):
		sequence=src.meta.get('sequence',0xffffffff)
		prevout=SOutput.from_dst(src)
		return SInput(SOutpoint.from_outref(src.ref),scriptSig,sequence,prevout)

	def has_scriptSig(self):
		return len(self.scriptSig) > 0
		

	
class SOutput(object):
	def __init__(self,value,scriptPubKey):
		self.value=value
		if(self.value < 0):
			raise Exception("This output cannot be negative")
		self.scriptPubKey=scriptPubKey

	def serialize(outp):
		out=bytearray()
		out+=struct.pack('<Q',outp.value)
		out+=SVarInt(len(outp.scriptPubKey)).serialize()
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
		#self.enforce_deterministic_ordering()

	def serialize(self):
		txo=self
		if(isinstance(txo,SWitnessTransaction)):
			return SWitnessTransaction._sc_serialize(txo)
		out=bytearray()
		out+=struct.pack('<L',txo.version)
		out+=SVarInt(len(txo.ins)).serialize()
		for inv in txo.ins:
			out+=inv.serialize()
		out+=SVarInt(len(txo.outs)).serialize()
		for ot in txo.outs:
			out+=ot.serialize()
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

	#If any of the inputs are segwit addresses, load this as a segwit transaction (must be done in coinimpl)
	@staticmethod
	def from_txo(txo):
		version=txo.meta.get('version',1)
		locktime=txo.meta.get('locktime',0xffffffff)
		ins=[]
		for src in txo.srcs:
			a=txo.authorizations.get(src.ref,None)
			if(a is None):
				scriptSig=src.meta.get('scriptSig',bytearray())
			else:
				scriptSig=src.coin.authorization2scriptSig(a,src)
			ins.append(SInput.from_src(src,scriptSig))
	
		outs=[SOutput.from_dst(o) for o in txo.dsts]
		return STransaction(version,ins,outs,locktime)

	#make a to_txo that parses authorizations from sigscript.


	#TODO: does the txid have to be compared backwards here?
	def enforce_deterministic_ordering(self): #TODO this isn't implemented correctly.  It can't be implemented correctly with the current API.  Should be a part of buildtx really.
		if(any([src.has_scriptSig() for src in self.ins])):
			raise Exception("Some of these inputs are already signed, permuting the transaction ordering would invalidate their signatures.")
			return
		
		def inp_key(inp):
			return (inp.outpoint.txid,inp.outpoint.index)
		def outp_key(outp):
			return (outp.value,outp.scriptPubKey)
		self.ins.sort(key=inp_key)
		self.outs.sort(key=outp_key)

	def txid_hash(self):
		pass
	
	def signature_authorization(self,index,klist,nhashtype=SIGHASH_ALL): #TODO get from coin of inputs.
		sho=SigHashOptions(nhashtype)
		siglist=[]
		pklist=[]
		for key in klist:
			sighash=legacy_sighash(self,index,nhashtype)
			signature=key.sign(sighash,use_der=True)
			signature+=chr(int(nhashtype) & 0xFF)
			signature=hexlify(signature)
			pubkey=hexlify(key.pub().pubkeydata)
			siglist.append(signature)
			pklist.append(pubkey)
		authorization={'sigs':siglist,'pubs':pklist}
		return authorization

	def validate_values(self):
		total_input=sum([inp.prevout.value for inp in self.ins])
		total_output=sum([outp.value for outp in self.outs])
		if(total_output > total_input):
			raise Exception("Transaction spends more than is input")

def legacy_preimage_scriptcode(stxo,script,input_index,sho):
	newscript=bytearray([x for x in script if x != _satoshiscript.OP_CODESEPARATOR])
	out=bytearray()
	out+=SVarInt(len(newscript)).serialize()
	out+=newscript
	return out

"""
    /** Serialize the passed scriptCode, skipping OP_CODESEPARATORs */
    template<typename S>
    void SerializeScriptCode(S &s) const {
        CScript::const_iterator it = scriptCode.begin();
        CScript::const_iterator itBegin = it;
        opcodetype opcode;
        unsigned int nCodeSeparators = 0;
        while (scriptCode.GetOp(it, opcode)) {
            if (opcode == OP_CODESEPARATOR)
                nCodeSeparators++;
        }
        ::WriteCompactSize(s, scriptCode.size() - nCodeSeparators);
        it = itBegin;
        while (scriptCode.GetOp(it, opcode)) {
            if (opcode == OP_CODESEPARATOR) {
                s.write((char*)&itBegin[0], it-itBegin-1);
                itBegin = it;
            }
        }
        if (itBegin != scriptCode.end())
            s.write((char*)&itBegin[0], it-itBegin);
    }"""



def legacy_preimage_input(stxo,script,index,input_index,sho):
	if(sho.anyonecanpay):
		index=input_index
	out=bytearray()
	out+=stxo.ins[index].outpoint.serialize()
	if(index != input_index):
		out+=SVarInt(0).serialize()
	else:
		x=legacy_preimage_scriptcode(stxo,script,input_index,sho)
		out+=x
	
	if(index != input_index and (sho.mode==SIGHASH_NONE or sho.mode == SIGHASH_SINGLE)):
		out+=struct.pack('<L',0)
	else:
		out+=struct.pack('<L',stxo.ins[index].sequence)
	return out
	
"""/** Serialize an input of txTo */
    template<typename S>
    void SerializeInput(S &s, unsigned int nInput) const {
        // In case of SIGHASH_ANYONECANPAY, only the input being signed is serialized
        if (fAnyoneCanPay)
            nInput = nIn;
        // Serialize the prevout
        ::Serialize(s, txTo.vin[nInput].prevout);
        // Serialize the script
        if (nInput != nIn)
            // Blank out other inputs' signatures
            ::Serialize(s, CScript());
        else
            SerializeScriptCode(s);
        // Serialize the nSequence
        if (nInput != nIn && (fHashSingle || fHashNone))
            // let the others update at will
            ::Serialize(s, (int)0);
        else
            ::Serialize(s, txTo.vin[nInput].nSequence);
    }
"""

#TODO: something with last executed codeseperator is required before here? And in the segwit version?  See https://github.com/bitcoin/bips/blob/master/bip-0143.mediawiki#Specification
def legacy_preimage_output(stxo,script,index,input_index,sho):
	out=bytearray()	
	if(sho.mode==SIGHASH_SINGLE and index != input_index):
		out+=SOutput(value=sighash_null_value,scriptPubKey=bytearray()).serialize()
	else:
		out+=stxo.outs[index].serialize()
	return out

"""
    /** Serialize an output of txTo */
    template<typename S>
    void SerializeOutput(S &s, unsigned int nOutput) const {
        if (fHashSingle && nOutput != nIn)
            // Do not lock-in the txout payee at other indices as txin
            ::Serialize(s, CTxOut());
        else
            ::Serialize(s, txTo.vout[nOutput]);
    }"""


def legacy_preimage(stxo,script,input_index,nhashtype,amount):
	sho=SigHashOptions(nhashtype)
	script=bytearray(script)
	out=bytearray()
	out+=struct.pack('<L',stxo.version)
	nInputs = 1 if sho.anyonecanpay else len(stxo.ins)
	out+=SVarInt(nInputs).serialize()
	for nInput in range(nInputs):
		out+=legacy_preimage_input(stxo,script,nInput,input_index,sho)

	if(sho.mode == SIGHASH_NONE):
		nOutputs = 0
	elif(sho.mode == SIGHASH_SINGLE):
		nOutputs = input_index+1
	else:
		nOutputs = len(stxo.outs)
	out+=SVarInt(nOutputs).serialize()
	for nOutput in range(nOutputs):
		out+=legacy_preimage_output(stxo,script,nOutput,input_index,sho)
	out+=struct.pack('<L',stxo.locktime)
	out+=struct.pack('<L',sho.nhashtype)
	return out
"""
    /** Serialize txTo */
    template<typename S>
    void Serialize(S &s) const {
        // Serialize nVersion
        ::Serialize(s, txTo.nVersion);
        // Serialize vin
        unsigned int nInputs = fAnyoneCanPay ? 1 : txTo.vin.size();
        ::WriteCompactSize(s, nInputs);
        for (unsigned int nInput = 0; nInput < nInputs; nInput++)
             SerializeInput(s, nInput);
        // Serialize vout
        unsigned int nOutputs = fHashNone ? 0 : (fHashSingle ? nIn+1 : txTo.vout.size());
        ::WriteCompactSize(s, nOutputs);
        for (unsigned int nOutput = 0; nOutput < nOutputs; nOutput++)
             SerializeOutput(s, nOutput);
        // Serialize nLockTime
        ::Serialize(s, txTo.nLockTime);
    }
"""

def legacy_sighash(stxo,input_index,nhashtype,script=None,amount=None):
	if(script is None):
		script=stxo.ins[input_index].prevout.scriptPubKey
	preimage=legacy_preimage(stxo,script,input_index,nhashtype,amount)
	return dblsha256(preimage)
