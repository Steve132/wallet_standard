#!/usr/bin/env python2
import argparse
import cliwallet
import json
from ..coins import fromticker
from pprint import pprint
import re
from itertools import islice
from lib import appdirs
import os.path
import coffer.operations

#this is a synced balance	

"""
	<ticker>:<path> (TODO: add OR <ticker>	
"""
class PathType(object):
	_pre=re.compile(r'([\w\-]+)(?::([\w\/]+))?')
	def __init__(self,p):
		mo=PathType._pre.match(p)
		if(not mo):
			raise argparse.ArgumentTypeError("'%s' is not recognized as an accountpath of the form ticker[:/path]")
		self.ticker,self.pa=mo.group(1,2)


class DestinationType(object):
	_amountre=re.compile(r'^(?P<amount>[\d\.]+)(?P<lp>[\(])?(?P<ticker>[\w-]+)?(?(lp)\)):(?P<address>\S+)')
	def __init__(self,p):
		mo=DestinationType._amountre.match(p)
		if(not mo):
			raise argparse.ArgumentTypeError("'%s' is not recognized as an amount of the form <amount>[ticker]:<address>")
		results=mo.groupdict()
		self.amount=float(results['amount'])
		self.ticker=results['ticker']
		self.address=results['address']
		

def _build_prefix(gname,aid,acc):
	tick=acc.coin.ticker
	prefix="%s/%s/%s" % (gname,tick,aid[:8])
	return prefix
				
def cmd_balance(w,args):
	for gname,group in w.iter_groups(args.group):
		for aid,acc in group.iter_accounts(args.chain):
			amount=acc.balance()
			prefix=_build_prefix(gname,aid,acc)
			print("%s\t%f" % (prefix,amount))

def cmd_sync(w,args):
	for gname,group in w.iter_groups(args.group):
		for aid,acc in group.iter_accounts(args.chain):
			acc.sync(retries=args.retries)

def cmd_add_account_auth(w,args):
	allauths=cliwallet.CliAuth.from_file(args.auth)
	for p in args.paths:
		coin=fromticker(p.ticker)
		for subauth in allauths:
				acc=subauth.toaccount(coin,authref=args.authname,root=p.pa) #accountnum=args.account_index)
				w.add_account(groupname=args.group,account=acc)

def cmd_send(w,args):
	for a in args.dsts:
		print(a.__dict__)
		
def cmd_get_address(w,args):
	for gname,group in w.iter_groups(args.group):
		for aid,acc in group.iter_accounts(args.chain):
			prefix=_build_prefix(gname,aid,acc)
			for extint in ['external','internal']:
				addrs=''.join([str(a) for a in acc.next_external(count=args.count)])
				print("%s/%s\t%s" % (prefix,extint,addrs))

if __name__=='__main__':
	default_wallet_dir=os.path.join(appdirs.user_data_dir("CofferCli","Coffer"),'default_wallet.zip')

	parser=argparse.ArgumentParser(description='The Coffer standalone wallet demo')
	parser.add_argument('--wallet','-w',type=str,help="The wallet file or directory you are going to read. (defaults to '%(default)s')",default=default_wallet_dir)
	parser.add_argument('--wallet_out','-wo',type=str,help="The wallet file you are going to write to (defaults to the input wallet)")
	subparsers=parser.add_subparsers()

	balance_parser=subparsers.add_parser('balance')
	balance_parser.add_argument('--chain','-c',action='append',help="The chain(s) to operate on. Can be entered multiple times.  Defaults to all.",default=[])
	balance_parser.add_argument('--group','-g',action='append',help="The wallet group(s) to lookup.  Can be entered multiple times.  Defaults to all.",default=[])
	balance_parser.add_argument('--totals_only','-t',action='store_true',help="Only print the totals")
	balance_parser.set_defaults(func=cmd_balance)

	sync_parser=subparsers.add_parser('sync')
	sync_parser.add_argument('--chain','-c',action='append',help="The chain(s) to operate on. Can be entered multiple times.  Defaults to all.",default=[])
	sync_parser.add_argument('--group','-g',action='append',help="The wallet group(s) to lookup.  Can be entered multiple times.  Defaults to all.",default=[])
	sync_parser.add_argument('--retries','-n',help="The number of retries to perform before a sync is considered failed",type=int,default=10)
	#sync_parser.add_argument('--unspents_only','-u',action='store_true',help="Only sync unspents <don't sync spends>")
	sync_parser.set_defaults(func=cmd_sync)

	add_account_auth_parser=subparsers.add_parser('add_account_from_auth')
	add_account_auth_parser.add_argument('--group','-g',help="The wallet group(s) to add the account to",default='main')
	add_account_auth_parser.add_argument('paths',nargs='+',help="A series of paths,each in the form <chain>:[/root/path]",type=PathType)
	add_account_auth_parser.add_argument('--auth','-a',help="Auth file",default='-',type=argparse.FileType('r'))
	add_account_auth_parser.add_argument('--authname','-an',help="Auth name",default='default',type=str)
	#add_account_auth.add_argument('--store','-s',action="store_true",help="Save encrypted private key for the account to file")
	add_account_auth_parser.set_defaults(func=cmd_add_account_auth)

	send_parser=subparsers.add_parser('send')
	send_parser.add_argument('--group','-g',action='append',help="The wallet group(s) to send from. Defaults to all",default=[])
	send_parser.add_argument('chain',help="The chain to operate on.",type=str)
	send_parser.add_argument('dsts',nargs='+',help="A series of amounts in the form <amount>[CURRENCY]:<address>",type=DestinationType)
	send_parser.add_argument('--input_select_algorithm','-is',help="The input selection algorithm",default='mintax')
	send_parser.add_argument('--change_select_algorithm','-cs',help="The change selection algorithm",default='simplechange')
	send_parser.add_argument('--output_file','-o',help="The output file to output for the unsigned transaction",type=argparse.FileType('w'),default='-')
	send_parser.set_defaults(func=cmd_send)

	get_address_parser=subparsers.add_parser('get_address')
	get_address_parser.add_argument('--group','-g',action='append',help="The wallet group(s) to send from. Defaults to all",default=[])
	get_address_parser.add_argument('--chain','-c',action='append',help="The chain(s) to operate on. Can be entered multiple times.  Defaults to all.",default=[])
	get_address_parser.add_argument('--count','-n',help="The number of addresses to get",type=int,default=1)
	get_address_parser.set_defaults(func=cmd_get_address)
	
	args=parser.parse_args()

	if(args.wallet_out is None):
		args.wallet_out=args.wallet

	w=cliwallet.CliWallet.from_archive(args.wallet)

	args.func(w,args)

	cliwallet.CliWallet.to_archive(w,args.wallet_out)

	





