import coffer.wallet as wallet
import coffer.account as account
import coffer.coins as coins
import coffer.auth as auth
import coffer.bip32 as bip32

from coffer.transaction import *
import json
import zipordir
import os,os.path
from binascii import hexlify,unhexlify
from pprint import pprint


try:
	from collections.abc import Mapping
except:
	from collections import Mapping

#Really, a wallet is a Mapping of accounts.
#The grouping is entirely artificial and is a function of the CLI wallet features.
class GroupedWallet(Mapping):
	def __init__(self):
		self._accounts={}
		self.account2group={}
		self.group2accounts={}

	def add_account(self,groupname,account):
		aid=account.id()
		if(aid in self.account2group):
			raise Exception("Error, account %r is already in group %s" % (account,self.account2group[aid]))
		if(aid in self._accounts):
			raise Exception("Error, account %r is already in the GroupedWallet" % (account))

		self._accounts[aid]=account
		self.account2group[aid]=groupname
		self.group2accounts.setdefault(groupname,set()).add(aid)

	def __getitem__(self,aid):
		return self._accounts[aid]
	def __iter__(self):
		return iter(self._accounts)
	def __len__(self):
		return len(self._accounts)

class CliAccount(object):
	@staticmethod
	def from_dict(dic):
		if(dic['type']=='bip32'):
			ctick=dic['chain'].lower()
			coin=coins.fromticker(ctick)
			wa=bip32.Bip32Account(coin,
				root=dic['root'],
				authref=dic['authref'],
				internal_path=dic['internal_path'],
				external_path=dic['external_path'],
				xkey=dic['xpub'],
				*dic.get('bip32args',[]),
				**dic.get('bip32kwargs',{})
			)
			wa.type='bip32'
			wa.label=dic.get('label',None)
			return wa

	@staticmethod
	def to_dict(acc):
		if(acc.type=='bip32'):
			return {'chain':acc.coin.chainid,
				'root':acc.internal[0].root,
				'authref':acc.authref,
				'internal_path':acc.internal[0].path,
				'external_path':acc.external[0].path,
				'xpub':str(acc.internal[0].xpub),
				'bip32kwargs':acc.bip32kwargs,
				'bip32args':acc.bip32args,
				'label':acc.label,
				'type':'bip32'}

	@staticmethod
	def meta_from_dict(ext,mdict):
		return mdict

	@staticmethod
	def meta_to_dict(ext,meta):
		return meta

	@staticmethod
	def get_all_meta_as_dict(acc):
		allmeta={}
		allmeta.update(acc.meta)
		txdict={str(k):v.to_dict() for k,v in acc.transactions.items()}
		allmeta['txs']=txdict
		return allmeta

	@staticmethod
	def set_meta_from_dict(acc,tag,val):
		if(tag=='txs'):
			acc.transactions.update({TransactionReference(k):Transaction.from_dict(v) for k,v in val.items()})
		else:
			acc.meta[tag]=val

class CliAuth(object):
	def __init__(self):
		self.subauths=[]

	@staticmethod
	def parse_auth(s,passphrase=''):
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
			return bip32.Bip32SeedAuth(seed=s)
		elif(' ' in s):
			return bip32.Bip32SeedAuth.from_mnemonic(words=s,passphrase=passphrase)
		elif(checkhex(''.join(x.split()))):
			return auth.PrivKeysAuth(keys=[unhexlify(k) for k in x.split()])
		else:
			raise NotImplementedError
			return bip32.Bip32Auth()
	
	@staticmethod
	def from_file(fo,passphrase=''):
		ca=[]		
		for al in fo:
			ca.append(CliAuth.parse_auth(al,passphrase=passphrase))
		return ca


class CliAccountGroup(object):
	@staticmethod
	def from_dict(da):
		return set([CliAccount.from_dict(p) for p in da])
		
	@staticmethod
	def to_dict(accountset):
		return [CliAccount.to_dict(acc) for acc in accountset]
		

class CliWallet(GroupedWallet):
	def __init__(self):
		super(CliWallet,self).__init__()	
					
	def _add_accountgroup_file(self,fn,fo):
		groupname,ext=os.path.splitext(fn)
		data=json.load(fo)
		for acc in CliAccountGroup.from_dict(data):
			self.add_account(groupname,acc)

	def _write_accountgroup_arc(self,group_aids,fn,arc):
		g=[self[ak] for ak in group_aids]
		data=CliAccountGroup.to_dict(g)
		arc.writestr(fn,json.dumps(data,indent=4,sort_keys=True))

	def _add_metadata_file(self,gn,ext,fo):
		data=json.load(fo)
		if(gn in self.group2accounts):
			group_aids=self.group2accounts[gn]
			for ak,accd in data.items():
				if(ak in group_aids):
					CliAccount.set_meta_from_dict(self[ak],ext,accd)
		else:
			logging.warning("No account group found with groupname '%s'" % groupname)

	def _write_metadata_arc(self,gn,arc):
		if(gn in self.group2accounts):
			dataout={}
			
			group_aids=self.group2accounts[gn]
			for ak in group_aids:
				for ext,edata in CliAccount.get_all_meta_as_dict(self[ak]).items():
					ga=dataout.setdefault(ext,{})
					ga[ak]=edata

			for ext,data in dataout.items():
				if(len(data) > 0):
					fn=gn+'.'+ext
					arc.writestr(fn,json.dumps(data,indent=4,sort_keys=True))
		else:
			logging.warning("No account group found with groupname '%s'" % (groupname))
		
	
	@staticmethod
	def from_archive(filename,wal=None,pin=None):
		if(wal is None):
			wal=CliWallet()

		arc=zipordir.ZipOrDir(filename,'r')
		files=[x for x in arc.namelist() if x[-1] != '/']
		#//add in sorted order, accountgroups first
		
		filesdic={}
		for f in files:
			bn,ext=os.path.splitext(f)
			filesdic.setdefault(ext,set()).add(f)
			
		special=['group']
		for fn in filesdic.get('.group',[]):					
			wal._add_accountgroup_file(fn,arc.open(fn))
	
		for fn in files:
			bn,ext=os.path.splitext(fn)
			ext=ext[1:]
			if(ext not in special):
				wal._add_metadata_file(bn,ext,arc.open(fn))
	
		return wal

	@staticmethod
	def to_archive(wal,filename,pin=None):
		arc=zipordir.ZipOrDir(filename,'w')
		for f,group_aids in wal.group2accounts.items():
			fn=(f+'.group')
			wal._write_accountgroup_arc(group_aids,fn,arc)
			wal._write_metadata_arc(f,arc)




	
		


				
					
					
			
			
