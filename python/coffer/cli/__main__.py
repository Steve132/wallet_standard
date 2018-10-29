#!/usr/bin/env python2
import argparse
import cliwallet
import json
from pprint import pprint
import re
from itertools import islice
import os.path
import logging
import _stdbip32
import sys
from binascii import hexlify,unhexlify
from coffer.chain import fromchainid
from coffer.coins import fromticker
from coffer.transaction import Output,Transaction
from coffer.ticker import get_current_price
from coffer.lib import appdirs
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
	gwiter=subwalletitems(w,args.chain,args.group)
	for gname,aid,acc in gwiter:
		logging.info("Attempting to sync account %s..." % (_build_prefix(gname,aid,acc)))
		acc.sync(retries=args.retries,targets=args.sync_targets)

#TODO: this needs to be refactored to not be a part of the gui
#URGENT TODO:Accounts need to have a way to specify the change address desired for the account beyond just the first one in the list
def cmd_add_account_auth(w,args):
	allauths=cliwallet.CliAuth.from_file(args.auth_file,args.mnemonic_passphrase)
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

#https://miningfees.com/currency/litecoin TODO: fetch feerate?
#TODO fold this into wallet operations.
def cmd_build_tx(w,args):
	chain=args.chain
	gwiter=subwalletitems(w,[chain],args.group)
	unspents=set()
	changeaddr=None
	coin=fromticker(chain)
	selected_unspent_mapping={}
	uref_to_aid={}
	wlist=[]
	#sweep input algorithm
	if(args.input_selection == "sweep"):
		for gname,aid,acc in gwiter:
			wlist.append((gname,aid,acc))
			incoming=set(acc.unspents_iter())
			for u in incoming:
				u.meta['aid']=aid
			unspents.update(incoming)
			selected_unspent_mapping.setdefault(acc,set()).update(incoming)
				
	else:
		raise Exception("Error, build_tx only supports the 'sweep' input selection method at the moment") #TODO: implement the other methods. #TODO refactor this into generic interactions

	if(args.change_account is not None):
		for gname,aid,acc in wlist:
			if(aid[:8]==args.change_account[:8]):
				changeaddr=acc.next_internal(count=1)[0]
				break
		else:	
			try:
				changeaddr=coin.parse_addr(args.change_account)
			except:
				raise Exception("Could not parse %s as an address, nor could account with id %s be found" % (args.change_account,args.change_account))
	elif(args.change_selection == "maxvalue"):
		acc,s=max(selected_unspent_mapping.items(),key=lambda a:a[0].balance(a[1]))
		changeaddr=acc.next_internal(count=1)[0]
	elif(args.change_selection == "maxitems"):
		acc,s=max(selected_unspent_mapping.items(),key=lambda a:len(a[1]))
		changeaddr=acc.next_internal(count=1)[0]
	elif(args.change_selection == "NO_CHANGE_ADDRESS"):
		changeaddr="NO_CHANGE_ADDRESS"
	else:
		raise Exception("Could not understand an argument for a change address")
		
	coin=fromticker(chain)
	outs=[]
	for dstarg in args.dsts:
		amount=dstarg.amount
		if(dstarg.ticker is not None and coin.chainid != dstarg.ticker):
			logging.warning("Warning, the ticker '%s' doesn't match %s" (coin.chainid,dstarg.ticker))
			rate=get_current_price(coin.chainid,dstarg.ticker)
			logging.warning("Using an exchange rate of %f %s" % (rate,coin.chainid+dstarg.ticker))
			amount/=rate
		addr=coin.parse_addr(dstarg.address)
		outs.append(Output(coin,addr,amount=amount))

	
		
	tx=coin.build_tx(unspents,outs,changeaddr,feerate=0.0000087)
	logging.warning("The generated transaction has a fee of %f" % (tx.fee))
	json.dump(tx.to_dict(),args.output_file)


#URGENT_TODO: The only supported auth is b32auth and b32seedauth
#URGENT_TODO: Add aid to the metadata for a search and only fall back to search for inputs that aren't authorized.
#URGENT_TODO: Add full path (or at least address index) to the metadata so that the authorizer doesn't have to search for the id in most cases.
def cmd_auth_tx(w,args):
	txo=Transaction.from_dict(json.load(args.input_file))
	cha=txo.chain
	subauths=cliwallet.CliAuth.from_file(args.auth_file,args.mnemonic_passphrase)
	for subauth in subauths:
		for srcidx,src in enumerate(txo.srcs):
			if(cha.is_src_fully_authorized(txo,srcidx)):
				continue
			if('aid' in src.meta and src.meta['aid'] in w):
				w[src.meta['aid']].auth_tx(txo,subauth,max_search=100)
			else:
				for gname,aid,acc in subwalletitems(w,[src.chainid],[]):
					acc.auth_tx(txo,subauth,max_search=100)
	json.dump(txo.to_dict(),args.output_file)
		

