def coverage(coin,args):
	if(args.coverage!='broad'):
		raise Exception("Unknown wallet coverage algorithm")

	
	#bitcoind core (https://github.com/bitcoin/bitcoin/pull/8035)
	yield "bitcoind","m/0h/0h","*h","*h",[],{}
	unhardened=coin.bip44_id-0x80000000
	#yield "multibit","m/0h","1/*","0/*",[],{}

	#https://github.com/ConsenSys/eth-lightwallet/issues/80	
	for accdex in range(args.num_accounts): 	
		#COIN bip44 account
		yield "bip44 (account %d)" % accdex,"m/44h/%dh/%dh" % (unhardened,args.num_accounts),"1/*","0/*",[],{}
		#BTC bip44 account (this is just really common.  E.g. electrum

		if(unhardened is not 0):
			yield "bip44-btc-root (account %d)" % accdex, "m/44h/0h/%dh" % (args.num_accounts),"1/*","0/*",[],{}
		

		#TODO: if(isinstance(Coin,SegWitCoin)) default segwit bip32 settings to load prefixes
		#TODO: if(isinstance(Coin,BCH)) default cashaddr
		#TODOD if(isinstance(Coin,ForkMixin) and Fork.originalchain != BTC)
			#yield coin chain accounts
		

