import zipfile
import os,os.path,sys

class DirFile(object):
	def __init__(self,dirname,mode):
		self.dirname=dirname
		self.mode=mode

	def namelist(self):
		lst=[]
		for f in os.listdir(self.dirname):
			if(os.path.isdir(f)):
				lst.append(f+'/')
			else:
				lst.append(f)
		return lst
	
	def open(self,name):
		return open(os.path.join(self.dirname,name),'r')

	def writestr(self,arcname, data):
		with open(os.path.join(self.dirname,arcname),'w') as fo:
			fo.write(data)
	def close(self):
		pass

def ZipOrDir(name,mode):
	if('.zip' in name):
		return zipfile.ZipFile(name,mode)
	else:
		return DirFile(name,mode)
		
