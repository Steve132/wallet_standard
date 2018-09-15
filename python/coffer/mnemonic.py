import hashlib,hmac
from binascii import hexlify,unhexlify
import json,codecs,bz2
import os,os.path
import locale
import _base
import unicodedata

###BOTH

class Wordlist(list):
	def __init__(self,*collection,**kwargs):
		list.__init__(self,*collection,**kwargs)
		self.lookup=dict((value,index) for index,value in enumerate(self))
        
	def index(self,x):
		try:
			return self.lookup[x]
		except KeyError as ke:
			raise IndexError("'%s' is not in list" % (ke.args))

	def __contains__(self,x):
		return x in self.lookup

reader = codecs.getreader("utf-8")
_wordlists_path=os.path.join(os.path.dirname(os.path.realpath(__file__)),'lib','wordlists.json.bz2')
wordlists = dict([(k,Wordlist(v)) for k,v in json.load(reader(bz2.BZ2File(_wordlists_path,'r'))).items()])

def _getdefaultname(default='en'):
	mdefaults={'en':'english','ja':'japanese','es':'spanish','fr':'french','zh':"chinese_simplified",'zt':"chinese_traditional"}
	loc=locale.getdefaultlocale()
	mdefaultwl=default
	if(loc):
		lc,cc=loc[0].split('_')
		mdefaultwl=mdefaults.get(lc,default)
		if(lc=='zh'):
			mdefaultwl='zh' if cc in ['HK','SG'] else 'zt'
	return mdefaultwl

default_wordlist=wordlists[_getdefaultname('en')]

def _entropy_cs(entbytes):
	entropy_size = 8 * len(entbytes)
	checksum_size = entropy_size // 32
	hd = hashlib.sha256(entbytes).digest()
	csint = _base.bytes2int(hd) >> (256 - checksum_size)
	return csint, checksum_size


#####Recover

def _pbkdf2_hmac_pure(password,salt,c,digestmod=hashlib.sha256):
	digest_size=digestmod().digest_size
	formatstring="%0"+str(2*digest_size)+"X"
	def prf(pwd,nacl):
		return int(hmac.new(pwd,nacl,digestmod=digestmod).hexdigest(),16)
	U=prf(password,salt+'\x00\x00\x00\x01')
	T=0
	for i in range(c):
		T^=U
		U=prf(password,unhexlify(formatstring % (U)))
	return unhexlify(formatstring % (T))

try:
	from hashlib import pbkdf2_hmac
	def pbkdf2_hmac_sha512(password,salt,iters=2048):
		return pbkdf2_hmac(hash_name='sha512',password=password,salt=salt,iterations=iters)
except ImportError:
	def pbkdf2_hmac_sha512(password,salt,iters=2048):
		return _pbkdf2_hmac_pure(password=password,salt=salt,c=iters,digestmod=hashlib.sha512)


def _nwords(words):
	if(isinstance(words,basestr)):
		words=words.split()
	return [w.strip().lower() for w in words]

#https://github.com/bitcoin/bips/blob/master/bip-0039/bip-0039-wordlists.md#japanese
def words_to_seed(words,passphrase=u''):
	words=_nwords(words)
	np=unicodedata.normalize('NFKD',u' '.join(words))
	ns=unicodedata.normalize('NFKD',u'mnemonic'+passphrase)
	return pbkdf2_hmac_sha512(password=np,salt=ns)

def words_to_mnemonic_int(words, wordlist=default_wordlist):
	words=_nwords(words)
	return sum([wordlist.index(w) << (11 * x) for x, w in enumerate(words[::-1])])

def mnemonic_int_verify(mint, mint_bits):
	cs_bits = mint_bits // 32
	entropy_bits = mint_bits - cs_bits
	eint = mint >> cs_bits
	csint = mint & ((1 << cs_bits) - 1)
	ebytes = _base.int2bytes(eint, entropy_bits//8)
	ecsint, ecsint_size = _entropy_cs(ebytes)
	return csint == ecsint

def words_verify(words,wordlist=default_wordlist):
	words=_nwords(words)
	mint,mintsize=words_to_mnemonic_int(words)
	mint_bits=len(words)*11
	return mnemonic_int_verify(mint,mint_bits)

######Generate

def mnemonic_int_to_words(mint, mint_num_words, wordlist=wordlists["english"]):
    backwords = [wordlist[(mint >> (11 * x)) & 0x7FF].strip() for x in range(mint_num_words)]
    return backwords[::-1]

def entropy_to_words(entbytes, wordlist=wordlists["english"]):
    if(len(entbytes) < 4 or len(entbytes) % 4 != 0):
        raise ValueError("The size of the entropy must be a multiple of 4 bytes (multiple of 32 bits)")
    entropy_size = 8 * len(entbytes)
    csint, checksum_size = entropy_cs(entbytes)
    entint = _base.bytes2int(entbytes)
    mint = (entint << checksum_size) | csint
    mint_num_words = (entropy_size + checksum_size) // 11

    return mnemonic_int_to_words(mint, mint_num_words, wordlist)
