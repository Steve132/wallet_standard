from coins import fromticker
from binascii import hexlify,unhexlify
from key import Address
from lib.index import IndexBase
#todo:  Output should be Output. SubmittedOutput should be SubmittedOutput
#	    Transaction should have a subclass SubmittedTransaction that includes the txhash and stuff
#		Only SubmittedTransactions can be referenced
#		Referenceable should be moved to the base.  Or maybe just into lib (because its special for the implementation here)



class TransactionReference(IndexBase):
	def __init__(self,ticker,refid=None,offchain_source=None): 												#source=None means the transaction was on chain. 
		if(refid==None and offchain_source==None and isinstance(ticker,basestring)): 
			ticker,offchain_source,refid=ticker.split(':')

		self.ticker=ticker
		self.refid=refid
		self.offchain_source=offchain_source
	
	def _reftuple(self):
		return (self.ticker,self.refid,self.offchain_source)

	def __repr__(self):
		return str(self)
	def __str__(self):
		return ':'.join((self.ticker,self.refid,self.offchain_source))

class Transaction(object):
	def __init__(self,coin,srcs,dsts,meta={},signatures={}):
		self.coin=coin
		self.srcs=srcs
		self.dsts=dsts
		self.meta=meta
		self.signatures=signatures

class SubmittedTransaction(Transaction,IndexBase):
	def __init__(self,coin,srcs,dsts,refid,timestamp,confirmations,offchain_source=None,meta={},signatures={}):
		super(SubmittedTransaction,self).__init__(coin,srcs,dsts,meta,signatures)
		self.ref=TransactionReference(ticker=coin.ticker,refid=refid,offchain_source=offchain_source)
		self.timestamp=timestamp
		self.confirmations=confirmations

	def _reftuple(self):
		return self.ref._reftuple()


class OutputReference(IndexBase):
	def __init__(self,ownertx,index=None):
		if(index==None and isinstance(ownertx,basestring)):	#parse parent as a serialization from a string
			txrefstr,index=ownertx.rsplit(':',1)
			ownertx=TransactionReference(txrefstr)
			
		self.ownertx=ownertx
		self.index=index

	def _reftuple(self):
		return (self.ownertx,self.index)

	def __repr__(self):
		return str(self)

	def __str__(self):
		return str(self.ownertx)+':'+str(self.index)

class Output(object):

	def __init__(self,coin,address,amount,meta={}):
		self.coin=coin
		self.address=address
		self.amount=amount
		self.meta=meta

class SubmittedOutput(Output,IndexBase):
	def __init__(self,coin,address,amount,ownertx,index,spenttx=None,spentindex=None,meta={}):
		self.ref=OutputReference(ownertx,index)

		self.spenttx=spenttx
		self.spentindex=spentindex
		super(SubmittedOutput,self).__init__(coin,address,amount,meta)
	def _reftuple(self):
		return self.ref._reftuple()

		

		

