class Coin
{
    static get(ticker);//returns an instantiation of a coin from a ticker
    
    constructor(ticker,network='main')
    {
        this.ticker=ticker;
        this.network=network;
    }

    //Part 0:
    //Begin0
    priv2pub(privkey);//converts a private key to a public key.
    pub2addr(pubkey); //optional args here, like cashaddr or not, segwit or not, various p2sh options, LTC etc.

    default_hdtype(); //from bip4...for example, returns 44 for BTC https://github.com/bitcoin/bips/blob/master/bip-0044.mediawiki#registered-coin-types

    seed2xpriv(root_seed); //defined in bip32..options can be required here like return Ltpub/Ltpriv
    
    //xpriv and xpub are "extended public keys and extended private keys and are totally different"
    xpriv2xpub(xpriv);//converts an xpriv to the equivalent xpub
    xpriv2priv(xpriv);//converts an xpriv to the equivalent priv
    xpub2pub(xpub);//converts an xpub to the equivalent pub

    descend(xprivorxpub,path); //path is a string matching a regex, or a single integer, or a list of numbers.  If the number is negative, then it's the 'hardened'.
        //It's important that -0 is accepted and distinguished from 0..can be done with Object.is(x,+0); https://stackoverflow.com/questions/7223359/are-0-and-0-the-same    
    //end0

    
    chain(); //get the blockchain Interface for this coin.

    //Part 1:
    //for all the ones below tx is a javascript object that represents a transaction.
    //for bitcoin it has ins, outs, amount.

    //get the minimum information required to sign the transaction. (usually the hash)
    hashtx(tx);
    
    //actually create the signatures from the minimum info.  privkeys is a list of private keys.
    signtxhash(txhash,privkeys);
    
    //put the signature into the transaction and return it. (add a 'signature' field)
    signtx(tx,signature);

    //verify the signed transaction
    verifytx(tx);

    deserializetx(txs); //read and write to a hex string in the right format.
    serializetx(tx);
    
    //end part 1
};

class AbstractCoinObject
{
    constructor(coin)//coin is the parent'coin' object instance.
    {
        this.coin=coin
    }
};

//abstract blockchain interface
class AbstractBlockchain extends AbstractCoinObject
{
    constructor(coin)
    {
        super(coin)
    }
    pushtx(tx,callback=null); //asynchronously or synchronously push a transaction (if null, sychronous). Returns txid
    
    gettx(txid); //txid is the hash
    
    unspents(account,path=null);//this gets all unspent transactions. account can be an xpub, an address, or a list of addresses or xpubs.  If is not null and 
                                //then when account contains an xpub the path is used by default to recurse (implement this later)
    txs(account,path=null); //gets all transactions...same as 

    //less important
    heights(account,path=null);//gets the detected address chain heights (only valid if there's an xpub. addresses this returns 0)
};

