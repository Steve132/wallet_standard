from ..mnemonic import *
import os,os.path

def _build_mnemonic_file():
	import urllib2
	mnemonic_languages=["english","japanese","spanish","french","chinese_simplified","chinese_traditional"]
	wordlists={}
	for la in mnemonic_languages:
		wordlists[la]=urllib2.urlopen("https://raw.githubusercontent.com/bitcoin/bips/master/bip-0039/%s.txt" % (la)).read().split()
	json.dump(wordlists,bz2.BZ2File('wordlists.json.bz2','w'))

def _testvectors():
	import json
	vectorfile=os.path.join(os.path.dirname(os.path.realpath(__file__)), 'vectors.json')
	testvectors=json.load(open(vectorfile,'r'))
	passed=True
	for v in testvectors['english']:
		ebytes=binascii.unhexlify(v[0])
		w=' '.join(entropy_to_words(ebytes))
		passed=words_verify(w)
		seed=mnemonic_to_seed(w,passphrase='TREZOR')
		passed = passed and w==v[1]
		passed = passed and binascii.hexlify(seed)==v[2]
	print("Tests %s." % ("Passed" if passed else "Failed"))
	return passed

ka="near rice perfect battle canyon cattle arctic harbor they receive gloom hope wonder custom century fame image buddy"
ka=ka.split()
print(hexlify(words_to_seed(ka)))
