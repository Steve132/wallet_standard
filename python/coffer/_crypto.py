#from ecdsa import SigningKey, VerifyingKey, SECP256k1
from lib import _pybitcointoolscrypto
import binascii

def _decode_pub(pub):
	if(len(pub) > 33):
		x=binascii.hexlify(self.pubkeydata[1:33])
		y=binascii.hexlify(self.pubkeydata[33:])
		return (int(x,16),int(y,16))
	else:
		x = int(binascii.hexlify(pub[1:33]),16)
		p = ord(pub[0])
		return _pybitcointoolscrypto.decompress_pub(p,x)

def _encode_pub(pub):
	return bytes(chr(2+(pub[1] % 2))) + binascii.unhexlify("%064X" % (pub[0]))

def _decode_priv(priv):
	return int(binascii.hexlify(priv),16)
def _encode_priv(priv):
	return binascii.unhexlify("%064X" % (priv))

def signdigest(privkey_bytes,digest):
	pass

def privkey_verify(privkey_bytes):
	v=_decode_priv(privkey_bytes)
	return v < _pybitcointoolscrypto.N

def privkey_add(privkey_bytes1,privkey_bytes2):
	a=_decode_priv(privkey_bytes1)
	b=_decode_priv(privkey_bytes2)
	c=_pybitcointoolscrypto.add_privkeys(a,b)
	return _encode_priv(c)

def pubkey_add(pubkey_bytes1,pubkey_bytes2):
	a=_decode_pub(pubkey_bytes1)
	b=_decode_pub(pubkey_bytes2)
	c=_pybitcointoolscrypto.add_pubkeys(a,b)
	return _encode_pub(c)

def privkey_to_compressed_pubkey(privkey_bytes1):
	priv=_decode_priv(privkey_bytes1)
	pub=_pybitcointoolscrypto.privkey_to_pubkey(priv)
	return _encode_pub(pub)

