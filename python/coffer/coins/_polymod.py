import sys

def polymod(values,generator):
    chk = 1
    for value in values:
        top = chk >> 35
        chk = ((chk & 0x07ffffffff) << 5) ^ value
        for i in generator:
            if top & i[0] != 0:
                chk ^= i[1]
    return chk ^ 1

def prefix_expand(prefix):
    return [ord(x) & 0x1f for x in prefix] + [0]

def calculate_checksum(prefix, payload, generator):
    poly = polymod(prefix_expand(prefix) + payload + [0, 0, 0, 0, 0, 0, 0, 0],generator)
    out = list()
    for i in range(8):
        out.append((poly >> 5 * (7 - i)) & 0x1f)
    return out

def verify_checksum(prefix, payload, generator):
    return polymod(prefix_expand(prefix) + payload,) == 0

def b32decode(inputs,charset):
    out = list()
    for letter in inputs:
        out.append(charset.find(letter))
    return out

def b32encode(inputs,charset):
    out = ''
    for char_code in inputs:
        out += charset[char_code]
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
        output = bytearray()
        for code in code_list:
            output += code
    return bytes(output)

def bytes2intlist(s):
    output=[]
    if sys.version_info > (3, 0):
        return list(bytes(s))
    else:
        for code in s:
            output += [ord(code)]
    return output
    

