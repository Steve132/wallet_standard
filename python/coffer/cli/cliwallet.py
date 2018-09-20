import coffer.wallet as wallet
import coffer.account as account
import coffer.coins as coins
from coffer.transaction import *
import json
import zipordir
import os,os.path
from binascii import hexlify,unhexlify

class CliAccount(object):
	@staticmethod
	def from_dict(dic):
		if(dic['type']=='bip32'):
			ctick=dic['chain'].lower()
			coin=coins.fromticker(ctick)
			wa=account.Bip32Account(coin,**dic)
			wa.type='bip32'
			return wa

	@staticmethod
	def to_dict(acc):
		if(acc.type=='bip32'):
			return {'chain':acc.coin.ticker,
				'root':acc.internal[0].root,
				'authref':acc.authref,
				'internal_path':acc.internal[0].path,
				'external_path':acc.external[0].path,
				'xpub':str(acc.internal[0].xpub),
				'type':'bip32'}

	@staticmethod
	def meta_from_dict(ext,mdict):
		if(ext=="txs"):
			return {k:Transaction.from_dict(v) for k,v in mdict.items()}
		return mdict

	@staticmethod
	def meta_to_dict(ext,meta):
		if(ext=="txs"):
			return {k:Transaction.to_dict(v) for k,v in meta.items()}
		return meta

class CliAuth(object):
	def __init__(self):
		self.subauths=[]
	
	@staticmethod
	def from_file(fo):
		ca=[]		
		for al in fo:
			ca.append(CliAuth.parse_auth(al))
		return ca


class CliAccountGroup(object):
	@staticmethod
	def from_dict(da):
		if('type' not in da):
			return wallet.AccountGroup({k:CliAccount.from_dict(p) for k,p in da.items()})
		return {}

	@staticmethod
	def to_dict(ag):
		if(isinstance(ag,wallet.AccountGroup)):
			return {k:CliAccount.to_dict(p) for k,p in ag.accounts.items()}
		return {}


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

	def _add_metadata_file(self,gn,ext,fo):
		data=json.load(fo)
		if(gn in self.groups):
			g=self.groups[gn]
			for ak,accd in data.items():
				if(ak in g.accounts):
					am=g.accounts[ak].meta.setdefault(ext,{})
					nm=CliAccount.meta_from_dict(ext,accd)
					for k,v in nm.items():
						am[k]=v
		else:
			logging.warning("No account group found with groupname '%s'" % groupname)

	def _write_metadata_arc(self,gn,arc):
		if(gn in self.groups):
			dataout={}
			
			g=self.groups[gn]
			for ak,acc in g.accounts.items():
				for ext,edata in acc.meta.items():
					ga=dataout.setdefault(ext,{})
					ga[ak]=CliAccount.meta_to_dict(ext,edata)
			for ext,data in dataout.items():
				if(len(data) > 0):
					fn=gn+'.'+ext
					arc.writestr(fn,json.dumps(data,indent=4,sort_keys=True))
		else:
			logging.warning("No account group found with groupname '%s'" % (groupname))
		
	
	@staticmethod
	def from_archive(filename,wal=None):
		if(wal is None):
			wal=CliWallet()

		arc=zipordir.ZipOrDir(filename,'r')
		files=[x for x in arc.namelist() if x[-1] != '/']
		#//add in sorted order, accountgroups first
		
		filesdic={}
		for f in files:
			bn,ext=os.path.splitext(f)
			filesdic.setdefault(ext,set()).add(f)
			
	
		for fn in filesdic.get('.group',[]):					
			wal._add_accountgroup_file(fn,arc.open(fn))
	
		for fn in files:
			bn,ext=os.path.splitext(fn)
			ext=ext[1:]
			if(ext != 'group'):
				wal._add_metadata_file(bn,ext,arc.open(fn))
	
		return wal

	@staticmethod
	def to_archive(wal,filename):
		arc=zipordir.ZipOrDir(filename,'w')
		for f,g in wal.groups.items():
			fn=(f+'.group')
			wal._write_accountgroup_arc(g,fn,arc)
			wal._write_metadata_arc(f,arc)

	@staticmethod
	def parse_auth(s):
		def checkhex(x):
			try:
				a=int(x,16)
				return True
			except ValueError:
				return False

		s.strip()
		if(s[:6]=='bip32:'):
			s=s.split().join().split(':')[-1]
			s=unhexlify(s)
			return auth.Bip32SeedAuth(seed=s)
		elif(' ' in s):
			return auth.Bip32SeedAuth(words=s)
		elif(checkhex(x)):
			return auth.HexPrivKeyAuth(key=x)
		else:
			return auth.Bip32Auth() #TODO
	
	#def __repr__(self):
		#return #json.dumps(self.groups,indent=4)




	
		


				
					
					
			
			
