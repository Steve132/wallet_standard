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
import coffer.ext.cli as extm
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
	totals={}

	for gname,aid,acc in sorted(list(gwiter),key=lambda gw:_build_prefix(*gw)):
		amount=acc.balance()
		prefix=_build_prefix(gname,aid,acc)
		if(not args.print_totals_only):
			if(not args.print_coin_value_only):
				if(acc.coin.ticker not in price_tickers):
					logging.info("Attempting to fetch current USD price informmation for %r",acc.coin)
					price_tickers[acc.coin.ticker]=get_current_price(acc.coin.ticker,'USD')
				print("%s\t%f ($%.02f)" % (prefix,amount,amount*price_tickers[acc.coin.ticker]))
			else:
				print("%s\t%f" % (prefix,amount))
		totals.setdefault(acc.coin.ticker,0.0)
		totals[acc.coin.ticker]+=amount
	print("\nTOTALS:")
	for ticker,total in sorted(list(totals.items()),key=lambda x: x[0]):
		if(not args.print_coin_value_only):
			print("%s\t%f ($%.02f)" % (ticker,total,total*price_tickers[ticker]))
		else:
			print("%s\t%f" % (ticker,total))
			

"""def cmd_unspents(w,args):
	gwiter=subwalletitems(w,args.chain,args.group)
	unspents=[]
	for gname,aid,acc in sorted(list(gwiter),key=lambda gw:_build_prefix(*gw)):
		for dst in acc.unspent_iter():
			unspents.append(_build_prefix(gname,aid,acc)+'$'+str(dst.ref))
	unspents.sort()
	for us in unspents:
		print(us)"""
	
#TODO: this needs to be refactored to not be a part of the gui
def cmd_sync(w,args):
	print(args)
	gwiter=subwalletitems(w,args.chain,args.group)
	for gname,aid,acc in gwiter:
		logging.info("Attempting to sync account %s..." % (_build_prefix(gname,aid,acc)))
		acc.sync(retries=args.retries,targets=args.sync_targets)

#TODO: this needs to be refactored to not be a part of the gui
def cmd_add_account_auth(w,args):
	allauths=cliwallet.CliAuth.from_file(args.auth,args.mnemonic_passphrase)
	for p in args.paths:
		coin=fromticker(p.ticker)
		for subauth in allauths:
			if(p.pa is not None):
				acc=subauth.to_account(coin,authref=args.authname,root=p.pa)
				w.add_account(groupname=args.group,account=acc)
			else:
				for cov in _stdbip32.coverage(coin,args):
					label,path,internal_path,external_path,b32args,b32kwargs=cov
					acc=subauth.to_account(coin,authref=args.authname,root=path,internal_path=internal_path,external_path=external_path,*b32args,**b32kwargs)
					acc.label=label
					w.add_account(groupname=args.group,account=acc)

def cmd_send(w,args):
	raise NotImplementedError
		
def cmd_list_addresses(w,args):
	gwiter=subwalletitems(w,args.chain,args.group)
	for gname,aid,acc in sorted(list(gwiter),key=lambda gw:_build_prefix(*gw)):
		prefix=_build_prefix(gname,aid,acc)
		addrs=''.join([str(a) for a in acc.next_external(count=args.count)])
		print("%s/%s\t%s" % (prefix,'external',addrs))
		addrs=''.join([str(a) for a in acc.next_internal(count=args.count)])
		print("%s/%s\t%s" % (prefix,'internal',addrs))

def cmd_crypt(w,args):
	pass

def cmd_ext(w,args):
	args.func_ext(w,args)

