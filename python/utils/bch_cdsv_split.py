#from coffer.coin.cli import cliwallet
from coffer.coins import fromticker
from binascii import hexlify,unhexlify
from hashlib import sha256
from coffer.transaction import *
from coffer.account import *
import sys
import argparse
#sendback='bchtest:qqmd9unmhkpx4pkmr6fkrr8rm6y77vckjvqe8aey35'

class CDSV_SplitAddressAccount(OnChainAddressSetAccount):
	def __init__(self,coin,pubkey):
		self.pubkey=pubkey		
		self.coin=coin
		self.addr=self._derive_addr()

		super(CDSV_SplitAddressAccount,self).__init__(coin,external=[[self.addr]],authref=str(self.addr),gap=1)

	def _derive_addr(self):
		OP_CHECKDATASIG=0xba
		OP_CHECKDATASIGVERIFY=0xbb
		pub=self.pubkey

		redeemScript=bytearray()
		redeemScript+=bytearray([len(pub.pubkeydata)])
		redeemScript+=pub.pubkeydata
		redeemScript+=bytearray([OP_CHECKDATASIG])

		addr=self.coin.script2address(redeemScript=redeemScript)
		self.redeemScript=redeemScript
		return addr
	
	def auth_tx(self,txo,authobj,max_search=100,*args,**kwargs):
		privkey=self.coin.parse_privkey(authobj)

		msg=os.urandom(32)
		msghash=sha256(msg).digest()
		sig=priv.sign(msghash,use_der=True)

		inputs=bytearray()
		inputs+=bytearray([len(sig)])
		inputs+=sig
		inputs+=bytearray([len(msg)])
		inputs+=msg

		auths=coin.sign_tx(txo,{self.addr:{'redeem':self.redeemScript,'inputs':inputs}})
		txo.authorizations=auths








if __name__=='__main__':
	parser=argparse.ArgumentParser()
	parser.add_argument('--testnet',action='store_true',default=False)
	parser.add_argument('secret',type=str)
	parser.add_argument('--dstaddr',type=str,default=None)
	parser.add_argument('--dstamount',type=float,default=0.001)

	args=parser.parse_args()

	ticker='BCH'+('-TEST' if args.testnet else '')
	coin=fromticker(ticker)
	pstr=sha256(args.secret).hexdigest()
	priv=coin.parse_privkey(pstr)
	pub=priv.pub()
	acc=CDSV_SplitAddressAccount(coin,pub)

	print("Address: "+str(acc.external[0][0]))

	if(args.dstaddr):
		args.dstaddr=coin.parse_addr(args.dstaddr)
	
		acc.sync()
		u=set(acc.unspents_iter())	#this should really be wallet.select([acc],sweep) but it's not.
		if(len(u)):
			dst=Output(coin,args.dstaddr,args.dstamount)
			txo=coin.build_tx(u,[dst],acc.addr,feerate=coin.denomination_whole2float(10))
			acc.auth_tx(txo,privkey)
			print(coin.format_tx(txo))
		
	#src=SubmittedOutput(coin,addr,srcamount,srctx,srcindex)
	#dst=Output(coin,outaddr,srcamount)
	#txo=coin.build_tx([src],[dst],'NO_CHANGE_ADDRESS',fee=0.001)
	#xs=coin.format_tx(txo)
	
	#print(coin.format_tx(txo))

#cliwallet.CliWallet.to_archive('testnetwallet')
#args.func(w,args)

#cliwallet.CliWallet.to_archive(w,args.wallet_out,pin=args.pin_out)
