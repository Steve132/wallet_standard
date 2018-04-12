from _interface import *
from binascii import hexlify,unhexlify
from .._coin import Previous


def _jsonunspent2utxo(coin,ju):
	amount=coin.denomination_float2whole(float(ju['amount']))
	if('satoshis' in ju):
		amount=int(ju['satoshis'])
	address=ju['address']#todo: normalize
	meta={'scriptPubKey':unhexlify(ju['scriptPubKey'])}
	if('confirmations' in ju):
		meta['confirmations']=ju['confirmations']
	if('height' in ju):
		meta['height']=int(ju['height'])
	previd=ju['txid']+':'+str(ju['vout'])
	
	return Previous(previd=previd,address=address,amount=amount,meta=meta)
	
class InsightBlockchainInterface(HttpBlockchainInterface):
	def __init__(self,coin,endpoint):
		super(InsightBlockchainInterface,self).__init__(coin,endpoint)

	
	
	def unspents_block(self,addressblock,retry_counter=1):
		data={'addrs':','.join(addressblock)}
		results=self.make_json_request('POST','/addrs/utxo',data,retry_counter=retry_counter)
		return [_jsonunspent2utxo(self.coin,r) for r in results]
			
	def transactions_block(self,addressblock,retry_counter=1):
		data={'addrs':','.join(addressblock)}
		return self.make_json_request('POST','/addrs/txs',data,retry_counter=retry_counter)

	def pushtx_bytes(self,txbytes):
		#TODO: error handling
		data={"rawtx":hexlify(txbytes)}
		return self.make_json_request('POST','/tx/send',data,retry_counter=retry_counter)


"""
if __name__=="__main__":
	t=InsightBlockchainInterface('btc','https://insight.bitpay.com/api')
	tcash=InsightBlockchainInterface('bch','https://bch-insight.bitpay.com/api')

	utxo=t.unspent(['12P7svS6CR3CapfRrY5KKFB3EqHbtw7g6G','157915jXeR1YAMFKiaEyUTExbQgsLxQLwY'])
	utxo_bch=tcash.unspent(['qru3f24ugu9mptz8ghppr6tgp2y73weznswfcvhn7d'])
	print(list(utxo_bch))

"""
