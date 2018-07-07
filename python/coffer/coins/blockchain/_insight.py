from _interface import *
from binascii import hexlify,unhexlify
from ...transaction import Previous,Transaction

from pprint import pprint

def _mkpid(txid,n):
	return txid+':'+str(n)


def _break_into_stringsize(items,size=1800):
	curstring=[]
	for i in items:
		curstring.append(i)
		slen=sum([len(x)+1 for x in curstring])
		if(slen > size):
			yield curstring
			curstring=[]
		
	if(len(curstring)):
		yield curstring
		

def _jsonunspent2utxo(coin,ju):
	if('satoshis' in ju):
		amount=int(ju['satoshis'])
	address=ju['address']#todo: normalize
	meta={'scriptPubKey':ju['scriptPubKey']}
	if('confirmations' in ju):
		meta['confirmations']=ju['confirmations']
	if('height' in ju):
		meta['height']=int(ju['height'])
	previd=_mkpid(ju['txid'],ju['vout'])
	
	return Previous(coin=coin,previd=previd,address=address,amount=amount,meta=meta,spentpid=None)

def _json2tx(coin,jtx):
	sigs={}
	txid=jtx['txid']
	inputs=[None]*len(jtx['vin'])
	for jsin in jtx['vin']:
		paddr=jsin['addr']
		pamount=jsin.get('valueSat',coin.denomination_float2whole(float(jsin['value'])))
		previd=_mkpid(jsin['txid'],jsin['vout'])
		sig=jsin['scriptSig']['hex']
		sigs[previd]=sig
		pmeta={'scriptSig':sig,'sequence':jsin['sequence']}
		prev=Previous(coin=coin,previd=previd,address=coin.parse_addr(paddr),amount=int(pamount),meta=pmeta)
		inputs[jsin['n']]=prev

	outputs=[None]*len(jtx['vout'])
	for jsout in jtx['vout']:
		#https://bitcoin.stackexchange.com/questions/30442/multiple-addresses-in-one-utxo
		detectaddr=jsout['scriptPubKey']['addresses']
		paddr=detectaddr[0] if len(detectaddr) > 0 else None
		
		pamount=jsout.get('valueSat',coin.denomination_float2whole(float(jsout['value'])))
		previd=_mkpid(txid,jsout['n'])
		pubkey=jsout['scriptPubKey']['hex']
		pmeta={'scriptPubKey':pubkey,
			'spentHeight':jsout.get('spentHeight',None),
            		'spentIndex':jsout.get('spentIndex',None),
			'spentTxId':jsout.get('spentTxId',None),
			'humanAddr':paddr
		}
		if(len(detectaddr) > 1):
			pmeta['legacy_multisig']=True
			logging.warning("Detected a legacy multisig payment!")
		if(len(detectaddr) < 1):
			pmeta['no_addr']=True
			logging.warning("Could not detect an address for a tx")
			
		pspent=None
		if(pmeta['spentTxId']):
			pspent=_mkpid(pmeta['spentTxId'],pmeta['spentIndex'])
		
		prev=Previous(coin=coin,previd=previd,address=coin.parse_addr(paddr),amount=int(pamount),meta=pmeta,spentpid=pspent)
		outputs[jsout['n']]=prev

	tmeta={k:jtx[k] for k in ['blockhash','blockheight','confirmations','locktime','time','version']}


	tx=Transaction(coin,inputs,outputs,tmeta,txid=txid)
	tx.signatures=sigs
		
	return tx
	
default_gap=20
class InsightBlockchainInterface(HttpBlockchainInterface):
	def __init__(self,coin,endpoints):
		super(InsightBlockchainInterface,self).__init__(coin)
		self.endpoints=endpoints

	def get_endpoint(self):
		return random.choice(self.endpoints)
		
	
	
	@retryable
	def _transactions_block(self,addressblock):
		addressblock=[self.coin.format(a) for a in addressblock]
		txlists=[]
		txpaginate=100

		for addrs in _break_into_stringsize(addressblock,1800):
			addrstr=','.join(addrs)
			txoffset=0
			txMax=None
			txlocallists=[]
			while(txMax==None or len(txlocallists) < txMax):
				data=None

				txresult=self.make_json_request('GET','/addrs/%s/txs?from=%d&to=%d' % (addrstr,txoffset,txoffset+txpaginate),data)
				
				txMax=txresult.get('totalItems',len(txlocallists))
				txlocallists+=txresult['items']
				txoffset+=txpaginate
			txlists+=txlocallists

		return txlists

	def transactions(self,addresses,gap=default_gap):
		txs={}
		for addrblock in break_into_blocks(addresses,gap):
			done=True
			
			kkk=self._transactions_block(addrblock)
			
			for sp in kkk:
				#logging.warning(kkk)
				done=False
				txo=_json2tx(self.coin,sp)
				print(txo)
				txs[txo.id()]=txo

			if(done):
				break
		#pprint(txs)
		return txs		
	

	def pushtx_bytes(self,txbytes):
		#TODO: error handling
		data={"rawtx":hexlify(txbytes)}
		return self.make_json_request('POST','/tx/send',data)


"""
if __name__=="__main__":
	t=InsightBlockchainInterface('btc','https://insight.bitpay.com/api')
	tcash=InsightBlockchainInterface('bch','https://bch-insight.bitpay.com/api')

	utxo=t.unspent(['12P7svS6CR3CapfRrY5KKFB3EqHbtw7g6G','157915jXeR1YAMFKiaEyUTExbQgsLxQLwY'])
	utxo_bch=tcash.unspent(['qru3f24ugu9mptz8ghppr6tgp2y73weznswfcvhn7d'])
	print(list(utxo_bch))

"""
