import hashlib,hmac
from binascii import hexlify,unhexlify
import struct
#https://github.com/iancoleman/bip39/issues/58#issuecomment-281905574
def _hparse(s):
	try:
		a=int(s,16)
		return unhexlify(s)
	except ValueError:
		return s

_xkeydatastruct=struct.Struct("!LBLL32s33s")
def _parse256(I):
	pass #todo: verify if valid key

def _dblsha256(byts):
	return hashlib.sha256(hashlib.sha256(byts).digest()).digest()
def _bytes2int(byts):
	return int(hexlify(byts),16)
def _int2bytes(bint,mxlen=None):
	fmt=("\%0%dX" % mxlen) if mxlen else "%X"
	sv=fmt % bint
	sv = '0'+sv if len(sv) & 1 else sv
	return unhexlify(sv)


def _bytes2checksum(byts):
	return _dblsha256(byts)[:4]

def _bytes2baseX(byts,basechars):
	maxint=(1 << (8*len(byts)))-1
	bint=_bytes2int(byts)
	base=len(basechars)
	out=[]
	while(maxint):
		cur=bint % base
		bint //=base
		maxint //=base
		out.append(basechars[cur])
	return "".join(out[::-1][1:]) #todo is this correct?
def _baseX2bytes(bXstr,basechars):
	base=len(basechars)
	bint=0
	maxint=1
	for c in bXstr:
		try:
			dex=basechars.index(c)
			bint=bint*base+dex
			maxint*=base
		except ValueError:
			raise Exception("Error, cannot convert %s to base %d." % (c,base))
	bsize=len(_int2bytes(maxint-1))
	byts=_int2bytes(bint)
	return byts


_b58cs="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
def _bytes2base58c(byts):
	csb=_bytes2checksum(byts)
	bytscs=byts+csb
	return _bytes2baseX(bytscs,_b58cs)

def _base58c2bytes(b58str):
	bytscs=_baseX2bytes(b58str,_b58cs)
	byts,cs=bytscs[:-4],bytscs[-4:]
	csvalidated=_bytes2checksum(byts)
	if(csvalidated!=cs):
		raise Exception("Base58check checksum for %s did not validate" % (b58str))
	return byts

class _Hardened(object):
	def __init__(self,k):
		self.k=abs(int(k))

def h(k):
	return _Hardened(k)
	
class Coin(object):
	def __init__(self,ticker,network='main'):
		self.ticker=ticker
		self.network=network

	def _serializexkey(self,version,depth,fingerprint,child,chaincode,keydata):
		data=_xkeydatastruct.pack(version,depth,fingerprint,child,chaincode,keydata)
		return _bytes2base58c(data)
	def _deserializexkey(self,b58str):
		data=_base58c2bytes(b58str)
		return _xkeydatastruct.unpack(data)

	def seed2master(self,seed):
		seed=_hparse(seed)
		digest=hmac.new(b"Bitcoin seed",seed,hashlib.sha512).digest()
		I_left,I_right=digest[32:],digest[:32]
		Irp=_parse256(I_right) #errror check
		version=self.masterversion(private=True)
		return self._serializexkey(version,0,0,0,I_left,b'\x00'+I_right)

	def descend(self,xkey,child):
		if(isinstance(child,basestr)):
			pass //do regex split and descend.
		try:
			children=list(child)
			return reduce(lambda xk,c: self.descend(xk,c),children,xk)
		except TypeError:
			pass

		isHardened=False
		if(isinstance(child,_Hardened)):
			isHardened=True
			dex=int(child.k)
		else:	
			dex=int(child)
			if(dex < 0):
				isHardened=True
		version,depth,fingerprint,child,chaincode,keydata=self._deserializexkey(xkey)
		private=(keydata[0]==b'\x00')
		#if(keydata[0]==b'\x00'):
			#if(version==self.masterversion(private=True)): #if it's a private key (can't trust the version info for this really...I mean I guess you could but meh)
			#private=True
		#else:

		if(private):
			
			
		

class BTC(Coin):
	def __init__(self,network='main'):
		super(BTC,self).__init__('BTC',network)
	def masterversion(self,private):
		if(self.network=='main'):
			return 0x0488ADE4 if private else 0x0488B21E
		else:
			return 0x04358394 if private else 0x043587CF
	
		
