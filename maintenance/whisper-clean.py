#!/usr/bin/python

import os
import sys
import getopt
from os.path import dirname, join, abspath, splitext, relpath


from pprint import pprint

# Figure out where we're installed
BIN_DIR = dirname(abspath(__file__))
ROOT_DIR = dirname(BIN_DIR)

# Make sure that carbon's 'lib' dir is in the $PYTHONPATH if we're running from
# source.
LIB_DIR = join(ROOT_DIR, 'lib')
sys.path.insert(0, LIB_DIR)
 
from carbon.hashing import ConsistentHashRing
from carbon.routers import ConsistentHashingRouter
from carbon.conf import settings
from carbon import util

## Read in options
local_node = ''
local_destinations = []

try:
    opts, args = getopt.getopt(sys.argv[1:],"hn:",["node="])
except getopt.GetoptError:
    print('Usage: python whisper-clean.py -n <address>')
    sys.exit(2)

for opt, arg in opts:
    if opt == '-h': 
        print('Usage: python whisper-clean.py -n <address>')
        sys.exit()
    elif opt in ("-n", "--node"):
        local_node = arg

if not local_node: 
    print('Usage: python whisper-clean.py -n <address>')
    sys.exit(2)


## Settings
# Absolute path to the Graphite Data Directory
DATA_DIR = join(ROOT_DIR, 'storage/whisper')

# Parse config
settings.readFrom(join(ROOT_DIR, 'conf/carbon.conf'), 'relay')

# Read in destinations from config
destinations = util.parseDestinations(settings.DESTINATIONS)

# Setup Router
router = ConsistentHashingRouter(settings.REPLICATION_FACTOR)
 
for destination in destinations:
    if destination[0] == local_node:
        local_destinations.append(destination) 
    
    router.addDestination(destination);    

 
# Walk Data dir and process orphaned whisper files 
for dirname, dirnames, filenames in os.walk(DATA_DIR):
    if dirname.startswith(join(DATA_DIR, settings.CARBON_METRIC_PREFIX)):
        continue
    for filename in filenames:
        pathname = os.path.join(dirname, filename)
        basename, ext = os.path.splitext(filename)
        if '.wsp' != ext:
            print('skipping %s' % relpath(pathname, DATA_DIR))
        
        metric_dest = router.getDestinations(relpath(join(dirname, basename), DATA_DIR).replace('/', '.'))
        
        orphaned = True
        for mdest in metric_dest:
            if mdest in local_destinations:
                orphaned = False
                break
        
        if orphaned:
            print('renaming %s' % pathname)
            os.rename(pathname, join(dirname, basename + '.wsp_orph'))
            # os.unlink(pathname)