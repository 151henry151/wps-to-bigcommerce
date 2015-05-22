#!/usr/bin/python

import requests
import io
import zipfile
import subprocess
import glob
import os
from cStringIO import StringIO

##This clears out any old csv files in the working directory
filenames = glob.glob('*.csv')
for filename in filenames:
    os.remove(filename)

##These are the login credentials
mypsswd = 'obscured'
mydlrcode = 'obscured'
myusrname = 'obscured'

##This logs in and obtains the token
payload = {'rememberMe': 'on', 'password': mypsswd, 'dealerCode': 
 mydlrcode, 'dm': '4', 'userName': myusrname}
loginurl = 'https://www.lemansnet.com/login'
r = requests.post(loginurl, data=payload)
token = r.headers['loginToken']

##xmlpayload is a one-time string, it will be the same any time this is run
xmlpayload = """<pricing><whoForDealer><dealerCode>MET087</dealerCode></whoForDealer><rememberPreferences>1</rememberPreferences></pricing>"""

##This will use the token to request the pricefile zip archive
pricingurl = 'https://www.lemansnet.com/pricing/2013/pos'
headers = {'loginToken': token, 'Content-Type': 'text/xml; charset=utf-8'}
d = requests.post(pricingurl, data=xmlpayload, headers=headers)

##This extracts the CSV file from the ZIP file that we just requested
##into our current directory.  

d_file = StringIO(d.content)
if zipfile.is_zipfile(d_file):
    z = zipfile.ZipFile(d_file)
    z.extractall()
else:
    print(d.content)
#z = zipfile.ZipFile(StringIO(d.content)); z.extractall()

##The following stuff takes the filename of the csv file sitting in the current 
##directory, and uses it as an argument when calling up the csv2mysql script 
##that also is in the current directory. the csv2mysql script then creates a 
##database and table based on the names used in the subprocess.call line, and 
##uses the data from that csv to populate it.

csvfiles = glob.glob('*.csv')
partlistfile = csvfiles[0]

subprocess.call(["./csv2mysql.py", "--table=PARTS_UNLIMITED", 
 "--database=PARTDATA", partlistfile])



