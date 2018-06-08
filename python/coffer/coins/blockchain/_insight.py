from _interface import *
from binascii import hexlify,unhexlify
from .._coin import Previous,Transaction

from pprint import pprint


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

def _json2tx(coin,jtx):
	sigs={}
	txid=jtx['txid']
	inputs=[None]*len(jtx['vin'])
	for jsin in jtx['vin']:
		paddr=jsin['addr']
		pamount=jsin.get('valueSat',coin.denomination_float2whole(float(jsin['value'])))
		previd=jsin['txid']+str(jsin['vout'])
		sig=unhexlify(jsin['scriptSig']['hex'])
		sigs[previd]=sig
		pmeta={'scriptSig':sig,'sequence':jsin['sequence']}
		prev=Previous(previd=previd,address=coin.parse_addr(paddr),amount=int(pamount),meta=pmeta)
		inputs[jsin['n']]=prev

	outputs=[None]*len(jtx['vout'])
	for jsout in jtx['vout']:
		#https://bitcoin.stackexchange.com/questions/30442/multiple-addresses-in-one-utxo
		detectaddr=jsout['scriptPubKey']['addresses']
		paddr=detectaddr[0] if len(detectaddr) > 0 else None
		
		pamount=jsout.get('valueSat',coin.denomination_float2whole(float(jsout['value'])))
		previd=txid+str(jsout['n'])
		pubkey=unhexlify(jsout['scriptPubKey']['hex'])
		pmeta={'scriptPubKey':pubkey,
			'spentHeight':jsout.get('spentHeight',None),
            		'spentIndex':jsout.get('spentIndex',None),
			'spentTxId':jsout.get('spentTxId',None)
		}
		if(len(detectaddr) > 1):
			pmeta['legacy_multisig']=True
			logging.warning("Detected a legacy multisig payment!")
		if(len(detectaddr) < 1):
			pmeta['no_addr']=True
			logging.warning("Could not detect an address for a tx")
			
		pspent=None
		if(pmeta['spentTxId']):
			pspent=pmeta['spentTxId']+str(pmeta['spentIndex'])
		
		prev=Previous(previd=previd,address=coin.parse_addr(paddr),amount=int(pamount),meta=pmeta,spentpid=pspent)
		outputs[jsout['n']]=prev

	tmeta={k:jtx[k] for k in ['blockhash','blockheight','confirmations','locktime','time','version']}

	tx=Transaction(inputs,outputs,tmeta,txid=txid)
	tx.signatures=sigs
		
	return tx
	
default_gap=16
class InsightBlockchainInterface(HttpBlockchainInterface):
	def __init__(self,coin,endpoint):
		super(InsightBlockchainInterface,self).__init__(coin,endpoint)

	def _transactions_block(self,addressblock,retry_counter=1):
		addressblock=[self.coin.format(a) for a in addressblock]
		data={'addrs':','.join(addressblock),'noAsm':'1'}
		txresult=self.make_json_request('POST','/addrs/txs',data,retry_counter=retry_counter)
		return txresult['items']
		

	def transactions(self,addresses,gap=default_gap,retry_counter=1):
		txs=[]
		for addrblock in break_into_blocks(addresses,gap):
			done=True
			
			kkk=self._transactions_block(addrblock,retry_counter=retry_counter)
			
			for sp in kkk:
				done=False
				txs.append(_json2tx(self.coin,sp))

			if(done):
				break
		#pprint(txs)
		return txs
				
	
	def unspents(self,addresses,gap=default_gap,retry_counter=1):
		utxos=[]
		txs=self.transactions(addresses,gap,retry_counter)
		for tx in txs:
			for p in tx.dsts:
				if(not p.spentpid):
					utxos.append(p)
		return utxos
		#return [_jsonunspent2utxo(self.coin,r) for r in results]
			
	

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
