import struct
from _coin import *
from ..wallet import *
from cStringIO import StringIO
from binascii import hexlify,unhexlify
from _satoshiscript import *
from .. import _base
from ..transaction import *

class SatoshiCoin(Coin): #a coin with code based on satoshi's codebase
	def __init__(self,ticker,is_testnet,wif_prefix,pkh_prefix,sh_prefix,sig_prefix):
		super(SatoshiCoin,self).__init__(
			ticker=ticker,
			is_testnet=is_testnet)

		self.wif_prefix=wif_prefix
		self.pkh_prefix=pkh_prefix
		self.sh_prefix=sh_prefix
		self.sig_prefix=sig_prefix
		
	#https://en.bitcoin.it/wiki/List_of_address_prefixes
	def pubkeys2addr(self,pubkeys,*args,**kwargs):
		#if(isinstance(pubkeys,basestring)):
		#	pubkeys=[pubkeys] #assume that if it's a single argument, then it's one pubkey
		#pubkeys=[(PublicKey(pub) if isinstance(pub,basestr) else pub) for pub in pubkeys] #if there's a string test

		multisig=len(pubkeys) > 1
		if(multisig):#P2SH multisig
			raise NotImplementedError
		else:  #P2PKH
			h160=_base.hash160(pubkeys[0].pubkeydata)
			return Address(chr(self.pkh_prefix)+h160,self,format_args=args,format_kwargs=kwargs)

	def format_addr(self,addr,*args,**kwargs):
		return _base.bytes2base58c(addr.addrdata)

	def format_privkey(self,privkey):
		oarray=chr(self.wif_prefix)+privkey.privkeydata+(b'\x01' if privkey.is_compressed else b'')
		return _base.bytes2base58c(oarray)

	#https://www.cryptocompare.com/coins/guides/what-are-the-bitcoin-STransaction-types/
	def parse_privkey(self,pkstring):
		try:
			return super(SatoshiCoin,self).parse_privkey(pkstring)
		except:
			pass
		
		pkbytes=_base.base58c2bytes(pkstring)
		if(pkbytes[0] != chr(self.wif_prefix)):
			raise Exception("WIF private key %s could not validate for coin %s.  Expected %d got %d." % (pkstring,self.ticker,ord(pkbytes[0]),self.wif_prefix))
		if(len(pkbytes)==34):
			return PrivateKey(pkbytes[1:-1],is_compressed=True)
		else:
			return PrivateKey(pkbytes[1:],is_compressed=False)

	def parse_addr(self,addrstring):
		return Address(_base.base58c2bytes(addrstring),self)

	def address2scriptPubKey(self,addr):
		version=ord(addr.addrdata[0])
		addrbytes=addr.addrdata[1:]
		if(len(addrbytes) != 20):
			raise Exception("legacy Address does not have 20 bytes")
		if(version==self.pkh_prefix):
			return b''.join([OP_DUP,OP_HASH160,chr(len(addrbytes)),addrbytes,OP_EQUALVERIFY,OP_CHECKSIG])
		elif(version==self.sh_prefix):
			return b''.join([OP_HASH160,chr(len(addrbytes)),addrbytes,OP_EQUAL])
		else:
			raise Exception("Invalid Address Version %h for address %s" % (version,addr))
		raise NotImplementedError




	#def format_tx(self,txo):
	#	stxo=STransaction.fromtxo(txo)
	#	return STransaction._sc_serialize(stxo)

	def deserializetx(self,sio):
		if(isinstance(sio,basestring)):
			sio=StringIO(sio)
		return STransaction._sc_deserialize(sio)

	def txto_dict(self,tx):
		return tx.to_dict()

	def txfrom_dict(self,dct):
		return STransaction.from_dict(dct)

	def denomination_float2whole(self,x):
		return super(SatoshiCoin,self).denomination_float2whole(x,100000000.0)
	
	def denomination_whole2float(self,x):
		return super(SatoshiCoin,self).denomination_whole2float(x,100000000.0)

	def signtx(self,tx,keys):
		satoshitxo=STransaction.from_txo(tx)
		print(hexlify(STransaction._sc_serialize(satoshitxo)))
		print(satoshitxo.to_dict())



	"""
	#todo: obviously broken
    def serialize_preimage(self, i):
        nVersion = int_to_hex(self.version, 4)
        nHashType = int_to_hex(1, 4)
        nLocktime = int_to_hex(self.locktime, 4)
        inputs = self.inputs()
        outputs = self.outputs()
        txin = inputs[i]
        # TODO: py3 hex
        if self.is_segwit_input(txin):
            hashPrevouts = bh2u(Hash(bfh(''.join(self.serialize_outpoint(txin) for txin in inputs))))
            hashSequence = bh2u(Hash(bfh(''.join(int_to_hex(txin.get('sequence', 0xffffffff - 1), 4) for txin in inputs))))
            hashOutputs = bh2u(Hash(bfh(''.join(self.serialize_output(o) for o in outputs))))
            outpoint = self.serialize_outpoint(txin)
            preimage_script = self.get_preimage_script(txin)
            scriptCode = var_int(len(preimage_script) // 2) + preimage_script
            amount = int_to_hex(txin['value'], 8)
            nSequence = int_to_hex(txin.get('sequence', 0xffffffff - 1), 4)
            preimage = nVersion + hashPrevouts + hashSequence + outpoint + scriptCode + amount + nSequence + hashOutputs + nLocktime + nHashType
        else:
            txins = var_int(len(inputs)) + ''.join(self.serialize_input(txin, self.get_preimage_script(txin) if i==k else '') for k, txin in enumerate(inputs))
            txouts = var_int(len(outputs)) + ''.join(self.serialize_output(o) for o in outputs)
            preimage = nVersion + txins + txouts + nLocktime + nHashType
        return preimage

	#note: this method is from update_signatures.  Could also need to use sign() from electrum
	def _signtxsatoshi(self,stx,privkeys):
		for i, txin in enumerate(self.inputs()):
			pubkeys, x_pubkeys = self.get_sorted_pubkeys(txin)
			sigs1 = txin.get('signatures')
			sigs2 = d['inputs'][i].get('signatures')
			for sig in sigs2:
				if sig in sigs1:
					continue

			pre_hash = Hash(bfh(self.serialize_preimage(i)))
			# der to string
			order = ecdsa.ecdsa.generator_secp256k1.order()
			r, s = ecdsa.util.sigdecode_der(bfh(sig[:-2]), order)
			sig_string = ecdsa.util.sigencode_string(r, s, order)
			compressed = True
			for recid in range(4):
				public_key = MyVerifyingKey.from_signature(sig_string, recid, pre_hash, curve = SECP256k1)
				pubkey = bh2u(point_to_ser(public_key.pubkey.point, compressed))
				if pubkey in pubkeys:
					public_key.verify_digest(sig_string, pre_hash, sigdecode = ecdsa.util.sigdecode_string)
					j = pubkeys.index(pubkey)
					print_error("adding sig", i, j, pubkey, sig)
					self._inputs[i]['signatures'][j] = sig

		        	break"""
