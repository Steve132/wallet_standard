#ifndef COIN_HPP
#define COIN_HPP

namespace coin
{

class Coin
{
	static Coin* get(size_t tickerid); //returns null if tickerid does not cointain a coin.
};

class CoinObject
{
public:
	Coin& coin;
	CoinObject(Coin& parent):coin(parent)
	{}
};

class PrivateKey
{
public:
};

class PublicKey
{
}
class Address
{}

class Transaction
{}

template<class CoinType,class SerializableType>
size_t printsize(const SerializableType&);

template<class CoinType,class SerializableType>
size_t print(char*,const SerializableType&,size_t limit=~size_t(0));

template<class CoinType,class SerializableType>
SerializableType deprint(const char*);










}



#endif
