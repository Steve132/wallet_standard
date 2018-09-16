#!/usr/bin/env python2
import argparse
import cliwallet
import json
from ..coins import fromticker
from pprint import pprint
import re
#this is a synced balance	
def balance(wallet,chainsel,groupsel):
	all_balances={}
	for groupname,accounts in wallet.get_filtered_accounts(groupsel,chainsel):
		group_balances={}
		for a,acc in accounts.items():
			tick=cliwallet.to_ticker(acc.coin)
			bci=acc.coin.blockchain()
	
			amount=0
			for aset in acc.internal+acc.external:
				unspents=bci.unspents(aset.addresses())
				amount+=sum([p.amount for p in unspents])

			group_balances[tick]=group_balances.get(tick,0)+amount

		all_balances[groupname]=group_balances
	return all_balances

def sync(wallet,chainsel,groupsel,retries=10):
	all_balances={}
	for groupname,accounts in wallet.get_filtered_accounts(groupsel,chainsel):
		group_balances={}
		for a,acc in accounts.items():
			tick=acc.coin.ticker
			bci=acc.coin.blockchain()
			bci.retries=retries
			acc.sync(bci)

def cmd_balance(wallet,args):
	all_balances=balance(wallet,args.chain,args.group)

def cmd_sync(wallet,args):
	sync(wallet,args.chain,args.group,retries=args.retries)

def cmd_add_account_auth(wallet,args):
	pre=re.compile(r'([\w\-]+)(?::([\w\/]+))?')
	auth=cliwallet.CliAuth.from_file(args.auth)
	
	for p in args.paths:
		mo=pre.match(p)
		if(not mo):
			raise Exception("'%s' is not recognized as an accountpath")
		ticker,pa=mo.group(1,2)
		coin=fromticker(ticker)
		for subauth in auth.subauths:
			acc=subauth.toaccount(coin,root=pa,authref=args.authname)
			
			g=wallet.groups.setdefault(args.group,{})
			g[acc.id()]=acc
			print(acc.id())


	

parser=argparse.ArgumentParser(description='The Coffer standalone wallet demo')
parser.add_argument('walletfile',type=str,help="The wallet file you are going to read")
parser.add_argument('--outwallet','-o',type=str,help="The wallet file you are going to write to (defaults to read)")
subparsers=parser.add_subparsers()

balance_parser=subparsers.add_parser('balance')
balance_parser.add_argument('--chain','-c',action='append',help="The chain(s) to operate on. Can be entered multiple times.  Defaults to all.",default=[])
balance_parser.add_argument('--group','-g',action='append',help="The wallet group(s) to lookup.  Can be entered multiple times.  Defaults to all.",default=[])
balance_parser.add_argument('--totals','-t',action='store_true',help="Only print the totals")
balance_parser.set_defaults(func=cmd_balance)

sync_parser=subparsers.add_parser('sync')
sync_parser.add_argument('--chain','-c',action='append',help="The chain(s) to operate on. Can be entered multiple times.  Defaults to all.",default=[])
sync_parser.add_argument('--group','-g',action='append',help="The wallet group(s) to lookup.  Can be entered multiple times.  Defaults to all.",default=[])
sync_parser.add_argument('--retries','-n',help="The number of retries to perform before a sync is considered failed",type=int,default=10)
#sync_parser.add_argument('--unspents_only','-u',action='store_true',help="Only sync unspents <don't sync spends>")
sync_parser.set_defaults(func=cmd_sync)

add_account_auth_parser=subparsers.add_parser('add_account_from_auth')
add_account_auth_parser.add_argument('--group','-g',help="The wallet group(s) to lookup.  Can be entered multiple times.",default='main')
add_account_auth_parser.add_argument('paths',nargs='+',help="A series of paths,each in the form <chain>:[/root/path]")
add_account_auth_parser.add_argument('--auth','-a',help="Auth file",default='-',type=argparse.FileType('r'))
add_account_auth_parser.add_argument('--authname','-an',help="Auth name",default='default',type=str)
add_account_auth_parser.add_argument('--name','-n',help='Account name',type=str)

#add_account_auth.add_argument('--store','-s',action="store_true",help="Save encrypted private key for the account to file")
add_account_auth_parser.set_defaults(func=cmd_add_account_auth)



args=parser.parse_args()

if(args.outwallet is None):
	args.outwallet=args.walletfile

wallet=cliwallet.CliWallet.from_archive(args.walletfile)

args.func(wallet,args)

cliwallet.CliWallet.to_archive(wallet,args.walletfile)

	





