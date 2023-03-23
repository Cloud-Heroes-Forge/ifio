# Tests for autofio.py
from argparse import Namespace
def setup_args():
    global args
    args = Namespace()
    args.blocksize = ['4k,randrw','64k,rw']
    args.readpercentages = [0, 50, 100]
    args.minimum = 1
    args.maximum = 3
    args.slices = 2
    args.verbose = True
    args.config = 'test/fio_config.ini'
    args.output = 'output'
    args.log = 'autofio.log'

def setup_fio_config():
    global fio_config
    fio_config = {
        'global': {
            'ioengine': 'libaio',
            'direct': '1',
            'time_based': '1',
            'runtime': '60',
            'iodepth': '1',
            'bs': '4k',
            'rw': 'randrw',
            'rwmixread': '0',
            'group_reporting': '1',
            'filename': '/tmp/testfile',
            'name': 'job1'
        }
    }
