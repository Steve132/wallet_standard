from _interface import *
from _insight import *


def getbci(coin):
	lookups={'btc':btc,
		'bch':bch}
	cticker=coin.ticker.lower()
	if(cticker in lookups):
		return lookups[cticker.lower()](coin)
	else:
		raise Exception("Could not find a suitable block-explorer interface instance for '%s'" % (coin.ticker))

def btc(coin):
	subcoins=[]
	
	if(not coin.is_testnet):
		insighturls=[
			"https://insight.bitpay.com/api",
			"https://blockexplorer.com/api",
			"https://localbitcoinschain.com/api",
			"https://bitcore2.trezor.io/api",
			"https://btc.blockdozer.com/insight-api"
		]
	else:
		insighturls=[
			"https://tbtc.blockdozer.com/insight-api",
			"https://test-insight.bitpay.com/api"
		]

	insights=[InsightBlockchainInterface(coin,u) for u in insighturls]
	subcoins.extend(insights)
	return MultiBlockchainInterface(coin,subcoins)

def bch(coin):
	subcoins=[]

	if(not coin.is_testnet):
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

	insights=[InsightBlockchainInterface(coin,u) for u in insighturls]
	subcoins.extend(insights)
	return MultiBlockchainInterface(coin,subcoins)



#https://insight.litecore.io/
#https://insight.dash.org/insight/
#https://insight.zcash.org/insight
