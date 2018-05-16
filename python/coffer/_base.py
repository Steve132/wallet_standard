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

def int2bytes(x,width=None):
	hx="%X" % x	
	if(width != None):
		hx=hx.zfill(width*2)

	if(len(hx) % 2):
		hx='0'+hx
	
	return unhexlify(hx)

def bytes2checksum(byts):
	return dblsha256(byts)[:4]

def bytes2int(x):
	return int(hexlify(x),16)

def bytes2baseX(x,chs,extend=False):
	xi=bytes2int(x)
	b=len(chs)
	u=(1 << 8*len(x))-1
	
	outchrs=[]
	l=0
	while(xi):
		sel=xi % b
		xi//=b
		u//=b
		l+=1
		outchrs.append(chs[sel])
		#print(sel,xi,b,outchrs)

	while(u):
		l+=1
		u//=b
	outchrs="".join(reversed(outchrs))
	if(extend):
		outchrs=outchrs.rjust(l,chs[0])

	return outchrs

def baseX2bytes(x,chs):
	xi=0
	b=len(chs)
	u=1
	for c in x:
		sel=chs.index(c)
		xi=xi*b+sel
		u*=b
	
	w=len(int2bytes(u-1))-1
	
	return int2bytes(xi,w)
def _countleading(it,lead):
	cnt=0
	for k in it:
		if(k != lead):
			break
		cnt+=1
	return cnt

#IMPORTANT SPEC STUFF HERE
_b58cs=b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
def bytes2base58c(byts):
	nz=_countleading(byts,b'\x00')
	csb=bytes2checksum(byts)
	bytscs=byts+csb
	
	aa=_b58cs[0]*nz+bytes2baseX(bytscs[nz:],_b58cs)
	return aa

def base58c2bytes(b58str):
	nz=_countleading(b58str,'1')
	bytscs=b'\x00'*nz + baseX2bytes(b58str[nz:],_b58cs)
	byts,cs=bytscs[:-4],bytscs[-4:]
	csvalidated=bytes2checksum(byts)
	#print(hexlify(cs),hexlify(csvalidated),hexlify(byts))
	if(csvalidated!=cs):
		raise Exception("Base58check checksum for %s did not validate" % (b58str))
	return byts
