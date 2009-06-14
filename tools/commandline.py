import config
import sys
import tools.defines as defs

def version():
    print '0'
    sys.exit(0)


def usage():
    print 'usage: ./get.py [options] [link]'
    print 'options are optional:'
    for i in cmd_list:
        sys.stdout.write('-%s ' % i[0])     # short
        if i[3]:
            sys.stdout.write('%s ' % i[3])  # parameter (if exists)
        sys.stdout.write('--%s ' % i[1])      # long
        if i[3]:
            sys.stdout.write('%s ' % i[3])  # parameter (if exists)
        sys.stdout.write((max_length - (i[2] + i[6])) * ' ') # fill with spaces, so that the ouptu is nice adjusted
        print ' %s' % i[5]    # description
    sys.exit(0)


def set_quality(arg):
    global config
    if arg:
        config.flash_quality = defs.Quality.High
        print 'set quality to high'
    else:
        config.flash_quality = defs.Quality.Low
        print 'set quality to low'


def set_curses(arg):
    global config
    config.txt_only = not arg
    if arg:
        print 'disabling curses'
    else:
        print 'enabling curses'


def set_dl_instances(arg):
    global config
    config.dl_instances = arg
    print 'setting download instances to %s' % arg


def parse_bool(txt):
    if txt[0] == '1' or txt.lower() == 'true' or txt.lower() == 'yes':
        return True
    elif txt[0] == '0' or txt.lower() == 'false' or txt.lower() == 'no':
        return False
    else:
        print 'argument required a bool (true,false,yes,no,0,1), but you\'ve written "%s"' % txt
        usage()


def parse_int(txt):
    try:
        ret = int(txt)
    except:
        print 'argument required an integer, but you\'ve written "%s"' % txt
        usage()
    return ret


def call(cmd, long, arg1, arg2):
    cmd_in_next_arg = False
    if cmd[3]: # search arg
        if long:
            arg = arg1[2 + cmd[2] + 1:] # 2='--' + length + 1 ='='
        else:
            arg = arg1[2:]
        if not arg:
            arg = arg2
            cmd_in_next_arg = True
        if not arg:
            print 'you have to define an argument for parameter %s' % arg1
            usage()
        if arg[0] == '=':
            arg = arg[1:]
        if arg[0] == ' ':
            arg = arg[1:]
        if not arg or arg[0] == '-':
            print 'you forgot to specify the parameter for option %s' % param
            usage()
        if cmd[3] == 'BOOL':
            arg = parse_bool(arg)
        if cmd[3] == 'INT':
            arg = parse_int(arg)
        cmd[4](arg)
    else:
        cmd[4]()
    return cmd_in_next_arg



cmd_list = []
max_length = 0 # used to adjust the output nice
def add_to_commands(short, long, param, call, descr):
    global cmd_list, max_length
    long_length = len(long)
    extra_length = 1
    if param:
        extra_length += 2 * len(param)
    else:
        extra_length -= 2
    if long_length + extra_length > max_length:
        max_length = long_length + extra_length
    cmd_list.append((short, long, long_length, param, call, descr, extra_length))


add_to_commands('h', 'help', None, usage, 'prints this help')
add_to_commands('v', 'version', None, version, 'prints the version')
add_to_commands('q', 'quality', 'BOOL', set_quality, 'quality like in the config-file 0=low, 1=high')
add_to_commands('d', 'dl_instances', 'INT', set_dl_instances, 'set the number of parallel downloads')
add_to_commands('c', 'curses', 'BOOL', set_curses, 'enables curses display or disables if argument is 0 *not yet implemented*')
def parse():
    sl = len(sys.argv)
    jump_over = False # when the argument is in the next argv we need to jump over this
    for i in xrange(1, sl):
        if jump_over:
            jump_over = False
            continue
        if sys.argv[i][0] == '-':
            if sys.argv[i][1] == '-':
                for cmds in cmd_list:
                    if sys.argv[i][2:2+cmds[2]] == cmds[1]:
                        next = ''
                        if i+1 < sl:
                            next = sys.argv[i + 1]
                        if call(cmds, True, sys.argv[i], next): # returns true, if the parameter was in the next arg
                            jump_over = True
                        break
                else: # cmd not found
                    print 'unknown option %s' % sys.argv[i]
                    usage()
                continue
            for cmds in cmd_list:
                if sys.argv[i][1] == cmds[0]:
                    next = ''
                    if i+1 < sl:
                        next = sys.argv[i + 1]
                    if call(cmds, False, sys.argv[i], next): # returns true, if the parameter was in the next arg
                        jump_over = True
                    break
            else: # cmd not found
                print 'unknown option %s' % sys.argv[i]
                usage()
            continue
        else:
            if i + 1 < sl:
                print 'something is wrong with this "%s"' % sys.argv[i]
                usage()
            # else the last parameter will be the url
            config.link = sys.argv[i]
