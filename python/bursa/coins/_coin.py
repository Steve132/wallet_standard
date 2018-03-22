from ...wallet import *

def h(k):
	return (abs(k) | (1 << 31)) & (0xFFFFFFFF)

class Coin(object):
	def __init__(self,ticker,is_testnet):
		self.ticker=ticker
		self.is_testnet=is_testnet
		self.childid=_slip44.lookups[self.ticker]
		#https://github.com/satoshilabs/slips/blob/master/slip-0044.md
	
	def seed2master(self,seed,version=None):
		if(not version):
			version=self.bip32_default_prefix_private if private else self.bip32_default_prefix_public

		seed=_hparse(seed)
		digest=hmac.new(b"Bitcoin seed",seed,hashlib.sha512).digest()
		I_left,I_right=digest[:32],digest[32:]
		Ilp=_parse256(I_left) #errror check
		return ExtendedKey(version,0,0,0,I_right,b'\x00'+I_left)

	def descend(self,xkey,child,ignore_tag=False):
		def _descend_extend(xkeyparent,isprivate,data,childindex):
			data+=unhexlify("%08X" % (childindex))
			digest=hmac.new(xkey.chaincode,data,hashlib.sha512).digest()
			I_left,I_right=digest[:32],digest[32:]
			Ilp=PrivateKey(I_left,is_compressed=True) #errror check
			if(isprivate):
				child_key=b'\x00'+_crypto.privkey_add(I_left,xkey.keydata[1:])
				parent_pubkey=PrivateKey(xkey.keydata[1:],is_compressed=True).pub().pubkeydata
			else:
				pk=Ilp.pub().pubkeydata
				child_key=_crypto.pubkey_add(pk,xkey.keydata)
				parent_pubkey=xkey.keydata
				
			child_chain=I_right
			fg=int(hexlify(_base.hash160(parent_pubkey)[:4]),16)
			return ExtendedKey(xkey.version,xkey.depth+1,fg,childindex,child_chain,child_key)

		if(isinstance(xkey,basestring)):
			xkey=ExtendedKey(xkey)

		if(isinstance(child,basestring)):
			def _checkvoidpath(p):
				return (p=="/" or p=="" or p.lower()=="m")
			
			child=child.strip()
			if(_checkvoidpath(child)):
				return xkey
			components=child.strip().split("/")
			if(_checkvoidpath(components[0])):
				components=components[1:]
			if(components[-1]==''):
				components=components[:-1]
			components=[(h(int(x.strip("'H"))) if ("'" in x or "H" in x) else int(x)) for x in components]
			return reduce(lambda xk,c: self.descend(xk,c),components,xkey)
		try:
			children=list(child)
			return reduce(lambda xk,c: self.descend(xk,c),children,xkey)
		except TypeError:
			pass

		try:
			child=int(child)
		except TypeError:
			raise Exception("Could not descend")

		isHardened=(child >= 0x70000000)
		
		private=(xkey.keydata[0]==b'\x00')
		
		if(private and (ignore_tag or xkey.version==self.bip32_prefix_private)):
			if(isHardened):
				data=xkey.keydata
			else:
				data=_crypto.privkey_to_compressed_pubkey(xkey.keydata)
			return _descend_extend(xkey,True,data,child)
		elif(ignore_tag or xkey.version==self.bip32_prefix_public):
			if(isHardened):
				raise Exception("Cannot find the child of hardened key %s" % (xkey))
			else:
				data=xkey.keydata
				return _descend_extend(xkey,False,data,child)
		else:
			raise Exception("The key type disagrees with the tag type")

	def pubkeys2addr_bytes(self,pubkeys,*args,**kwargs):
		raise NotImplementedError

	def pubkeys2addr(self,pubkeys,*args,**kwargs):
		raise NotImplementedError

	def parse_privkey(self,pkstring):
		raise NotImplementedError

	def parse_pubkey(self,pkstring):
		raise NotImplementedError
	
	#Todo: come up with a coin-agnostic unspent serialize/deserialzie


