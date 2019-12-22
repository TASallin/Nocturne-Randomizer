'''
To be mostly removed by Markro's FileSystem stuff.

The set of values that are usable with a customizer. Contains no actual code.
A customizer decompresses field scripts and adds space at the end of each script. That space is used as a stack.
version: Version string.
extended_sizes: Amount of bytes extended to each script.
customizer_offsets: Absolute offsets of each script to the ISO.
hint_msgs: Tuples of script names and message labels to be used (or at least looked at) for hint usage.
'''

version = "0p2a"
extended_sizes = 1000
script_sizes = {
    'e601': 0x166d,
    'e634': 12887,
    'e658': 5875,
    'e673': 5885,
    'e674': 25048,
    'e723': 5317,
    'e731': 3854,
    'e740': 4665,
    'e741': 3032,
    'e742': 3260,
    'e743': 3291,
    'e744': 2709,
    'e745': 2561,
    'e746': 2887,
    'e747': 4757,
    'e748': 4343,
    'e749': 6346,
    'e750': 3994,
    'f001': 20950,
    'f002': 18635,
    'f003': 17621,
    'f004': 19914,
    'f005': 13178,
    'f006': 13326,
    'f007': 13779,
    'f008': 13234,
    'f011': 19121,
    'f012': 15981,
    'f013': 13990,
    'f014': 43202,
    'f015': 70423,
    'f016': 91809,
    'f017': 41669,
    'f018': 32427,
    'f019': 44682,
    'f020': 67530,
    'f021': 38853,
    'f022': 47062,
    'f023': 39986,
    'f024': 76511,
    'f025': 73863,
    'f026': 33819,
    'f027': 44046,
    'f028': 40055,
    'f029': 19187,
    'f030': 14336,
    'f031': 128151,
    'f032': 63730,
    'f033': 87249,
    'f034': 82000,
    'f035': 34928,
    'f036': 43634,
    'f037': 57289,
    'f038': 29942,
    'f039': 18702,
    'f040': 21120,
    'f041': 60446,
    'f042': 51521,
    'f043': 93887,
    'f044': 69839,
    'f045': 88575
}
customizer_offsets = {
    'e506': 0xd7310800,
    'e601': 0xd85dd000,
    'e618': 0xdc39b800,
    'e634': 0xdf3cd000,
    'e658': 0xe2af9800,
    'e673': 0xe6166800,
    'e674': 0xe6756800,
    'e723': 0xf0e67000,
    'e731': 0xf1ec1800,
    'e740': 0xf2090000,
    'e741': 0xf22c8800,
    'e742': 0xf2418000,
    'e743': 0xf262f800,
    'e744': 0xf2794000,
    'e745': 0xf28e7000,
    'e746': 0xf2a5a000,
    'e747': 0xf2cad800,
    'e748': 0xf2ed5000,
    'e749': 0xf3235800,
    'e750': 0xf349e800,
    'f001': 0x855CA210,
    'f002': 0x85B59210,
    'f003': 0x861D4210,
    'f004': 0x86743210,
    'f005': 0x86C24A10,
    'f006': 0x87179210,
    'f007': 0x8759C210,
    'f008': 0x87A6DA10,
    'f011': 0x87DE3A10,
    'f012': 0x882AFA10,
    'f013': 0x887A4A10,
    'f014': 0x88a51210,
    'f015': 0x89707210,
    'f016': 0x8B4CF210,
    'f017': 0x8F00AA10,
    'f018': 0x903EF210,
    'f019': 0x911DAA10,
    'f020': 0x91F55210,
    'f021': 0x95ED3210,
    'f022': 0x97D3EA10,
    'f023': 0x9A4B7A10,
    'f024': 0x9B37AA10,
    'f025': 0x9D33DA10,
    'f026': 0x9ed79210,
    'f027': 0xA0698A10,
    'f028': 0xa2621210,
    'f029': 0xa329c210,
    'f030': 0xa4256210,
    'f031': 0xa4429a10,
    'f032': 0xA64BAA10,
    'f033': 0xa862c210,
    'f034': 0xab9b3210,
    'f035': 0xADE67210,
    'f036': 0xAF165A10,
    'f037': 0xB0F78210,
    'f038': 0xB3674210,
    'f039': 0xB3A59A10,
    'f040': 0xB3CF8210,
    'f041': 0xB4031A10,
    'f042': 0xB6387210,
    'f043': 0xB97DFA10,
    'f044': 0xBCD29A10,
    'f045': 0xC053BA10
}
hint_msgs = [
    ('f015',"F015_SINEN02"),
    ('f015',"F015_SINEN03"),
    ('f015',"F015_SINEN13"),
    ('f015',"F015_SINEN10_01"),
    ('f015',"F015_SINEN16_YES_02"),
    ('f015',"F015_SINEN21"),
    ('f015',"F015_SINEN22"),
    ('f002',"F002_SINEN_02"),
    ('f002',"F002_SINEN_03"),
    ('f002',"F002_SINEN_04"),
    ('f016',"F016_INKYU01_02"),
    ('f016',"F016_SINEN03_05"),
    ('f017',"F017_SINEN_01_01"),
    ('f017',"F017_SINEN_02"),
    ('f017',"F017_SINEN_03_02"),
    ('f017',"F017_SINEN_03"),
    ('f017',"F017_SINEN_05_02"),
    ('f017',"F017_SINEN_06"),
    ('f019',"F019_SINEN11_02"),
    ('f019',"F019_SINEN01"),
    ('f019',"F019_SINEN03_01"),
    ('f019',"F019_BAR_SINEN01_03"),
    ('f003',"F003_SINEN05"),
    ('f003',"F003_SINEN03_00"),
    ('f003',"F003_SINEN06"),
    ('f022',"F022_SINEN01"),
    ('f023',"F023_DEVIL_TARM_05"),
    ('f023',"F023_SINEN01_02"),
    ('f024',"ONI_003_03"),
    ('f004',"F004_SINEN03_02"),
    ('f004',"F004_SINEN04"),
    ('f026',"F026_SINEN01"),
    ('f026',"F026_SINEN04"),
    ('f026',"F026_SINEN08"),
    ('f026',"F026_SINEN05_01"),
    ('f026',"F26_AREA12_NPC1"),
    ('f026',"F026_MANE03"),
    ('f026',"F026_MANE05"),
    ('f031',"F031_SINEN_01_01"),
    ('f031',"F031_SINEN_04_01"),
    ('f031',"F031_SINEN_10"),
    ('f031',"F031_SINEN_11_01"),
    ('f029',"F029_SINEN01_02"),
    ('f029',"F029_SINEN02_02"),
    ('f016',"F016_SINEN09_02"),
    ('f016',"F016_SINEN06_02"),
    ('f016',"F016_SINEN10_02"),
    ('f016',"F016_SINEN07_02"),
    ('f016',"F016_SINEN13_02"),
    ('f021',"F021_SINEN02_02"),
    ('f021',"F021_SINEN01"),
    ('f021',"F021_SINEN03"),
    ('f033',"F033_SINEN02"),
    ('f033',"F033_SINEN01_02"),
    ('f033',"F033_SINEN06_02"),
    ('f033',"F033_SINEN05"),
    ('f033',"F033_SINEN07_02"),
]