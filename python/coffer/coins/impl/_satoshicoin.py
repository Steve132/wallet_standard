import struct
from .._coin import *
from coffer.wallet import *
from cStringIO import StringIO
from binascii import hexlify,unhexlify
from _satoshiscript import *
import coffer._base as _base
from coffer.transaction import *
from _satoshitx import STransaction,SVarInt
import logging

class SatoshiCoin(Coin,ScriptableMixin): #a coin with code based on satoshi's codebase
	def __init__(self,ticker,is_testnet,wif_prefix,pkh_prefix,sh_prefix,sig_prefix):
		super(SatoshiCoin,self).__init__(
			ticker=ticker,
			is_testnet=is_testnet)

		self.wif_prefix=wif_prefix
		self.pkh_prefix=pkh_prefix
		self.sh_prefix=sh_prefix
		self.sig_prefix=sig_prefix
		self._p2ps_prefix=0xFF		#USE this for an internal representation of a p2ps address

	######INHERITED METHODS
	@property
	def denomination_scale(self):
		return 100000000.0

	######PARSING AND FORMATTING
	def format_addr(self,addr,*args,**kwargs):
		if(ord(addr.adddrdata[0])==self._p2ps_prefix):
			return 'p2ps_'+hexlify(addr.addrdata[1:])
		return _base.bytes2base58c(addr.addrdata)

	def parse_addr(self,addrstring):
		if(addrstring[:5]=='p2ps_'):
			return Address(bytearray([self._p2ps_prefix])+unhexlify(addrstring[5:]),self,'p2ps')
		byt=_base.base58c2bytes(addrstring)
		v=ord(byt[0])
		if(v==self.pkh_prefix):
			addrtype='p2sh'
		elif(v==self.sh_prefix):
			addrtype='p2pkh'
		else:
			addrtype='unknown_'
		return Address(byt,self,addrtype)

	def format_privkey(self,privkey):
		oarray=bytearray()
		oarray+=bytearray([self.wif_prefix])
		oarray+=privkey.privkeydata
		oarray+=bytearray([0x01] if privkey.is_compressed else [])
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

	def parse_tx(self,sio):
		if(isinstance(sio,basestring)):
			sio=StringIO(unhexlify(sio))
		return STransaction._sc_deserialize(hexlify(sio))

	def format_tx(self,txo):
		stxo=self.txo2internal(txo)
		return hexlify(stxo.serialize())

	def txo2internal(self,txo):
		return STransaction.from_txo(txo)


	#########PUBKEYS, ADDRESSES, and SIGNING


	#https://en.bitcoin.it/wiki/List_of_address_prefixes
	def pubkeys2addr(self,pubkeys,*args,**kwargs):
		multisig=len(pubkeys) > 1
		if(multisig):  #P2SH multisig
			raise NotImplementedError
		else:
			h160=_base.hash160(pubkeys[0].pubkeydata)
			return Address(chr(self.pkh_prefix)+h160,self,'p2pkh',format_args=args,format_kwargs=kwargs)

	def address2scriptPubKey(self,addr):
		version=ord(addr.addrdata[0])
		addrbytes=bytearray()
		addrbytes+=addr.addrdata[1:]
		
		if(len(addrbytes) != 20):
			raise Exception("legacy Address does not have 20 bytes")
		if(version==self.pkh_prefix):
			return bytearray([OP_DUP,OP_HASH160,len(addrbytes)])+addrbytes+bytearray([OP_EQUALVERIFY,OP_CHECKSIG])
		elif(version==self.sh_prefix):
			return bytearray([OP_HASH160,len(addrbytes)])+addrbytes+bytearray([OP_EQUAL])
		elif(version=self._p2ps_prefix):
			return bytearray([])+addrbytes
		else:
			raise Exception("Invalid Address Version %h for address %s" % (version,addr))
		raise NotImplementedError

	def scriptPubKey2address(self,scriptPubKey):
		spk=scriptPubKey
		if((spk[0],spk[1],spk[23],spk[24])==(OP_DUP,OP_HASH160,OP_EQUALVERIFY,OP_CHECKSIG)):
			return Address(chr(self.pkh_prefix)+spk[3:23],self,'p2pkh')
		if((spk[0],spk[22])==(OP_HASH160,OP_EQUAL)):
			return Address(chr(self.sh_prefix)+spk[2:22],self,'p2sh')
		return Address(chr(self._p2ps_prefix)+spk,self,'p2ps')

	def script2addr(self,scriptData,*args,**kwargs):
		raise NotImplementedError
			
		

	def authorization2scriptSig(self,authorization,src):
		pklist=authorization.get('pubs',[])
		siglist=authorization.get('sigs',[])
		multisig=len(pklist) > 1 or len(siglist) > 1
		if(multisig):
			raise NotImplementedError
		version=ord(src.address.addrdata[0])
		if(version!=self.pkh_prefix):
			raise NotImplementedError
		sig0=unhexlify(siglist[0])
		pk0=unhexlify(pklist[0])
		
		out=bytearray()
		out+=bytearray([len(sig0)])
		out+=sig0
		out+=bytearray([len(pk0)])
		out+=pk0
		return out


	#################BUILDING AND SIGNING

	def _sighash(self,stxo,index,nhashtype):
		return legacy_sighash(stxo,index,nhashtype)

	def _authorize_index(self,stxo,index,addr,redeem_param,nhashtype=_satoshitx.SIGHASH_ALL): #redeem_param is a private key for p2pk, a list of private keys for a multisig, redeemscript for p2sh, etc.
		version=ord(src.address.addrdata[0])
		if(version==self.pkh_prefix):
			siglist=[]
			pklist=[]
			if(isinstance(klist,basestring)):
				klist=[self.parse_privkey(privkey)]
			elif(isinstance(klist,PrivateKey)):
				klist=[klist]

			for key in klist:
				sighash=self._sighash(stxo,index,nhashtype)
				signature=key.sign(sighash,use_der=True)
				signature+=chr(int(nhashtype) & 0xFF)
				signature=hexlify(signature)
				pubkey=hexlify(key.pub().pubkeydata)
				siglist.append(signature)
				pklist.append(pubkey)
			authorization={'sigs':siglist,'pubs':pklist}
			return authorization
		else:
			raise NotImplementedError


	#addr2keys is a mapping from an address to a privkey or (list of privkeys for signing an on-chain transaction, or a redeem_param (multisig p2sh, or just p2sh)
	#returns a dictionary mapping the src ref to an authorization (an authorization is always a dictionary but in this case is a signature,pubkey pair) (can be directly stored later)
	#this is a part of a coin, NOT a chain
	def sign_tx(self,tx,addr2redeem):
		satoshitxo=self.txo2internal(tx)
		outauthorizations={}

		for addr,redeem_param in addr2keys.items():
			naddr=addr
			if(isinstance(naddr,basestring)):
				naddr=self.parse_addr(naddr)
			
			for index,inp in enumerate(satoshitxo.ins):
				if(self.address2scriptPubKey(naddr)==inp.prevout.scriptPubKey):
					outauthorizations[inp.outpoint.to_outref(self.chainid)]=self._authorize_index(satoshitxo,index,addr,redeem_param) #TODO multiple address authorizations?  That's weird/wrong

		return outauthorizations

	def sign_msg(self,msg,privkey):
		preimage=bytearray()
		preimage+=SVarInt(len(self.sig_prefix)).serialize()+self.sig_prefix
		preimage+=SVarInt(len(msg)).serialize()+bytearray(msg)
		sighash=_base.dblsha256(preimage)
		return privkey.sign(sighash,use_der=False)

	def verify_tx(self,txo):
		setunspents=frozenset(txo.srcs)
		if(len(setunspents) < len(txo.srcs)):
			raise Exception("Duplicates detected in sources.  All sources must be unique in a transaction for this coin")

		def outlistcheck(outlist):
			total=0
			for out in outlist:
				if(out.coin != self):
					raise Exception("All the sources or destinations must be an on-chain transaction for %r." % (self))
				if(out.iamount < 0):
					raise Exception("All sources or destinations must have a nonnegative amount")
				total+=out.iamount
			return total
		
		src_total=outlistcheck(txo.srcs)
		dst_total=outlistcheck(txo.dsts)

		if(src_total < dst_total):
			raise Exception("The total value of the sources must be more than the total value of the destinations")
		return src_total,dst_total

	def build_tx(self,sources,destinations,changeaddr,fee=None,feerate=None):
		if(fee is None and feerate is None):
			raise Exception("fee or feerate must be specified.  Pass fee=0.0 if you want to override this")
		
		if(changeaddr is None):
			raise Exception('There is no change address specified.  Are you sure you meant this?  Add a change address or pass the string "NO_CHANGE_ADDRESS" as the changeaddr argument to override this warning')

		txo=Transaction(self,list(sources),list(destinations))	#important list() makes a copy for later mutability below when estimating the fees
	
		if(str(changeaddr) != 'NO_CHANGE_ADDRESS'):
			change_output=Output(self,changeaddr,self.denomination_whole2float(1))
			txo.dsts.append(change_output)
			if(fee is None or fee < 0.0):
				fee=self.estimate_fee(txo,feerate)
			src_total,dst_total=self.verify_tx(txo)
			change_iamount=src_total-dst_total
			ifee=self.denomination_float2whole(fee)
			if(change_iamount > ifee):
				change_iamount-=self.denomination_float2whole(fee)
				txo.dsts[-1].iamount=change_iamount #set the appended change amount to the leftover minus the fee
			else:
				txo.dsts.pop()
				logging.warning("Not using a change address because the selected fee was more than the leftover change.")
	
		self.verify_tx(txo)

		return txo

	def is_src_fully_authorized(self,tx,index):   #TODO This could almost certainly be implemented better by checking the sig and pubkey to see if they verify (verify signatures)
		src=tx.srcs[index]
		if(src.ref not in tx.authorizations):
			return False
		
		az=tx.authorizations[src.ref]
		if('sigs' in az and 'pubs' in az and len(az['sigs']) > 0 and len(az['pubs']) > 0):
			return True

		#TODO: check signatures

		return False
		
	##########################blockchain stuff

	def estimate_fee(self,txo,fee_amount_per_byte,estimate_after_signatures=True):
		satoshitxo=self.txo2internal(txo)
		#TODO: do this differently for a segwit transaction
		estimated_post_sig_bytes=0
		if(estimate_after_signatures):
			num_unsigned_sigs=sum([1 for inp in satoshitxo.ins if not inp.has_scriptSig()])
			bytes_per_signature=75+33#assuming a compressed pubkey legacy p2pkh
			estimated_post_sig_bytes=num_unsigned_sigs*bytes_per_signature
		txbytes=len(unhexlify(self.format_tx(txo)))
		return (txbytes+estimated_post_sig_bytes)*fee_amount_per_byte




	"""
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



