//Anywhere where the behavior is coin-specific, put it in here.
class BTC extends Coin
{
	constructor(network='main')
	{
		super('BTC',network);
	}
	default_hdtype()
	{
		if(network=='main')
		{
			return -0;
		}
		else
		{
			return -1;
		}		
	}
	//other overloads as necessary...call the base as much as possible
};

class LTC extends Coin
{
constructor(network='main')
	{
		super('BTC',network);
	}
	default_hdtype()
	{
		if(network=='main')
		{
			return -2; //https://github.com/satoshilabs/slips/blob/master/slip-0044.md
		}
		else
		{
			return -1;
		}		
	}
	//other overloads as necessary...call the base as much as possible
};

//https://iancoleman.io/bip39/ use "gift evidence change" to generate these tests.
tests:

seed="897438c2952a883edbee6cdb5ee4421455e812216684a44441d7e404d88c33902315262cfa3309ecffb5885c042ca4620cd48e23971630d99a4f123b4788b9e4"

coin=BTC() //mainnet.
rootxpriv=coin.seed2xpriv(seed); //xprv9s21ZrQH143K4RDZvqR4ZkUYgucJESKobMAXpb7pMkLCza16xrDFx5fUb1vtoc8cWGcHBcLCHZNmDg7XGWzhkhoxJCasuoscvAAAQ4Jrz2u
account0_xpriv=coin.descend(rootxpriv,[-44,coin.default_hdtype(),-0]); //xprv9yJ44LiEGJEU5okR6EGbDiVhcd8TWAebK4HqZVfgktM1ZJUY8hAbzXACru99kEHmHFGywycrvhzRYDLmhfsBxTMGSJC18uNsvVi4M6vUfvF

//get an address by xpriv->descend->xpriv->pub->address
account0_address01_xpriv=coin.descend(account0_xpriv,[0,1]); //xprvA3mazHLHXBhzL5giN2qGtAnS516sL2fMShmrejgagW7uexpL1SJbbettSEuMf3kwyjpc7z9EGsVLNR5Wse2StuNUBrbZAYvXG2aqCxpkuBz
account0_address01_priv=coin.xpriv2priv(account0_address01_xpriv); //Kyg2kB8mCcvna8aqvTdHj7mqQFyH1dt2ETq3aF1QpR7npaDRGJ2q
account0_address01_pub=coin.priv2pub(account0_address01_priv); //02b02d05514c901191902d311937f6b42edd7ecb3cab8a79599f29e3ffc88bb33f
account0_address01=coin.pub2addr(account0_address01_pub); //1Lh64tuHRPVP7Asd2PcApocQ8QQC9qZ5xw

//get an address by xpriv->xpub->descend->xpub->pub->address
account0_xpub=coin.xpriv2xpub(account0_xpriv); //xpub6CHQTrF86fnmJHptCFobarSSAexwudNSgHDSMt5JKDszS6oggEUrYKUgiAcB2e139xgEaD9x72AewKqg52aEKvffGuP1ChWrVbeHYRExBEj
account0_address02_xpub=coin.descend(account0_xpub,"0/2"); //regex usage.  //xpub6GkwPnsBMZGHb7TrbAWPCZ8CAKrVGShZi2TgnTxwcm2i8NmiFLkumnsASBwXbibHcvNaRuyfRua9etfJ3d2U3B8GmD4Hgnu4pu9S3nEtA6r
account0_address02_pub=coin.xpub2pub(account0_address02_xpub); //026a35b421f1b7568702510fbb432ffec591a8e4d145eb1dae3795c4589fb920b0
account0_address02=coin.pub2addr(account0_address02_pub); //1JJg5dv2o3m5R8eMPXnyrt3c9QPBqyiYAu

//SAME TEST, BUT LITECOIN
coin=LTC()
rootxpriv=coin.seed2xpriv(seed); //Ltpv71G8qDifUiNeuPs9NjTgiAhHtB5AKS191LC5n5WFMPvJ1NmyqUypJvN8YnTugKmoRPBZG7yiSe5RDBEbfdygPpBJFmY4DkveiYn4TZ9d49t
account0_xpriv=coin.descend(rootxpriv,[-44,coin.default_hdtype(),-0]); //Ltpv7866g4HGkF2B6dzi2KWJoKwMMsUft89mP9reNezSBx7pUQYwTP8oVCDHBhHSHFcFJocUq67cUrfKaARJGcfoQduEc78RD9kqZpM7xYCp2fM

