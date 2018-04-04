from _interface import *
from binascii import hexlify,unhexlify

class InsightBlockchainInterface(HttpBlockchainInterface):
	def __init__(self,coin,endpoint):
		super(InsightBlockchainInterface,self).__init__(coin,endpoint)
	
	def unspent_block(self,addressblock,retry_counter=1):
		data={'addrs':','.join(addressblock)}
		return self.make_json_request('POST','/addrs/utxo',data,retry_counter=retry_counter)

	def pushtx_bytes(self,txbytes):
		#TODO: error handling
		data={"rawtx":hexlify(txbytes)}
		return self.make_json_request('POST','/tx/send',data,retry_counter=retry_counter)


if __name__=="__main__":
	t=InsightBlockchainInterface('btc','https://insight.bitpay.com/api')
	tcash=InsightBlockchainInterface('bch','https://bch-insight.bitpay.com/api')

	utxo=t.unspent(['12P7svS6CR3CapfRrY5KKFB3EqHbtw7g6G','157915jXeR1YAMFKiaEyUTExbQgsLxQLwY'])
	utxo_bch=tcash.unspent(['qru3f24ugu9mptz8ghppr6tgp2y73weznswfcvhn7d'])
	print(list(utxo_bch))
