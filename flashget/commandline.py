from __future__ import print_function
import sys
from . import __version__
import argparse
from .config import updateConfig, loadConfig


def version():
    print('Flashget version %s' % __version__)
    sys.exit(0)


# returns a line, which could be used to log the commandline
# the idea is to return the commandline args so they could get pasted back into the console
def get_log_line():
    args = sys.argv[:]
    args[1:] = [x.replace(' ', '\ ') for x in args[1:]]
    return ' '.join(args)


def listPagesAndStreams(*dummy1, **dummy2):
    from .stream import getAllStreams
    from .page import getAllPages

    print("Pages:\n-------")
    for page, path in getAllPages():
        print(page.name+" "+page.url+" "+path)

    print("\nStreams:\n------")
    for stream, path in getAllStreams():
        print(stream.ename+" "+stream.url+" "+path)
    sys.exit(0)


class Commandline(object):
    def __init__(self):
        self.config = loadConfig()

        parser = argparse.ArgumentParser(description='download flashfiles or dump videodatabases in a local database',
                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        # parser.add_argument('--help', '-h', const='b1', nargs='?', help='prints the help')
        parser.add_argument('--version', '-v', action='store_true', help='prints the version')
        parser.add_argument('--dl_instances', '-d', type=int, help='number of parallel downloads')
        parser.add_argument('--title', '-t', help='is used to set the filename', dest='dl_title')
        parser.add_argument('--name', '-n', help='is used to set the foldername', dest='dl_name')
        parser.add_argument('--list', '-a', help='list available pages and streams', type=listPagesAndStreams)
        parser.add_argument('--limit', '-l', help='limit bandwidth in kb/s', dest='limit')
        parser.add_argument('--selfsolve', '-s', help='Solve the captcha by yourself', dest="captcha_selfsolve", action="store_true")
        parser.add_argument('links', nargs="*", help='One or more urls to webpages - use -l to see which are supported, if empty it will \
                resume unfinished downloads (all empty directories in the flash_dir)')

        self.changeableConfigs = ['dl_instances', 'dl_title', 'dl_name', 'limit', 'links', 'captcha_selfsolve']
        default_argument_configs = {}
        for name in self.changeableConfigs:
            default_argument_configs[name] = self.config.get(name)
        parser.set_defaults(**default_argument_configs)
        self.parser = parser

    def parse(self):
        args = self.parser.parse_args()
        configs = vars(args)
        if configs['version']:
            version()
        for name in self.changeableConfigs:
            self.config[name] = configs[name]
        updateConfig(self.config)
        return self.config

    def usage(self):
        self.parser.print_help()
        sys.exit(0)
