from __future__ import print_function
import sys
from . import __version__
import argparse
from .config import updateConfig, loadConfig, getConfigLocations, createConfigFile, getConfigInfo


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
    from .plugins import getAllStreams, getAllPages

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

        parser = argparse.ArgumentParser(description='Download videos from various sources',
                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        # parser.add_argument('--help', '-h', const='b1', nargs='?', help='prints the help')
        parser.add_argument('--version', '-v', action='store_true', help='prints the version')
        parser.add_argument('--list', '-a', help='list available pages and streams', dest="list_pages_and_streams", action="store_true")
        parser.add_argument('--csv', '-c', help='Creates a csv instead of downloading', dest="csv", action="store_true")
        parser.add_argument('--writesettings', '-w', help='Will write the current settings to the config file', dest="write_settings", action="store_true")
        parser.add_argument('links', nargs="*", help='One or more urls to webpages - use -l to see which are supported, if empty it will resume unfinished downloads (all empty directories in the flash_dir)')
        self.changeableConfigs = ['links', 'csv']
        for item in getConfigInfo():
            if 'args' in item:
                self.changeableConfigs.append(item['id'])
                h = ''
                if 'help' in item:
                    h = item['help']
                action = 'store'
                if item['type'] is 'bool':
                    action = 'store_true'
                parser.add_argument(*item['args'], help=h, dest=item['id'], action=action)

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
        if configs['list_pages_and_streams']:
            listPagesAndStreams()

        for name in self.changeableConfigs:
            self.config[name] = configs[name]
        updateConfig(self.config)
        if (configs['write_settings']):
            configFiles = getConfigLocations()
            createConfigFile(configFiles[1], self.config)
        return self.config

    def usage(self):
        self.parser.print_help()
        sys.exit(0)
