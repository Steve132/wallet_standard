import sys

class InvalidAddress(Exception):
    pass

CHARSET = 'qpzry9x8gf2tvdw0s3jn54khce6mua7l'
PAYLOAD_LENGTHS=[((vsize+5-(vsize & 4))*(4 + (vsize & 4))) for vsize in range(8)]

def polymod(values):
    chk = 1
    generator = [
        (0x01, 0x98f2bc8e61),
        (0x02, 0x79b76d99e2),
        (0x04, 0xf33e5fb3c4),
        (0x08, 0xae2eabe2a8),
        (0x10, 0x1e4f43e470)]
    for value in values:
        top = chk >> 35
        chk = ((chk & 0x07ffffffff) << 5) ^ value
        for i in generator:
            if top & i[0] != 0:
                chk ^= i[1]
    return chk ^ 1


def prefix_expand(prefix):
    return [ord(x) & 0x1f for x in prefix] + [0]


def calculate_checksum(prefix, payload):
    poly = polymod(prefix_expand(prefix) + payload + [0, 0, 0, 0, 0, 0, 0, 0])
    out = list()
    for i in range(8):
        out.append((poly >> 5 * (7 - i)) & 0x1f)
    return out


def verify_checksum(prefix, payload):
    return polymod(prefix_expand(prefix) + payload) == 0


def b32decode(inputs):
    out = list()
    for letter in inputs:
        out.append(CHARSET.find(letter))
    return out


def b32encode(inputs):
    out = ''
    for char_code in inputs:
        out += CHARSET[char_code]
    return out



def convertbits(data, frombits, tobits, pad=True):
    """General power-of-2 base conversion."""
    acc = 0
    bits = 0
    ret = []
    maxv = (1 << tobits) - 1
    max_acc = (1 << (frombits + tobits - 1)) - 1
    for value in data:
        acc = ((acc << frombits) | value ) & max_acc
        bits += frombits
        while bits >= tobits:
            bits -= tobits
            ret.append((acc >> bits) & maxv)

    if pad and bits:
        ret.append((acc << (tobits - bits)) & maxv)

    return ret


def intlist2bytes(code_list):
    if sys.version_info > (3, 0):
        output = bytes()
        for code in code_list:
            output += bytes([code])
    else:
        output = b''
        for code in code_list:
            output += chr(code)
    return bytes(output)

def bytes2intlist(s):
    output=[]
    if sys.version_info > (3, 0):
        return list(bytes(s))
    else:
        for code in s:
            output += [ord(code)]
    return output
    

def encode(prefix,version_int,payload):
    payload = bytes2intlist(payload)
    try:
        vsize=PAYLOAD_LENGTHS.index(len(payload))
    except IndexError:
        raise InvalidAddress("Payload too long for CashAddr format")

    #print(vsize)
    version_int = (version_int & 0x0F) << 3
    version_int = version_int | vsize

    payload = [version_int] + payload
    payload = convertbits(payload, 8, 5)
    checksum = calculate_checksum(prefix, payload)
    return prefix + ':' + b32encode(payload + checksum)

allprefixes=['bitcoincash','bchtest','bchreg']
def decode(address_string):
    if address_string.upper() != address_string and address_string.lower() != address_string:
        raise InvalidAddress('Cash address contains uppercase and lowercase characters')
    address_string = address_string.lower()

    if ':' not in address_string:
        for tpfx in allprefixes:
            try:
                taddrstr=tpfx+':'+address_string
                return decode(taddrstr)
            except:
                pass
        else:
            raise InvalidAddress('No prefix could validate')

    prefix, base32string = address_string.split(':')
    decoded = b32decode(base32string)
    
    if not verify_checksum(prefix, decoded):
        raise InvalidAddress('Bad cash address checksum')

    converted=convertbits(decoded,5,8,False)
    version=(converted[0] >> 3) & 0xF 
    vsize=(converted[0]) & 0x07
    vsizebytes=PAYLOAD_LENGTHS[vsize]

    payload=converted[1:-5]
    if(len(payload) != (vsizebytes)):
        raise InvalidAddress('Size bits in CashAddr do not match length')

    return prefix,version,intlist2bytes(payload)



