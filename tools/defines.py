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

class Stream:
    VEOH       = 1
    EATLIME    = 2
    MEGAVIDEO  = 3
    HDWEB      = 4
    SEVENLOAD  = 5
    MYSPACECDN = 6
    IMEEM      = 7
    HDSHARE    = 8
    #      0     1      2             3         4      5            6           7       8
    str = ('', 'Veoh', 'EatLime', 'MegaVideo', 'HDWeb', '7Load', 'MyspaceCDN', 'Imeem', 'HDShare')