def cmd_send_tx(w,args):
	txo=Transaction.from_dict(json.load(args.input_file))
	cha=txo.chain
	if(args.submit and hasattr(cha,'format_tx')):
		bci=cha.blockchain()
		ftx=cha.format_tx(txo)
		logging.info(bci.pushtx_bytes(unhexlify(ftx)))
	if(args.serialize and hasattr(cha,'format_tx')):
		print(cha.format_tx(txo))
	logging.warning("fee: %f" % (txo.fee))
	
		
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
	args.func_ext(w,args)  /insight-api/tx/send

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

	auth_parser=argparse.ArgumentParser(description="Account Authorization Options",add_help=False)
	auth_parser.add_argument('--auth_file','-a',help="Auth file",required=True,type=argparse.FileType('r'))
	auth_parser.add_argument('--authname','-an',help="Auth name",default='default',type=str)
	auth_parser.add_argument('--mnemonic_passphrase',help="The bip39 passphrase for a bip39 mnemonic (default none)",type=str)

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

	add_account_auth_parser=subparsers.add_parser('add_account_from_auth',help="Add an account from a private key file",parents=[wallet_parser,auth_parser])
	add_account_auth_parser.add_argument('--group','-g',help="The wallet group(s) to add the account to",default='main')
	add_account_auth_parser.add_argument('paths',nargs='+',help="A series of paths,each in the form <chain>:[/root/path]",type=PathType)
	add_account_auth_parser.add_argument('--coverage',help="the coverage algorithm for pathless chains",type=str,default='broad')
	add_account_auth_parser.add_argument('--num_accounts',help="The number of accounts to check for a bip32 wallet (default1)",type=int,default=1)
	#add_account_auth.add_argument('--store','-s',action="store_true",help="Save encrypted private key for the account to file")
	add_account_auth_parser.set_defaults(func=cmd_add_account_auth)

	list_addresses_parser=subparsers.add_parser('list_addresses',help="List addresses from each account",parents=[wallet_parser,peraccount_parser])
	list_addresses_parser.add_argument('--count','-n',help="The number of addresses to get",type=int,default=1)
	list_addresses_parser.set_defaults(func=cmd_list_addresses)

	crypt_parser=subparsers.add_parser('rekey',description="Decrypt, Encrypt, or Re-encrypt a wallet file (this operation is implied in all other wallet operations too)",parents=[wallet_parser])
	crypt_parser.set_defaults(func=cmd_crypt)

	#TODO THIS ONLY WORKS ON-CHAIN
	build_tx_parser=subparsers.add_parser('build_tx',help="build a transaction to be sent on chain",parents=[wallet_parser])
	build_tx_parser.add_argument('--group','-g',action='append',help="The wallet group(s) to send from. Defaults to all",default=[])
	build_tx_parser.add_argument('chain',help="The chain to operate on.",type=str)
	build_tx_parser.add_argument('dsts',nargs='+',help="A series of amounts in the form <amount>[CURRENCY]:<address>",type=DestinationType)
	build_tx_parser.add_argument('--input_selection','-is',help="The input selection algorithm",choices=["mintax","stdin","lowestfee","sweep"],default='mintax')
	build_tx_change_group=build_tx_parser.add_mutually_exclusive_group(required=False)
	build_tx_change_group.add_argument('--change_selection','-cs',help="The change selection algorithm",choices=["privacy,first,maxvalue,maxinput,NO_CHANGE_ADDRESS"],default='maxvalue')
	build_tx_change_group.add_argument('--change_account','-ca',help="Explicitly select an account id or address for the change to go to.")
	build_tx_parser.add_argument('--output_file','-o',help="The output file to output for the unsigned transaction",type=argparse.FileType('w'),default=sys.stdout)
	build_tx_parser.set_defaults(func=cmd_build_tx)

	auth_tx_parser=subparsers.add_parser('auth_tx',help="authorize a transaction to be broadcast",parents=[wallet_parser,auth_parser])
	auth_tx_parser.add_argument('--input_file','-i',help="The input unsigned transaction json utx file",type=argparse.FileType('r'),default=sys.stdin)
	auth_tx_parser.add_argument('--output_file','-o',help="The output signed transaction json utx file",type=argparse.FileType('w'),default=sys.stdout)
	auth_tx_parser.set_defaults(func=cmd_auth_tx)

	send_tx_parser=subparsers.add_parser('send_tx',help="send or serialize a transaction to be sent on chain")
	send_tx_parser.add_argument('--input_file','-i',help="The input authorized transaction json stx file",type=argparse.FileType('r'),default=sys.stdin)
	send_tx_submit_group=send_tx_parser.add_mutually_exclusive_group(required=True)
	send_tx_submit_group.add_argument('--submit',help="Submit the authorized transaction",action='store_true')
	send_tx_submit_group.add_argument('--serialize',help="Output the formatted transaction to stdout",action='store_true')
	send_tx_parser.set_defaults(func=cmd_send_tx)
	send_tx_parser.set_defaults(nowallet=True)

	ext_parser=subparsers.add_parser('ext',help="Run an extension plugin command",parents=[wallet_parser])
	extsubparsers=ext_parser.add_subparsers(title='ext',description="EXT DESCRIPTION",dest="ext_command",help="EXT HELP")
	ext_parser.set_defaults(func=cmd_ext)
	extm.load_cli_exts_subparsers(extsubparsers,parents_available={'wallet_parser':wallet_parser,'peraccount_parser':peraccount_parser})

	args=parser.parse_args()

	if(hasattr(args,'nowallet')):
		args.func(None,args)
	else:
		if(args.wallet_out is None):
			args.wallet_out=args.wallet
		if(args.pin_out is None):
			args.pin_out=args.pin
	
		w=cliwallet.CliWallet.from_archive(args.wallet,pin=args.pin)

		args.func(w,args)

		cliwallet.CliWallet.to_archive(w,args.wallet_out,pin=args.pin_out)

	





