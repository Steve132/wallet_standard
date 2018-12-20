#from coffer.coin import fromticker
import copy
import coffer.account
#import claimer


def register_fork(claimerFork):
	pass
	

def fork_migrate_account(account,new_coin):
	if(not isinstance(account.OnChainAddressSet)):
		raise Exception("Cannot migrate an account that's not on-chain")
	#if(account.coin
	account.coin=new_coin
	for a in account.external:
		a.coin=new_coin
	for a in account.internal:
		a.coin=new_coin

	newtransactions={}
	for txr,tx in account.transactions.items():
		txr.chainid=new_coin.chainid
		tx.chain=new_coin
		tx.ref.chainid=new_coin.chainid
		if(tx.spenttx is not None):
			tx.spenttx.chainid=new_coin.chainid

		for src in tx.srcs:
			src.coin=new_coin
		for dst in tx.dsts:
			dst.coin=new_coin
		newtransactions[txr]=tx
	account.transactions=newtransactions
	

def forks_add_account_from_fork(w,target_ticker,selchains=[],selgroups=[]):
	target_coin=fromticker(target_ticker)
	finfo=target_coin.fork_info()
	source_coin=fromticker(finfo.ticker)
	new_coin=BTC()
	new_coin.ticker('STV')
	for gname,said,sacc in w.subwalletitems(selchains,selgroups):
		if(sacc.coin==source_coin):
			tacc=copy.deepcopy(sacc)
			fork_migrate_account(tacc,new_coin)
			w.add_account(gname+'_forks',tacc)

	



def cmd_forks_add_account_from_fork(w,args):
	for ft in args.forkticker:
		forks_add_account_from_fork(w,ft,args.group,args.chain)
	

def load_cli_subparsers(extsubparsers,parents_available):
	forks_parser=extsubparsers.add_parser('forks',help="Modules and options related to forks")
	parents=[parents_available['wallet_parser'],parents_available['peraccount_parser'],parents_available['auth_parser']]
	#raise Exception("This is temporarily disabled")
	#add_accounts_from_fork_parser=forks_parser.add_subparser('add_accounts_from_fork',parents=parents)
	#add_accounts_from_fork_parser.add_argument('forkticker',nargs='+')
	#add_accounts_from_fork_parser.set_defaults(func_ext=cmd_forks_add_account_from_fork)


	
