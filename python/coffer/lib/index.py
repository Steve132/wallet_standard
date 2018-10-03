import hashlib

class IndexBase(object):
	def _reftuple(self):
		raise NotImplementedError

	def __cmp__(self,other):
		return cmp(self._reftuple(),other._reftuple())
		
	def __hash__(self):
		return hash(self._reftuple())

	def __repr__(self):
		return '<'+'|'.join([repr(x) for x in self._reftuple()])+'>'


class UuidBase(IndexBase):
	def id(self):
		idt=self._reftuple()
		return hashlib.sha256(str(idt)).hexdigest()

