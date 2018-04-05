from ..coins.btc import BTC
from ..blockchain._insight import InsightBlockchainInterface
btc1=BTC()

bc=btc1.blockchain()

#for _ in range(10):
#	unspents=bc.unspents(['12P7svS6CR3CapfRrY5KKFB3EqHbtw7g6G'])
#	print(list(unspents))


bc=InsightBlockchainInterface(btc1,'https://blockexplorer.com/api')
unspents=bc.unspents(['12P7svS6CR3CapfRrY5KKFB3EqHbtw7g6G'])
print(list(unspents))




