#!/usr/bin/env python2
import argparse
import coffer.wallet as wallet
import coffer.coins as coins
from pprint import pprint
import json


	
class CliWallet(wallet.Wallet):
	def __init__(self):
		super(CliWallet,self).__init__()
	

	@staticmethod
	def _read_account(daccount):
		if(daccount['type']=='bip32'):
			ctick=daccount['chain'].lower()
			is_testnet=False
			if('-test') in ctick:
				is_testnet=True
				ctick=ctick[:3]
	
			coincls=coins.fromticker(ctick)
			coin=coincls(is_testnet=is_testnet)
			internal=wallet.XPubAddressSet(coin,xpub=daccount['xpub'],path=daccount['internal'],root=daccount['path'])
			external=wallet.XPubAddressSet(coin,xpub=daccount['xpub'],path=daccount['external'],root=daccount['path'])
			wa=wallet.Account(internal=[internal],external=[external],authref=daccount['authref'])
			wa.type='bip32'
			return wa

	@staticmethod
	def _write_account(account):
		if(account.type=='bip32'):
			ctick=account.coin.ticker
			if(account.coin.is_testnet):
				ctick+='-test'
			
			return {'coin':ctick,
				'path':account.internal[0].root,
				'authref':account.authref,
				'internal':account.internal[0].path,
				'external':account.external[0].path,
				'xpub':str(account.internal[0].xpub),
				'type':'bip32'}

	def _add_accounts(self,dic):
		for gname,group in dic.items():
			groupaccounts={}
			for aname,daccount in group.items():
				ga=CliWallet._read_account(daccount)
				if(ga is not None):
					groupaccounts[aname]=ga
			self.groups[gname]=groupaccounts


	def _write_accounts(self):
		groups={}
		for gn,g in self.groups.items():
			groupaccounts={}
			for aname,a in g.items():
				groupaccounts[aname]=CliWallet._write_account(a)
			
			groups[gn]=groupaccounts
		return groups

	def add_dict(self,dic):
		for key,val in dic.items():
			if(key=='accounts'):
				self._add_accounts(val)

	@staticmethod
	def from_dict(wd):
		dw=CliWallet()
		dw.add_dict(wd)
		return dw

	def to_dict(self):
		out={}
		out['accounts']=self._write_accounts()
		return out

	def __repr__(self):
		return json.dumps(self.to_dict(),indent=4)
		
def balance(ticker,xpub,is_testnet=False):
	#wallet.Account
	coincls=coins.fromticker(ticker)
	coin=coincls(is_testnet=is_testnet)
	internal=[wallet.XPubAddressSet(coin,xpub,"1/*")]
	external=[wallet.XPubAddressSet(coin,xpub,"0/*")]

	account=wallet.Account(external=external,internal=internal)
	bci=coin.blockchain()

	internal_unspents=bci.unspents(account.external[0].addresses())
	external_unspents=bci.unspents(account.internal[0].addresses())
	
	amount=sum([p.amount for p in internal_unspents])
	amount+=sum([p.amount for p in external_unspents])
	print(amount)

args=object()

ticker='BTC'
xpub='xpub6BepLctGphRm3trCJcYEx5mWNysBBz8AaTsMbkoyJ6QTUnxcu82bm47gycmjjT3TzYBqkHwfH4JkCXwyKvXTFiStcnUJXmqqnaKEbNzrAr7'
xpub='xpub6BpjvZNyjEDCL4MhqPoEfrVcsfUE71crUj6vzezEFHxXP7eJn1JPMcWngKqHmVMSuBUgog4dNwcnFuVXwRF4ZSbDmuoe3s8itsv4RS56Pvw'
#print(ticker,xpub)
#balance(ticker,xpub)


dw=CliWallet.from_dict(json.load(open('mywallet.json','r')))
print(dw)



	





