import coffer.wallet as wallet
import coffer.coins as coins
import json
import zipordir
import os,os.path




def to_ticker(coin):
	ctick=coin.ticker
	if(coin.is_testnet):
		ctick+='-test'
	return ctick.lower()

class CliWallet(wallet.Wallet):
	def __init__(self):
		super(CliWallet,self).__init__()
		self.groupfilenames={}
	
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
			ctick=to_ticker(account.coin)
			
			return {'chain':ctick,
				'path':account.internal[0].root,
				'authref':account.authref,
				'internal':account.internal[0].path,
				'external':account.external[0].path,
				'xpub':str(account.internal[0].xpub),
				'type':'bip32'}

	def _add_accounts(self,dic):
		for gname,group in dic.items():
			groupaccounts=[]
			for daccount in group:
				ga=CliWallet._read_account(daccount)
				if(ga is not None):
					groupaccounts.append(ga)
			self.groups[gname]=groupaccounts


	def _write_accounts(self):
		groups={}
		for gn,g in self.groups.items():
			groupaccounts=[]
			for a in g:
				groupaccounts.append(CliWallet._write_account(a))
			
			groups[gn]=groupaccounts
		return groups

	def _add_group(self,filename,dic):
		self._add_accounts(dic)
		for k in dic.keys():
			self.groupfilenames[k]=filename

	def to_dict(self):
		return {'files':self.groupfilenames,'accounts':self._write_accounts()}
		
	@staticmethod
	def from_archive(filename,wallet={}):
		wallet=CliWallet()
		arc=zipordir.ZipOrDir(filename,'r')
		files=[x for x in arc.namelist() if x[-1] != '/']
		for fn in files:
			if(fn[-1] != '/'):
				data=json.load(arc.open(fn))
				wallet._add_group(fn,data)
		return wallet

	@staticmethod
	def to_archive(wallet,filename):
		pass
		#arc=zipordir.ZipOrDir(filename,'r')
		#json.dump(self.to_dict(),fo,indent=4)
		    

	def __repr__(self):
		return json.dumps(self.to_dict(),indent=4)

	def get_filtered_accounts(self,selgroups=[],selchains=[]):
		selgroups=set([x.lower() for x in selgroups])
		selchains=set([x.lower() for x in selchains])
		outgroups={}
		for gname,g in self.groups.items():
			if(len(selgroups)==0 or gname in selgroups):
				outgroup=[]
				for a in g:
					if(len(selchains)==0 or a.coin.ticker in selchains):
						outgroup.append(a)
				yield gname,outgroup


				
					
					
			
			
