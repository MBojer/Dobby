#!/usr/bin/python

import requests

# url = "http://10.0.1.11/NMC/st+N11W1jmAUTWSxGL+exw/data.htm"
url = "http://10.0.1.11/logon.htm"
username = 'script'
password = 'pass'
print(requests.get(url, auth=(username, password)).content)















# import urllib2


# http://10.0.1.11/NMC/st+N11W1jmAUTWSxGL+exw/data.htm

# url = "http://10.0.1.11/NMC/st+N11W1jmAUTWSxGL+exw/data.htm"
# username = "script"
# password = "pass"
#
# req = urllib2.Request(url)
#
# handle = ''
#
# try:
#     handle = urllib2.urlopen(req)
# except IOError, e:
#     if hasattr(e, 'code'):
#         if e.code != 401:
#             print 'We got another error'
#             print e.code
#         else:
#             print e.headers
#             print e.headers['www-authenticate']
#
# print handle
