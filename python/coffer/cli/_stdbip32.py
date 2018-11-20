def coverage(coin,accounts=[0],algorithm='broad'):
	if(algorithm!='broad'):
		raise Exception("Unknown wallet coverage algorithm")
	if(isinstance(accounts,int)):
		accounts=[accounts]

	
	#bitcoind core (https://github.com/bitcoin/bitcoin/pull/8035)
	#yield "bitcoind","m/0h/0h","*h","*h",[],{} #<---this doesn't work because you can't decend to a hardened child
	#yield "multibit","m/0h","1/*","0/*",[],{}


	unhardened=coin.bip44_id-0x80000000
	#https://github.com/ConsenSys/eth-lightwallet/issues/80	
	for accdex in accounts: 	
		#COIN bip44 account
		yield "bip44 (account %d)" % accdex,"m/44h/%dh/%dh" % (unhardened,accdex),"1/*","0/*",[],{}
		#BTC bip44 account (this is just really common.  E.g. electrum

		if(unhardened is not 0 and unhardened is not 1):
			yield "bip44-btc-root (account %d)" % accdex, "m/44h/0h/%dh" % (accdex),"1/*","0/*",[],{}
		

		#TODO: if(isinstance(Coin,SegWitCoin)) default segwit bip32 settings to load prefixes
		#TODO: if(isinstance(Coin,BCH)) default cashaddr
		#TODO: if(isinstance(Coin,LTC)) append use_ltpub=True to the options
		#TODOD if(isinstance(Coin,ForkMixin) and Fork.originalchain != BTC)
			#yield coin chain accounts
		

