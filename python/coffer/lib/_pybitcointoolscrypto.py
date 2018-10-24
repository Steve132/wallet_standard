#this crypto implementation is ECDSA from pybitcointools
import re
from binascii import unhexlify,hexlify
import hmac
import hashlib

P = 2**256 - 2**32 - 977
N = 115792089237316195423570985008687907852837564279074904382605163141518161494337
A = 0
B = 7
Gx = 55066263022277343669578718895168534326250603453777594175500187360389116729240
Gy = 32670510020758816978083085130507043184471273380659243275938904335757337482424
G = (Gx, Gy)


def change_curve(p, n, a, b, gx, gy):
	global P, N, A, B, Gx, Gy, G
	P, N, A, B, Gx, Gy = p, n, a, b, gx, gy
	G = (Gx, Gy)


def getG():
	return G

# Extended Euclidean Algorithm


def inv(a, n):
	if a == 0:
		return 0
	lm, hm = 1, 0
	low, high = a % n, n
	while low > 1:
		r = high//low
		nm, new = hm-lm*r, high-low*r
		lm, low, hm, high = nm, new, lm, low
	return lm % n

def isinf(p):
	return p[0] == 0 and p[1] == 0


def to_jacobian(p):
	o = (p[0], p[1], 1)
	return o


def jacobian_double(p):
	if not p[1]:
		return (0, 0, 0)
	ysq = (p[1] ** 2) % P
	S = (4 * p[0] * ysq) % P
	M = (3 * p[0] ** 2 + A * p[2] ** 4) % P
	nx = (M**2 - 2 * S) % P
	ny = (M * (S - nx) - 8 * ysq ** 2) % P
	nz = (2 * p[1] * p[2]) % P
	return (nx, ny, nz)


def jacobian_add(p, q):
	if not p[1]:
		return q
	if not q[1]:
		return p
	U1 = (p[0] * q[2] ** 2) % P
	U2 = (q[0] * p[2] ** 2) % P
	S1 = (p[1] * q[2] ** 3) % P
	S2 = (q[1] * p[2] ** 3) % P
	if U1 == U2:
		if S1 != S2:
			return (0, 0, 1)
		return jacobian_double(p)
	H = U2 - U1
	R = S2 - S1
	H2 = (H * H) % P
	H3 = (H * H2) % P
	U1H2 = (U1 * H2) % P
	nx = (R ** 2 - H3 - 2 * U1H2) % P
	ny = (R * (U1H2 - nx) - S1 * H3) % P
	nz = (H * p[2] * q[2]) % P
	return (nx, ny, nz)


def from_jacobian(p):
	z = inv(p[2], P)
	return ((p[0] * z**2) % P, (p[1] * z**3) % P)


