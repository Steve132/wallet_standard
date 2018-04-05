import hashlib
from binascii import hexlify,unhexlify

#https://github.com/iancoleman/bip39/issues/58#issuecomment-281905574

def dblsha256(byts):
	return hashlib.sha256(hashlib.sha256(byts).digest()).digest()
def hash160(byts):
	rmd=hashlib.new('ripemd160')
	rmd.update(hashlib.sha256(byts).digest())
	return rmd.digest()

def bytes2int(byts):
	return int(hexlify(byts),16)

def int2bytes(bint,mxlen=None):
	print(mxlen)
	fmt=("%%0%dX" % (2*mxlen)) if mxlen else "%X"
	sv=fmt % bint
	sv = '0'+sv if len(sv) & 1 else sv
	return unhexlify(sv)

def bytes2checksum(byts):
	return dblsha256(byts)[:4]

def bytes2baseX(byts,basechars):
	maxint=(1 << (8*len(byts)))-1
	bint=bytes2int(byts)
	base=len(basechars)
	out=[]
	while(maxint):
		cur=bint % base
		bint //=base
		maxint //=base
		out.append(basechars[cur])
	return "".join(out[::-1][1:]) #todo is this correct?

def baseX2bytes(bXstr,basechars):
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
	bsize=len(int2bytes(maxint-1))

	byts=int2bytes(bint,bsize)
	return byts


_b58cs="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
def bytes2base58c(byts):
	csb=bytes2checksum(byts)
	bytscs=byts+csb
	return bytes2baseX(bytscs,_b58cs)

def base58c2bytes(b58str):
	bytscs=baseX2bytes(b58str,_b58cs)
	byts,cs=bytscs[:-4],bytscs[-4:]
	csvalidated=bytes2checksum(byts)
	if(csvalidated!=cs):
		raise Exception("Base58check checksum for %s did not validate" % (b58str))
	return byts
