#from ecdsa import SigningKey, VerifyingKey, SECP256k1
from lib import _pybitcointoolscrypto
import binascii
import _base

def _decode_pub(pub):
	pub=bytearray(pub)
	vbyte=pub[0]
	if(len(pub) > 33):	#TODO: look for version 04 here, version 03 and 02 below,
		if(vbyte != 0x04):
			raise Exception("Version byte %02X incorrect for uncompressed pubkey.  Expected 04" % (vbyte))
 
		x=binascii.hexlify(pub[1:33])
		y=binascii.hexlify(pub[33:])
		return (int(x,16),int(y,16)),False
	else:
		x = int(binascii.hexlify(pub[1:33]),16)
		return _pybitcointoolscrypto.decompress_pub(vbyte,x),True

def _encode_pub(pub,compressed=True):
	if(compressed):
		out=bytearray([(2+(pub[1] % 2))]) + binascii.unhexlify("%064X" % (pub[0]))
	else:
		out=bytearray([4])+binascii.unhexlify("%064X" % (pub[0]))+binascii.unhexlify("%064X" % (pub[1]))
	return out

def _decode_priv(priv):
	return int(binascii.hexlify(priv),16)
def _encode_priv(priv):
	return binascii.unhexlify("%064X" % (priv))

def privkey_verify(privkey_bytes):
	v=_decode_priv(privkey_bytes)
	return v < _pybitcointoolscrypto.N

def privkey_add(privkey_bytes1,privkey_bytes2):
	a=_decode_priv(privkey_bytes1)
	b=_decode_priv(privkey_bytes2)
	c=_pybitcointoolscrypto.add_privkeys(a,b)
	return _encode_priv(c)

def pubkey_add(pubkey_bytes1,pubkey_bytes2,compressed=True):
	a,is_compressed=_decode_pub(pubkey_bytes1)
	b,is_compressed2=_decode_pub(pubkey_bytes2)
	c=_pybitcointoolscrypto.add_pubkeys(a,b)
	return _encode_pub(c,compressed)

def privkey_to_pubkey(privkey_bytes1,compressed=True):
	priv=_decode_priv(privkey_bytes1)
	pub=_pybitcointoolscrypto.privkey_to_pubkey(priv)
	return _encode_pub(pub,compressed)


#todo decode/encode signature
#this should involve der.  However, there's a different encoding for e.g. a signed message
def sign(msghash_bytes,privkey_bytes,compressed=True,use_der=False):
	v,r,s=_pybitcointoolscrypto.ecdsa_raw_sign(msghash_bytes, privkey_bytes,compressed=compressed)
	if(use_der):
		return binascii.unhexlify(_pybitcointoolscrypto.der_encode_sig(v, r, s))
	else:
		return _encode_sig((v,r,s))

def _encode_sig(sig):
	v,r,s=sig
	b=bytearray([v & 0xFF])
	b+=_base.int2bytes(r,32)
	b+=_base.int2bytes(s,32)
	return b

def _decode_sig(byts):
	v=int(byts[1])
	r=_base.bytes2int(byts[1:33])
	s=_base.bytes2int(byts[33:])
	return v,r,s

#TODO: implement verify
#def verify()
#	raise 

