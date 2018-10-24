from coins import fromticker
from binascii import hexlify,unhexlify
from key import Address
from lib.index import IndexBase
from chain import fromchainid
#todo:  Output should be Output. SubmittedOutput should be SubmittedOutput
#	    Transaction should have a subclass SubmittedTransaction that includes the txhash and stuff
#		Only SubmittedTransactions can be referenced
#		Referenceable should be moved to the base.  Or maybe just into lib (because its special for the implementation here)

class TransactionReference(IndexBase):
	def __init__(self,chainid,refid=None):
		if(refid==None and isinstance(chainid,basestring)): 
			chainid,refid=chainid.split(':') 		

		self.chainid=chainid
		self.refid=refid
	
	def _reftuple(self):
		return (self.chainid,self.refid)

	def __repr__(self):
		return str(self)
	def __str__(self):
		return ':'.join((self.chainid,self.refid))

#TODO: this should not have a coin object, it should have an 'offchain source' object only (for multiple coin transactions)
#the output can have a coin, but really it should just have a denomination (for USD?)
#output should have an amount object which has members famount and iamount and overloads number
class Transaction(object):
	def __init__(self,chain,srcs,dsts,meta={},authorizations={}):
		self.chain=chain
		self.srcs=srcs
		self.dsts=dsts
		self.meta=meta
		self.authorizations=authorizations

	@staticmethod
	def from_dict(dct,_force_base=False):
		if('ref' in dct and not _force_base):
			return SubmittedTransaction.from_dict(dct)

		chain=fromchainid(dct['chain'])
		srcs=[Output.from_dict(x) for x in dct['srcs']]
		dsts=[Output.from_dict(x) for x in dct['dsts']]
		meta=dct.get('meta',{})
		authorizations=dct.get('authorizations',{})
		return Transaction(chain,srcs=srcs,dsts=dsts,meta=meta,authorizations=authorizations)

	def to_dict(self):
		dct={'chain':self.chain.chainid,
			'srcs':[x.to_dict() for x in self.srcs],
			'dsts':[x.to_dict() for x in self.dsts],
			'meta':self.meta,
			'authorizations':{str(k):v for k,v in self.authorizations.items()}
		}
		return dct
			

class SubmittedTransaction(Transaction,IndexBase):
	def __init__(self,chain,srcs,dsts,refid,timestamp,confirmations,meta={},authorizations={}):
		super(SubmittedTransaction,self).__init__(chain,srcs,dsts,meta,authorizations)
		self.ref=TransactionReference(chainid=chain.chainid,refid=refid)
		self.timestamp=timestamp
		self.confirmations=confirmations

	def _reftuple(self):
		return self.ref._reftuple()

	@staticmethod
	def from_dict(dct):
		tx=Transaction.from_dict(dct,_force_base=True)
		if('ref' not in dct):
			return tx
		
		txref=TransactionReference(dct['ref'])
		timestamp=None,
		if('timestamp' in dct):
			timestamp=float(dct['timestamp'])
		confirmations=None
		if('confirmations' in dct):
			confirmations=int(dct['confirmations'])
		return SubmittedTransaction(chain=tx.chain,
				srcs=tx.srcs,
				dsts=tx.dsts,
				refid=txref.refid,
				timestamp=timestamp,
				confirmations=confirmations,
				meta=tx.meta,authorizations=tx.authorizations)
	
	def to_dict(self):
		dct=Transaction.to_dict(self)
		dct.update({
			'ref':str(self.ref),
			'timestamp':self.timestamp,
			'confirmations':self.confirmations,
		})
		return dct

class OutputReference(IndexBase):
	def __init__(self,ownertx,index=None):
		if(index==None and isinstance(ownertx,basestring)):	#parse parent as a serialization from a string
			txrefstr,index=ownertx.rsplit(':',1)
			ownertx=TransactionReference(txrefstr)
			
		self.ownertx=ownertx
		self.index=int(index)

	def _reftuple(self):
		return (self.ownertx,self.index)

	def __repr__(self):
		return str(self)

	def __str__(self):
		return str(self.ownertx)+':'+str(self.index)

class Output(object):
	def __init__(self,coin,address,amount,meta={},iamount=None):
		self.coin=coin
		if(not isinstance(address,Address)):
			address=coin.parse_addr(address)
		self.address=address
		if(iamount is not None):
			self.iamount=iamount
		else:
			self.iamount=coin.denomination_float2whole(float(amount))
		self.meta=meta

	@staticmethod
	def from_dict(dct,_force_base=False):
		if('ref' in dct and not _force_base):
			return SubmittedOutput.from_dict(dct)

		coin=fromticker(dct['coin'])
		address=dct.get('address',None)
		if(address is not None):
			address=coin.parse_addr(address)
		iamount=dct.get('iamount',None)
		if(iamount is not None):
			iamount=int(iamount)
		meta=dct.get('meta',{})
		return Output(coin,address,amount=None,meta=meta,iamount=iamount)

	def to_dict(self):
		return {'coin':self.coin.ticker,
				'address':str(self.address),
				'iamount':str(int(self.iamount)),
				'meta':self.meta}
	@property
	def amount(self):
		return self.coin.denomination_whole2float(self.iamount)

	@amount.setter
	def amount(self,v):
		self.iamount=self.coin.denomination_float2whole(float(v))


class SubmittedOutput(Output,IndexBase):
	def __init__(self,coin,address,amount,ownertx,index,spenttx=None,spentindex=None,meta={}):
		self.ref=OutputReference(ownertx,index)

		self.spenttx=spenttx
		self.spentindex=spentindex
		super(SubmittedOutput,self).__init__(coin,address,amount,meta)
	def _reftuple(self):
		return self.ref._reftuple()

	@staticmethod
	def from_dict(dct):
		oo=Output.from_dict(dct,_force_base=True)
		if('ref' not in dct):
			return oo
		ref=OutputReference(dct['ref'])
		spenttx=dct.get('spenttx',None)
		spentindex=dct.get('spentindex',None)
		return SubmittedOutput(coin=oo.coin,address=oo.address,amount=oo.amount,ownertx=ref.ownertx,index=ref.index,spenttx=spenttx,spentindex=spentindex,meta=oo.meta)
		
	def to_dict(self):
		dct=Output.to_dict(self)
		dct.update({'ref':str(self.ref)})
		if(self.spenttx is not None):
			dct['spenttx']=str(self.spenttx)
		if(self.spentindex is not None):
			dct['spentindex']=int(self.spentindex)
		return dct

		

