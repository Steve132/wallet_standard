import struct
from .._coin import *
from coffer.wallet import *
from cStringIO import StringIO
from binascii import hexlify,unhexlify
from _satoshiscript import *
import coffer._base as _base
from coffer.transaction import *
from _satoshitx import STransaction,SVarInt,SIGHASH_ALL
import logging



"""
pklist=authorization.get('pubs',[])
		siglist=authorization.get('sigs',[])
			
		multisig=len(pklist) > 1 or len(siglist) > 1

		if(multisig):
			raise NotImplementedError #p2sh multisig TODO
"""

#TODO MULTISIG
#TODO Script Registry for P2SH
#TODO Verify authorization signatures.

class SatoshiAddress(Address):
	def __init__(self,coin,version,addrdata):
		super(SatoshiAddress,self).__init__(coin,version,addrdata)

	def __str__(self):
		if(self.version==self.coin.ps_prefix):
			return 'p2ps_'+hexlify(self.addrdata)		
		out=bytearray()
		out+=chr(self.version)
		out+=self.addrdata
		return _base.bytes2base58c(out)
		
class SatoshiPKHAddress(SatoshiAddress):
	def __init__(self,coin,addrdata):
		super(SatoshiPKHAddress,self).__init__(coin,coin.pkh_prefix,addrdata)

	def _scriptPubKey(self):
		if(len(self.addrdata) != 20):
			raise Exception("legacy Address does not have 20 bytes")
		return bytearray([OP_DUP,OP_HASH160,len(self.addrdata)])+self.addrdata+bytearray([OP_EQUALVERIFY,OP_CHECKSIG])

	def _authorization2scriptSig(self,authorization):
		pklist=authorization.get('pub',[])
		#siglist=authorization.get('scriptSig',[])
			
		multisig=len(pklist) > 1 or len(siglist) > 1

		if(multisig):
				raise Exception("p2pkh addresses never have multisig")
		
		sig0=unhexlify(siglist[0])
		pk0=unhexlify(pklist[0])
	
		out=bytearray()
		out+=bytearray([len(sig0)])
		out+=sig0
		out+=bytearray([len(pk0)])
		out+=pk0
		return out

	def _authorize_index(satoshitxo,index,redeem_param):
		if(isinstance(redeem_param,basestring)):
			key=self.parse_privkey(redeem_param)
		elif(isinstance(redeem_param,PrivateKey)):
			key=redeem_param

		signature,pubkey=self.coin._sigpair(key,satoshitxo,index,_satoshitx.SIGHASH_ALL)				
		authorization={'sig':hexlify(signature),'pub':hexlify(pubkey)}
		return authorization

	def _is_authorized(az,tx,index):
		if('sig' in az and 'pub' in az):
			return True
		return False
	
class SatoshiSHAddress(SatoshiAddress):
	def __init__(self,coin,addrdata):
		super(SatoshiSHAddress,self).__init__(coin,coin.sh_prefix,addrdata)

	def _scriptPubKey(self):
		return bytearray([OP_HASH160,len(self.addrdata)])+self.addrdata+bytearray([OP_EQUAL])

	def _authorization2scriptSig(self,authorization):			#TODO refactor all script stuff to use script type and serialize/compile from lists of bytes objects
		out=bytearray()
		inputs=authorization.get('inputs',bytearray())
		out+=unhexlify(inputs)
		redeem=unhexlify(authorization.get('redeem',bytearray()))
		out+=bytearray([len(redeem)])
		out+=redeem
		return out

	def _authorize_index(self,satoshitxo,index,redeem_param):
		#if(isinstance(redeem_param,basestring)):
		#	r
		#if(isinstance(redeem_param,dict)):
		#	raise NotImplementedError
		#if(isinstance(redeem_param,list)):
		#	raise NotImplementedError
		return {'inputs':hexlify(redeem_param['inputs']),'redeem':hexlify(redeem_param['redeem'])}

	def _is_authorized(az,tx,index):
		if('inputs' in az and 'redeem' in az):
			return True
		return False

class SatoshiPSAddress(SatoshiAddress):
	def __init__(self,coin,addrdata):
		super(SatoshiPSAddress,self).__init__(coin,coin.ps_prefix,addrdata)

	def _scriptPubKey(self):
		return bytearray([])+self.addrdata

	def _authorization2scriptSig(self,authorization):
		if(multisig):
			raise NotImplementedError #bare multisig TODO  #https://bitcoin.org/en/glossary/multisig
		return unhexlify(authorization.get('inputs',bytearray()))

	def _is_authorized(self,az,tx,index):
		if('inputs' in az):
			return True

		return False

	def _authorize_index(self,satoshitxo,index,redeem_param):
		return {'inputs':hexlify(redeem_param['inputs'])}


