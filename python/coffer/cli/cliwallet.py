import coffer.wallet as wallet
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
			wa=wallet.Bip32Account(coin,**dic)
			wa.type='bip32'
			return wa

	@staticmethod
	def to_dict(account):
		if(account.type=='bip32'):
			return {'chain':account.coin.ticker,
				'root':account.internal[0].root,
				'authref':account.authref,
				'internal_path':account.internal[0].path,
				'external_path':account.external[0].path,
				'xpub':str(account.internal[0].xpub),
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
			return wallet.Bip32SeedAuth(seed=s)
		elif(' ' in s):
			return wallet.Bip32SeedAuth(words=s)
		elif(checkhex(x)):
			return wallet.HexPrivKeyAuth(key=x)
		else:
			return wallet.Bip32Auth() #TODO
		
	@staticmethod
	def from_file(fo):
		ca=CliAuth()		
		for al in fo:
			ca.subauths.append(CliAuth.parse_auth(al))
		return ca


class CliAccountGroup(object):
	@staticmethod
	def from_dict(da):
		if('type' not in da):
			return {k:CliAccount.from_dict(p) for k,p in da.items()}
		return {}

	@staticmethod
	def to_dict(wg):
		if(isinstance(wg,dict)):
			return {k:CliAccount.to_dict(p) for k,p in wg.items()}
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
				if(ak in g):
					am=g[ak].meta.setdefault(ext,{})
					nm=CliAccount.meta_from_dict(ext,accd)
					for k,v in nm.items():
						am[k]=v
		else:
			logging.warning("No account group found with groupname '%s'" % groupname)

	def _write_metadata_arc(self,gn,arc):
		if(gn in self.groups):
			dataout={}
			
			g=self.groups[gn]
			for ak,acc in g.items():
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
	def from_archive(filename,wallet=None):
		if(wallet is None):
			wallet=CliWallet()

		arc=zipordir.ZipOrDir(filename,'r')
		files=[x for x in arc.namelist() if x[-1] != '/']
		#//add in sorted order, accountgroups first
		
		filesdic={}
		for f in files:
			bn,ext=os.path.splitext(f)
			filesdic.setdefault(ext,set()).add(f)
			
	
		for fn in filesdic['.group']:					
			wallet._add_accountgroup_file(fn,arc.open(fn))
	
		for fn in files:
			bn,ext=os.path.splitext(fn)
			ext=ext[1:]
			if(ext != 'group'):
				wallet._add_metadata_file(bn,ext,arc.open(fn))
	
		return wallet

	@staticmethod
	def to_archive(wallet,filename):
		arc=zipordir.ZipOrDir(filename,'w')
		for f,g in wallet.groups.items():
			fn=(f+'.group')
			wallet._write_accountgroup_arc(g,fn,arc)
			wallet._write_metadata_arc(f,arc)
	
	#def __repr__(self):
		#return #json.dumps(self.groups,indent=4)

	def get_filtered_accounts(self,selgroups=[],selchains=[]):
		selgroups=set([x.lower() for x in selgroups])
		selchains=set([x.lower() for x in selchains])
		outgroups={}
		for gname,g in self.groups.items():
			if(len(selgroups)==0 or gname in selgroups):
				outgroup={}
				for a,acc in g.items():
					if(len(selchains)==0 or acc.coin.ticker.lower() in selchains):
						outgroup[a]=acc
				yield gname,outgroup

		


				
					
					
			
			
