#!/usr/bin/env python
import re
import os
import csv
import sys

if (len(sys.argv) > 1):
    mydir = os.path.abspath(sys.argv[1])
    print mydir
else:
    print 'Please include the path to the NYT corpus.'
    exit()
    

#mydir = '/Users/astorer/Dev/iqss-text-organizer/corpus'
f = open(mydir+'/info.csv','w')
names = ['FILEPATH','YEAR','MONTH','DAY']
dw = csv.DictWriter(f, names)
dw.writerow({k:k for k in names})
for root, dirnames, filenames in os.walk(mydir):
    for filename in filenames:
        if not filename.endswith('.xml'):
            continue
        m = re.match('.*/(\d{4})/(\d{2})/(\d{2})',root)
        m.group(0)
        dw.writerow({'YEAR':m.group(1),'MONTH':m.group(2),'DAY':m.group(3),'FILEPATH':os.path.join(root,filename)})

f.close()
