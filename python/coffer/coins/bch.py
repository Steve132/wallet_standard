from ..wallet import *
from _coin import *

from .. import _base
from blockchain._insight import InsightBlockchainInterface
from blockchain._interface import MultiBlockchainInterface

from impl._satoshicoin import *
import impl._cashaddr as _cashaddr
import impl._satoshitx as _satoshitx
import impl._segwittx as _segwittx

@ForkMixin.fork_decorator
class BCH(SatoshiCoin,ForkMixin):
	def __init__(self,is_testnet=False):
		
		if(not is_testnet):
			pkh_prefix=0x00
			sh_prefix=0x05
			wif_prefix=0x80
		else:
			pkh_prefix=0x6F
			sh_prefix=0xC4
			wif_prefix=0xEF

		sig_prefix=b'Bitcoin Signed Message:\n'
		
		super(BCH,self).__init__('BCH',is_testnet=is_testnet,
			pkh_prefix=pkh_prefix,
			sh_prefix=sh_prefix,
			wif_prefix=wif_prefix,
			sig_prefix=sig_prefix)

	def fork_info(self):
		return ForkMixin.ForkInfo(ticker='BTC',timestamp=1501593374,height=478558,forkUSD=277.0,ratio=1.0)
	
	#https://github.com/bitcoincashorg/spec/blob/master/cashaddr.md
	def parse_cashaddr(self,addrstring):
		prefix,version_int,payload=_cashaddr.decode(addrstring)
		addrversions=[self.pkh_prefix,self.sh_prefix]
		addrtypes=["p2pkh","p2sh"]
		addrtype=addrtypes[version_int]
		addrversion=addrversions[version_int]
	
		return Address(bytes(chr(addrversion))+payload,self,addrtype,format_kwargs={'cashaddr':True,'prefix':prefix})
	
	def _write_cashaddr(self,abytes,prefix=None):
		tprefix=prefix
		if(prefix==None or prefix==True or prefix==False or len(prefix)==0):
			if(self.is_testnet):
				tprefix='bchtest'
			else:
				tprefix='bitcoincash'
			
		addrpayload=abytes[1:]
		addrversion=abytes[0]
		vint=[self.pkh_prefix,self.sh_prefix].index(ord(addrversion))
		out=_cashaddr.encode(tprefix,vint,addrpayload)
		if(prefix==None or prefix==False):
			return out.split(':')[1]
		
		return out

	def format_addr(self,addr,cashaddr=True,prefix=None,*args,**kwargs):
		if(cashaddr):
			return self._write_cashaddr(addr.addrdata,prefix)
		else:
			return super(BCH,self).format_addr(addr,*args,**kwargs)

	def parse_addr(self,addrstring):
		if(':' in addrstring):
			return self.parse_cashaddr(addrstring)
		try:
			return self.parse_cashaddr(addrstring)
		except Exception as caerr:
			try:
				return super(BCH,self).parse_addr(addrstring)
			except Exception as err:
				raise Exception("Could not parse BCH address %s: %r,%r" % (addrstring,err,caerr))

	def blockchain(self):
		subcoins=[]

		if(not self.is_testnet):
			insighturls=[
				"https://insight.yours.org/insight-api",
				"https://bitcoincash.blockexplorer.com/api",
				"https://bch-bitcore2.trezor.io/api",
				"https://blockdozer.com/insight-api",
				"https://bch-insight.bitpay.com/api"
			]
		else:
			insighturls=[
				"https://tbch.blockdozer.com/insight-api",
				"https://test-bch-insight.bitpay.com/api"
			]

		insights=[InsightBlockchainInterface(self,insighturls)]
		subcoins.extend(insights)
		return MultiBlockchainInterface(self,subcoins).select()
	

	def _sighash(self,stxo,index,nhashtype):
		if(nhashtype & _satoshitx.SIGHASH_FORKID):
			return bitcoincash_sighash(stxo,index,nhashtype,forkIdValue=0)
		else:
			return super(BCH,self)._sighash(self,stxo,index,nhashtype)

	def authorize_index(self,stxo,index,addr,redeem_param,nhashtype=_satoshitx.SIGHASH_FORKID|_satoshitx.SIGHASH_ALL): #redeem_param is a private key for p2pk, a list of private keys for a multisig, redeemscript for p2sh, etc.
		return super(BCH,self).authorize_index(stxo,index,addr,redeem_param,nhashtype)






def bitcoincash_sighash(stxo,input_index,nhashtype,script=None,amount=None,forkIdValue=0):
	nhashtype|=_satoshitx.SIGHASH_FORKID
	nhashtype|= (forkIdValue & 0xFFFFFF) << 8;
	if(script is None):
		script=stxo.ins[input_index].prevout.scriptPubKey		#TODO: is this correct?  script seems to be the redeemScript for p2sh and other stuff 

	preimage=_segwittx.segwit_preimage(stxo,script,input_index,nhashtype,amount)
	return dblsha256(preimage)


