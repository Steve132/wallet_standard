from collections import namedtuple
from copy import deepcopy

BasisEntry=namedtuple('BasisEntry','timestamp','currency','price','amount','orefs')
def BasisEstimate(object):
	def __init__(self,transactions,wallet_dsts,unknown_incoming_callback,algorithm="fifo",basis_inits={}):
		self.known_basis={}			#basis_inits is a mapping from oref to a list of known basis entries

		self.transactions=transactions
		self.unknown_incoming_callback=unknown_incoming_callback
		self.wallet_dsts=wallet_dsts
		self.algorithm=algorithm

	def partition(self,txo,inputs):
		#assign entries to outputs	
		if(self.algorithm=="star"):#fifo or star.  If star send one entry from each source recursively down.  if fifo-time just aggregate based on time, fifo-order just aggregate based on order.
			pass
		if(self.algorithm=="fifo-order"):
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

	def _compute_tx(self,txref):
		#if(txref in self.known_basis_tx):
		#	return self.known_basis_tx[txref]

		if(txref not in self.transactions):
			raise Exception("source referenced transaction which we don't know")
		txo=self.transactions[txref]

		inputs=[self.get(src.ref) for src in txo.srcs]
		
		partitions=self.partition(txo,inputs)
		
		for oref,obasislist in partition.items():
			self.known_basis[oref]=obasislist

	def get(self,oref):
		if(oref in self.known_basis):
			return self.known_basis[oref]

		if(oref in self.wallet_dsts): #then this is a spend from the wallet and the tx src is a spend
			self._compute_tx(oref.ownertx)	#this has, as a side effect, sets the child oref basis data.
		else:
			self.known_basis[oref]=self.unknown_incoming_callback(oref)
		return self.known_basis[oref]

		#if(oref not in self.wallet_dsts):
		#	raise Exception("oref was not found in wallet")
		
		
		#short term gets 'spent' first allocating transaction bases
		
