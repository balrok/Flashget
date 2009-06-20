class Log:
    ERROR           = 0x1
    WARNING         = 0x2
    BUG             = 0x4
    INFO            = 0x8
    DEBUG           = 0x10
    ALL             = 0xFF
    str = {ERROR: 'error', WARNING: 'warning', BUG: 'bug', INFO: 'info', DEBUG: 'debug'}

class Homepage:
    NONE         = 0
    ANIMELOADS   = 1
    ANIMEKIWI    = 2
    ANIMEJUNKIES = 3
    YOUTUBE      = 4
    KINOTO       = 5
    Plain        = 6
    #       0   1               2           3               4       5               6
    str = ('', 'AnimeLoads', 'AnimeKiwi', 'AnimeJunkies', 'Youtube', 'Kino.to', 'Plain')

class Stream:
    NONE       = 0
    VEOH       = 1
    EATLIME    = 2
    MEGAVIDEO  = 3
    HDWEB      = 4
    SEVENLOAD  = 5
    YOUTUBE    = 6
    IMEEM      = 7
    HDSHARE    = 8
    PLAIN      = 9
    ZEEC       = 10
    XVID       = 11
    CCF        = 12
    #      0     1      2             3         4      5            6           7       8           9      10      11     12
    str = ('', 'Veoh', 'EatLime', 'MegaVideo', 'HDWeb', '7Load', 'YouTube', 'Imeem', 'HDShare', 'Plain', 'Zeec', 'xvid', 'CCF')

class Quality:
    LOW  = 0
    HIGH = 1
