try:
	from collections import MutableMapping
except:
	from collections.abc import MutableMapping

class AccountGroup(object):
	def __init__(self,accounts={}):
		self.accounts=accounts

	def iter_accounts(self,selchains=[]):
		selchains=set([x.lower() for x in selchains])
		for a,acc in self.accounts.items():
			if(len(selchains)==0 or acc.coin.ticker.lower() in selchains):
				yield a,acc
		
	#def balance(self,chainsel=[],bci=None):
	#	group_balances={}
	#	for a,acc in self.iter_accounts(chainsel):
	#		tick.acc.coin.ticker
	#		amount=acc.balance(bci)
	#		group_balances[tick]=group_balances.get(tick,0)+amount
	#	return group_balances
	
	#def sync(self,chainsel=[],bci=None):
	#	for a,acc in self.iter_accounts(chainsel):
	#		acc.sync(bci)

	#def iter_addresses(self,chainsel=[]):
	#	group_addresses={}
	#	for a,acc in self.get_accounts(chainsel).items():
	#		group_addresses[a]={'external':acc.next_external_iter(),'internal':acc.next_internal_iter()}
	#	return group_addresses
	
#AccountGroup = dict
class Wallet(object):
	def __init__(self):
		self.groups={}
		self.accountmapping={}

	def iter_groups(self,selgroups=[]):
		selgroups=set([x.lower() for x in selgroups])
		for gname,g in self.groups.items():
			if(len(selgroups)==0 or gname.lower() in selgroups):
				yield gname,g

	def add_account(self,groupname,acc):
		aid=account.id()
		if(aid in self.accountmapping):
			raise Exception("Error, account %r is already in group %s" % (account,self.accountmapping[aid]))
		g=self.groups.setdefault(groupname,AccountGroup())
		self.accountmapping[aid]=groupname
		g[aid]=account

	def add_group(self,groupname,group):
		if(groupname in self.groups):
			raise Exception("Error, group %s is already in wallet" % (groupname))

		for a,account in group.iter_accounts():
			aid=account.id()
			if(aid in self.accountmapping):
				raise Exception("Error, account %r is already in group %s" % (account,self.accountmapping[aid]))
			self.accountmapping[aid]=groupname
		self.groups[groupname]=group