alltests="""
|20|0|bitcoincash:qr6m7j9njldwwzlg9v7v53unlr4jkmx6eylep8ekg2|F5BF48B397DAE70BE82B3CCA4793F8EB2B6CDAC9|
|20|1|bchtest:pr6m7j9njldwwzlg9v7v53unlr4jkmx6eyvwc0uz5t|F5BF48B397DAE70BE82B3CCA4793F8EB2B6CDAC9|
|20|1|pref:pr6m7j9njldwwzlg9v7v53unlr4jkmx6ey65nvtks5|F5BF48B397DAE70BE82B3CCA4793F8EB2B6CDAC9|
|20|15|prefix:0r6m7j9njldwwzlg9v7v53unlr4jkmx6ey3qnjwsrf|F5BF48B397DAE70BE82B3CCA4793F8EB2B6CDAC9|
|24|0|bitcoincash:q9adhakpwzztepkpwp5z0dq62m6u5v5xtyj7j3h2ws4mr9g0|7ADBF6C17084BC86C1706827B41A56F5CA32865925E946EA|
|24|1|bchtest:p9adhakpwzztepkpwp5z0dq62m6u5v5xtyj7j3h2u94tsynr|7ADBF6C17084BC86C1706827B41A56F5CA32865925E946EA|
|24|1|pref:p9adhakpwzztepkpwp5z0dq62m6u5v5xtyj7j3h2khlwwk5v|7ADBF6C17084BC86C1706827B41A56F5CA32865925E946EA|
|24|15|prefix:09adhakpwzztepkpwp5z0dq62m6u5v5xtyj7j3h2p29kc2lp|7ADBF6C17084BC86C1706827B41A56F5CA32865925E946EA|
|28|0|bitcoincash:qgagf7w02x4wnz3mkwnchut2vxphjzccwxgjvvjmlsxqwkcw59jxxuz|3A84F9CF51AAE98A3BB3A78BF16A6183790B18719126325BFC0C075B|
|28|1|bchtest:pgagf7w02x4wnz3mkwnchut2vxphjzccwxgjvvjmlsxqwkcvs7md7wt|3A84F9CF51AAE98A3BB3A78BF16A6183790B18719126325BFC0C075B|
|28|1|pref:pgagf7w02x4wnz3mkwnchut2vxphjzccwxgjvvjmlsxqwkcrsr6gzkn|3A84F9CF51AAE98A3BB3A78BF16A6183790B18719126325BFC0C075B|
|28|15|prefix:0gagf7w02x4wnz3mkwnchut2vxphjzccwxgjvvjmlsxqwkc5djw8s9g|3A84F9CF51AAE98A3BB3A78BF16A6183790B18719126325BFC0C075B|
|32|0|bitcoincash:qvch8mmxy0rtfrlarg7ucrxxfzds5pamg73h7370aa87d80gyhqxq5nlegake|3173EF6623C6B48FFD1A3DCC0CC6489B0A07BB47A37F47CFEF4FE69DE825C060|
|32|1|bchtest:pvch8mmxy0rtfrlarg7ucrxxfzds5pamg73h7370aa87d80gyhqxq7fqng6m6|3173EF6623C6B48FFD1A3DCC0CC6489B0A07BB47A37F47CFEF4FE69DE825C060|
|32|1|pref:pvch8mmxy0rtfrlarg7ucrxxfzds5pamg73h7370aa87d80gyhqxq4k9m7qf9|3173EF6623C6B48FFD1A3DCC0CC6489B0A07BB47A37F47CFEF4FE69DE825C060|
|32|15|prefix:0vch8mmxy0rtfrlarg7ucrxxfzds5pamg73h7370aa87d80gyhqxqsh6jgp6w|3173EF6623C6B48FFD1A3DCC0CC6489B0A07BB47A37F47CFEF4FE69DE825C060|
|40|0|bitcoincash:qnq8zwpj8cq05n7pytfmskuk9r4gzzel8qtsvwz79zdskftrzxtar994cgutavfklv39gr3uvz|C07138323E00FA4FC122D3B85B9628EA810B3F381706385E289B0B25631197D194B5C238BEB136FB|
|40|1|bchtest:pnq8zwpj8cq05n7pytfmskuk9r4gzzel8qtsvwz79zdskftrzxtar994cgutavfklvmgm6ynej|C07138323E00FA4FC122D3B85B9628EA810B3F381706385E289B0B25631197D194B5C238BEB136FB|
|40|1|pref:pnq8zwpj8cq05n7pytfmskuk9r4gzzel8qtsvwz79zdskftrzxtar994cgutavfklv0vx5z0w3|C07138323E00FA4FC122D3B85B9628EA810B3F381706385E289B0B25631197D194B5C238BEB136FB|
|40|15|prefix:0nq8zwpj8cq05n7pytfmskuk9r4gzzel8qtsvwz79zdskftrzxtar994cgutavfklvwsvctzqy|C07138323E00FA4FC122D3B85B9628EA810B3F381706385E289B0B25631197D194B5C238BEB136FB|
|48|0|bitcoincash:qh3krj5607v3qlqh5c3wq3lrw3wnuxw0sp8dv0zugrrt5a3kj6ucysfz8kxwv2k53krr7n933jfsunqex2w82sl|E361CA9A7F99107C17A622E047E3745D3E19CF804ED63C5C40C6BA763696B98241223D8CE62AD48D863F4CB18C930E4C|
|48|1|bchtest:ph3krj5607v3qlqh5c3wq3lrw3wnuxw0sp8dv0zugrrt5a3kj6ucysfz8kxwv2k53krr7n933jfsunqnzf7mt6x|E361CA9A7F99107C17A622E047E3745D3E19CF804ED63C5C40C6BA763696B98241223D8CE62AD48D863F4CB18C930E4C|
|48|1|pref:ph3krj5607v3qlqh5c3wq3lrw3wnuxw0sp8dv0zugrrt5a3kj6ucysfz8kxwv2k53krr7n933jfsunqjntdfcwg|E361CA9A7F99107C17A622E047E3745D3E19CF804ED63C5C40C6BA763696B98241223D8CE62AD48D863F4CB18C930E4C|
|48|15|prefix:0h3krj5607v3qlqh5c3wq3lrw3wnuxw0sp8dv0zugrrt5a3kj6ucysfz8kxwv2k53krr7n933jfsunqakcssnmn|E361CA9A7F99107C17A622E047E3745D3E19CF804ED63C5C40C6BA763696B98241223D8CE62AD48D863F4CB18C930E4C|
|56|0|bitcoincash:qmvl5lzvdm6km38lgga64ek5jhdl7e3aqd9895wu04fvhlnare5937w4ywkq57juxsrhvw8ym5d8qx7sz7zz0zvcypqscw8jd03f|D9FA7C4C6EF56DC4FF423BAAE6D495DBFF663D034A72D1DC7D52CBFE7D1E6858F9D523AC0A7A5C34077638E4DD1A701BD017842789982041|
|56|1|bchtest:pmvl5lzvdm6km38lgga64ek5jhdl7e3aqd9895wu04fvhlnare5937w4ywkq57juxsrhvw8ym5d8qx7sz7zz0zvcypqs6kgdsg2g|D9FA7C4C6EF56DC4FF423BAAE6D495DBFF663D034A72D1DC7D52CBFE7D1E6858F9D523AC0A7A5C34077638E4DD1A701BD017842789982041|
|56|1|pref:pmvl5lzvdm6km38lgga64ek5jhdl7e3aqd9895wu04fvhlnare5937w4ywkq57juxsrhvw8ym5d8qx7sz7zz0zvcypqsammyqffl|D9FA7C4C6EF56DC4FF423BAAE6D495DBFF663D034A72D1DC7D52CBFE7D1E6858F9D523AC0A7A5C34077638E4DD1A701BD017842789982041|
|56|15|prefix:0mvl5lzvdm6km38lgga64ek5jhdl7e3aqd9895wu04fvhlnare5937w4ywkq57juxsrhvw8ym5d8qx7sz7zz0zvcypqsgjrqpnw8|D9FA7C4C6EF56DC4FF423BAAE6D495DBFF663D034A72D1DC7D52CBFE7D1E6858F9D523AC0A7A5C34077638E4DD1A701BD017842789982041|
|64|0|bitcoincash:qlg0x333p4238k0qrc5ej7rzfw5g8e4a4r6vvzyrcy8j3s5k0en7calvclhw46hudk5flttj6ydvjc0pv3nchp52amk97tqa5zygg96mtky5sv5w|D0F346310D5513D9E01E299978624BA883E6BDA8F4C60883C10F28C2967E67EC77ECC7EEEAEAFC6DA89FAD72D11AC961E164678B868AEEEC5F2C1DA08884175B|
|64|1|bchtest:plg0x333p4238k0qrc5ej7rzfw5g8e4a4r6vvzyrcy8j3s5k0en7calvclhw46hudk5flttj6ydvjc0pv3nchp52amk97tqa5zygg96mc773cwez|D0F346310D5513D9E01E299978624BA883E6BDA8F4C60883C10F28C2967E67EC77ECC7EEEAEAFC6DA89FAD72D11AC961E164678B868AEEEC5F2C1DA08884175B|
|64|1|pref:plg0x333p4238k0qrc5ej7rzfw5g8e4a4r6vvzyrcy8j3s5k0en7calvclhw46hudk5flttj6ydvjc0pv3nchp52amk97tqa5zygg96mg7pj3lh8|D0F346310D5513D9E01E299978624BA883E6BDA8F4C60883C10F28C2967E67EC77ECC7EEEAEAFC6DA89FAD72D11AC961E164678B868AEEEC5F2C1DA08884175B|
|64|15|prefix:0lg0x333p4238k0qrc5ej7rzfw5g8e4a4r6vvzyrcy8j3s5k0en7calvclhw46hudk5flttj6ydvjc0pv3nchp52amk97tqa5zygg96ms92w6845|D0F346310D5513D9E01E299978624BA883E6BDA8F4C60883C10F28C2967E67EC77ECC7EEEAEAFC6DA89FAD72D11AC961E164678B868AEEEC5F2C1DA08884175B|
"""

