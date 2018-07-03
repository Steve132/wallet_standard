import coffer.wallet as wallet
import coffer.coins as coins
from coffer.transaction import *
import json
import zipordir
import os,os.path

def to_ticker(coin):
	ctick=coin.ticker
	if(coin.is_testnet):
		ctick+='-test'
	return ctick.lower()


class CliAccount(object):
	@staticmethod
	def from_dict(dic):
		if(dic['type']=='bip32'):
			ctick=dic['chain'].lower()
			coin=coins.fromticker(ctick)
			wa=wallet.Bip32Account(coin,**dic)
			wa.type='bip32'
			return wa

	@staticmethod
	def to_dict(account):
		if(account.type=='bip32'):
			return {'chain':account.coin.ticker,
				'path':account.internal[0].root,
				'authref':account.authref,
				'internal':account.internal[0].path,
				'external':account.external[0].path,
				'xpub':str(account.internal[0].xpub),
				'type':'bip32'}

class CliAccountGroup(wallet.AccountGroup):
	@staticmethod
	def from_dict(da):
		if(isinstance(da,list)):
			return [CliAccount.from_dict(p) for p in da]
		return []

	@staticmethod
	def to_dict(wg):
		if(isinstance(wg,list)):
			return [CliAccount.to_dict(p) for p in wg]
			

class CliWallet(wallet.Wallet):
	def __init__(self):
		super(CliWallet,self).__init__()	
					
	def _add_accountgroup_file(self,fn,fo):
		groupname,ext=os.path.splitext(fn)
		data=json.load(fo)
		self.groups.setdefault(groupname,CliAccountGroup.from_dict(data))

	def _write_accountgroup_arc(self,g,fn,arc):
		data=CliAccountGroup.to_dict(g)
		arc.writestr(fn,json.dumps(data,indent=4,sort_keys=True))
		
	files_exts=['accountgroup','accounttxs','accountmeta']

	@staticmethod
	def from_archive(filename,wallet=None):
		if(wallet is None):
			wallet=CliWallet()

		arc=zipordir.ZipOrDir(filename,'r')
		files=[x for x in arc.namelist() if x[-1] != '/']
		#//add in sorted order, accountgroups first
		
		filesdic={}
		for f in files:
			bn,ext=os.path.splitext(f)
			filesdic.setdefault(ext,[]).append(f)
			
	
		for fn in filesdic['.accountgroup']:					
			wallet._add_accountgroup_file(fn,arc.open(fn))
	
		return wallet

	@staticmethod
	def to_archive(wallet,filename):
		arc=zipordir.ZipOrDir(filename,'w')
		for f,g in wallet.groups.items():
			fn=(f+'.accountgroup')
			wallet._write_accountgroup_arc(g,fn,arc)
		

	#def __repr__(self):
		#return #json.dumps(self.groups,indent=4)

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


				
					
					
			
			
