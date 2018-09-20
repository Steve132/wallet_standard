try:
	from collections import MutableMapping
except:
	from collections.abc import MutableMapping

class AccountGroup(object):
	def __init__(self,accounts={}):
		self.accounts=accounts

	def get_accounts(self,selchains=[]):
		selchains=set([x.lower() for x in selchains])
		outgroup={}
		for a,acc in self.accounts.items():
			if(len(selchains)==0 or acc.coin.ticker.lower() in selchains):
				outgroup[a]=acc
		return outgroup

	def balance(self,chainsel=[]):
		group_balances={}
		accounts=self.get_accounts(chainsel)
		for a,acc in accounts.items():
			tick.acc.coin.ticker
			bci=acc.coin.blockchain()
			
			amount=0
			for aset in acc.internal+acc.external:
				unspents=bci.unspents(aset.addresses())
				amount+=sum([p.amount for p in unspents])

			group_balances[tick]=group_balances.get(tick,0)+amount
		return group_balances
	
	def sync(self,chainsel=[],retries=10):
		for a,acc in self.get_accounts(chainsel).items():
			tick=acc.coin.ticker
			bci=acc.coin.blockchain()
			bci.retries=retries
			acc.sync(bci)

	def add_account_from_auth(self,coin,auth,root,authname):
		acc=auth.toaccount(coin,root=root,authref=authname)
		self.accounts[acc.id()]=acc
	
#AccountGroup = dict
class Wallet(object):
	def __init__(self):
		self.groups={}

	def get_groups(self,selgroups=[]):
		selgroups=set([x.lower() for x in selgroups])
		outgroups={}
		for gname,g in self.groups.items():
			if(len(selgroups)==0 or gname in selgroups):
				outgroups[gname]=g
		return outgroups
	
	def balance(self,groupsel=[],chainsel=[]):
		return {groupname:group.balance(chainsel) for groupname,group in self.get_groups(groupsel).items()}
		

	def sync(self,groupsel=[],chainsel=[],retries=10):
		for groupname,group in self.get_groups(groupsel).items():
			group.sync(chainsel,retries)
		
		
	def get_addresses(self,groupsel=[],chainsel=[]):
		return {groupname:group.get_addresses(chainsel) for groupname,group in self.get_groups(groupsel).items()}

	def add_account_from_auth(self,groupname,coin,auth,root,authname):
		g=self.groups.setdefault(groupname,AccountGroup())
		g.add_account_from_auth(coin,auth,root,authname)



