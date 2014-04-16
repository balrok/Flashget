import sys
import config

def version():
    print 'Flashget version 2.0.1'
    sys.exit(0)



# returns a line, which could be used to log the commandline
# the idea is to return the commandline args so they could get pasted back into the console
def get_log_line():
    args = sys.argv[:]
    args[-1] = "\\'".join("'" + p + "'" for p in args[-1].split("'"))
    return ' '.join(args)


def listPagesAndStreams(*args, **kwargs):
    from tools.stream import flashExt
    from tools.page import pages

    print("Pages:\n-------")
    for page in pages.extensions:
        p = page()
        print(p.name+" "+p.url)

    print("\nStreams:\n------")
    for stream in flashExt.extensions:
        print(stream.ename)
    sys.exit(0)

import argparse


parser = argparse.ArgumentParser(description='download flashfiles or dump videodatabases in a local database',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
#parser.add_argument('--help', '-h', const='b1', nargs='?', help='prints the help')
parser.add_argument('--version', '-v', action='store_true', help='prints the version')
parser.add_argument('--dl_instances', '-d', type=int, help='number of parallel downloads')
parser.add_argument('--title', '-t', help='is used to set the filename', dest='dl_title')
parser.add_argument('--name', '-n', help='is used to set the foldername', dest='dl_name')
parser.add_argument('--list', '-l', help='list available pages and streams', type=listPagesAndStreams)
parser.add_argument('link')

import inspect
changeableConfigs = ['dl_instances', 'dl_title', 'dl_name', 'link']
configs = {}
for name, obj in inspect.getmembers(config):
    if name in changeableConfigs:
        configs[name] = obj
parser.set_defaults(**configs)
#parser.get_default('fileName')

def parse():
    args = parser.parse_args()
    configs = vars(args)
    if configs['version']:
        version()
    for name in changeableConfigs:
        setattr(config, name, configs[name])

def usage():
    parser.print_help()
    sys.exit(0)
