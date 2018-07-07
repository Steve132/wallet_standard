class Output(object):
	@staticmethod	
	def _amountcheck(x):
		if(not isinstance(x, (int, long))):
			raise Exception("Amount must be an integer not %r" % (type(x)))
		return x

	def __init__(self,coin,address,amount,meta={}):
		self.coin=coin
		self.address=address
		self._amount=Output._amountcheck(amount)
		self.meta=meta

	@property
	def amount(self):
		return self._amount

	@amount.setter
	def amount(self,x):
		self._amount=Output._amountcheck(amount)

	@staticmethod
	def from_dict(dic):
		coin=coins.fromticker(dic['coin'])
		amount=Output._amountcheck(int(dic['amount']))
		address=dic['address']
		meta=dic.get('meta',{})
		return Output(coin,coin.parse_addr(address),amount,meta)

	def to_dict(self):
		dic={	'coin':self.coin.ticker,
			'amount':str(self._amount),
			'address':self.coin.format_addr(self.address),
			'meta':self.meta
		}
		return dic

class Previous(Output):
	def __init__(self,coin,previd,amount,address,meta={},spentpid=None):
		super(Previous,self).__init__(coin,address,amount,meta)
		self.previd=previd
		self.spentpid=spentpid

	def __repr__(self):
		fmt='%s(previd=%s,address=%s,amount=%d,meta=%r,spentpid=%s)'
		tpl=(
			type(self).__name__,
			self.previd,
			self.address,
			self._amount,
			self.meta,
			self.spentpid
			)
		return fmt % tpl

	@staticmethod
	def make_id(ticker,previd):
		return ticker+'::'+previd

	def id(self):
		return Previous.make_id(self.coin.ticker,self.previd)

	@staticmethod
	def from_dict(dic):
		out=Output.from_dict(dic)
		if('previd' not in dic):
			return out
		
		previd=dic['previd']
		spentpid=dic.get('spentpid',None)
		return Previous(out.coin,previd,out.amount,out.address,out.meta,out.spentpid)

	def to_dict(self):
		dic=super(Previous,self).to_dict()
		dic['previd']=self.previd
			
		if(self.spentpid != None):
			dic['spentpid']=self.spentpid
		return dic
		

#class SubmittedPrevious(Previous):
#	def __init__(self,previd,amount,address,height,confirmations=0,meta={}):
#		super(Previous,self).__init__(previd,amount,address,meta)
#		self.height=height
#		self.confirmations=confirmations

class Transaction(object):
	def __init__(self,coin,prevs,dsts,meta={},txid=None):
		self.coin=coin
		self.prevs=prevs
		self.dsts=dsts
		self.meta=meta
		self.signatures=None
		self.txid=txid
		#self.confirmations=confirmations
		#self.time=None

	def __repr__(self):
		fmt='Transaction(coin=%r,txid=%r,prevs=%r,dsts=%r,meta=%r)'
		tpl=(
			self.coin.ticker,
			self.txid,
			self.prevs,
			self.dsts,	
			self.meta
			)
		return fmt % tpl
	
	@staticmethod
	def from_dict(dic):
		coin=coins.fromticker(dic['coin'])
		prevs=[Previous.from_dict(d) for d in dic['prevs']]
		dsts=[Previous.from_dict(d) for d in dic['dsts']]
		meta=dic['meta']
		signatures=dic.get('signatures',None)
		txid=dic.get('txid',None) 
		txo=Transaction(coin,prevs,dsts,meta,txid)
		if(txo.signatures != None):
			txo.signatures=signatures
		return txo

	def to_dict(self):
		dic={
			'coin':self.coin.ticker,
			'prevs':[p.to_dict() for p in self.prevs],
			'dsts':[d.to_dict() for d in self.dsts],
			'meta':self.meta,
		}
		if(self.txid != None):
			dic['txid']=self.txid
		if(self.signatures != None):
			dic['signatures']=self.signatures
		return dic

	@staticmethod
	def make_id(ticker,txid):
		return ticker+'::'+txid

	def id(self):
		return Transaction.make_id(self.coin.ticker,self.txid)