//get an address by xpriv->descend->xpriv->pub->address
account0_address01_xpriv=coin.descend(account0_xpriv,[0,1]); //Ltpv7C1iFeefzr3LB4LHovsu2b1BGGZjR2LgrgoQcE51g9hzfmbCt559xVbYQ1SNXmQ8trPtCVnkRxBzMvCbGm1RY1jp9RYjUVyZ4RCjGSaKos4
account0_address01_priv=coin.xpriv2priv(account0_address01_xpriv); //T7mpQVE5xh22Wm2LDgxCbym435nMXDxt63MoSD3FyWzZgthvbiTF
account0_address01_pub=coin.priv2pub(account0_address01_priv); //0245d041b77f4e2cbbc356d76f558d98007f8b0fe858df46e4a7e8f5d288729d5a
account0_address01=coin.pub2addr(account0_address01_pub); //LXk5AXyQeDEjc6SJYg25tA7yogu9GPA7Nc

//get an address by xpriv->xpub->descend->xpub->pub->address
account0_xpub=coin.xpriv2xpub(account0_xpriv); //Ltub2ZGSGqhozPZ8iWhYGvzgsumZoSArxNiRTfxg3dkj88uR4mk1nJBEVoKYS5AA3QVmxgPYtDaBnQjwJNEG6MqY5yoSmW4Pud8Us3gZHXQn22h
account0_address02_xpub=coin.descend(account0_xpub,"0/2"); //regex usage.  //Ltub2dC3rS5DEzaHqUjoBeWP4RERF8B42EDhqJffcYi3zFsQrkQWuMFebSMbo4TZG7zYD8nA23NDGwDXkz2QxX7ut6uh4LwkMUf7KPumxJB6ESu
account0_address02_pub=coin.xpub2pub(account0_address02_xpub); //02fa27c9ba7a76bf9fe9c9402ca2c712dfc8a4cc2eab0180d00ba2597f26913b44
account0_address02=coin.pub2addr(account0_address02_pub); //LKSF1rq3ES9qkZurqPbY7RS8eXnANQhonR

//SAME TEST,BITCOIN TESTNET
coin=BTC(network='test') //mainnet.
rootxpriv=coin.seed2xpriv(seed); //tprv8ZgxMBicQKsPfET6bQGZjQ6Y132WTxMovu5eh1YGqipgnAkBxDZ1Tq2vWC6YoyWvsi94BhwxSuxZgXfGPjLeZm5YpqoBaAbfqFuaqo58sVR
account0_xpriv=coin.descend(rootxpriv,[-44,coin.default_hdtype(),-0]); //tprv8fzeLdjC8uTjucgmVci4EBrAszyydMPSjbfbRvTv9StyQTsfdXtryavwkM8PCddFGsA46hjX3TZMYrgqgfDryFVYkJtukwWTp9LoA58JhGc

//get an address by xpriv->descend->xpriv->pub->address
account0_address01_xpriv=coin.descend(account0_xpriv,[0,1]); //tprv8kSXmcecvTY4vtvF2bgn3pQRP8X5ZYhMnFgyXA73AUcPSZZQzoeM7QGLMR51fR9GMBMP85kzSE58qGdFzrNPhxe4iVorpueaB8LFedh5dfW
account0_address01_priv=coin.xpriv2priv(account0_address01_xpriv); //cQ6oqKbB1zc3Ev9FQgi3Kw8cPqmf7HBH1aXsEkhvLpeAUuB69qV5
account0_address01_pub=coin.priv2pub(account0_address01_priv); //039f79c1a37b7c40980e65656cffb0c5903bf014139e197a6ee2d7e05e2878058d
account0_address01=coin.pub2addr(account0_address01_pub); //mxdZoaGVtonrvhSajrZrK61t9nkAFvYXox

//get an address by xpriv->xpub->descend->xpub->pub->address
account0_xpub=coin.xpriv2xpub(account0_xpriv); //tpubDCggV3mSHH9Qo5iZPGNedbWHT2VungaMJuGNiSWDZihNEx8SFviTA5YovWc8xdw8cXxG6dF9YHNgjkzCXiSXArY54mWvvqUAN6E35p6aNzE
account0_address02_xpub=coin.descend(account0_xpub,"0/2"); //regex usage.  //tpubDH8Zv2gs4qDjruei3MVUQUTZVSx9FqCdFf3z9225xfnbsfSRKZbzvEXzgE2K8DYXQpuV3VVXy1QCM59uSUshvcaZpoobNKZJQrjqoqaUSx2
account0_address02_pub=coin.xpub2pub(account0_address02_xpub); //02da4aafa2598f7759885d5932791816e4891a76a29b66eacca574ce6ba33aa590
account0_address02=coin.pub2addr(account0_address02_pub); //n1o3hcBFs3iT9seE63YTgm7K2f3xy9gcnB

