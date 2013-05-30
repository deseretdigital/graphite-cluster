#!/usr/bin/python

import os
import sys
from getopt import getopt
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
metric_key = ''
metric_type = ''

# TODO add in metric type

try:
    opts, args = getopt(sys.argv[1:],"hk:",["key="])
except getopt.GetoptError:
    print('Usage: python graphite-router.py -k <metric key>')
    sys.exit(2)

for opt, arg in opts:
    if opt == '-h': 
        print('Usage: python graphite-router.py -k <metric key>')
        sys.exit()
    elif opt in ("-k", "--key"):
        metric_key = arg

# Check required key        
if not metric_key: 
    print('Usage: python graphite-router.py -k <metric key>')
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
    router.addDestination(destination);    
    
# Echo routes
print('routes for ' + metric_key) 
routes = router.getDestinations(metric_key)
for route in routes:
    print(route)


