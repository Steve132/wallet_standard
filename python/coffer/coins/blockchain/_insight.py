from _interface import *
from binascii import hexlify,unhexlify
from ...transaction import *
from ...key import Address
from coffer.lib.make_request import make_json_request as mjr
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
		
"""
def _jsonunspent2utxo(coin,ju):
	if('satoshis' in ju):
		amount=coin.denomination_whole2float(int(ju['satoshis']))
	address=ju['address']#todo: normalize
	meta={'scriptPubKey':ju['scriptPubKey']}
	if('confirmations' in ju):
		meta['confirmations']=ju['confirmations']
	if('height' in ju):
		meta['height']=int(ju['height'])
	previd=_mkpid(ju['txid'],ju['vout'])
	
	return SubmittedOutput(coin=coin,previd=previd,address=address,amount=amount,meta=meta,spentpid=None)"""


def _lazygetval(coin,vs):
	amountv=vs.get('value',None)
	amountvS=vs.get('valueSat',None)
	if(amountvS is not None):
		return coin.denomination_whole2float(int(amountvS))
	elif(amountv is not None):
		return amountv
	else:
		logging.warning("Detected a transaction input or output without a value!")
		return None

def _json2tx(httpi,coin,jtx):
	sigs={}
	txid=jtx['txid']
	inputs=[None]*len(jtx['vin'])
	for jsin in jtx['vin']:
		spenttx=TransactionReference(coin.ticker,txid)
		
		#TODO: fix implementation of detecting segwit addresses from insight!
		#if addr=None hash the 
		if('addr' not in jsin or jsin['addr'] is None):
			logging.warning("The address is probably a segwit address which insight and coffer cannot handle at the moment.  Trying to get the scriptPubKey")
			newjs=httpi.make_json_request('GET','/tx/%s' % (jsin['txid']))
			oidx=int(jsin['vout'])
			spkh=newjs['vout'][oidx]['scriptPubKey']['hex']
			addr=coin.scriptPubKey2addressess(bytearray()+unhexlify(spkh))
		else:
			addr=coin.parse_addr(jsin['addr'])  #insight doesn't support pure segwit transactions or weird transaction types sometimes the address cannot be parsed from the scriptPubKey..so insight bugs out here.
												#really long term the solution is to rely on electrum servers for this and get rid of insight and parse the address from the raw transactions
		
		amount=_lazygetval(coin,jsin)
		ownerindex=int(jsin['vout'])
		ownertx=TransactionReference(coin.ticker,jsin['txid'])
		
		sig=jsin['scriptSig']['hex']
		pmeta={'scriptSig':sig,'sequence':jsin['sequence'],'doubleSpentTxID':jsin.get('doubleSpentTxID',None)}
		spentindex=int(jsin['n'])
		prev=SubmittedOutput(coin=coin,
			ownertx=ownertx,
			index=ownerindex,
			address=addr,
			amount=amount,
			spenttx=spenttx,
			spentindex=spentindex,
			meta=pmeta)
		sigs[prev.ref]=sig
		inputs[spentindex]=prev

	outputs=[None]*len(jtx['vout'])
	for jsout in jtx['vout']:
		#https://bitcoin.stackexchange.com/questions/30442/multiple-addresses-in-one-utxo
		detectaddr=jsout['scriptPubKey'].get('addresses',[])
		pmeta={}
		pubkey=jsout['scriptPubKey']['hex']
		if(len(detectaddr) > 1):
			pmeta['legacy_multisig']=True
			logging.warning("Detected a legacy multisig payment!")
		if(len(detectaddr) < 1):
			#pmeta['no_addr']=True
			#logging.warning("Could not detect an address for a txout")
			detectaddr=[coin.scriptPubKey2addressess(bytearray()+unhexlify(pubkey))]
		haddr=detectaddr[0]
		addr=None if haddr is None else coin.parse_addr(haddr)
		#pprint(jsout)
		amount=_lazygetval(coin,jsout)
		if(jsout.get('spentTxId',None) is not None):
			spenttx=TransactionReference(coin.ticker,jsout['spentTxId'])
			spentindex=int(jsout['spentIndex'])
		else:
			spenttx,spentindex=None,None

		ownertx=TransactionReference(coin.ticker,txid)
		ownerindex=int(jsout['n'])
		
		pmeta.update({'scriptPubKey':pubkey,
			'spentHeight':jsout.get('spentHeight',None),
			'humanAddr':haddr,
			'legacy_addresses':detectaddr
		})
		
		dst=SubmittedOutput(coin=coin,
			ownertx=ownertx,
			index=ownerindex,
			address=addr,
			amount=amount,
			spenttx=spenttx,
			spentindex=spentindex,
			meta=pmeta)
		outputs[ownerindex]=dst

	tmeta={k:jtx[k] for k in ['blockhash','blockheight','locktime','version'] if k in jtx}

	timestamp=int(jtx['time'])
	confirmations=int(jtx['confirmations'])
	
	tx=SubmittedTransaction(chain=coin,
		srcs=inputs,
		dsts=outputs,
		refid=txid,
		timestamp=timestamp,
		confirmations=confirmations,
		authorizations={}, #signatures=sigs #URGENT TODO: parse previous signatures for verification.		
		meta=tmeta)

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
		txpaginate=40

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
				txo=_json2tx(self,self.coin,sp)
				#print(txo)
				txs[txo.ref]=txo

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
