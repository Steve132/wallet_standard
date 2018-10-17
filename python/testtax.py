import sys
from coffer.cli.cliwallet import CliWallet
from coffer.ext import taxes
from pprint import pprint
from coffer.ticker.price import get_price,get_current_price,PriceLookupPastError
from coffer.coins._coin import ForkMixin
import time
import logging
from coffer.ticker.price_coincap2 import bsearch_to_find_earliest

logging.basicConfig(level=logging.DEBUG)

w=CliWallet.from_archive(sys.argv[1])

use_zero_basis_for_forks=False
def pu(dst,txo):
	#there has to be a return value here.
	if(txo==None):
		print("Cannot find transaction with input %s" % (u))

	current_timestamp=txo.timestamp
	finfo=None

	priceUSD=0.0

	#todo estimate prices from preset basis or estimated prices
	if('priceUSD_estimate' in dst.meta):
		priceUSD=dst.meta['priceUSD_estimate']
	if('basisUSD' in dst.meta):
		priceUSD=dst.meta['basisUSD']

	if(isinstance(dst.coin,ForkMixin)):
		finfo=dst.coin.fork_info()
		if(current_timestamp < finfo.timestamp):
			current_timestamp=finfo.timestamp
		if(use_zero_basis_for_forks):
			priceUSD=0.0

	return [taxes.BasisEntry(timestamp=current_timestamp,coin=dst.coin,iamount=dst.iamount,priceUSD=priceUSD,orefs=[dst.ref])]


#TODO this should split into long/short here instead, or just combine all the entries out
def summarize_basis_entries(belist):
	amount=0
	timestamp=0
	priceUSD=0
	for be in belist:
		amount+=be.coin.denomination_whole2float(be.iamount)
		priceUSD+=be.priceUSD*amount
		timestamp=max(be.timestamp,timestamp)

	return amount,timestamp,priceUSD/amount

bestimate=taxes.BasisEstimate(w.items(),pu)

"""basisEstimates={}
for dst in bestimate.unspents.values():
	be=bestimate.get(dst.ref)
	amount,timestamp,priceUSD=summarize_basis_entries(be)
	currUSD=get_current_price(dst.coin.ticker,'USD')
	basisEstimates[dst.ref]=(amount,timestamp,priceUSD,currUSD)


long_term_gain=0.0
short_term_gain=0.0
loss=0.0
now=time.time()
for k,v in basisEstimates.items():
	amount,timestamp,priceUSD,currUSD=v
	if(priceUSD < currUSD):
		loss+=(currUSD-priceUSD)*amount
	elif(timestamp < now-31536000): #TODO this really needs to be an actual time diff"""


long_term_gain=[]
short_term_gain=[]
loss=[]

allbes=[]

now=time.time()
for dst in bestimate.unspents.values():
	belist=bestimate.get(dst.ref)
	print(dst.ref,belist)
	currUSD=get_current_price(dst.coin.ticker,'USD')
	for be in belist:
		entry=(be,currUSD,dst.ref)
		#print(entry)
		if(currUSD < be.priceUSD):
			loss.append(entry)
		elif(be.timestamp < now-31536000):
			long_term_gain.append(entry)
		else:
			short_term_gain.append(entry)

def gain_or_loss(entrylist):
	amount=0.0
	for be,currUSD,dstref in entrylist:
		amount+=be.coin.denomination_whole2float(be.iamount)*(currUSD-be.priceUSD)
	return amount

print("long: $"+str(gain_or_loss(long_term_gain)))
print("short: $"+str(gain_or_loss(short_term_gain)))
print("loss: $"+str(gain_or_loss(loss)))
		
