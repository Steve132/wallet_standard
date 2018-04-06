from ..coins.btc import BTC
from ..coins.blockchain._insight import InsightBlockchainInterface
from pprint import pprint
from ..coins.blockchain.chains import getbci

btc1=BTC()

bc=getbci(btc1)

#for _ in range(10):
#	unspents=bc.unspents(['12P7svS6CR3CapfRrY5KKFB3EqHbtw7g6G'])
#	print(list(unspents))


#bc=InsightBlockchainInterface(btc1,'https://blockexplorer.com/api')
unspents=bc.unspents(['12P7svS6CR3CapfRrY5KKFB3EqHbtw7g6G'])
#print(list(unspents))


pprint(list(unspents))
