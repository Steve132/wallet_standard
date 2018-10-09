from collections import namedtuple
from copy import deepcopy


#todo adapt this to correct filtering

BasisEntry=namedtuple('BasisEntry',['timestamp','currency','price','amount','orefs'])
class BasisEstimate(object):	#only over a full wallet.
	def __init__(self,transactions,wallet_dsts,unknown_incoming_callback,algorithm="fifo-order",basis_inits={}):
		self.known_basis={}			#basis_inits is a mapping from oref to a list of known basis entries

		self.transactions=transactions
		self.unknown_incoming_callback=unknown_incoming_callback
		self.wallet_dsts=wallet_dsts
		self.algorithm=algorithm
		self.known_basis_tx=set()

	#TODO: handle multi currency transactions
	def _partition(self,txo,inputs):
		#assign entries to outputs	
		if(self.algorithm=="star"):#fifo or star.  If star send one entry from each source recursively down.  if fifo-time just aggregate based on time, fifo-order just aggregate based on order.
			pass
		elif(self.algorithm=="fifo-order"):
			outs={}
			inputsleft=sum(inputs)
			inputsleft.reverse()

			for d in txo.dsts:
				outlist=[]
				remaining=d.amount
				while(remaining > 0.0):
					ia=inputs[-1].amount
					if(ia <= remaining):
						remaining-=ia.amount
						outlist.append(inputs.pop())
					else:
						a=inputs[-1]
						newentry=deepcopy(a)
						newentry.amount-=remaining
						remaining=0.0
						inputs[-1]=newentry
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
			inputs=[self.get(src.ref) for src in txo.srcs if src.ref in inputs_from_wallet]
			partitions=self._partition(txo,inputs)
		
			for oref,obasislist in partition.items():
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
		
