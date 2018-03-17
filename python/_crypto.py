#from ecdsa import SigningKey, VerifyingKey, SECP256k1
import _pybitcointoolscrypto
import binascii


def _decode_pub(pub):
	x = int(binascii.hexlify(pub[1:33]),16)
	return decompress_pub(x)

def _encode_pub(pub):
	return bytes(chr(2+(pub[1] % 2))) + binascii.unhexlify("%064X" % (pub[0]))

def _decode_priv(priv):
	return int(binascii.hexlify(priv),16)
def _encode_priv(priv):
	return binascii.unhexlify("%064X" % (priv))

def signdigest(privkey_bytes,digest):
	pass

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

