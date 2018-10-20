#a chain is a source of a transaction.  Can be a blockchain or even an exchange or lightning network transaction.
from coins import fromticker

class Chain(object):
	@property
	def chainid(self):
		raise NotImplementedError

def fromchainid(chainid):
	try:
		return fromticker(chainid)
	else:
		raise Exception("Unrecognized chain %s" % (chainid))