def jacobian_multiply(a, n):
	if a[1] == 0 or n == 0:
		return (0, 0, 1)
	if n == 1:
		return a
	if n < 0 or n >= N:
		return jacobian_multiply(a, n % N)
	if (n % 2) == 0:
		return jacobian_double(jacobian_multiply(a, n//2))
	if (n % 2) == 1:
		return jacobian_add(jacobian_double(jacobian_multiply(a, n//2)), a)


def fast_multiply(a, n):
	return from_jacobian(jacobian_multiply(to_jacobian(a), n))


def fast_add(a, b):
	return from_jacobian(jacobian_add(to_jacobian(a), to_jacobian(b)))

# Functions for handling pubkey and privkey formats

def privkey_to_pubkey(privkey_int):
	privkey = privkey_int
	if privkey >= N:
		raise Exception("Invalid privkey")
	
	pubkey_val=fast_multiply(G, privkey)
	return pubkey_val

def decompress_pub(prefix,x):
		beta = pow(int(x*x*x+A*x+B), int((P+1)//4), int(P))
		y = (P-beta) if ((beta + prefix) % 2) else beta
		return (x, y)

def add_privkeys(p1,p2):
	return (p1+p2) % N

def add_pubkeys(p1,p2):
	return fast_add(p1,p2)

def int2bytes(x,width=None):
	hx="%X" % x	
	if(width != None):
		hx=hx.zfill(width*2)

	if(len(hx) % 2):
		hx='0'+hx
	
	return unhexlify(hx)

def encode_sig(v, r, s):
	vb, rb, sb = bytearray([v & 0xFF]), int2bytes(r), int2bytes(s)
	
	result = base64.b64encode(vb+b'\x00'*(32-len(rb))+rb+b'\x00'*(32-len(sb))+sb)
	return result if is_python2 else str(result, 'utf-8')


def decode_sig(sig):
	bytez = bytearray(base64.b64decode(sig))
	return int(bytez[0]), int(hexlify(bytez[1:33]), 16), int(hexlify(bytez[33:]),16)

# https://tools.ietf.org/html/rfc6979#section-3.2

def deterministic_generate_k(msghash, priv):
	v = b'\x01' * 32
	k = b'\x00' * 32
	if(len(priv) != 32):
		raise Exception("Error, privkey is wrong length")
	priv=bytearray(priv)
	if(len(msghash) != 32):
		raise Exception("Error, msghash must be 32 bytes")
	msghash=bytearray(msghash)
	k = hmac.new(k, v+b'\x00'+priv+msghash, hashlib.sha256).digest()
	v = hmac.new(k, v, hashlib.sha256).digest()
	k = hmac.new(k, v+b'\x01'+priv+msghash, hashlib.sha256).digest()
	v = hmac.new(k, v, hashlib.sha256).digest()
	return int(hmac.new(k, v, hashlib.sha256).hexdigest(),16)


def ecdsa_raw_sign(msghash, priv,compressed=True):
	z = int(hexlify(msghash),16)
	k = deterministic_generate_k(msghash, priv)
	
	r, y = fast_multiply(G, k)
	pint=int(hexlify(priv),16)
	s = inv(k, N) * (z + r*pint) % N

	v, r, s = 27+((y % 2) ^ (0 if s * 2 < N else 1)), r, s if s * 2 < N else N - s
	if compressed:
		v += 4
	return v, r, s


"""def ecdsa_sign(msg, priv):
	v, r, s = ecdsa_raw_sign(electrum_sig_hash(msg), priv)
	sig = encode_sig(v, r, s)
	assert ecdsa_verify(msg, sig, 
		privtopub(priv)), "Bad Sig!\t %s\nv = %d\n,r = %d\ns = %d" % (sig, v, r, s)
	return sig"""
"""
#pub MUST be decoded
def ecdsa_raw_verify(msghash, vrs, decodedpub):
	v, r, s = vrs
	if not (27 <= v <= 34):
		return False

	w = inv(s, N)
	z = hash_to_int(msghash)

	u1, u2 = z*w % N, r*w % N
	x, y = fast_add(fast_multiply(G, u1), fast_multiply(decodedpub, u2))
	return bool(r == x and (r % N) and (s % N))"""

def _toxbyte(k):
	return "%02X" % (k)

def der_encode_sig(v, r, s):
	b1, b2 = hexlify(int2bytes(r)), hexlify(int2bytes(s))
	if len(b1) and b1[0] in '89abcdef':
		b1 = '00' + b1
	if len(b2) and b2[0] in '89abcdef':
		b2 = '00' + b2
	left = '02'+_toxbyte(len(b1)//2)+b1
	right = '02'+_toxbyte(len(b2)//2)+b2
	return '30'+_toxbyte(len(left+right)//2)+left+right

def der_decode_sig(sig):
	leftlen = int(sig[6:8], 16)*2
	left = sig[8:8+leftlen]
	rightlen = int(sig[10+leftlen:12+leftlen], 16)*2
	right = sig[12+leftlen:12+leftlen+rightlen]
	return (None, int(left, 16), int(right, 16))

def is_bip66(sig):
	"""Checks hex DER sig for BIP66 consistency"""
	#https://raw.githubusercontent.com/bitcoin/bips/master/bip-0066.mediawiki
	#0x30  [total-len]  0x02  [R-len]  [R]  0x02  [S-len]  [S]  [sighash]
	sig = bytearray.fromhex(sig) if re.match('^[0-9a-fA-F]*$', sig) else bytearray(sig)
	if (sig[0] == 0x30) and (sig[1] == len(sig)-2):	 # check if sighash is missing
			raise Exception("Sighash byte of signature is missing") 
			#sig.extend(b"\1")						   	# add SIGHASH_ALL for testing
			#(sig[-1] & 124 == 0) and (not not sig[-1]), "Bad SIGHASH value"
	
	if len(sig) < 9 or len(sig) > 73: return False
	if (sig[0] != 0x30): return False
	if (sig[1] != len(sig)-3): return False
	rlen = sig[3]
	if (5+rlen >= len(sig)): return False
	slen = sig[5+rlen]
	if (rlen + slen + 7 != len(sig)): return False
	if (sig[2] != 0x02): return False
	if (rlen == 0): return False
	if (sig[4] & 0x80): return False
	if (rlen > 1 and (sig[4] == 0x00) and not (sig[5] & 0x80)): return False
	if (sig[4+rlen] != 0x02): return False
	if (slen == 0): return False
	if (sig[rlen+6] & 0x80): return False
	if (slen > 1 and (sig[6+rlen] == 0x00) and not (sig[7+rlen] & 0x80)):
		return False
	return True
