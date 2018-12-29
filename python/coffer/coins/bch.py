from ..wallet import *
from _coin import *

from .. import _base
from blockchain._insight import InsightBlockchainInterface
from blockchain._interface import MultiBlockchainInterface

from impl._satoshicoin import *
import impl._cashaddr as _cashaddr
import impl._satoshitx as _satoshitx
import impl._segwittx as _segwittx


def make_cash_address_type(name,SatoshiAddressBase):
	class CashAddressTemplate(SatoshiAddressBase):
		def __init__(self,coin,addrdata,prefix=None,cashaddr=True):
			super(CashAddressTemplate,self).__init__(coin,addrdata=addrdata)
			self.cashaddr=cashaddr
			self.prefix=prefix
		
		def __str__(self):
			if(self.cashaddr):
				return self.coin._write_cashaddr(self.version,self.addrdata,self.prefix)
			else:
				return super(CashAddressTemplate,self).__str__()

	CashAddressTemplate.__name__=name
	return CashAddressTemplate

CashPKHAddress=make_cash_address_type('CashPKHAddress',SatoshiPKHAddress)
CashSHAddress=make_cash_address_type('CashSHAddress',SatoshiSHAddress)
CashPSAddress=make_cash_address_type('CashPSAddress',SatoshiPSAddress)

	
@ForkMixin.fork_decorator
class BCH(SatoshiCoin,ForkMixin):
	def __init__(self,is_testnet=False,ticker='BCH'):
		
		if(not is_testnet):
			pkh_prefix=0x00
			sh_prefix=0x05
			wif_prefix=0x80
		else:
			pkh_prefix=0x6F
			sh_prefix=0xC4
			wif_prefix=0xEF

		sig_prefix=b'Bitcoin Signed Message:\n'
		
		super(BCH,self).__init__(ticker,is_testnet=is_testnet,
			pkh_prefix=pkh_prefix,
			sh_prefix=sh_prefix,
			wif_prefix=wif_prefix,
			sig_prefix=sig_prefix)

		self._prefix_to_class={self.pkh_prefix:CashPKHAddress,self.sh_prefix:CashSHAddress,self.ps_prefix:CashPSAddress}

	def fork_info(self):
		return ForkMixin.ForkInfo(ticker='BTC',timestamp=1501593374,height=478558,forkUSD=277.0,ratio=1.0)
	
	#https://github.com/bitcoincashorg/spec/blob/master/cashaddr.md
	def parse_cashaddr(self,addrstring):
		prefix,version_int,payload=_cashaddr.decode(addrstring)
		addrversions=[self.pkh_prefix,self.sh_prefix,self.ps_prefix]
		addrclasses=[self._prefix_to_class[v] for v in addrversions] #TODO implement cashaddr p2ps
		addrclass=addrclasses[version_int]
		
		return addrclass(self,bytearray()+payload,prefix=prefix)
	
	def _write_cashaddr(self,version,addrdata,prefix):
		tprefix=prefix
		if(prefix==None or prefix==True or prefix==False or len(prefix)==0):
			if(self.is_testnet):
				tprefix='bchtest'
			else:
				tprefix='bitcoincash'
			
		addrpayload=addrdata
		addrversion=version
		vint=[self.pkh_prefix,self.sh_prefix,self.ps_prefix].index(version)
		out=_cashaddr.encode(tprefix,vint,addrpayload)
		if(prefix==None or prefix==False):
			return out.split(':')[1]
		
		return out


	#https://en.bitcoin.it/wiki/List_of_address_prefixes
	def make_addr(self,version,addrdata,cashaddr=True,prefix=None,*args,**kwargs):
		if(not cashaddr):
			return super(BCH,self).make_address(pubkeys,*args,**kwargs)	
		return self._prefix_to_class[version](self,addrdata,*args,**kwargs)

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
	

	def _sigpair(self,key,stxo,index,nhashtype,add_forkid=True):
		if(add_forkid):
			nhashtype |= _satoshitx.SIGHASH_FORKID
		
		return super(BCH,self)._sigpair(key,stxo,index,nhashtype)

	def _sighash(self,stxo,index,nhashtype,add_forkid=True):
		if(add_forkid):
			nhashtype |= _satoshitx.SIGHASH_FORKID
		
		if(nhashtype & _satoshitx.SIGHASH_FORKID):
			return bitcoincash_sighash(stxo,index,nhashtype,forkIdValue=0)
		else:
			return super(BCH,self)._sighash(self,stxo,index,nhashtype)

def bitcoincash_sighash(stxo,input_index,nhashtype,script=None,amount=None,forkIdValue=0):
	nhashtype|=_satoshitx.SIGHASH_FORKID
	nhashtype|= (forkIdValue & 0xFFFFFF) << 8;
	
	sh=_segwittx.segwit_sighash(stxo,input_index,nhashtype,script,amount)
	return sh