from binascii import unhexlify,hexlify
if __name__=="__main__":

	
	for line in alltests.split():
		K=line.split('|')
		length,version,addr,hpayload=(int(K[1]),int(K[2]),K[3],K[4])
		payload=unhexlify(hpayload)
		prefix,dversion,dpayload=decode(addr)
		
		if(payload!=dpayload):
			print("Decoded payload mismatch")
		if(version!=dversion):
			print(K)
			print(dversion)
			print("Decoded version mismatch")
	
		encoded=encode(prefix,version,payload)
		if(encoded!=addr):
			print(K)
			print("Encoded addr mismatch")


	for z in range(16):
		print(z)
		print(encode('bitcoincash',z,'76A9F5BF48B397DAE70BE82B3CCA4793F8EB2B6CDAC988AC'))
"""
    from binascii import unhexlify,hexlify
    from random import getrandbits,choice
    def print_testcase(prefix,typ,hx,printre=True):
	z=encode(prefix,typ,unhexlify(hx))
	f,v,p=decode(z)
	if(printre):
		print("%d|%s|%s" % (len(hx)//2,z,hx))
        if(hexlify(p).lower()!=hx.lower()):
		raise "INVALID conversion found!"

    for pl in PAYLOAD_LENGTHS:
	payload=getrandbits(pl*8)
	plhx = ("%%0%dX" % (pl*2)) % (payload)
        print_testcase('bitcoincash',0,plhx)
        print_testcase('bchtest',1,plhx)
        print_testcase('pref',1,plhx)


    for k in range(1 << 16):
	pl=choice(PAYLOAD_LENGTHS)
	payload=getrandbits(pl*8)
 	plhx = ("%%0%dX" % (pl*2)) % (payload)
        print_testcase('bitcoincash',0,plhx,printre=False)
       
    #print_testcase('bitcoincash',0,'76a04053bda0a88bda5177b86a15c3b29f559873')
    #z=encode('bitcoincash',0,unhexlify('76a04053bda0a88bda5177b86a15c3b29f559873'))
    #print(z)
    #f,v,p=decode(z)
    #print(hexlify(p))"""
