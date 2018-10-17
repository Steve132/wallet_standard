from collections import namedtuple
from copy import deepcopy


#todo adapt this to correct filtering

BasisEntry=namedtuple('BasisEntry',['timestamp','currency','price','amount','orefs'])

class BasisEntry(object):
	def __init__(self,coin,iamount,timestamp,priceUSD,orefs=[]):
		self.timestamp=timestamp
		self.priceUSD=priceUSD
		self.coin=coin
		self.iamount=iamount
		self.orefs=orefs

	def __repr__(self):
		return str(self.__dict__)

class BasisEstimate(object):	#only over a full wallet.
	def __init__(self,witer,unknown_incoming_callback,algorithm="fifo-order",basis_inits={}):
		self.known_basis={}			#basis_inits is a mapping from oref to a list of known basis entries
		self.unknown_incoming_callback=unknown_incoming_callback
		self.known_basis_tx=set()
		self.algorithm=algorithm

		alltxs={}
		alldsts={}
		unspents={}
		for ak,acc in witer:
			for txr,txo in acc.transactions.items():
				alltxs[txr]=txo
			for dst in acc.intowallet_iter():
				alldsts[dst.ref]=dst
			for dst in acc.unspents_iter():
				unspents[dst.ref]=dst
		
		self.transactions=alltxs
		self.wallet_dsts=alldsts
		self.unspents=unspents

		for u in unspents.values():
			self.get(u.ref)

	#TODO: handle multi currency transactions
	def _partition(self,txo,inputs):
		#assign entries to outputs	
		if(self.algorithm=="star"):#fifo or star.  If star send one entry from each source recursively down.  if fifo-time just aggregate based on time, fifo-order just aggregate based on order.
			pass
		elif(self.algorithm=="fifo-order"):
			outs={}
			#print(inputs)
			inputsleft=sum(inputs,[])
			inputsleft.reverse()

			for d in txo.dsts:
				outlist=[]
				remaining=d.iamount
				while(remaining > 0.0):
					ia=inputsleft[-1].iamount
					if(ia <= remaining):
						remaining-=ia
						outlist.append(inputsleft.pop())
					else:
						a=inputsleft[-1]
						newentry=deepcopy(a)
						newentry.iamount-=remaining
						remaining=0.0
						inputsleft[-1]=newentry
						outlist.append(a)
					
				outs[d.ref]=outlist
			#TODO fee output.
			return outs
		else:
			raise Exception("Unknown partition algorithm '%s' selected!" % (self.algorithm))

	def _compute_tx(self,txref):
		if(txref in self.known_basis_tx):
			return

		if(txref not in self.transactions):
			raise Exception("source referenced transaction which we don't know")
		txo=self.transactions[txref]

		inputs_from_wallet=set()
		inputs_not_from_wallet=set()
		for src in txo.srcs:
			if(src.ref in self.wallet_dsts):
				self.get(src.ref)
				inputs_from_wallet.add(src.ref)
			else:
				inputs_not_from_wallet.add(src.ref)
				
		if(len(inputs_not_from_wallet) > 0):
			for dst in txo.dsts:
				if(dst.ref in self.wallet_dsts):
					self.known_basis[dst.ref]=self.unknown_incoming_callback(dst,txo)
				else:
					self.known_basis[dst.ref]=None #Todo is htis correct?
		else:
			inputs=[self.get(src.ref) for src in txo.srcs if src.ref in inputs_from_wallet]
			partitions=self._partition(txo,inputs)
		
			for oref,obasislist in partitions.items():
				self.known_basis[oref]=obasislist

		self.known_basis_tx.add(txref)

	def get(self,oref):
		if(oref in self.known_basis):
			return self.known_basis[oref]

		if(oref.ownertx in self.transactions):
			self._compute_tx(oref.ownertx)	#this has, as a side effect, sets the child oref basis data.
			out=self.get(oref)
		else:
			out=None

		self.known_basis[oref]=out
		return out
		

		#if(oref not in self.wallet_dsts):
		#	raise Exception("oref was not found in wallet")
		
		
		#short term gets 'spent' first allocating transaction bases



def priceUSD_estimate(dst,txo):
	#there has to be a return value here.
	if(txo==None):
		print("Cannot find transaction with input %s" % (u))

	current_timestamp=txo.timestamp
	finfo=None
	if(isinstance(dst.coin,ForkMixin)):
		finfo=dst.coin.fork_info()
		if(current_timestamp < finfo.timestamp):
			current_timestamp=finfo.timestamp

	try:
		priceUSD=get_price(dst.coin.ticker,'USD',timestamp=current_timestamp)
	except PriceLookupPastError as plpe:
		if(finfo is not None and current_timestamp==finfo.timestamp):
			logging.info("Requested a forked price, using price at fork time")
			
			if(finfo.forkUSD is not None):
				priceUSD=finfo.forkUSD
			else:
				nts,priceUSD=bsearch_to_find_earliest(dst.coin.ticker,bottom=finfo.timestamp+3600*20,top=finfo.timestamp)
		else:
			raise plpe

	return priceUSD
	
def sync_tx(txo):
	if(not hasattr(txo,'timestamp')):
		return
	
	for dst in txo.dsts:
		priceUSD=priceUSD_estimate(dst,txo)
		dst.meta['priceUSD_estimate']=priceUSD
	
def sync(witer,args):
	allaccounts=dict(witer)	
	for ak,acc in allaccounts.items():
		for txr,tx in acc.transactions.items():
			sync_tx(tx)
		
def cmd_taxes(w,args):
	print("TAXES!")

def load_cli_subparsers(extsubparsers,parents_available):
	taxes_parser=extsubparsers.add_parser('taxes',help="Modules and options related to taxes")
	taxes_parser.set_defaults(func_ext=cmd_taxes)
