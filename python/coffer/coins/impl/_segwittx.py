from _satoshitx import *
import struct

#https://bitcoincore.org/en/segwit_wallet_dev/
class SWitnessTransaction(STransaction):
	def __init__(version,flag,ins,outs,witness,locktime):
		super(SWitnessTransaction,self).__init__(version,ins,outs,locktime)
		self.flag=flag
		self.witness=witness

	def serialize(self):
		txo=self

		#if(not isinstance(txo,SWitnessTransaction) and isinstance(txo,STransaction)):
		#	return STransaction._sc_serialize(txo)

		out=bytearray()
		out+=struct.pack('<L',txo.version)
		out+=b'\x00'
		out+=struct.pack('B',txo.flag)

		out+=SVarInt(len(txo.ins)).serialize()
		for inv in txo.ins:
			out+=inv.serialize()

		out+=SVarInt(len(txo.outs)).serialize()
		for ot in txo.outs:
			out+=ot.serialize()

		if(len(txo.witness) != len(txo.ins)):
			raise Exception("Witness data not the same length as number of inputs")
		for wit in txo.witness:		#load witness data
			out+=SVarInt(len(wit)).serialize()
			for wititem in wit:
				out+=SVarInt(len(wititem)).serialize()
				out+=wititem #TODO: .serialize()
				
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
	#TODO: from tx that calls coin.signature

	def txid_hash(self):
		return dblsha256(super(SWitnessTransaction,self).serialize())
	def wtxid_hash(self):
		return dblsha256(self.serialize())

def segwit_get_prevouthash(stxo):
	out=bytearray()
	for inp in stxo.ins:
		out+=inp.outpoint.serialize()

	return dblsha256(out)

"""template <class T>
uint256 GetPrevoutHash(const T& txTo)
{
    CHashWriter ss(SER_GETHASH, 0);
    for (const auto& txin : txTo.vin) {
        ss << txin.prevout;
    }
    return ss.GetHash();
}"""

def segwit_get_sequencehash(stxo):
	out=bytearray()
	for inp in stxo.ins:
		out+=struct.pack('<L',inp.sequence)
	return dblsha256(out)

"""template <class T>
uint256 GetSequenceHash(const T& txTo)
{
    CHashWriter ss(SER_GETHASH, 0);
    for (const auto& txin : txTo.vin) {
        ss << txin.nSequence;
    }
    return ss.GetHash();
}"""


def segwit_get_outputshash(stxo):
	out=bytearray()
	for outp in stxo.outs:
		out+=outp.serialize()
	return dblsha256(out)

"""template <class T>
uint256 GetOutputsHash(const T& txTo)
{
    CHashWriter ss(SER_GETHASH, 0);
    for (const auto& txout : txTo.vout) {
        ss << txout;
    }
    return ss.GetHash();
}
"""
	
#TODO: segwit needs the right thing provided in script (redeemscript for p2sh or witness script or scriptPubKey for p2pkh)
#https://bitcoin.stackexchange.com/questions/57994/what-is-scriptcode
def segwit_preimage(stxo,script,input_index,nhashtype,amount=None):
	hashPrevouts=b'\x00'*32
	hashSequence=b'\x00'*32
	hashOutputs=b'\x00'*32
	nhashtype=int(nhashtype)
	
	sho=SigHashOptions(nhashtype)

	"""if (sigversion == SigVersion::WITNESS_V0) {
		    uint256 hashPrevouts;
		    uint256 hashSequence;
		    uint256 hashOutputs;
		    const bool cacheready = cache && cache->ready;

		    if (!(nHashType & SIGHASH_ANYONECANPAY)) {
		        hashPrevouts = cacheready ? cache->hashPrevouts : GetPrevoutHash(txTo);
		    }

		    if (!(nHashType & SIGHASH_ANYONECANPAY) && (nHashType & 0x1f) != SIGHASH_SINGLE && (nHashType & 0x1f) != SIGHASH_NONE) {
		        hashSequence = cacheready ? cache->hashSequence : GetSequenceHash(txTo);
		    }


		    if ((nHashType & 0x1f) != SIGHASH_SINGLE && (nHashType & 0x1f) != SIGHASH_NONE) {
		        hashOutputs = cacheready ? cache->hashOutputs : GetOutputsHash(txTo);
		    } else if ((nHashType & 0x1f) == SIGHASH_SINGLE && nIn < txTo.vout.size()) {
		        CHashWriter ss(SER_GETHASH, 0);
		        ss << txTo.vout[nIn];
		        hashOutputs = ss.GetHash();
		    }"""
	
	if(not sho.anyonecanpay):
		hashPrevouts=segwit_get_prevouthash(stxo)
		
	if(not sho.anyonecanpay and sho.mode != SIGHASH_NONE and sho.mode != SIGHASH_SINGLE):
		hashSequence=segwit_get_sequencehash(stxo)

	if(sho.mode != SIGHASH_SINGLE and sho.mode != SIGHASH_NONE):
		hashOutputs=segwit_get_outputshash(stxo)
	elif(sho.mode == SIGHASH_SINGLE and input_index < len(stxo.ins)):
		hashOutputs=dblsha256(stxo.outs[input_index].serialize())

	"""
        CHashWriter ss(SER_GETHASH, 0);
        // Version
        ss << txTo.nVersion;
        // Input prevouts/nSequence (none/all, depending on flags)
        ss << hashPrevouts;
        ss << hashSequence;
        // The input being signed (replacing the scriptSig with scriptCode + amount)
        // The prevout may already be contained in hashPrevout, and the nSequence
        // may already be contain in hashSequence.
        ss << txTo.vin[nIn].prevout;
        ss << scriptCode;
        ss << amount;
        ss << txTo.vin[nIn].nSequence;
        // Outputs (none/one/all, depending on flags)
        ss << hashOutputs;
        // Locktime
        ss << txTo.nLockTime;
        // Sighash type
        ss << nHashType;

        return ss.GetHash();"""

	out=bytearray()
	out+=struct.pack('<L',stxo.version)
	out+=hashPrevouts
	out+=hashSequence
	out+=stxo.ins[input_index].outpoint.serialize()

	out+=SVarInt(len(script)).serialize()
	out+=script

	if(amount is None):
		a=stxo.ins[input_index].prevout.value
	else:
		a=int(amount)
	out+=struct.pack('<Q',a)
	out+=struct.pack('<L',stxo.ins[input_index].sequence)
	out+=hashOutputs;
	out+=struct.pack('<L',stxo.locktime)
	out+=struct.pack('<L',sho.nhashtype)
	
	return out
	
def segwit_sighash(stxo,input_index,nhashtype,script=None,amount=None):
	if(script is None):
		#if(p2pkh)USE for 
		script=stxo.ins[input_index].prevout.scriptPubKey		#TODO: is this correct?  script seems to be the redeemScript for p2sh and other stuff YEAH use for p2sh when redeemScript includes CHECKSIG
		#if(p2sh)
			#script=stxo.ins[input_index].scriptSig[0] 				#redeemscript from scriptSig of input gives pubkey o
 
	preimage=segwit_preimage(stxo,script,input_index,nhashtype,amount)
	return dblsha256(preimage)
