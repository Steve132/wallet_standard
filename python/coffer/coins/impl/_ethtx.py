#https://lsongnotes.wordpress.com/2017/12/21/ethereum-transaction-structure/
#https://medium.com/@codetractio/inside-an-ethereum-transaction-fa94ffca912f
#https://ethereum.github.io/yellowpaper/paper.pdf
#https://lsongnotes.wordpress.com/2018/01/14/signing-an-ethereum-transaction-the-hard-way/

https://github.com/ethereum/wiki/wiki/RLP
def rlp_encode(inp):
    if isinstance(inp,str):
        if len(inp) == 1 and ord(inp) < 0x80: return inp
        else: return encode_length(len(inp), 0x80) + inp
    elif isinstance(inp,list):
        output = ''
        for item in inp: output += rlp_encode(item)
        return encode_length(len(output), 0xc0) + output

def encode_length(L,offset):
    if L < 56:
         return chr(L + offset)
    elif L < 256**8:
         BL = to_binary(L)
         return chr(len(BL) + offset + 55) + BL
    else:
         raise Exception("inp too long")

def to_binary(x):
    if x == 0:
        return ''
    else: 
        return to_binary(int(x / 256)) + chr(x % 256)

def rlp_decode(inp):
    if len(inp) == 0:
        return
    output = ''
    (offset, dataLen, type) = decode_length(inp)
    if type is str:
        output = instantiate_str(substr(inp, offset, dataLen))
    elif type is list:
        output = instantiate_list(substr(inp, offset, dataLen))
    output + rlp_decode(substr(inp, offset + dataLen))
    return output

def decode_length(inp):
    length = len(inp)
    if length == 0:
        raise Exception("inp is null")
    prefix = ord(inp[0])
    if prefix <= 0x7f:
        return (0, 1, str)
    elif prefix <= 0xb7 and length > prefix - 0x80:
        strLen = prefix - 0x80
        return (1, strLen, str)
    elif prefix <= 0xbf and length > prefix - 0xb7 and length > prefix - 0xb7 + to_integer(substr(inp, 1, prefix - 0xb7)):
        lenOfStrLen = prefix - 0xb7
        strLen = to_integer(substr(inp, 1, lenOfStrLen))
        return (1 + lenOfStrLen, strLen, str)
    elif prefix <= 0xf7 and length > prefix - 0xc0:
        listLen = prefix - 0xc0;
        return (1, listLen, list)
    elif prefix <= 0xff and length > prefix - 0xf7 and length > prefix - 0xf7 + to_integer(substr(inp, 1, prefix - 0xf7)):
        lenOfListLen = prefix - 0xf7
        listLen = to_integer(substr(inp, 1, lenOfListLen))
        return (1 + lenOfListLen, listLen, list)
    else:
        raise Exception("inp don't conform RLP encoding form")

def to_integer(b):
    length = len(b)
    if length == 0:
        raise Exception("inp is null")
    elif length == 1:
        return ord(b[0])
    else:
        return ord(substr(b, -1)) + to_integer(substr(b, 0, -1)) * 256