if __name__=='__main__':

	default_wallet_dir=os.path.join(appdirs.user_data_dir("CofferCli","Coffer"),'default_wallet.zip')

	#getpass.html
	wallet_parser=argparse.ArgumentParser(description="Wallet Options",add_help=False)
	wallet_group=wallet_parser.add_argument_group(title="Wallet I/O", description="These options are related to the wallet that you are operating on")
	wallet_group.add_argument('--wallet','-w',type=str,help="The wallet file or directory you are going to read. (defaults to '%(default)s')",default=default_wallet_dir)
	wallet_group.add_argument('--pin',type=str,help="The wallet file pin for the encrypted wallet that you are going to read")
	wallet_group.add_argument('--wallet_out','-wo',type=str,help="The wallet file you are going to write to (defaults to the input wallet)")
	wallet_group.add_argument('--pin_out',type=str,help="The wallet file pin for the encrypted wallet that you are going to write (defaults to the read pin)")

	peraccount_parser=argparse.ArgumentParser(description="Account Selection Options",add_help=False)
	peraccount_group=peraccount_parser.add_argument_group(title="Account Selection Options",description="These options directly control filters on which group/chain to operate on")
	peraccount_group.add_argument('--chain','-c',action='append',help="The chain(s) to operate on. Can be entered multiple times.  Defaults to all.",default=[])
	peraccount_group.add_argument('--group','-g',action='append',help="The wallet group(s) to lookup.  Can be entered multiple times.  Defaults to all.",default=[])

	parser=argparse.ArgumentParser(description='The Coffer standalone CLI wallet tool')
	subparsers=parser.add_subparsers(title='main',description="MAIN DESCRIPTION",dest="main_command",help="MAIN HELP")

	balance_parser=subparsers.add_parser('balance',help="Get balance for each account",parents=[wallet_parser,peraccount_parser]) #action?
	balance_parser.add_argument('--print_coin_value_only',action='store_true',help="Do not fetch or print approximate fiat value")
	balance_parser.add_argument('--print_totals_only','-pt',action='store_true',help="Only print the totals")
	balance_parser.set_defaults(func=cmd_balance)

	sync_parser=subparsers.add_parser('sync',help="Sync account information from the internet",parents=[wallet_parser,peraccount_parser])
	sync_parser.add_argument('--retries','-n',help="The number of retries to perform before a sync is considered failed",type=int,default=10)
	sync_parser.add_argument('sync_targets',nargs="*",help="Targets to sync",choices=["transactions","priceusd"],default=[])
	#sync_parser.add_argument('--unspents_only','-u',action='store_true',help="Only sync unspents <don't sync spends>")
	sync_parser.set_defaults(func=cmd_sync)

	add_account_auth_parser=subparsers.add_parser('add_account_from_auth',help="Add an account from a private key file",parents=[wallet_parser])
	add_account_auth_parser.add_argument('--group','-g',help="The wallet group(s) to add the account to",default='main')
	add_account_auth_parser.add_argument('paths',nargs='+',help="A series of paths,each in the form <chain>:[/root/path]",type=PathType)
	add_account_auth_parser.add_argument('--auth','-a',help="Auth file",required=True,type=argparse.FileType('r'))
	add_account_auth_parser.add_argument('--authname','-an',help="Auth name",default='default',type=str)
	add_account_auth_parser.add_argument('--mnemonic_passphrase',help="The bip39 passphrase for a bip39 mnemonic (default none)",type=str)
	add_account_auth_parser.add_argument('--coverage',help="the coverage algorithm for pathless chains",type=str,default='broad')
	add_account_auth_parser.add_argument('--num_accounts',help="The number of accounts to check for a bip32 wallet (default1)",type=int,default=1)
	#add_account_auth.add_argument('--store','-s',action="store_true",help="Save encrypted private key for the account to file")
	add_account_auth_parser.set_defaults(func=cmd_add_account_auth)

	list_addresses_parser=subparsers.add_parser('list_addresses',help="List addresses from each account",parents=[wallet_parser,peraccount_parser])
	list_addresses_parser.add_argument('--count','-n',help="The number of addresses to get",type=int,default=1)
	list_addresses_parser.set_defaults(func=cmd_list_addresses)

	crypt_parser=subparsers.add_parser('rekey',description="Decrypt, Encrypt, or Re-encrypt a wallet file (implied in all other wallet operations too",parents=[wallet_parser])
	crypt_parser.set_defaults(func=cmd_crypt)

	"""	send_parser=subparsers.add_parser('send')
		send_parser.add_argument('--group','-g',action='append',help="The wallet group(s) to send from. Defaults to all",default=[])
		send_parser.add_argument('chain',help="The chain to operate on.",type=str)
		send_parser.add_argument('dsts',nargs='+',help="A series of amounts in the form <amount>[CURRENCY]:<address>",type=DestinationType)
		send_parser.add_argument('--input_select_algorithm','-is',help="The input selection algorithm",default='mintax')
		send_parser.add_argument('--change_select_algorithm','-cs',help="The change selection algorithm",default='simplechange')
		send_parser.add_argument('--output_file','-o',help="The output file to output for the unsigned transaction",type=argparse.FileType('w'),default='-')
		send_parser.set_defaults(func=cmd_send)
	"""
	ext_parser=subparsers.add_parser('ext',help="Run an extension plugin command",parents=[wallet_parser])
	extsubparsers=ext_parser.add_subparsers(title='ext',description="EXT DESCRIPTION",dest="ext_command",help="EXT HELP")
	ext_parser.set_defaults(func=cmd_ext)
	extm.load_cli_exts_subparsers(extsubparsers,parents_available={'wallet_parser':wallet_parser,'peraccount_parser':peraccount_parser})

	args=parser.parse_args()

	if(args.wallet_out is None):
		args.wallet_out=args.wallet
	if(args.pin_out is None):
		args.pin_out=args.pin
	

	w=cliwallet.CliWallet.from_archive(args.wallet,pin=args.pin)

	args.func(w,args)

	cliwallet.CliWallet.to_archive(w,args.wallet_out,pin=args.pin_out)

	





