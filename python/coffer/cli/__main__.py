#!/usr/bin/env python2
import argparse
import cliwallet
import json
from ..coins import fromticker
from pprint import pprint
import re
from itertools import islice
from ..lib import appdirs
import os.path
import logging
from coffer.ticker import get_current_price
import _stdbip32

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
	prefix="%s/%s/%s(%s)" % (gname,tick,aid[:8],acc.label)
	return prefix

def subwalletitems(wallet,selchains,selgroups):
	selgroups=frozenset([x.lower() for x in selgroups])
	selchains=frozenset([x.lower() for x in selchains])
	for aid,acc in wallet.items():
		gname=wallet.account2group[aid]
		if(len(selgroups)==0 or gname in selgroups):
			if(len(selchains)==0 or acc.coin.ticker.lower() in selchains):
				yield gname,aid,acc

				
def cmd_balance(w,args):
	gwiter=subwalletitems(w,args.chain,args.group)
	price_tickers={}

	for gname,aid,acc in sorted(list(gwiter),key=lambda gw:_build_prefix(*gw)):
		amount=acc.balance()
		prefix=_build_prefix(gname,aid,acc)
		if(not args.print_value_only):
			if(acc.coin.ticker not in price_tickers):
				logging.info("Attempting to fetch current USD price informmation for %r",acc.coin)
				price_tickers[acc.coin.ticker]=get_current_price(acc.coin.ticker,'USD')
			print("%s\t%f ($%.02f)" % (prefix,amount,amount*price_tickers[acc.coin.ticker]))
		else:
			print("%s\t%f" % (prefix,amount))

def cmd_unspents(w,args):
	gwiter=subwalletitems(w,args.chain,args.group)
	unspents=[]
	for gname,aid,acc in sorted(list(gwiter),key=lambda gw:_build_prefix(*gw)):
		for dst in acc.unspent_iter():
			unspents.append(_build_prefix(gname,aid,acc)+'$'+str(dst.ref))
	unspents.sort()
	for us in unspents:
		print(us)
	
def cmd_sync(w,args):
	gwiter=subwalletitems(w,args.chain,args.group)
	for gname,aid,acc in gwiter:
		logging.info("Attempting to sync account %s..." % (_build_prefix(gname,aid,acc)))
		acc.sync(retries=args.retries)

def cmd_add_account_auth(w,args):
	allauths=cliwallet.CliAuth.from_file(args.auth,args.mnemonic_passphrase)
	for p in args.paths:
		coin=fromticker(p.ticker)
		for subauth in allauths:
			if(p.pa is not None):
				acc=subauth.toaccount(coin,authref=args.authname,root=p.pa)
				w.add_account(groupname=args.group,account=acc)
			else:
				for cov in _stdbip32.coverage(coin,args):
					print(cov)
					label,path,internal_path,external_path,b32args,b32kwargs=cov
					acc=subauth.toaccount(coin,authref=args.authname,root=path,internal_path=internal_path,external_path=external_path,*b32args,**b32kwargs)
					acc.label=label
					w.add_account(groupname=args.group,account=acc)

def cmd_send(w,args):
	for a in args.dsts:
		print(a.__dict__)
		
def cmd_get_address(w,args):
	for gname,aid,acc in sorted(list(gwiter),key=lambda gw:_build_prefix(*gw)):
		prefix=_build_prefix(gname,aid,acc)
		addrs=''.join([str(a) for a in acc.next_external(count=args.count)])
		print("%s/%s\t%s" % (prefix,'external',addrs))
		addrs=''.join([str(a) for a in acc.next_internal(count=args.count)])
		print("%s/%s\t%s" % (prefix,'internal',addrs))


if __name__=='__main__':
	default_wallet_dir=os.path.join(appdirs.user_data_dir("CofferCli","Coffer"),'default_wallet.zip')

	parser=argparse.ArgumentParser(description='The Coffer standalone wallet demo')
	parser.add_argument('--wallet','-w',type=str,help="The wallet file or directory you are going to read. (defaults to '%(default)s')",default=default_wallet_dir)
	parser.add_argument('--pin',type=str,help="The wallet file pin for the encrypted wallet that you are going to read")
	parser.add_argument('--wallet_out','-wo',type=str,help="The wallet file you are going to write to (defaults to the input wallet)")
	parser.add_argument('--pin_out',type=str,help="The wallet file pin for the encrypted wallet that you are going to write (defaults to the read pin)")
	subparsers=parser.add_subparsers()

	balance_parser=subparsers.add_parser('balance')
	balance_parser.add_argument('--chain','-c',action='append',help="The chain(s) to operate on. Can be entered multiple times.  Defaults to all.",default=[])
	balance_parser.add_argument('--group','-g',action='append',help="The wallet group(s) to lookup.  Can be entered multiple times.  Defaults to all.",default=[])
	balance_parser.add_argument('--print_value_only',action='store_true',help="Do not fetch or print approximate fiat value")
	#balance_parser.add_argument('--print_totals_only','-pt',action='store_true',help="Only print the totals")
	balance_parser.set_defaults(func=cmd_balance)

	unspents_parser=subparsers.add_parser('unspents')
	unspents_parser.add_argument('--chain','-c',action='append',help="The chain(s) to operate on. Can be entered multiple times.  Defaults to all.",default=[])
	unspents_parser.add_argument('--group','-g',action='append',help="The wallet group(s) to lookup.  Can be entered multiple times.  Defaults to all.",default=[])
	unspents_parser.add_argument('--print_value_only',action='store_true',help="Do not fetch or print approximate fiat value")
	#balance_parser.add_argument('--print_totals_only','-pt',action='store_true',help="Only print the totals")
	unspents_parser.set_defaults(func=cmd_unspents)

	sync_parser=subparsers.add_parser('sync')
	sync_parser.add_argument('--chain','-c',action='append',help="The chain(s) to operate on. Can be entered multiple times.  Defaults to all.",default=[])
	sync_parser.add_argument('--group','-g',action='append',help="The wallet group(s) to lookup.  Can be entered multiple times.  Defaults to all.",default=[])
	sync_parser.add_argument('--retries','-n',help="The number of retries to perform before a sync is considered failed",type=int,default=10)
	#sync_parser.add_argument('--unspents_only','-u',action='store_true',help="Only sync unspents <don't sync spends>")
	sync_parser.set_defaults(func=cmd_sync)

	add_account_auth_parser=subparsers.add_parser('add_account_from_auth')
	add_account_auth_parser.add_argument('--group','-g',help="The wallet group(s) to add the account to",default='main')
	add_account_auth_parser.add_argument('paths',nargs='+',help="A series of paths,each in the form <chain>:[/root/path]",type=PathType)
	add_account_auth_parser.add_argument('--auth','-a',help="Auth file",required=True,type=argparse.FileType('r'))
	add_account_auth_parser.add_argument('--authname','-an',help="Auth name",default='default',type=str)
	add_account_auth_parser.add_argument('--mnemonic_passphrase',help="The bip39 passphrase for a bip39 mnemonic (default none)",type=str)
	add_account_auth_parser.add_argument('--coverage',help="the coverage algorithm for pathless chains",type=str,default='broad')
	add_account_auth_parser.add_argument('--num_accounts',help="The number of accounts to check for a bip32 wallet (default1)",type=int,default=1)
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
	if(args.pin_out is None):
		args.pin_out=args.pin
	

	w=cliwallet.CliWallet.from_archive(args.wallet,pin=args.pin)

	args.func(w,args)

	cliwallet.CliWallet.to_archive(w,args.wallet_out,pin=args.pin_out)

	