class SatoshiCoin(Coin,ScriptableMixin): #a coin with code based on satoshi's codebase
	def __init__(self,ticker,is_testnet,wif_prefix,pkh_prefix,sh_prefix,sig_prefix):
		super(SatoshiCoin,self).__init__(
			ticker=ticker,
			is_testnet=is_testnet)

		self.wif_prefix=wif_prefix
		self.pkh_prefix=pkh_prefix
		self.sh_prefix=sh_prefix
		self.sig_prefix=sig_prefix
		self.ps_prefix=0xFF		#USE this for an internal representation of a p2ps address

	######INHERITED METHODS
	@property
	def denomination_scale(self):
		return 100000000.0

	######PARSING AND FORMATTING

	def make_addr(self,version,addrdata,*args,**kwargs):
		v=version
		byt=addrdata
		if(v==self.pkh_prefix):
			return SatoshiPKHAddress(self,byt)
		elif(v==self.sh_prefix):
			return SatoshiSHAddress(self,byt)
		elif(v==self.ps_prefix):
			return SatoshiPSAddress(self,byt)
		return Address(self,v,byt)

	def parse_addr(self,addrstring,*args,**kwargs):
		if(addrstring[:5]=='p2ps_'):
			return SatoshiPSAddress(self,unhexlify(addrstring[5:]))

		byt=_base.base58c2bytes(addrstring)
		v=byt[0]
		return self.make_addr(v,byt[1:],*args,**kwargs)

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
		if(pkbytes[0] != self.wif_prefix):
			raise Exception("WIF private key %s could not validate for coin %s.  Expected %d got %d." % (pkstring,self.ticker,pkbytes[0],self.wif_prefix))
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
	def pubkeys2address(self,pubkeys,bare_multisig=False,*args,**kwargs):
		multisig=len(pubkeys) > 1
		if(multisig):  #P2SH multisig TODO
			raise NotImplementedError
		else:
			h160=_base.hash160(pubkeys[0].pubkeydata)
			return self.make_addr(self.pkh_prefix,h160,*args,**kwargs)

	def address2scriptPubKey(self,addr):
		return addr._scriptPubKey()

	def scriptPubKey2address(self,scriptPubKey,*args,**kwargs):
		spk=scriptPubKey

		if(len(spk) > 24 and (spk[0],spk[1],spk[23],spk[24])==(OP_DUP,OP_HASH160,OP_EQUALVERIFY,OP_CHECKSIG)):
			return self.make_addr(self.pkh_prefix,spk[3:23],*args,**kwargs)
		if(len(spk) > 22 and (spk[0],spk[22])==(OP_HASH160,OP_EQUAL)):
			return self.make_addr(self.sh_prefix,spk[2:22],*args,**kwargs)
		return self.make_addr(self.ps_prefix,spk,*args,**kwargs)

	def script2scriptPubKey(self,redeemScript,p2ps=False):
		if(p2ps):
			return redeemScript
		else:
			scriptHash=_base.hash160(redeemScript)
			scriptPubKey=bytearray([OP_HASH160,20])+scriptHash
			scriptPubKey+=bytearray([OP_EQUAL])
			return scriptPubKey

	def script2address(self,redeemScript=None,p2ps=False,*args,**kwargs):
		sPK=self.script2scriptPubKey(redeemScript=redeemScript,p2ps=p2ps,*args,**kwargs)
		return self.scriptPubKey2address(sPK,*args,**kwargs)

	#def _authorization2redeemScript(self

	def authorization2scriptSig(self,authorization,src):
		return src.address._authorization2scriptSig(authorization)
		
	#################BUILDING AND SIGNING

	def _sighash(self,stxo,index,nhashtype):
		return legacy_sighash(stxo,index,nhashtype)

	def _sigpair(self,key,stxo,index,nhashtype):
		sighash=self._sighash(stxo,index,nhashtype)
		signature=key.sign(sighash,use_der=True)
		signature+=chr(int(nhashtype) & 0xFF)
		pubkey=key.pub().pubkeydata
		return signature,pubkey

	#TODO refactor all of this
	#addr2keys is a mapping from an address to a privkey or (list of privkeys for signing an on-chain transaction, or a redeem_param (multisig p2sh, or just p2sh)
	#returns a dictionary mapping the src ref to an authorization (an authorization is always a dictionary but in this case is a signature,pubkey pair) (can be directly stored later)
	#this is a part of a coin, NOT a chain
	def sign_tx(self,tx,addr2redeem):
		satoshitxo=self.txo2internal(tx)
		outauthorizations={}

		for addr,redeem_param in addr2redeem.items():
			naddr=addr
			if(isinstance(naddr,basestring)):
				naddr=self.parse_addr(naddr)
			
			for index,inp in enumerate(satoshitxo.ins):
				if(self.address2scriptPubKey(naddr)==inp.prevout.scriptPubKey):
					#redeem_param is a private key for p2pk, a list of private keys for a multisig, redeemscript for p2sh, etc.
					outauthorizations[inp.outpoint.to_outref(self.chainid)]=addr._authorize_index(satoshitxo,index,redeem_param) #TODO multiple address authorizations?  That's weird/wrong

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
		return src.address._is_authorized(az,tx,index)
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



