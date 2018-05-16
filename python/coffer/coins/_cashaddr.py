import sys

class InvalidAddress(Exception):
    pass

CHARSET = 'qpzry9x8gf2tvdw0s3jn54khce6mua7l'

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
    acc = 0
    bits = 0
    ret = []
    maxv = (1 << tobits) - 1
    max_acc = (1 << (frombits + tobits - 1)) - 1
    for value in data:
        if value < 0 or (value >> frombits):
            return None
        acc = ((acc << frombits) | value) & max_acc
        bits += frombits
        while bits >= tobits:
            bits -= tobits
            ret.append((acc >> bits) & maxv)
    if pad:
        if bits:
            ret.append((acc << (tobits - bits)) & maxv)
    elif bits >= frombits or ((acc << (tobits - bits)) & maxv):
        return None
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
    return bytearray(output)

def bytes2intlist(s):
    return list(bytearray(s))
    

def encode(prefix,version_int,payload):
    payload = bytes2intlist(payload)
    vsize=(len(payload)-20)//4
    if(vsize > 0x7):
        raise InvalidAddress("Payload too long for CashAddr format")
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

    converted=convertbits(decoded,5,8)
    version=(int(converted[0]) >> 3) & 0xF 
    vsize=(int(converted[0])) & 0x07
    vsizebytes=20+4*vsize

    payload=converted[1:-6]
    if(len(payload) != vsizebytes):
        raise InvalidAddress('Size bits in CashAddr do not match length')

    return prefix,version,intlist2bytes(payload)

if __name__=="__main__":
    from binascii import unhexlify,hexlify
    z=encode('bitcoincash',0,unhexlify('76a04053bda0a88bda5177b86a15c3b29f559873'))
    print(z)
    f,v,p=decode(z)
    print(hexlify(p))
