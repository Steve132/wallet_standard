from ..coins.btc import BTC
from ..coins.blockchain._insight import InsightBlockchainInterface
from pprint import pprint
from ..coins.blockchain.chains import getbci
from ..bip32 import paths
btc1=BTC()

bc=getbci(btc1)

#for _ in range(10):
#	unspents=bc.unspents(['12P7svS6CR3CapfRrY5KKFB3EqHbtw7g6G'])
#	print(list(unspents))


#bc=InsightBlockchainInterface(btc1,'https://blockexplorer.com/api')
unspents=bc.unspents(['12P7svS6CR3CapfRrY5KKFB3EqHbtw7g6G'])
#print(list(unspents))

xpub=""
for k,p in zip(range(100),paths("*/0-1")):
	print(p)
	pubkey=btc1.descend(xpub,p).key()
	addr=btc1.pubkeys2address([pubkey])
	print(k,addr)
