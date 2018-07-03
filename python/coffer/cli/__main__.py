#!/usr/bin/env python2
import argparse
import cliwallet
import json
from pprint import pprint
	
#this is a synced balance	
def balance(wallet,chainsel,groupsel):
	all_balances={}
	for groupname,accounts in wallet.get_filtered_accounts(groupsel,chainsel):
		group_balances={}
		for a in accounts:
			tick=cliwallet.to_ticker(a.coin)
			bci=a.coin.blockchain()
	
			amount=0
			for aset in a.internal+a.external:
				unspents=bci.unspents(aset.addresses())
				amount+=sum([p.amount for p in unspents])

			group_balances[tick]=group_balances.get(tick,0)+amount

		all_balances[groupname]=group_balances
	return all_balances



def sync(wallet,chainsel,groupsel):
	all_balances={}
	for groupname,accounts in wallet.get_filtered_accounts(groupsel,chainsel):
		group_balances={}
		for a in accounts:
			tick=cliwallet.to_ticker(a.coin)
			bci=a.coin.blockchain()
			group_balances[tick]=group_balances.get(tick,0)+amount

		all_balances[groupname]=group_balances
	return all_balances

def cmd_balance(wallet,args):
	all_balances=balance(wallet,args.chain,args.group)

def cmd_sync(wallet,args):
	print(wallet)
	

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
sync_parser.add_argument('--unspents-only','-u',action='store_true',help="Only sync unspents <don't sync spends>")
sync_parser.set_defaults(func=cmd_sync)
args=parser.parse_args()

if(args.outwallet is None):
	args.outwallet=args.walletfile

wallet=cliwallet.CliWallet.from_archive(args.walletfile)

args.func(wallet,args)

cliwallet.CliWallet.to_archive(wallet,args.walletfile)

	





