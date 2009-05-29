class Log:
    ERROR           = 0x1
    WARNING         = 0x2
    BUG             = 0x4
    INFO            = 0x8
    ALL             = 0xF
    str = {ERROR: 'error', WARNING: 'warning', BUG: 'bug', INFO: 'info'}

class Homepage:
    NONE         = 0
    ANIMELOADS   = 1
    ANIMEKIWI    = 2
    ANIMEJUNKIES = 3
    YOUTUBE      = 4
    #       0   1               2           3               4
    str = ('', 'AnimeLoads', 'AnimeKiwi', 'AnimeJunkies', 'Youtube')

class Stream:
    VEOH       = 1
    EATLIME    = 2
    MEGAVIDEO  = 3
    HDWEB      = 4
    SEVENLOAD  = 5
    YOUTUBE    = 6
    IMEEM      = 7
    HDSHARE    = 8
    PLAIN      = 9
    #      0     1      2             3         4      5            6           7       8           9
    str = ('', 'Veoh', 'EatLime', 'MegaVideo', 'HDWeb', '7Load', 'YouTube', 'Imeem', 'HDShare', 'Plain')
