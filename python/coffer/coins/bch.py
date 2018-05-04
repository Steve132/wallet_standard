from ..wallet import *
from _coin import *
from _satoshicoin import *
from .. import _base

class CashAddrChecksumError(Exception):
	def __init__(self,msg):
		super(CashAddrChecksumError,self).__init__(msg)

_base32chars="qpzry9x8gf2tvdw0s3jn54khce6mua7l"
class BCH(SatoshiCoin):
	def __init__(self,is_testnet=False,cashaddr=False):
		
		if(not is_testnet):
			bip32_prefix_private=0x0488ADE4
			bip32_prefix_public=0x0488B21E
			pkh_prefix=0x00
			sh_prefix=0x05
			wif_prefix=0x80
		else:
			bip32_prefix_private=0x04358394
			bip32_prefix_public=0x043587CF
			pkh_prefix=0x6F
			sh_prefix=0xC4
			wif_prefix=0xEF

		sig_prefix=b'\x18Bitcoin Signed Message:\n'
		
		super(BCH,self).__init__('BCH',is_testnet=is_testnet,
			bip32_prefix_private=bip32_prefix_private,
			bip32_prefix_public=bip32_prefix_public,
			pkh_prefix=pkh_prefix,
			sh_prefix=sh_prefix,
			wif_prefix=wif_prefix,
			sig_prefix=sig_prefix)

	def cashaddr_checksum(self,prefix,addrstring):
		data=[ord(p) & 0x1F for p in prefix]
		data+=[0]
		data+=[_base32chars.index(a) for a in addrstring[:-8]]
		data+=[0]*8
		c=1
		for d in data:
			c0 = c >> 35
			c = ((c & 0x07ffffffff) << 5) ^ d
			if (c0 & 0x01):
				c ^= 0x98f2bc8e61
			if (c0 & 0x02):
				c ^= 0x79b76d99e2
			if (c0 & 0x04):
				c ^= 0xf33e5fb3c4
			if (c0 & 0x08):
				c ^= 0xae2eabe2a8
			if (c0 & 0x10):
				c ^= 0x1e4f43e470
		return _base.int2bytes(c ^ 1,5)

	
	#https://github.com/bitcoincashorg/spec/blob/master/cashaddr.md
	def parse_cashaddr(self,addrstring):
	
		prefix=None
		if(':' in addrstring):
			prefix,addrstring=addrstring.split(':')
		
		byts=_base.baseX2bytes(addrstring,_base32chars)
		version=ord(byts[0])
		vsize=version & 0x07
		vtype=(version & 0x78) >> 3
		size=20+4*vsize
		addrpayload=byts[1:-5]
		checksum=byts[-5:]

		
		
		possible_prefixes=["bitcoincash","bchtest","bchreg"]
		if(prefix == None):
			prefix="bchtest" if self.is_testnet else "bitcoincash"
			
		if(self.cashaddr_checksum(prefix,addrstring)!=checksum):
			raise CashAddrChecksumError('CashAddr checksum failed for "%s"' % (addrstring))
		
		addrversions=[self.pkh_prefix,self.sh_prefix]
		addrversion=addrversions[vtype]
	
		return bytes(chr(addrversion))+addrpayload
	
	def _write_cashaddr(self,abytes,prefix=None):
		if(prefix==None):
			if(self.is_testnet):
				prefix='bchtest'
			else:
				prefix='bitcoincash'
			
		addrstring=''
		csprefix=prefix if prefix != '' else 'bitcoincash'
		addrpayload=abytes[1:]
		addrversion=abytes[0]
		
		vtype=[self.pkh_prefix,self.sh_prefix].index(ord(addrversion))
		vsize=(len(addrpayload)-20)//4
		version=chr((vtype << 3) | vsize)
		frontstr=b''+version+addrpayload+'\x00'*5
		b32nocs=_base.bytes2baseX(frontstr,_base32chars)
		checksum=self.cashaddr_checksum(csprefix,addrstring)
		frontstr=b''+version+addrpayload+checksum
		return _base.bytes2baseX(frontstr,_base32chars)

	def format_addr(self,addr,cashaddr=False,prefix=None,*args,**kwargs):
		if(cashaddr):
			return self._write_cashaddr(addr.addrdata,prefix)
		else:
			return _base.bytes2base58c(addr.addrdata)

	def parse_addr(self,addrstring):
		if(':' in addrstring):
			return self.parse_cashaddr(addrstring)
		try:
			return self.parse_cashaddr(addrstring)
		except Exception as caerr:
			try:
				return Address(_base.base58c2bytes(addrstring))
			except Exception as err:
				raise Exception("Could not parse BCH address: %r,%r" % (err.msg,caerr.msg))

	
