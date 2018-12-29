from ..wallet import *
from _coin import *
from ..bip32 import Bip32
from blockchain._insight import InsightBlockchainInterface
from blockchain._interface import MultiBlockchainInterface
from bch import bitcoincash_sighash

from impl._segwitcoin import *


@ForkMixin.fork_decorator
class BTG(SegwitCoin,ForkMixin):
	def __init__(self,is_testnet=False):

		if(not is_testnet):
			pkh_prefix=38
			sh_prefix=23
			wif_prefix=0x80
			bech32_prefix="btg"
		else:
			pkh_prefix=111
			sh_prefix=196
			wif_prefix=239
			bech32_prefix="tbtg"

		sig_prefix=b'Bitcoin Signed Message:\n'
		
		super(BTC,self).__init__('BTC',is_testnet=is_testnet,
			pkh_prefix=pkh_prefix,
			sh_prefix=sh_prefix,
			wif_prefix=wif_prefix,
			sig_prefix=sig_prefix,bech32_prefix=bech32_prefix)

	def fork_info(self):
		return ForkMixin.ForkInfo(ticker='BTC',timestamp=1510493641,height=491407,forkUSD=138.0,ratio=1.0)
		
	def blockchain(self,*args,**kwargs):
		subcoins=[]
	
		if(not self.is_testnet):
			insighturls=[
				"https://btgexplorer.com/api",
				"https://explorer.bitcoingold.org/insight-api/"
			]
		else:
			insighturls=[
				"https://test-explorer.bitcoingold.org/insight-api"
			]

		insights=[InsightBlockchainInterface(self,insighturls)]
		subcoins.extend(insights)
		return MultiBlockchainInterface(self,subcoins).select()


	def _sigpair(self,key,stxo,index,nhashtype):
		nhashtype |= _satoshitx.SIGHASH_FORKID
		return super(BCH,self)._sigpair(key,stxo,index,nhashtype)

	def _sighash(self,stxo,index,nhashtype):
		return btg_sighash(stxo,index,nhashtype)
		
def btg_sighash(stxo,input_index,nhashtype,script=None,amount=None):
	return bitcoincash_sighash(stxo,input_index,nhashtype,script,amount,forkIdValue=79)
