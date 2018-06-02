
if __name__=='__main__':
	for p in paths('0h/0h-10h,15/0-*'):
		print(p)

#http://www.ietf.org/rfc/rfc1738.txt
#$-_.+!*'(),
#standard path uri for 
#base58c
#pre='\x22\x56\x53'+64 bits of hash160 which makes (xidXXXXXXX) in base58c (TODO: use () or just raw xid?
#path is (xid) OR rangeset, where rangeset is range(,range)* and range is int(h|'|H)?(-'*' OR int(h|'|H))
#That's the path component.  URI component is
#bip32://[slip44string][:network (main/test.  default main)]/path
#try to get this to be a bip?

#- means range mix inclusive, _means range donotmix
#comma means include1 inclusive, +means seperate exclusive

#bip32://btc:main/m/44h/60h+0h+145h/0h-15h,5h/45-65,100/0-1
#bip32://btc:main/m/44h/60h,0h,145h/0h-15h,5h/45-65,100/0-1
#bip32://btc:main/m/44h/60h,0h,145h/0h-15h,5h/45-65,100/0-1
#bip32://btc:main/m/44h/60h,0h,145h/0h-15h,5h/45-65,100/0-1
#bip32://btc:main/m/44h/60h,0h,145h/0h-15h,5h/45-65,100/0-1
#xpub://btc:main/m/44h/60h
#two subbips.  One for path and one for URI
#path
#there can only be one '*' in the whole URI ??

#	uri='bip32://' authority '/' path
#	authority=chain   #['+' chain]?
#	chain=\a+ [':' \a+]?
#	path:= root [label]? ['/' subpath]*
#	root:='m' | xpubstmt  #| xsi		#xsi (id master seed)
#	xpubstmt:= xpubstr ['!' solidroot ]? 
#	solidroot:=solidval ['.' solidval]*
#	solidval1:= \d+('h'|'H'|'\''|'s'|'S')?
#	solidval1:= \d+('h'|'H'|'\''|'s'|'S')?
#	subpath=subrange [(','|'+') subrange]*
#	subrange=solidval [('-','_') (solidval | '*')]? [label]?
#	label='(' urlencodedstring ')'

#topub(key(m/0'/0'))/0/0 #ALLOWED
#topub(key(m/0'/0'))/0'  #NOT ALLOWED
#P(m/0'/0')/0/0
#K=P(m/44'/24'/6)
#k/b = ckd(k,b)
#key/b'/c' = ckd_hard(ckd_hard(key,b),c) 
#m/419'/575'/11'/99'/*/13
#m/44'/0'/0'/*/0 for i in 0 to infinity
#m/*/0
#m/44'/0'/0'/*/1
#m/0'/0'/0'/*/0
#m/0'/*
#J=P(m/44'/0'/0')
#J/*/0    m/44'/0'/0'/*/0
#J/*
#J,childpathsregex  <-iterate all addresses
#private(J),childpathsregex <-  get all private keys from privJ
#m,44'/0'/0' <--get privJ from seed entropy.
#44'/145'/0'/0/0
#bip32://btc:main/m/44h/60h,0h,145h/0h-15h,5h/45-*,100/0-1
#bip32://btc:main/m/44h/50/23/xpub6BepLctGphRm3trCJcYEx5mWNysBBz8AaTsMbkoyJ6QTUnxcu82bm47gycmjjT3TzYBqkHwfH4JkCXwyKvXTFiStcnUJXmqqnaKEbNzrAr7/45-*,100/0-1
#m/44'/

#44h_60h,0h,145h_0h-15h,5h_45-*,100_0-1

#purpose: communicate 

def parse_xurl_path(x):
	items=filter(None,'/'.split(x))
	items=[parse_b201_subpath(r) for r in items]
	#todo error
	return items

def parse_xurl_root(x):
	if(x.lower() == 'm'):
		return 'm'
	xp=ExtendedKey(x)
	if(xp.is_private()):
		raise Exception("parsed xpub root cannot be private")

def parse_xurl_subrange(x):
	items=filter(None,','.split(x))
	items=[parse_b201_subrange(r) for r in items]
	return items

def parse_xurl_subpath(x):
	items=filter(None,','.split(x))
	root=parse_b201_root(x[0])
	items=[parse_b201_subrange(r) for r in items[:1]]
	return [root]+items

class PathIterator(object):
	def __init__(self,pathstr):
		pass

#hierarchical wallet
#sign
#class Wallet(object):
#	def addresses(): #return a series of address,tickers
#		pass
#	def add(self,keyobject,coin,meta=None): #..must be a (xpub or xpriv) or (priv or pub) OBJECT or string
#		pass
	
