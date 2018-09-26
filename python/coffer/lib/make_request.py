import json
import random
import logging
import time

try:
	from urllib.request import urlopen,Request
	from urllib.error import URLError
	from urllib.parse import urlencode
except:
	from urllib2 import urlopen,Request,URLError
	from urllib import urlencode

def make_json_request(request_type,endpoint,call="",callargs=None,retry_counter=10,delay=0.25,*args,**kwargs):
	encodeargs=None		
	if(callargs):
		encodeargs=urlencode(callargs)

	ep=endpoint
	headers={'User-Agent': 'Mozilla/5.0%d'%(random.randrange(1000000))}

	if(request_type is 'GET'):
		url=ep+call+(('?'+encodeargs) if encodeargs else '')
		data=None
		headers.update({'Accept':'application/json'})
	elif(request_type is 'POST'):
		url=ep+call
		data=encodeargs
		headers.update({'Accept':'application/json', 'Content-Length': str(len(data)),'Content-Type': 'application/x-www-form-urlencoded'})
	else:
		raise Exception("Unhandled request type")

	req=Request(url,data,headers)

	time.sleep(delay)
	logging.debug("Request(%r,%r,%r)" % (url,data,headers))
	response=urlopen(req,*args,**kwargs)
	response=response.read().strip()
	return json.loads(response)
