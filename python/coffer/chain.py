#a chain is a source of a transaction.  Can be a blockchain or even an exchange or lightning network transaction.
from coins import fromticker
from lib.index import IndexBase

class Chain(object):
	@property
	def chainid(self):
		raise NotImplementedError

	def is_src_fully_authorized(self,tx,index):
		raise NotImplementedError

def fromchainid(chainid):
	try:
		return fromticker(chainid)
	except:
		raise Exception("Unrecognized chain %s" % (chainid))

class Denomination(IndexBase):
	@property
	def denomination_scale(self):
		raise NotImplementedError

	def denomination_float2whole(self,x):
		return int(x*self.denomination_scale)
	
	def denomination_whole2float(self,x):
		ipart,fpart=divmod(int(x),int(self.denomination_scale))
		return ipart+float(fpart)/self.denomination_scale;
	
	@property
	def ticker(self):
		raise NotImplementedError
	
	def _reftuple(self):
		return (self.ticker)

	def __repr__(self):
		return self.ticker



