from logging import config
import nocturne_script_assembler as assembler
import customizer_values as custom_vals
import nocturne

from io import BytesIO
from os import path
import copy

from fs.Iso_FS import *
from fs.DDS3_FS import *
from fs.LB_FS import *
from paths import PATCHES_PATH

''' Assembler bf_script modification functions:
def changeProcByIndex(self, instructions, relative_labels, index):
def changeMessageByIndex(self, message_obj, index):
def appendProc(self, instructions, relative_labels, proc_label):
def appendMessage(self, message_str, message_label_str, is_decision = False, name_id = 0):
def appendPUSHSTR(self,str):
def getMessageIndexByLabel(self, label_str):
def getPUSHSTRIndexByStr(self, str):
def getProcIndexByLabel(self, label_str):
def getProcInstructionsLabelsByIndex(self, proc_index):
'''

'''
#Example of procedure replacement:
f0##_obj = get_script_obj_by_name(dds3, 'f0##')
f0##_xxx_room = f0##_obj.getProcIndexByLabel("PROC_LABEL")
f0##_xxx_insts = [
    inst("PROC",f0##_xxx_room),
    #Insert instructions here
    inst("END")
]
f0##_xxx_labels = [
    assembler.label("BRANCH_LABEL",LINE_NUMBER)
]

f0##_obj.changeProcByIndex(f0##_xxx_insts, f0##_xxx_labels, f0##_xxx_room)
f0##_lb = push_bf_into_lb(f0##_obj, 'f0##')
dds3.add_new_file(custom_vals.LB0_PATH['f0##'], f0##_lb)
'''
'''
Hints plan:
Specter: Hijiri will tell you on 2nd open trigger.
    "..Oh yeah, there's something you should know" 
Troll: The Eligor tells you
	"This is Ginza, the city under the rule"
	or
	Add it to 006_start
Berith: ??? (2nd Eligor tells you)
Kaiwan: ??? (1st Eligor tells you)
Ose: ??? (Door tells you)
Mizuchi: Jack Frost tells you
Sisters: ???
Ongyo-Ki: Text when going in early
Black Frost: ??? (text from NPC?)
Specter 2: Last door block trap will tell you
Girimehkala: Maybe high pixies tell you?
Specter 3: Hijiri would tell you before going in.
Futomimi: Yes/No text tells you
Archantels: Door would tell you
Mara: ???
Surt: ???
Mada: ???
Mot: ???
Mithra: ???
Samael: ???
Dante 2: ???
Beelzebub: ???
Metatron: ???
'''
SCRIPT_DEBUG = False

IMMERSIVE_NAMES = {
    "Thor 1": "Thor",
    "Thor 2": "Thor",
    "Specter 1": "Specter",
    "Specter 2": "Specter",
    "Specter 3": "Specter",
    "Dante 1": "Dante",
    "Dante 2": "Dante",
    "Sisters": "Lachesis",
    "Archangels": "Gabriel",
}

#instruction creation shortcut
def inst(opcode_str,operand=0):
    return assembler.instruction(assembler.OPCODES[opcode_str],operand)

class Script_Modifier:
    def __init__(self, dds3):
        self.dds3 = dds3
        
    # gets the script object from dds3 fs by provided path
    def get_script_obj_by_path(self, script_path):
        script = bytearray(self.dds3.get_file_from_path(script_path).read())
        return assembler.parse_binary_script(script)

    def get_script_obj_by_name(self, script_name):
        return self.get_script_obj_by_path(custom_vals.SCRIPT_OBJ_PATH[script_name])

    def push_bf_into_lb(self, bf_obj, name):
        # get the field lb and parse it
        lb_data = self.dds3.get_file_from_path(custom_vals.LB0_PATH[name])
        lb = LB_FS(lb_data)
        lb.read_lb()
        # add the uncompressed, modified BF file to the LB and add it to the dds3 fs
        return lb.export_lb({'BF': BytesIO(bytearray(bf_obj.toBytes()))})
    def get_reward_str(self, check_name, world):
        reward_str = "You defeated "+world.checks[check_name].boss.name+"."
        if world.checks[check_name].boss.reward:
            reward_str += "^n"+custom_vals.MAGATAMA_REWARD_MSG[world.checks[check_name].boss.reward.name]
        if world.checks[check_name].flag_rewards:
            for flag_reward in world.checks[check_name].flag_rewards:
                if flag_reward.flag_id in custom_vals.FLAG_REWARD_MSG:
                    reward_str+="^n"+custom_vals.FLAG_REWARD_MSG[flag_reward.flag_id]
                else:
                    print ("Warning: In get_reward_str(). No reward string found for flag",hex(flag_reward.flag_id))
        return reward_str
    def get_flag_reward_insts(self, check_name, world):
        ret_insts = []
        #ret_insts = [inst("PUSHIS",1),inst("COMM",0xe)] #for testing purposes
        #ret_insts.extend([inst("PUSHIS",1), inst("PUSHIS",2), inst("COMM",0x70)]) #Add 1 Medicine previously for testing purposes
        for flag in world.checks[check_name].flag_rewards:
            ret_insts.append(inst("PUSHIS",flag.flag_id))
            ret_insts.append(inst("COMM",8))
            if flag.additional_ids:
                for extra_id in flag.additional_ids:
                    ret_insts.append(inst("PUSHIS",extra_id))
                    ret_insts.append(inst("COMM",8))
        if world.checks[check_name].boss.name == "Kagutsuchi" and world.checks[check_name].boss.reward is not None: #Fix for Kagutsuchi not dropping rewards
            magatama = world.checks[check_name].boss.reward.id
            ret_insts.append(inst("PUSHIS",magatama))
            ret_insts.append(inst("COMM",0x122))
        #ret_insts.extend([inst("PUSHIS",1), inst("PUSHIS",55), inst("COMM",0x70)]) #Add 1 Float Ball post for testing purposes
        ret_insts.extend( [inst("PUSHIS",20),inst("COMM",0xe)] )#small pause so you can read through skipping
        return ret_insts
    def get_flag_reward_location_string(self, flag_id, world):
        for check_name, check_obj in world.checks.items():
            for flag in check_obj.flag_rewards:
                if flag_id == flag.flag_id:
                    return custom_vals.LOCATION_NAMES_BY_CHECK[check_name]
        print ("Warning: In get_flag_reward_location_string(), flag",hex(flag_id),"not found.")
        return ""
    def get_checks_boss_id(self, check_name, world, index=0):
        boss_of_check = world.checks[check_name].boss.name
        #if boss_of_check in custom_vals.DEMON_ID_BY_NAME:
        #    return custom_vals.DEMON_ID_BY_NAME[boss_of_check]
        if boss_of_check in custom_vals.BOSS_DEMON_MODEL_IDS_BY_NAME:
            return custom_vals.BOSS_DEMON_MODEL_IDS_BY_NAME[boss_of_check][index]
        #print("Error: In get_checks_boss_id(), ID of boss",boss_of_check,"who is",check_name,"was not found")
        print("Error: a field boss model does not exist and will show a generic replacement")
        return 122 #Mothman!
    def get_checks_boss_name(self, check_name, world, immersive=False):
        boss_name = world.checks[check_name].boss.name
        if immersive and boss_name in IMMERSIVE_NAMES:
            boss_name = IMMERSIVE_NAMES[boss_name]
        return boss_name
    def insert_callback(self, field_string, location_insert, fun_name_insert, overwrite_warning=True):
        if len(fun_name_insert) > 15:
            print("ERROR: In insert_callback().",fun_name_insert,"is over 15 characters long")
            return
        file_path = custom_vals.WAP_PATH[field_string]
        wap_file = self.dds3.get_file_from_path(file_path).read()
        #print("Inserting",fun_name_insert,"as callback for",field_string,". wap_file len:",len(wap_file))
        if wap_file[location_insert] != 0 and overwrite_warning:
            print("WARNING: Callback insertion of",fun_name_insert,"overwriting data.")
        wap_file = wap_file[:location_insert] + bytes([2]) + bytes(assembler.ctobb(fun_name_insert,15)) + wap_file[location_insert+16:]
        self.dds3.add_new_file(file_path,BytesIO(wap_file))
    def script_debug_out(self,bf_obj, bf_name):
        assembler.bytesToFile(bf_obj.toBytes(),self.logpath+bf_name)
        print("Logging script",bf_name)
        outfile = open(self.logpath+bf_name+"asm",'w')
        outfile.write(bf_obj.exportASM())
        outfile.close()
        #outfile.close()
        # assembler.bytesToFile(f024_obj.toBytes(),"piped_scripts/f024.bf")
        #outfile = open("piped_scripts/f024.bfasm",'w')
        #outfile.write(f024_obj.exportASM())
        #outfile.close()

    def run(self, world=None, config_settings=None):
        
        if SCRIPT_DEBUG:
            self.logpath = 'logs/script_log{}/'.format(world.seed)
            if not os.path.exists(self.logpath):
                os.mkdir(self.logpath)
        
        #World object: world.checks is a dict. Key is boss name as string (in logic.py)
        #   Value has boss.name to check with.
        #world.checks['Forneus'].boss.name is name of boss at Forneus check.
        #reward is world.checks['Forneus'].boss.reward
        #what will be added is world.checks['Forneus'].boss.flag_rewards. A list of flags to be set on defeat.
        #Candelabra is part of reward message even though currently they technically don't do anything.
        #if world==None:
        #    world = object()
        #    world.checks = {}
        #    for bn in custom_vals.BOSS_NAMES:
        #        world.checks[bn] = object()
        #        world.checks[bn].boss = object()
                
        bonus_magatama = 1
        if world != None:
            bonus_magatama = world.bonus_magatama.id

        # get the 601 event script and add our hook
        #add in extra flag sets for cutscene removal
        e601_obj = self.get_script_obj_by_name('e601')
        e601_insts = [
            inst("PROC",0),
            inst("PUSHIS",0x7f3), #Tutorial cutscene skip
            inst("COMM",8),
            inst("PUSHIS",0x440), #SMC Splash removal
            inst("COMM",8),
            inst("PUSHIS",0x403),
            inst("COMM",8),
            inst("PUSHIS",0x480), #Shibuya Splash removal
            inst("COMM",8),
            inst("PUSHIS",0x9), #Shibuya Chiaki cutscene
            inst("COMM",8),
            inst("PUSHIS",0xa), #Initial Cathedral cutscene
            inst("COMM",8),
            inst("PUSHIS",0xb), #Hijiri Shibuya cutscene
            inst("COMM",8),
            inst("PUSHIS",0xa2), #Fountain cutscene removal
            inst("COMM",8),
            inst("PUSHIS",0x404), #SMC exit cutscene removal
            inst("COMM",8),
            #inst("PUSHIS",0x4a0), #Amala Network 1 cutstscene 1
            #inst("COMM",8), #Turns off SMC healing and pixie cutscene in Yoyogi.
            inst("PUSHIS",0x4a1), #AN1c2
            inst("COMM",8),
            inst("PUSHIS",0x4a2), #AN1c3. (looks weird but eh)
            inst("COMM",8),
            inst("PUSHIS",0x4a4), #AN1c4
            inst("COMM",8),
            inst("PUSHIS",0x4a5), #AN1c5
            inst("COMM",8),
            inst("PUSHIS",0x4c0), #Ginza splash
            inst("COMM",8),
            inst("PUSHIS",0x4c3), #Harumi Warehouse splash
            inst("COMM",8),
            inst("PUSHIS",0x510), #Ginza Underpass splash
            inst("COMM",8),
            inst("PUSHIS",0x512), #Underpass Manikin 1
            inst("COMM",8),
            inst("PUSHIS",0x513), #UM2
            inst("COMM",8),
            inst("PUSHIS",0x514), #UM3
            inst("COMM",8),
            inst("PUSHIS",0x515), #UM4
            inst("COMM",8),
            inst("PUSHIS",0x520), #Actual Ginza Underpass splash (What is actually 0x510?)
            inst("COMM",8),
            inst("PUSHIS",0x526), #Turns on encounters in Ginza Underpass. Combine with open underpass.
            inst("COMM",8),
            inst("PUSHIS",0x560), #Thor Gauntlet shorten
            inst("COMM",8),
            inst("PUSHIS",0x540), #Ikebukuro enter flag 1
            inst("COMM",8),
            inst("PUSHIS",0x54a), #Ikebukuro 2
            inst("COMM",8),
            inst("PUSHIS",0x931), #Ikebukuro 3
            inst("COMM",8),
            inst("PUSHIS",0x56c), #Ikebukuro 4
            inst("COMM",8),
            inst("PUSHIS",0x54b), #Ikebukuro 5
            inst("COMM",8),
            inst("PUSHIS",0x54c), #Ikebukuro 6
            inst("COMM",8),
            inst("PUSHIS",0x54d), #Ikebukuro 7
            inst("COMM",8),
            inst("PUSHIS",0x912), #Ikebukuro 8
            inst("COMM",8),
            inst("PUSHIS",0x4ec), #East Nihilo textbox. 4e0 should NOT be set.
            inst("COMM",8),
            inst("PUSHIS",0x4f4), #Kaiwan maze 1
            inst("COMM",8),
            inst("PUSHIS",0x4f5), #Kaiwan maze 2
            inst("COMM",8),
            inst("PUSHIS",0x4f6), #Kaiwan maze 3
            inst("COMM",8),
            inst("PUSHIS",0x700), #Kaiwan empty cube
            inst("COMM",8),
            inst("PUSHIS",0x6c5), #Kaiwan scene 1
            inst("COMM",8),
            inst("PUSHIS",0x6c6), #Kaiwan scene 2
            inst("COMM",8),
            inst("PUSHIS",0x6c7), #Kaiwan scene 3
            inst("COMM",8),
            inst("PUSHIS",0x580), #Kabukicho Splash
            inst("COMM",8),
            inst("PUSHIS",0x583), #Cutscene before Mizuchi
            inst("COMM",8),
            inst("PUSHIS",0x594), #Cutscene with Futomimi after Mizuchi
            inst("COMM",8),
            inst("PUSHIS",0x5a0), #Ikebukuro Tunnel Splash
            inst("COMM",8),
            #inst("PUSHIS",0x5e0), #Amala Network 2 Splash
            #inst("COMM",8), #Turned off because it's short and has a bunch of necessary code so I'm not going to bother with it yet. If I get to it I'll probably want to keep this off anyway.
            inst("PUSHIS",0x5eb), #Amala Network 2 Cutscene
            inst("COMM",8),
            inst("PUSHIS",0x43), #Amala Network 2 Cutscene 2
            inst("COMM",8),
            inst("PUSHIS",0x5ed), #Amala Network 2 Cutscene 3
            inst("COMM",8),
            inst("PUSHIS",0x42), #Amala Network 2 Cutscene 4
            inst("COMM",8),
            inst("PUSHIS",0x600), #Asakusa Tunnel Splash
            inst("COMM",8),
            inst("PUSHIS",0x640), #Obelisk Splash
            inst("COMM",8),
            inst("PUSHIS",0x650), #Sisters Talk at entrance (Consider to keep on, but change their models to the randomized boss)
            inst("COMM",8),
            inst("PUSHIS",0x46), #Obelisk flag 1
            inst("COMM",8),
            inst("PUSHIS",0x4e), #Obelisk flag 2
            inst("COMM",8),
            inst("PUSHIS",0x4c3), #Obelisk flag 3 (possibly Mara flag?)
            inst("COMM",8),
            inst("PUSHIS",0x50), #Hijiri cutscene post Obelisk
            inst("COMM",8),
            inst("PUSHIS",0x6e2), #Mifunashiro splash
            inst("COMM",8),
            inst("PUSHIS",0x6e5), #Mifunashiro cutscene
            inst("COMM",8),
            inst("PUSHIS",0x464), #Yoyogi Park 1
            inst("COMM",8),
            inst("PUSHIS",0x465), #Yoyogi Park 2
            inst("COMM",8),
            inst("PUSHIS",0x466), #Yoyogi Park 3
            inst("COMM",8),
            inst("PUSHIS",0x467), #Yoyogi Park 4
            inst("COMM",8),
            inst("PUSHIS",0x474), #Yoyogi Park 5
            inst("COMM",8),
            inst("PUSHIS",0x4b),  #Yuko in Yoyogi (no cutscene possible)
            inst("COMM",8),
            inst("PUSHIS",0x4d), #Hijiri in Asakusa cutscene
            inst("COMM",8),
            inst("PUSHIS",0x3dd), #Yoyogi Key
            inst("COMM",8),
            inst("PUSHIS",0x51), #Amala Temple dropping Hijiri cutscene
            inst("COMM",8),
            inst("PUSHIS",0x500), #Yurakucho Splash
            inst("COMM",8),
            inst("PUSHIS",0x506), #Auto-Shige (Kimon Stone location)
            inst("COMM",8),
            inst("PUSHIS",0x680), #Diet Building Splash
            inst("COMM",8),
            inst("PUSHIS",0x69E), #Diet Building Message 1
            inst("COMM",8),
            inst("PUSHIS",0x688), #Diet Building Message 2
            inst("COMM",8),
            inst("PUSHIS",0x689), #Diet Building Message 3
            inst("COMM",8),
            inst("PUSHIS",0x733), #Bishamon temple shorten
            inst("COMM",8),
            inst("PUSHIS",0x660), #ToK entrance cutscene
            inst("COMM",8),
            inst("PUSHIS",0x665), #Final room splash
            inst("COMM",8),
            inst("PUSHIS",0x760), #1st Kalpa splash
            inst("COMM",8),
            inst("PUSHIS",0x780), #2nd Kalpa splash
            inst("COMM",8),
            inst("PUSHIS",0x7a0), #3rd Kalpa splash
            inst("COMM",8),
            inst("PUSHIS",0x7c0), #4th Kalpa splash
            inst("COMM",8),
            inst("PUSHIS",0x7e0), #5th Kalpa splash
            inst("COMM",8),
            inst("PUSHIS",0x10f), #LoA lobby first cutscene
            inst("COMM",8),
            inst("PUSHIS",0x10c), #LoA lobby first cutscene flag 2
            inst("COMM",8),
            inst("PUSHIS",0x3ea), #Candelabrum of Sovereignty
            inst("COMM",8),
            inst("PUSHIS",0x75e), #LoA lobby initial visit flag
            inst("COMM",8),
            inst("PUSHIS",0x3d9), #Spoon
            inst("COMM",8),
            inst("PUSHIS",0x78a), #Metatron's voice in Kalpa 2
            inst("COMM",8),
            inst("PUSHIS",0x7b8), #Kalpa 3 Rider Cutscene
            inst("COMM",8),
            inst("PUSHIS",0x11d), #Met Dante in Kalpa 3
            inst("COMM",0x8),
            inst("PUSHIS",0x7b1), #Dante switch
            inst("COMM",0x8),
            inst("PUSHIS",0x7b3), #Dante switch
            inst("COMM",0x8),
            inst("PUSHIS",0x7b4), #Dante switch
            inst("COMM",0x8),
            inst("PUSHIS",0x7a6), #Dante textbox
            inst("COMM",0x8),
            inst("PUSHIS",0x7b9), #Dante textbox
            inst("COMM",0x8),
            inst("PUSHIS",0x7aa), #Dante textbox
            inst("COMM",0x8),
            inst("PUSHIS",0x7a8), #Dante textbox
            inst("COMM",0x8),
            inst("PUSHIS",0x7a7), #Dante textbox
            inst("COMM",0x8),
            inst("PUSHIS",0x110), #Said no to recruit Dante
            inst("COMM",0x8),
            #inst("PUSHIS",0x3f1), #Black Key (testing purposes)
            #inst("COMM",8),
            #inst("PUSHIS",0x3f2), #White Key (testing purposes)
            #inst("COMM",8),
            #inst("PUSHIS",0x3f3), #Red Key (testing purposes)
            #inst("COMM",8),
            #inst("PUSHIS",0x3f4), #Apocalypse Stone (unlocks white rider check - testing purposes)
            #inst("COMM",8),
            #inst("PUSHIS",0x3f5), #Golden Goblet (unlocks mother harlot check - testing purposes)
            #inst("COMM",8),
            #inst("PUSHIS",0x3f6), #Eggplant (unlocks mara check - testing purposes)
            #inst("COMM",8),
            #inst("PUSHIS",506), 
            #inst("COMM",0x66), 
            #Imported from 506
            #Story cutscenes
            inst("PUSHIS",18),
            inst("COMM",8),
            inst("PUSHIS",1),
            inst("COMM",8),
            inst("PUSHIS",3),
            inst("COMM",8),
            inst("PUSHIS",5),
            inst("COMM",8),
            inst("PUSHIS",976),
            inst("COMM",8),
            inst("PUSHIS",1066),
            inst("COMM",8),
            inst("PUSHIS",6),
            inst("COMM",8),
            inst("PUSHIS",7),
            inst("COMM",8),
            inst("PUSHIS",1094),
            inst("COMM",8),
            inst("PUSHIS",37),
            inst("COMM",8),
            inst("PUSHIS",40),
            inst("COMM",8),
            inst("PUSHIS",2325),
            inst("COMM",8),
            inst("PUSHIS",1086),
            inst("COMM",8),
            inst("PUSHIS",1059),
            inst("COMM",8),
            
            inst("PUSHIS",1), 
            inst("PUSHIS",15), #Sacred water
            inst("COMM",0x70), #Add item
            inst("PUSHIS",1), 
            inst("PUSHIS",10), #Soma
            inst("COMM",0x70), #Add item
            inst("PUSHIS",10),
            inst("PUSHIS",2), #Medicine
            inst("COMM",0x70), #Add item
            inst("PUSHIS",10),
            inst("PUSHIS",3), #Life Stone
            inst("COMM",0x70), #Add item
            inst("PUSHIS",10),
            inst("PUSHIS",55), #Light Ball
            inst("COMM",0x70), #Add item

            inst("PUSHIS",bonus_magatama), # bonus magatama
            inst("COMM",0x122), # give magatama
            
            #Open mode
            inst("PUSHIS",44), #Asakusa Front Door
            inst("COMM",8),
            inst("PUSHIS",43), #Mantra HQ East Door
            inst("COMM",8),
            inst("PUSHIS",1386), #^
            inst("COMM",8),
            inst("PUSHIS",36), #Ikebukuro Tunnel, maybe remove this one?
            inst("COMM",8),
            inst("PUSHIS",35), #^
            inst("COMM",8),
            inst("PUSHIS",53), #West Nihilo
            inst("COMM",8),
            #inst("PUSHIS",86), #Yurakucho Tunnel
            #inst("COMM",8),
            inst("PUSHIS",26), #East Nihilo
            inst("COMM",8),
            inst("PUSHIS",15), #East Nihilo (Hijiri)
            inst("COMM",8),
            inst("PUSHIS",84), #Mifunashiro
            inst("COMM",8),
            inst("PUSHIS",47), #
            inst("COMM",8),
            inst("PUSHIS",63), #Asakusa West
            inst("COMM",8),
            
            #Fusion flags
            inst("PUSHIS",2304), #aciel
            inst("COMM",8),
            inst("PUSHIS",2305), #albion
            inst("COMM",8),
            inst("PUSHIS",2306), #skadi
            inst("COMM",8),
            inst("PUSHIS",2307), #seraphs?
            inst("COMM",8),
            inst("PUSHIS",2308), #samael
            inst("COMM",8),
            inst("PUSHIS",2312), #girimehkala
            inst("COMM",8),
            inst("PUSHIS",2313), #thor
            inst("COMM",8),
            inst("PUSHIS",2314), #kaiwan
            inst("COMM",8),
            inst("PUSHIS",2315), #moirae sisters
            inst("COMM",8),
            inst("PUSHIS",2316), 
            inst("COMM",8),
            inst("PUSHIS",2317),
            inst("COMM",8),
            inst("PUSHIS",2318), #kin-ki
            inst("COMM",8),
            inst("PUSHIS",2319), #sui-ki
            inst("COMM",8),
            inst("PUSHIS",2320), #fuu-ki
            inst("COMM",8),
            inst("PUSHIS",2321), #ongyo-ki
            inst("COMM",8),
            inst("PUSHIS",2326), #mada
            inst("COMM",8),
            inst("PUSHIS",2327), #mot
            inst("COMM",8),
            inst("PUSHIS",2328), #surt
            inst("COMM",8),
            inst("PUSHIS",2329), #mithra
            inst("COMM",8),
            inst("PUSHIS",2330), #bishamon
            inst("COMM",8),
            inst("PUSHIS",2331), #metatron
            inst("COMM",8),
            inst("PUSHIS",2333), #pale rider
            inst("COMM",8),
            inst("PUSHIS",2334), #white rider
            inst("COMM",8),
            inst("PUSHIS",2335), #red rider
            inst("COMM",8),
            inst("PUSHIS",2336), #black rider
            inst("COMM",8),
            inst("PUSHIS",2337), #matador
            inst("COMM",8),
            inst("PUSHIS",2338), #hell biker
            inst("COMM",8),
            inst("PUSHIS",2339), #daisoujou
            inst("COMM",8),
            inst("PUSHIS",2340), #harlot
            inst("COMM",8),
            inst("PUSHIS",2341), #trumpeter
            inst("COMM",8),
            inst("PUSHIS",2342), #futomimi
            inst("COMM",8),
            inst("PUSHIS",2343), #sakahagi
            inst("COMM",8),
            inst("PUSHIS",2344), #beelzebub
            inst("COMM",8),
            inst("PUSHIS",2345), #black frost
            inst("COMM",8),
            #open mode
            inst("PUSHIS",9), #chiaki cutscene
            inst("COMM",8),
            inst("PUSHIS",1152), #shibuya splash
            inst("COMM",8),
            inst("PUSHIS",1216), #ginza splash
            inst("COMM",8),
            inst("PUSHIS",914), #ginza splash 2
            inst("COMM",8),
            inst("PUSHIS",1320), #accepted collector quest
            inst("COMM",8),
            inst("PUSHIS",1314), #ginza underpass cutscene
            inst("COMM",8),
            inst("PUSHIS",1315), 
            inst("COMM",8),
            inst("PUSHIS",1316),
            inst("COMM",8),
            inst("PUSHIS",1317),
            inst("COMM",8),
            inst("PUSHIS",1219), #harumi underpass cutscene
            inst("COMM",8),
            inst("PUSHIS",1344), #ikebukuro entrance cutscene
            inst("COMM",8),
            inst("PUSHIS",1354), #?
            inst("COMM",8),
            inst("PUSHIS",1388), #?
            inst("COMM",8),
            inst("PUSHIS",1346), #minor textbox
            inst("COMM",8),
            inst("PUSHIS",34), #isamu smacked
            inst("COMM",8),
            inst("PUSHIS",1376), #mantra entrance
            inst("COMM",8),
            #inst("PUSHIS",1248), #nihilo splash. Should not be set.
            inst("PUSHIS",23), #chiaki in ikebukuro
            inst("COMM",8),
            inst("PUSHIS",25), #agree with chiaki
            inst("COMM",8),
            inst("PUSHIS",1408), #kabukicho splash
            inst("COMM",8),
            inst("PUSHIS",984), #instant umugi
            inst("COMM",8),
            inst("PUSHIS",1412), #umugi
            inst("COMM",8),
            inst("PUSHIS",1413),
            inst("COMM",8),
            inst("PUSHIS",1414),
            inst("COMM",8),
            inst("PUSHIS",1415),
            inst("COMM",8),
            inst("PUSHIS",1440), #east ikebukuro
            inst("COMM",8),
            inst("PUSHIS",1449), 
            inst("COMM",8),
            inst("PUSHIS",1472), #asakusa entrance
            inst("COMM",8),
            inst("PUSHIS",1536), #asakusa tunnel
            inst("COMM",8),
            inst("PUSHIS",1141), #asakusa tunnel
            inst("COMM",8),
            inst("PUSHIS",1600), #obelisk entrance
            inst("COMM",8),
            inst("PUSHIS",1616), #obelisk sisters
            inst("COMM",8),
            inst("PUSHIS",1704), #amala temple entrance
            inst("COMM",8),
            #inst("PUSHIS",1696), #amala temple entrance. Should not be set
            inst("PUSHIS",1664),
            inst("COMM",8),
            inst("PUSHIS",1717), #divines text
            inst("COMM",8),
            inst("PUSHIS",1718), #kagutsuchi text
            inst("COMM",8),
            inst("PUSHIS",1760), #mifunashiro entrance
            inst("COMM",8),
            inst("PUSHIS",1925), #loki sidequest started
            inst("COMM",8), 
            inst("PUSHIS",4), #insert TDE flags before this line
            inst("COMM",0x158), #+4 stock
            inst("PUSHIS",0),
            inst("PUSHIS",0),
            inst("COMM",0x121), #Name MC
            inst("PUSHIS",1),
            inst("PUSHIS",1),
            inst("COMM",0x121), #Name
            inst("PUSHIS",1),
            inst("PUSHIS",2),
            inst("COMM",0x121),
            inst("PUSHIS",1),
            inst("PUSHIS",3),
            inst("COMM",0x121),
            inst("PUSHIS",616),
            inst("PUSHIS",15),
            inst("PUSHIS",1),
            inst("COMM",0x97),
            inst("PUSHIS",618),
            inst("COMM",0x66),
            inst("END",0)
        ]
       
        e601_bonus_insts = []   
        if config_settings.open_ikebukuro:
            e601_bonus_insts += [
                inst("PUSHIS", 0x3f7),
                inst("COMM", 0x8)
            ]

        if config_settings.open_yurakucho:
            e601_bonus_insts += [
                inst("PUSHIS", 0x56),
                inst("COMM", 0x8)
            ]
        
        e601_insts = e601_insts[:-21] + e601_bonus_insts + e601_insts[-21:]

        e601_obj.changeProcByIndex(e601_insts,[],0) #empty list is relative branch labels
        # convert the script object to a filelike object and add it to the dds3 file system
        e601_data = BytesIO(bytearray(e601_obj.toBytes()))
        self.dds3.add_new_file(custom_vals.SCRIPT_OBJ_PATH['e601'], e601_data)
        #Don't need to put it into a LB file because it is an event script, not a field script.

        # Shorten 618 (intro)
        # Cutscene removal in SMC f015

        # SMC area flag
        # get the uncompressed field script from the folder instead of the LB
        f015_obj = self.get_script_obj_by_path('/fld/f/f015/f015.bf')
        tri_preta_room_index = f015_obj.getProcIndexByLabel("012_start")
        f015_012_start_insts = [
            inst("PROC",tri_preta_room_index),
            inst("PUSHIS",0),
            inst("PUSHIS",0x21),
            inst("COMM",7), #Check flag
            inst("PUSHREG"), #Push the result of previous operation as a parameter, in this case, 0 == flagcheck(7)
            inst("EQ"), #Check if flag 0x21 is 0 (unset)
            inst("PUSHIS",0x452),
            inst("COMM",7),
            inst("PUSHREG"), #Check if flag 0x452 is 1 (set)
            inst("AND"), #If both
            inst("IF",0), #Branch to label number 0 in our label list if true
            inst("PUSHIS",0x21),
            inst("COMM",8), #Set flag 0x21
            inst("PUSHIS",0x1f7),
            inst("PUSHIS",0xf),
            inst("PUSHIS",1),
            inst("COMM",0x97), #Call next procedure index f (probably this one?)
            inst("PUSHIS",0x5D),
            inst("COMM",0x67), #Initiate battle 0x5D
            inst("END"), #Label: _END - Line number 19 (20th)
            inst("PUSHIS",0), #Line number 20 (21st) Label: _366
            inst("PUSHIS",0x453),
            inst("COMM",7),
            inst("PUSHREG"),
            inst("EQ"),
            inst("PUSHIS",0x452),
            inst("COMM",7),
            inst("PUSHREG"),
            inst("AND"),
            inst("IF",1), #Branch to END if (flag 0x453 is unset) is true
            inst("PUSHSTR",0), # - "01cam_01" - fixed camera
            inst("COMM",0x94), #Set cam
            inst("PUSHREG"),
            inst("COMM",0xA3),
            inst("PUSHIS",1),
            inst("MINUS"),
            inst("COMM",0x12), #Go to fixed camera.
            inst("COMM",1), #Open text box
            inst("PUSHIS",0xe),
            inst("COMM",0), #Print out message index e (You got pass)
            inst("COMM",2),
            inst("PUSHIS",0x3d1),
            inst("COMM",8), #Set flag 0x3d1
            inst("PUSHIS",0x453),
            inst("COMM",8), #Set flag 0x453
            inst("COMM",0x61), #Give player control back
            inst("END")
        ]
        f015_012_start_labels = [
            assembler.label("PRETA_FIGHT_DONE",20), #both needs to be changed if above procedure is shifted
            assembler.label("GATE_PASS_OBTAINED",19) #given number is line number
        ]
        f015_obj.changeProcByIndex(f015_012_start_insts, f015_012_start_labels, tri_preta_room_index)

        #Forneus
        forneus_room_index = f015_obj.getProcIndexByLabel("002_start") #index 18 / 0x12
        #Can't figure out what flag 769 is for. I'll just not set it and see what happens.
        #Flag 8 is definitely the defeat forneus flag.
        #000_dh_plus is the one that has the magatama text that is called after beating forneus. Proc index 60 / 0x3c
        f015_002_start_insts = [
            inst("PROC",forneus_room_index),
            inst("PUSHIS",0),
            inst("PUSHIS",0x8),
            inst("COMM",7), #Check Forneus fought flag
            inst("PUSHREG"),
            inst("EQ"),
            inst("IF",0), #Branch to first label if fought
            inst("PUSHIS",1),
            inst("PUSHIS",0x44f),
            inst("COMM",7), #2F check
            inst("PUSHREG"),
            inst("EQ"),
            inst("IF",0),
            inst("PUSHIS",8),
            inst("COMM",8), #Set Forneus fought flag
            inst("PUSHIS",0x1f4),
            inst("PUSHIS",0xf),
            inst("PUSHIS",1),
            inst("COMM",0x97), #Call next
            inst("PUSHIS",0xe),
            inst("COMM",0x67), #Fight Forneus
            inst("END"),
            inst("PUSHIX", 7),
            inst("COMM",0x16), #No idea what this does
            inst("END") #Label 0 here
        ]
        #print 0 positions: 002_01eve_04, 005_01eve_05, 007_01eve_06, 007_01eve_08
        f015_002_start_labels = [
            assembler.label("FORNEUS_DEAD",24)
        ]
        f015_obj.changeProcByIndex(f015_002_start_insts, f015_002_start_labels, forneus_room_index)

        f015_obj.changeMessageByIndex(assembler.message(self.get_reward_str("Forneus",world),"FORNEUS_REWARD"),0x5b)
        
        #000_dh_plus - flag insertion
        f015_forneus_reward_proc = f015_obj.getProcIndexByLabel('000_dh_plus')
        f015_forneus_reward_insts, f015_forneus_reward_labels = f015_obj.getProcInstructionsLabelsByIndex(f015_forneus_reward_proc) #Has no labels.
        f015_forneus_reward_insts = f015_forneus_reward_insts[:-1] + self.get_flag_reward_insts("Forneus",world) + [inst("END")]
        f015_obj.changeProcByIndex(f015_forneus_reward_insts,[],f015_forneus_reward_proc)
        
        f015_obj.changeMessageByIndex(assembler.message("What!? You're going to defeat^n^r"+self.get_checks_boss_name("Forneus",world)+"^p!?","F015_SINEN19_01"),0xf1)
        f015_obj.changeMessageByIndex(assembler.message("You're going to defeat^n^r"+self.get_checks_boss_name("Forneus",world)+"^p?^nRiiiiiiight!","F015_SINEN19_02"),0xf5)
        f015_obj.changeMessageByIndex(assembler.message("You really beat ^r"+self.get_checks_boss_name("Forneus",world)+"^p?","F015_SINEN19_05"),0xf9)
        f015_obj.changeMessageByIndex(assembler.message("What!? You're going to defeat^n^r"+self.get_checks_boss_name("Forneus",world)+"^p!?","BOSSMAE"),0x29)
        f015_obj.changeMessageByIndex(assembler.message("Amazing... You really beat ^r"+self.get_checks_boss_name("Forneus",world)+"^p!!","BOSSMAEFNASI"),0x2d)
        #Other messages that mention Forneus: 0x78, 0xa5, 0xa6, 0xb8, 0xba, 0xbe, 0xc1, 0xdb, 0xdc, 0xe5, 0x10a, 0x10b, 0x110
        f015_obj.changeMessageByIndex(assembler.message("You sense the presence of^n^r"+self.get_checks_boss_name("Black Rider",world)+"^p.","FIRE_YURE"),0x6e)
        
        #Black Rider
        f015_br_proc = f015_obj.getProcIndexByLabel('014_b_rider')
        f015_br_insts, f015_br_labels = f015_obj.getProcInstructionsLabelsByIndex(f015_br_proc)
        f015_br_insts[4] = inst("PUSHIS",0x3f4) #Change rider trigger check from 7b8 to key item
        f015_br_insts[7] = inst("PUSHIS",0x3f4) #"Remove" story trigger check. (Yuko in Obelisk cutscene)
        f015_obj.changeProcByIndex(f015_br_insts, f015_br_labels, f015_br_proc)

        f015_14_proc = f015_obj.getProcIndexByLabel('014_01eve_01')
        f015_14_insts = [
            inst("PROC",f015_14_proc),
            inst("PUSHIS",0x106), #Red Rider dead
            inst("COMM",7),
            inst("PUSHREG"),
            inst("PUSHIS",0x3f4), #Key item to enable Riders
            inst("COMM",7),
            inst("PUSHREG"),
            inst("PUSHIS",0),
            inst("PUSHIS",0x757), #Didn't already run away
            inst("COMM",7),
            inst("PUSHREG"),
            inst("EQ"),
            inst("PUSHIS",0),
            inst("PUSHIS",0x109), #Didn't already beat him
            inst("COMM",7),
            inst("PUSHREG"),
            inst("EQ"),
            inst("AND"),
            inst("AND"), 
            inst("AND"),
            inst("IF",0), #End label
            inst("COMM",0x60),
            inst("COMM",1),
            inst("PUSHIS",0x6f), #"Stay here?"
            inst("COMM",0),
            inst("PUSHIS",0),
            inst("PUSHIS",0x70), #">Yes/no"
            inst("COMM",3),
            inst("PUSHREG"),
            inst("EQ"),
            inst("IF",1), #Not quite end label
            inst("PUSHIS",0x109), #Fought flag
            inst("COMM",8),
            inst("PUSHIS",0x3e2), #Candelabra
            inst("COMM",8),
            inst("PUSHIS",0x920), #Fusion flag
            inst("COMM",8),
            inst("PUSHIS",0x2e9),
            inst("PUSHIS",0xf),
            inst("PUSHIS",1),
            inst("COMM",0x97), #Call next
            inst("PUSHIS",0x403),
            inst("COMM",0x67), #Fight Black Rider
            inst("END"),
            inst("PUSHIS",0x757),
            inst("COMM",8),
            inst("COMM",0x61),
            inst("END")
        ]
        f015_14_labels = [
            assembler.label("BRIDER_FOUGHT",47),
            assembler.label("BRIDER_RAN",44)
        ]
        if config_settings.menorah_groups: #Remove candelabra if randomized
            del f015_14_insts[33:35]
            f015_14_labels = [
                assembler.label("BRIDER_FOUGHT",45),
                assembler.label("BRIDER_RAN",42)
            ]
        f015_obj.changeProcByIndex(f015_14_insts, f015_14_labels, f015_14_proc)

        f015_brider_callback_str = "BR_CB"
        f015_brider_rwms_index = f015_obj.appendMessage(self.get_reward_str("Black Rider",world), "BR_REWARD")
        f015_br_rwms_insts = [
            inst("PROC",len(f015_obj.p_lbls().labels)),
            inst("COMM",0x60),
            inst("COMM",1),
            inst("PUSHIS",f015_brider_rwms_index),
            inst("COMM",0),
            inst("COMM",2),
            inst("COMM",0x61)
        ] + self.get_flag_reward_insts("Black Rider",world) + [
            inst("END")
        ]

        f015_obj.appendProc(f015_br_rwms_insts, [], f015_brider_callback_str)
        self.insert_callback('f015',0x3b0,f015_brider_callback_str)

        f015_lb = self.push_bf_into_lb(f015_obj, 'f015')
        self.dds3.add_new_file(custom_vals.LB0_PATH['f015'], f015_lb)
        if SCRIPT_DEBUG:
            self.script_debug_out(f015_obj,'f015.bf')

        #Cutscene removal in Shibuya f017
        f017_obj = self.get_script_obj_by_name('f017')
        #001_01eve_01 -> 009_start
        #normal bit check line of 001_01eve_01 is 0x483 on line 20. We want it to be a key item instead.
        #cut out 24-29 inclusive for FULL check. put in an AND instead
        f017_01_proc = f017_obj.getProcIndexByLabel('001_01eve_01')
        f017_01_insts, f017_01_labels = f017_obj.getProcInstructionsLabelsByIndex(f017_01_proc)
        #f017_01_insts[16] = inst("PUSHIS",0x3f6)
        #Fails if: 0x3f6 is not set. Also fails if 0x482 is set.
        #I need the negation of that though.
        f017_01_insert_insts = [
            inst("PUSHIS",0),
            inst("PUSHIS",0x3f6),
            inst("COMM",7),
            inst("PUSHREG"),
            inst("EQ"),
            inst("OR")
        ]
        precut = 19
        postcut = 30
        diff = postcut - precut
        f017_01_insts = f017_01_insts[:precut] + f017_01_insert_insts + f017_01_insts[postcut:]
        for l in f017_01_labels:
            if l.label_offset > precut:
                l.label_offset -= diff
                l.label_offset += len(f017_01_insert_insts)
        f017_obj.changeProcByIndex(f017_01_insts, f017_01_labels, f017_01_proc)

        #009_start also takes care of callback
        #"Baphomet and the manikins ran away"
        #check 0x488 to make sure mara wasn't already fought
        #cut out 10 - 420 inclusive
        #callback text id is 0x19
        #can hint about location of item with text id 0x1. "It seems fishy..."
        f017_09_proc = f017_obj.getProcIndexByLabel('009_start')
        f017_09_insts, f017_09_labels = f017_obj.getProcInstructionsLabelsByIndex(f017_09_proc)
        precut = 10
        postcut = 421
        diff = postcut - precut
        f017_09_insert_insts = self.get_flag_reward_insts("Mara",world)
        f017_09_insts = f017_09_insts[:precut] + f017_09_insert_insts + f017_09_insts[postcut:]
        for l in f017_09_labels:
            if l.label_offset > precut:
                if l.label_offset < postcut:
                    l.label_offset=0
                else:
                    l.label_offset-=diff
                    l.label_offset+=len(f017_09_insert_insts)
        f017_obj.changeProcByIndex(f017_09_insts, f017_09_labels, f017_09_proc)
        f017_obj.changeMessageByIndex(assembler.message(self.get_reward_str("Mara",world),"MARA_RWMS"),0x19)

        #TODO: Change fire text to White Rider boss name
        #Mara hint message
        f017_obj.changeMessageByIndex(assembler.message("> A ceremony is being prepared^nto summon ^r"+self.get_checks_boss_name("Mara",world)+"^p with an eggplant^nfrom ^g"+self.get_flag_reward_location_string(0x3f6,world)+"^p.","AYASII"),0x1)

        #001_w_rider for warning.
        #bit checks: 5c0, 7b8, 112 unset. Turns off 0x755.
        #7b8 is riders flag. We want that as a key item (3c3). 112 is defeating white rider.
        #5c0 is a flag that gets set when going into Shibuya. It is also the Asakusa entrance cutscene splash that we've set to be always on. Do we replicate this effect or ignore it? Ignoring it for now.
        f017_wr_proc = f017_obj.getProcIndexByLabel("001_w_rider")
        f017_wr_insts, f017_wr_labels = f017_obj.getProcInstructionsLabelsByIndex(f017_wr_proc)
        f017_wr_insts[4] = inst("PUSHIS",0x3f4)
        f017_obj.changeProcByIndex(f017_wr_insts, f017_wr_labels, f017_wr_proc)
        f017_wr2_proc = f017_obj.getProcIndexByLabel("003_pixy") #There are two of these. Booooo
        f017_wr2_insts, f017_wr2_labels = f017_obj.getProcInstructionsLabelsByIndex(f017_wr2_proc)
        f017_wr2_insts[4] = inst("PUSHIS",0x3f4)
        f017_obj.changeProcByIndex(f017_wr2_insts, f017_wr2_labels, f017_wr2_proc)
        #003_01eve_01
        #bit checks: 5c0, 7b8, 755 off, 112 off.
        #Run away: 755 on.
        #003_01eve_02 and 03 is dupe.
        f017_03_1_proc = f017_obj.getProcIndexByLabel("003_01eve_01")
        f017_03_2_proc = f017_obj.getProcIndexByLabel("003_01eve_02")
        f017_03_3_proc = f017_obj.getProcIndexByLabel("003_01eve_03")
        f017_03_insts = [ #See Daisoujou proc for more detailed comments on this proc
            inst("PROC",f017_03_1_proc),
            inst("PUSHIS",0x5c0), #"Story trigger" to enable Riders, which is already set from the start.
            inst("COMM",7),
            inst("PUSHREG"),
            inst("PUSHIS",0x3f4), #Key item to enable Riders
            inst("COMM",7),
            inst("PUSHREG"),
            inst("PUSHIS",0),
            inst("PUSHIS",0x755), #Didn't already run away
            inst("COMM",7),
            inst("PUSHREG"),
            inst("EQ"),
            inst("PUSHIS",0),
            inst("PUSHIS",0x112), #Didn't already beat him
            inst("COMM",7),
            inst("PUSHREG"),
            inst("EQ"),
            inst("AND"),
            inst("AND"), 
            inst("AND"),
            inst("IF",0), #End label
            inst("COMM",0x60),
            inst("COMM",1),
            inst("PUSHIS",0x35), #"Stay here?"
            inst("COMM",0),
            inst("PUSHIS",0),
            inst("PUSHIS",0x36), #">Yes/no"
            inst("COMM",3),
            inst("PUSHREG"),
            inst("EQ"),
            inst("IF",1), #Not quite end label
            inst("PUSHIS",0x112), #Fought flag
            inst("COMM",8),
            inst("PUSHIS",0x3e4), #Candelabra
            inst("COMM",8),
            inst("PUSHIS",0x91e), #Fusion flag
            inst("COMM",8),
            inst("PUSHIS",0x2e7),
            inst("PUSHIS",0x11),
            inst("PUSHIS",1),
            inst("COMM",0x97), #Call next
            inst("PUSHIS",0x401),
            inst("COMM",0x67), #Fight White Rider
            inst("END"),
            inst("PUSHIS",0x755),
            inst("COMM",8),
            inst("COMM",0x61),
            inst("END")
        ]
        f017_03_labels = [
            assembler.label("WRIDER_FOUGHT",47),
            assembler.label("WRIDER_RAN",44)
        ]
        if config_settings.menorah_groups: #Remove candelabra if randomized
            del f017_03_insts[33:35]
            f017_03_labels = [
                assembler.label("WRIDER_FOUGHT",45),
                assembler.label("WRIDER_RAN",42)
            ]

        f017_03_2_insts = [
            inst("PROC",f017_03_2_proc),
            inst("CALL",f017_03_1_proc),
            inst("END"),
        ]
        f017_03_3_insts = [
            inst("PROC",f017_03_3_proc),
            inst("CALL",f017_03_1_proc),
            inst("END"),
        ]
        f017_obj.changeProcByIndex(f017_03_insts, f017_03_labels, f017_03_1_proc)
        f017_obj.changeProcByIndex(f017_03_2_insts, [], f017_03_2_proc)
        f017_obj.changeProcByIndex(f017_03_3_insts, [], f017_03_3_proc)
        f017_wr_rwms_index = f017_obj.appendMessage(self.get_reward_str("White Rider",world),"WR_RWMS")
        f017_wr_callback_str = "WR_CB"
        f017_wr_callback_insts = [
            inst("PROC",len(f017_obj.p_lbls().labels)),
            inst("COMM",0x60),
            inst("COMM",1),
            inst("PUSHIS",f017_wr_rwms_index),
            inst("COMM",0),
            inst("COMM",2),
            inst("COMM",0x61),
        ] + self.get_flag_reward_insts("White Rider",world) + [
            inst("END")
        ]
        f017_obj.appendProc(f017_wr_callback_insts, [], f017_wr_callback_str)
        self.insert_callback('f017', 0x34c, f017_wr_callback_str)

        f017_obj.changeMessageByIndex(assembler.message("You sense the presence of^n^r"+self.get_checks_boss_name("White Rider",world)+"^p.","FIRE_YURE"),0x34)

        f017_lb = self.push_bf_into_lb(f017_obj, 'f017')
        self.dds3.add_new_file(custom_vals.LB0_PATH['f017'], f017_lb)

        if SCRIPT_DEBUG:
            self.script_debug_out(f017_obj,'f017.bf')

        #Hijiri in Ginza
        #Shorten e623. e623_trm
        e623_obj = self.get_script_obj_by_name('e623')
        e623_trm_proc = e623_obj.getProcIndexByLabel('e623_trm')
        e623_insts, e623_labels = e623_obj.getProcInstructionsLabelsByIndex(e623_trm_proc)
        #Turning the cutscene into a noop
        e623_insts[84] = inst("PUSHIS",1)
        e623_insts[85] = inst("COMM",0xe)
        e623_insts[89] = inst("PUSHIS",1)
        e623_insts[90] = inst("COMM",0xe)
        e623_obj.changeProcByIndex(e623_insts, e623_labels, e623_trm_proc)

        #Specter 1 hint
        e623_obj.changeMessageByIndex(assembler.message("Help me rid the Amala^nNetwork of ^r"+self.get_checks_boss_name("Specter 1",world)+"^p.","MSG_TRM_1"),0xd)        

        self.dds3.add_new_file(custom_vals.SCRIPT_OBJ_PATH['e623'],BytesIO(bytes(e623_obj.toBytes())))

        if SCRIPT_DEBUG:
            self.script_debug_out(self.get_script_obj_by_name('f018'),'f018.bf')
            self.script_debug_out(self.get_script_obj_by_name('e623'),'e623.bf')

        #Cutscene removal in Amala Network 1 f018
        #4A0, 4A1, 4A2 (looks weird but eh).
        #Shorten cutscene for 4A3 in 002_start - 4A7 gets set going in and unset immediately. Remove 55 - 164.
        f018_obj = self.get_script_obj_by_name('f018')
        f018_02_room = f018_obj.getProcIndexByLabel("002_start")
        f018_02_insts, f018_02_labels = f018_obj.getProcInstructionsLabelsByIndex(f018_02_room)
        precut = 55
        postcut = 164
        diff = postcut - precut
        f018_02_insts = f018_02_insts[:precut] + f018_02_insts[postcut:]
        for l in f018_02_labels:
            if l.label_offset > precut:
                l.label_offset-=diff
                if l.label_offset < 0:
                    l.label_offset = 1
                    #TODO: Do better than just move the labels
        f018_obj.changeProcByIndex(f018_02_insts, f018_02_labels, f018_02_room)
        #TODO: Change remaining text to make a little more sense.
        #"Damn"
        #0x16
        #TODO: Make it not softlock if 4A2 wasn't already set.

        #4A4 needs to be set for this
        #4A5 is ???
        #Shorten cutscene for 4A6 in 007_start (shared) - 4A8 gets set going in and unset immediately. Remove lines 91 - 272
        f018_07_room = f018_obj.getProcIndexByLabel("007_start")
        f018_07_insts, f018_07_labels = f018_obj.getProcInstructionsLabelsByIndex(f018_07_room)
        precut = 91
        postcut = 272
        diff = postcut - precut
        f018_07_insts = f018_07_insts[:precut] + f018_07_insts[postcut:]
        for l in f018_07_labels:
            if l.label_offset > precut:
                l.label_offset-=diff
                if l.label_offset < 0:
                    l.label_offset = 1
                    #TODO: Do better than just move the labels
                    
        f018_obj.changeProcByIndex(f018_07_insts, f018_07_labels, f018_07_room)

        #Shorten cutscene for Specter 1 in 009_start (shared) - 4AB is defeated flag. 4A9 gets set going in. 4AA gets set during cutscene.
        # 171 - 247
        #return: 4AB set
        f018_09_room = f018_obj.getProcIndexByLabel("009_start")
        f018_09_insts, f018_09_labels = f018_obj.getProcInstructionsLabelsByIndex(f018_09_room)
        f018_09_insert_insts = [ #Instructions to be inserted before fighting specter 1
            inst("PUSHSTR", 697), #"atari_hoji_01"
            inst("PUSHIS", 0),
            inst("PUSHIS", 0),
            inst("COMM",0x108), #Remove the barrier
            inst("PUSHIS", 2),
            inst("PUSHSTR", 711), #"md_hoji_01"
            inst("PUSHIS", 0),
            inst("PUSHIS", 0),
            inst("COMM",0x104), #Remove the visual barrier
            inst("PUSHIS", 0xe),
            inst("COMM", 8) #set flag 0xE
        ] + self.get_flag_reward_insts("Specter 1",world)
        #change 0x16 for specter 1 reward.
        f018_obj.changeMessageByIndex(assembler.message(self.get_reward_str("Specter 1",world),"SPEC1_REWARD"),0x27)
        #TODO: Change message to tell you that Specter 1 is there. "..Oh yeah, there's something you should know" 
        
        precut1 = 35
        postcut1 = 161
        precut2 = 171
        postcut2 = 247
        diff1 = postcut1 - precut1
        diff2 = postcut2 - precut2
        f018_09_insts = f018_09_insts[:precut1] + f018_09_insts[postcut1:precut2] + f018_09_insert_insts + f018_09_insts[postcut2:]
        for l in f018_09_labels:
            if l.label_offset > precut1:
                if l.label_offset > precut2:
                    l.label_offset-=diff2
                    l.label_offset+=len(f018_09_insert_insts)
                l.label_offset-=diff1
                if l.label_offset < 0:
                    l.label_offset = 1
                    #TODO: Do better than just move the labels
        f018_obj.changeProcByIndex(f018_09_insts, f018_09_labels, f018_09_room)
        #Change the end warp to LoA Lobby to Ginza in front of terminal.
        f018_wap = bytearray(self.dds3.get_file_from_path(custom_vals.WAP_PATH['f018']).read())
        f018_wap[0x2b02] = 0x13 #Ginza
        f018_wap[0x2b0f] = 0x34 #(change position string to pos_04)
        self.dds3.add_new_file(custom_vals.WAP_PATH['f018'],BytesIO(f018_wap))
        #For some reason it uses the WAP in the LB file, so we'll have to push it in there alongside the BF file.
        f018_lb_data = self.dds3.get_file_from_path(custom_vals.LB0_PATH['f018'])
        f018_lb = LB_FS(f018_lb_data)
        f018_lb.read_lb()
        f018_lb = f018_lb.export_lb({'BF': BytesIO(bytearray(f018_obj.toBytes())), 'WAP': BytesIO(f018_wap)})
        self.dds3.add_new_file(custom_vals.LB0_PATH['f018'], f018_lb)
        if SCRIPT_DEBUG:
            self.script_debug_out(f018_obj,'f018.bf')


        #reward message
        #flag insertion in pre-portion

        #75E gets set going into LoA Lobby.
        #4C2 gets set leaving LoA Lobby.

        #Cutscene removal in Ginza (Hijiri mostly) f019
        #Optional: Shorten Troll (already short)
        #Should be done as an entry point
        f019_obj = self.get_script_obj_by_name("f019")
        f019_troll_rwms_index = f019_obj.appendMessage(self.get_reward_str("Troll",world),"TROLL_REWARD")
        f019_troll_callback_str = "TROLL_CB"
        f019_troll_callback_insts = [
            inst("PROC",len(f019_obj.p_lbls().labels)),
            inst("COMM",0x60),
            inst("COMM",1),
            inst("PUSHIS",f019_troll_rwms_index),
            inst("COMM",0),
            inst("COMM",2),
            inst("COMM",0x61),
        ] + self.get_flag_reward_insts("Troll",world) + [
            inst("END")
        ]
        f019_obj.appendProc(f019_troll_callback_insts,[],f019_troll_callback_str)
        self.insert_callback('f019',0x1350,f019_troll_callback_str)

        f019_troll_proc = f019_obj.getProcIndexByLabel("006_start") #Change troll model to new boss
        f019_troll_insts, f019_troll_labels = f019_obj.getProcInstructionsLabelsByIndex(f019_troll_proc)
        f019_troll_insts[13] = inst("PUSHIS",self.get_checks_boss_id("Troll",world))
        f019_troll_insts[44] = inst("PUSHIS",self.get_checks_boss_id("Troll",world))
        f019_obj.changeProcByIndex(f019_troll_insts, f019_troll_labels, f019_troll_proc)
        
        f019_obj.changeMessageByIndex(assembler.message("> The door was locked by^n^r"+self.get_checks_boss_name("Troll",world)+"^p.^x> Will you unlock it?" ,"F019_DOOR01a"),0x51)        

        #Remove white rider from Ginza always
        f019_rider_flame_proc = f019_obj.getProcIndexByLabel("001_w_rider")
        f019_rider_flame_insts, f019_rider_flame_labels = f019_obj.getProcInstructionsLabelsByIndex(f019_rider_flame_proc)
        f019_rider_flame_insts[6] = inst("PUSHIS",0x113) #Switch flag to pale rider fought so it's never relevant
        f019_obj.changeProcByIndex(f019_rider_flame_insts, f019_rider_flame_labels, f019_rider_flame_proc)
        f019_rider_fight_proc = f019_obj.getProcIndexByLabel("001_01eve_01")
        f019_rider_fight_insts, f019_rider_fight_labels = f019_obj.getProcInstructionsLabelsByIndex(f019_rider_fight_proc)
        f019_rider_fight_insts[1] = inst("PUSHIS",0x113) #Switch flag to pale rider fought so it's never relevant
        f019_obj.changeProcByIndex(f019_rider_fight_insts, f019_rider_fight_labels, f019_rider_fight_proc)
        f019_rider_fight2_proc = f019_obj.getProcIndexByLabel("001_01eve_02")
        f019_rider_fight2_insts, f019_rider_fight2_labels = f019_obj.getProcInstructionsLabelsByIndex(f019_rider_fight2_proc)
        f019_rider_fight2_insts[1] = inst("PUSHIS",0x113) #Switch flag to pale rider fought so it's never relevant
        f019_obj.changeProcByIndex(f019_rider_fight2_insts, f019_rider_fight2_labels, f019_rider_fight2_proc)
        f019_rider_fight3_proc = f019_obj.getProcIndexByLabel("001_01eve_03") #There are 3 Ginza rider battles because why?
        f019_rider_fight3_insts, f019_rider_fight3_labels = f019_obj.getProcInstructionsLabelsByIndex(f019_rider_fight3_proc)
        f019_rider_fight3_insts[1] = inst("PUSHIS",0x113) #Switch flag to pale rider fought so it's never relevant
        f019_obj.changeProcByIndex(f019_rider_fight3_insts, f019_rider_fight3_labels, f019_rider_fight3_proc)
        
        f019_lb = self.push_bf_into_lb(f019_obj, 'f019')
        self.dds3.add_new_file(custom_vals.LB0_PATH['f019'], f019_lb)
        
        if SCRIPT_DEBUG:
            self.script_debug_out(f019_obj,'f019.bf')

        #Cutscene removal in Ginza Underpass f022
        #Shorten Matador
        #4C3 is Harumi Warehouse splash.
        #510 is Ginza underpass splash
        #512, 513, (517?), 514, 515 - Underpass Manikin cutscenes. 511 is underpass terminal.
        #522 - Gatewatch Manikin, 523 - Collector Manikin, 520 - Yes to Collector Manikin.
        #4C4 and 4C5 for Troll Cutscene. Should be shortened and not removed.
        #529 & 4D6 - Giving the bill to collector. 
        #4D6 unset talking to gatekeeper. Set: 526, 75C
        #11 set fighting Matador in e740 (is it?). After, set: 751 and 3E9. Also 921 and 108

        #Plan: Don't even call e740
        #Original Callback after e740 is 013_shuku_mes. Index 27 (0x1b)
        #Callback seems to work, so we can use 013_shuku_mes
        f022_obj = self.get_script_obj_by_name('f022')
        f022_mata_room = f022_obj.getProcIndexByLabel("013_01eve_01")
        f022_013_e1_insts = [
            inst("PROC",f022_mata_room),
            inst("PUSHIS",0),
            inst("PUSHIS",0x108),
            inst("COMM",7), #Check Matador fought flag
            inst("PUSHREG"),
            inst("EQ"),
            inst("IF",0), #Branch to label 0 if fought
            inst("PUSHIS",0x108),
            inst("COMM",8), #Set Matador fought flag
            inst("PUSHIS",0x751), #Possibly open LoA flag
            inst("COMM",8), 
            inst("PUSHIS",0x3e9), #Matador's Candelabra
            inst("COMM",8), 
            inst("PUSHIS",0x921), #Gets set, but not sure what it does? Maybe this is the textbox flag.
            inst("COMM",8),
            inst("PUSHIS",0x2e4),
            inst("PUSHIS",0x16),
            inst("PUSHIS",1),
            inst("COMM",0x97), #Call next
            inst("PUSHIS",0x404),
            inst("COMM",0x67), #Fight Matador
            inst("END"),#Label 0 here
        ]
        f022_013_e1_labels = [
            assembler.label("MATADOR_GONE",21)
        ]
        f022_mata_callback = f022_obj.getProcIndexByLabel("013_shuku_mes")
        f022_mata_callback_insts = [
            inst("PROC",f022_mata_callback),
            inst("COMM",0x60),
            inst("COMM",1),
            inst("PUSHIS",0x1d),
            inst("COMM",0),
            inst("COMM",2),
            inst("COMM",0x61),
        ] + self.get_flag_reward_insts("Matador",world) + [
            inst("END")
        ]
        f022_obj.changeMessageByIndex(assembler.message(self.get_reward_str("Matador",world),"MATA_REWARD"),0x1d)
        f022_obj.changeMessageByIndex(assembler.message("You sense the presence of^n^r"+self.get_checks_boss_name("Matador",world)+"^p.","F22_YURE"),0x1a)
        f022_rr_hint_msg = f022_obj.appendMessage("You sense the presence of^n^r"+self.get_checks_boss_name("Red Rider",world)+"^p.","RR_HINT")
        f022_obj.changeProcByIndex(f022_mata_callback_insts,[],f022_mata_callback)

        f022_obj.changeProcByIndex(f022_013_e1_insts, f022_013_e1_labels, f022_mata_room)
        
        f022_rr_proc = f022_obj.getProcIndexByLabel('010_r_rider')
        f022_rr_insts, f022_rr_labels = f022_obj.getProcInstructionsLabelsByIndex(f022_rr_proc)
        f022_rr_insts[4] = inst("PUSHIS",0x3f4) #Change rider trigger check from 7b8 to key item
        f022_rr_insts[46] = inst("PUSHIS",f022_rr_hint_msg)
        f022_obj.changeProcByIndex(f022_rr_insts, f022_rr_labels, f022_rr_proc)

        f022_10_proc = f022_obj.getProcIndexByLabel('010_01eve_01')
        f022_10_insts = [
            inst("PROC",f022_10_proc),
            inst("PUSHIS",0x112), #White Rider dead
            inst("COMM",7),
            inst("PUSHREG"),
            inst("PUSHIS",0x3f4), #Key item to enable Riders
            inst("COMM",7),
            inst("PUSHREG"),
            inst("PUSHIS",0),
            inst("PUSHIS",0x756), #Didn't already run away
            inst("COMM",7),
            inst("PUSHREG"),
            inst("EQ"),
            inst("PUSHIS",0),
            inst("PUSHIS",0x106), #Didn't already beat him
            inst("COMM",7),
            inst("PUSHREG"),
            inst("EQ"),
            inst("AND"),
            inst("AND"), 
            inst("AND"),
            inst("IF",0), #End label
            inst("COMM",0x60),
            inst("COMM",1),
            inst("PUSHIS",0x5a), #"Stay here?"
            inst("COMM",0),
            inst("PUSHIS",0),
            inst("PUSHIS",0x5b), #">Yes/no"
            inst("COMM",3),
            inst("PUSHREG"),
            inst("EQ"),
            inst("IF",1), #Not quite end label
            inst("PUSHIS",0x106), #Fought flag
            inst("COMM",8),
            inst("PUSHIS",0x3e3), #Candelabra
            inst("COMM",8),
            inst("PUSHIS",0x91f), #Fusion flag
            inst("COMM",8),
            inst("PUSHIS",0x2e8),
            inst("PUSHIS",0x16),
            inst("PUSHIS",1),
            inst("COMM",0x97), #Call next
            inst("PUSHIS",0x402),
            inst("COMM",0x67), #Fight Red Rider
            inst("END"),
            inst("PUSHIS",0x756),
            inst("COMM",8),
            inst("COMM",0x61),
            inst("END")
        ]
        f022_10_labels = [
            assembler.label("RRIDER_FOUGHT",47),
            assembler.label("RRIDER_RAN",44)
        ]
        if config_settings.menorah_groups: #Remove candelabra if randomized
            del f022_10_insts[33:35]
            f022_10_labels = [
                assembler.label("RRIDER_FOUGHT",45),
                assembler.label("RRIDER_RAN",42)
            ]
        f022_obj.changeProcByIndex(f022_10_insts, f022_10_labels, f022_10_proc)

        f022_rrider_callback_str = "RR_CB"
        f022_rrider_rwms_index = f022_obj.appendMessage(self.get_reward_str("Red Rider",world), "RR_REWARD")
        f022_rr_rwms_insts = [
            inst("PROC",len(f022_obj.p_lbls().labels)),
            inst("COMM",0x60),
            inst("COMM",1),
            inst("PUSHIS",f022_rrider_rwms_index),
            inst("COMM",0),
            inst("COMM",2),
            inst("COMM",0x61),
        ] + self.get_flag_reward_insts("Red Rider",world) + [
            inst("END")
        ]

        f022_obj.appendProc(f022_rr_rwms_insts, [], f022_rrider_callback_str)
        self.insert_callback('f022',0x1bc,f022_rrider_callback_str)
        
        f022_lb = self.push_bf_into_lb(f022_obj, 'f022')
        self.dds3.add_new_file(custom_vals.LB0_PATH['f022'], f022_lb)

        if SCRIPT_DEBUG:
            self.script_debug_out(f022_obj,'f022.bf')

        #Cutscene removal in Ikebukuro f023
        #913 set in Ikebukuro. 54b 54c 54d - 540, 549, 56C, 931, 75E
        #Shorten Daisoujou

        f023_obj = self.get_script_obj_by_name('f023')
        f023_03_room = f023_obj.getProcIndexByLabel("003_01eve_02")
        f023_03_insts = [
            inst("PROC",f023_03_room),
            inst("PUSHIS",0x1a), #Story trigger to enable Daisoujou
            inst("COMM",7),
            inst("PUSHREG"),
            inst("PUSHIS",0),
            inst("PUSHIS",0x753), #Didn't already run away
            inst("COMM",7),
            inst("PUSHREG"),
            inst("EQ"),
            inst("PUSHIS",0),
            inst("PUSHIS",0x107), #Didn't already beat him
            inst("COMM",7),
            inst("PUSHREG"),
            inst("EQ"),
            inst("AND"),
            inst("AND"), #If not (f[1a] == 1 and f[753] == 0 and f[107] == 0)
            inst("IF",0), #End label
            inst("COMM",0x60),#RM_FLD_CONTROL
            inst("COMM",1), #MSG_WND_DSP
            inst("PUSHIS",0x1d), #"Do you want to stay here"
            inst("COMM",0),
            inst("PUSHIS",0),
            inst("PUSHIS",0x1e), #Yes/no
            inst("COMM",3),
            inst("PUSHREG"),
            inst("EQ"),
            inst("IF",1), #If no is selected, go to label 1. Differs from label 0 in that you set 0x753
            inst("PUSHIS",0x3e7), #set 3e7, 923, 107
            inst("COMM",8),
            inst("PUSHIS",0x923),
            inst("COMM",8),
            inst("PUSHIS",0x107),
            inst("COMM",8),
            inst("PUSHIS",0x2e6),
            inst("PUSHIS",0x17),
            inst("PUSHIS",1),
            inst("COMM",0x97), #Call next
            inst("PUSHIS",0x406),
            inst("COMM",0x67), #Fight Daisoujou
            inst("END"),
            inst("PUSHIS",0x753),
            inst("COMM",8),
            inst("COMM",0x61),#GIVE_FLD_CONTROL
            inst("END")
        ]
        f023_03_labels = [
            assembler.label("DAISOUJOU_FOUGHT",43),
            assembler.label("DAISOUJOU_RAN",40)
        ]
        if config_settings.menorah_groups: #Remove candelabra if randomized
            del f023_03_insts[27:29]
            f023_03_labels = [
                assembler.label("DAISOUJOU_FOUGHT",41),
                assembler.label("DAISOUJOU_RAN",38)
            ]
        f023_obj.changeProcByIndex(f023_03_insts, f023_03_labels, f023_03_room)

        f023_03_room_2 = f023_obj.getProcIndexByLabel("003_01eve_01") #Completely copy-pasted from the above, but is triggered from a different position. Just call the other one dammit.
        f023_03_2_insts = [
            inst("PROC",f023_03_room_2),
            inst("CALL",f023_03_room),
            inst("END"),
        ]

        f023_obj.changeProcByIndex(f023_03_2_insts, [], f023_03_room_2)
        f023_daisoujou_callback_str = "DAI_CB"
        f023_daisoujou_rwms_index = f023_obj.appendMessage(self.get_reward_str("Daisoujou",world), "DAI_REWARD")

        f023_daisoujou_hint_msg = f023_obj.appendMessage("You sense the presence of^n^r"+self.get_checks_boss_name("Daisoujou",world)+"^p.","DAI_HINT")
        f023_03_start_proc = f023_obj.getProcIndexByLabel("003_daisojo")
        f023_03_start_insts, f023_03_start_labels = f023_obj.getProcInstructionsLabelsByIndex(f023_03_start_proc)
        f023_03_start_insts[42] = inst("PUSHIS",f023_daisoujou_hint_msg)
        f023_obj.changeProcByIndex(f023_03_start_insts, f023_03_start_labels, f023_03_start_proc)

        f023_proclen = len(f023_obj.p_lbls().labels)
        f023_daisoujou_rwmspr_insts = [ #reward message proc
            inst("PROC",f023_proclen),
            inst("COMM",0x60),
            inst("COMM",1),
            inst("PUSHIS",f023_daisoujou_rwms_index),
            inst("COMM",0),
            inst("COMM",2),
            inst("COMM",0x61),
        ] + self.get_flag_reward_insts("Daisoujou",world) + [
            inst("END")
        ]
        f023_obj.appendProc(f023_daisoujou_rwmspr_insts, [], f023_daisoujou_callback_str)
        self.insert_callback('f023',0x284,f023_daisoujou_callback_str)
        #seek to 0x284 of f023.wap. write 02 then "DAI_RWMSPR"

        f023_obj.changeMessageByIndex(assembler.message("I've come here to join the Mantra,^nso that I can become just like^nthe great King, hee ho!^n............^n^xBut, I'm too scared to go in, hee ho!^n^r"+self.get_checks_boss_name("Dante 1",world)+"^p's on the roof ho." ,"F023_HIHO"),0x6f)        
        
        #Remove white rider from Ikebukero always
        f023_rider_flame_proc = f023_obj.getProcIndexByLabel("001_w_rider")
        f023_rider_flame_insts, f023_rider_flame_labels = f023_obj.getProcInstructionsLabelsByIndex(f023_rider_flame_proc)
        f023_rider_flame_insts[6] = inst("PUSHIS",0x113) #Switch flag to pale rider fought so it's never relevant
        f023_obj.changeProcByIndex(f023_rider_flame_insts, f023_rider_flame_labels, f023_rider_flame_proc)
        f023_rider_fight_proc = f023_obj.getProcIndexByLabel("006_01eve_02")
        f023_rider_fight_insts, f023_rider_fight_labels = f023_obj.getProcInstructionsLabelsByIndex(f023_rider_fight_proc)
        f023_rider_fight_insts[1] = inst("PUSHIS",0x113) #Switch flag to pale rider fought so it's never relevant
        f023_obj.changeProcByIndex(f023_rider_fight_insts, f023_rider_fight_labels, f023_rider_fight_proc)
        
        #pushis 0x32a, comm 0x66 is call dante
        #set bit 0x100
        #dante start code is short enough I'll just rewrite the whole thing
        f023_01_dante_proc = f023_obj.getProcIndexByLabel("001_01eve_03")
        f023_01_dante_insts = [
            inst("PROC",f023_01_dante_proc),
            inst("PUSHIS",0),
            inst("PUSHIS",0x100),
            inst("COMM",7),#Check that Dante isn't beaten
            inst("PUSHREG"),
            inst("EQ"),
            inst("PUSHIS",0x549),
            inst("COMM",7),#Check that Thor is beaten
            inst("PUSHREG"),
            inst("AND"),
            inst("IF",0),#end proc if not both
            inst("PUSHIS",0x100),
            inst("COMM",8), #Set 0x100
            inst("PUSHIS",0x2d3),
            inst("PUSHIS",0x17),
            inst("PUSHIS",1),
            inst("COMM",0x97),
            inst("PUSHIS",1033),
            inst("COMM",0x67), #Fight Dante
            inst("END")
        ]
        f023_01_dante_labels = [
            assembler.label("DANTE_FOUGHT",19)
        ]
        f023_obj.changeProcByIndex(f023_01_dante_insts, f023_01_dante_labels, f023_01_dante_proc)

        f023_dante_callback_str = "DANTE_CB"
        f023_dante_reward_index = f023_obj.appendMessage(self.get_reward_str("Dante 1",world), "DANTE_REWARD")
        f023_dante_reward_insts = [
            inst("PROC",f023_proclen + 1), #+1 from Daisoujou one.
            inst("COMM",0x60),
            inst("COMM",1),
            inst("PUSHIS",f023_dante_reward_index),
            inst("COMM",0),
            inst("COMM",2),
            inst("COMM",0x61),
        ] + self.get_flag_reward_insts("Dante 1",world) + [
            inst("END")
        ]
        f023_obj.appendProc(f023_dante_reward_insts, [], f023_dante_callback_str)
        self.insert_callback('f023',0x220,f023_dante_callback_str)

        f023_dante_hint_msg = f023_obj.appendMessage("You sense the presence of^n^r"+self.get_checks_boss_name("Dante 1",world)+"^p.","DANTE1_HINT")
        f023_01_start_proc = f023_obj.getProcIndexByLabel("001_dantesign")
        f023_01_start_insts, f023_01_start_labels = f023_obj.getProcInstructionsLabelsByIndex(f023_01_start_proc)
        f023_01_start_insts[47] = inst("PUSHIS",f023_dante_hint_msg)
        f023_obj.changeProcByIndex(f023_01_start_insts, f023_01_start_labels, f023_01_start_proc)
        
        f023_lb = self.push_bf_into_lb(f023_obj, 'f023')
        self.dds3.add_new_file(custom_vals.LB0_PATH['f023'], f023_lb)

        if SCRIPT_DEBUG:
            self.script_debug_out(f023_obj,'f023.bf')

        #Cutscene removal in Mantra HQ f024
        #560 on. Put into jail cell scene.
        #Shorten Thor Gauntlet
        #   We can use 001_start to optionally warp to Thor Gauntlet. All it has is the "Chiaki Left" message, which we just straight up don't need. It uses flag 0x572.

        f024_obj = self.get_script_obj_by_name('f024')
        f024_01_room = f024_obj.getProcIndexByLabel("001_start")
        f024_thor_gauntlet_msg_index = f024_obj.appendMessage("Do you want to go directly to the Thor gauntlet? It starts with ^r"+self.get_checks_boss_name("Orthrus",world)+"^p.", "THOR_GAUNTLET_MSG")
        f024_thor_gauntlet_msg_no_index = f024_obj.appendMessage("If you would like to do the Thor gauntlet, go to the center room^non the 3rd floor.", "THOR_GAUNTLET_MSG_NO")
        f024_yesno_sel = 174 #that is the literal label name

        f024_01_insts = [
            inst("PROC",f024_01_room),
            inst("PUSHIS", 0),
            inst("PUSHIS", 0x572), #Make sure this gets set when you fight Thor.
            inst("COMM", 7),
            inst("PUSHREG"),
            inst("EQ"),
            inst("IF", 0), #End label
            inst("PUSHIS", 0x572), 
            inst("COMM", 8), #set the bit to not show the messsage again.
            inst("COMM", 0x60),
            inst("COMM", 1),
            inst("PUSHIS", f024_thor_gauntlet_msg_index),
            inst("COMM", 0),
            inst("PUSHIS",0),
            inst("PUSHIS", f024_yesno_sel),
            inst("COMM", 3),
            inst("PUSHREG"),
            inst("EQ"),
            inst("IF",1), #Semi-end label. Show the "no" textbox and give control back.
            inst("COMM", 0x61),
            inst("COMM", 2),
            inst("PUSHIS",0x565),
            inst("COMM",0x8), #TODO in here. Close the Thor gauntlet jail if that setting is on.
            inst("PUSHIS",0x1f4),
            inst("PUSHIS",0x18),
            inst("PUSHIS",0x1),
            inst("COMM",0x97),
            inst("PUSHIS",0x53),
            inst("COMM",0x67),
            inst("END"),
            inst("PUSHIS", f024_thor_gauntlet_msg_no_index),
            inst("COMM",0),
            inst("COMM", 0x61),
            inst("COMM", 2),
            inst("END")
        ]
        f024_01_labels = [
            assembler.label("_01_END",34),
            assembler.label("_01_NO", 30)
        ]

        f024_obj.changeProcByIndex(f024_01_insts, f024_01_labels, f024_01_room)

        f024_10_room = f024_obj.getProcIndexByLabel("010_start")
        f024_10_insts, f024_10_labels = f024_obj.getProcInstructionsLabelsByIndex(f024_10_room)
        f024_10_insert_insts = [
            inst("PUSHIS", self.get_checks_boss_id("Orthrus",world)), 
            inst("PUSHIS",6),
            inst("COMM",0x15),
            inst("PUSHREG"),
            inst("POPLIX",0x3a), #store the result in a global variable
            inst("PUSHSTR",1576), #01pos_12
            inst("COMM",0x94),
            inst("PUSHREG"),
            inst("PUSHLIX",0x3a),
            inst("COMM",0x4a),
            inst("PUSHLIX",0x3a),
            inst("COMM",0x21e)
        ]
        f024_orthrus_rwms = f024_obj.appendMessage(self.get_reward_str("Orthrus",world),"ORTHRUS_RWMS")
        f024_10_insert_insts_yaksini = [
            inst("PUSHIS", self.get_checks_boss_id("Yaksini",world)), 
            inst("PUSHIS",6),
            inst("COMM",0x15),
            inst("PUSHREG"),
            inst("POPLIX",0x3b), #store the result in a global variable
            inst("PUSHSTR",1576), #01pos_12
            inst("COMM",0x94),
            inst("PUSHREG"),
            inst("PUSHLIX",0x3b),
            inst("COMM",0x4a),
            inst("PUSHLIX",0x3b),
            inst("COMM",0x21e),
            inst("COMM",1),
            inst("PUSHIS",f024_orthrus_rwms), #Orthrus reward message
            inst("COMM",0),
            inst("COMM",2)
        ] + self.get_flag_reward_insts("Orthrus",world)
        f024_yaksini_rwms = f024_obj.appendMessage(self.get_reward_str("Yaksini",world),"YAKSINI_RWMS")
        f024_10_insert_insts_thor_pre = [
            inst("PUSHIS", self.get_checks_boss_id("Thor 1",world)), #Thor's ID
            inst("PUSHIS",6),
            inst("COMM",0x15),
            inst("PUSHREG"),
            inst("POPLIX",0x39), #store the result in a global variable
            inst("PUSHSTR",1576), #01pos_12
            inst("COMM",0x94),
            inst("PUSHREG"),
            inst("PUSHLIX",0x39),
            inst("COMM",0x4a),
            inst("PUSHLIX",0x39),
            inst("COMM",0x21e),
            inst("COMM",1),
            inst("PUSHIS",f024_yaksini_rwms), #Yaksini reward message
            inst("COMM",0),
            inst("COMM",2)
        ] + self.get_flag_reward_insts("Yaksini",world)
        #from  726-881
        f024_obj.changeMessageByIndex(assembler.message(self.get_reward_str("Thor 1",world),"THOR_REWARD"),97)
        f024_10_insert_insts_thor_post = [ #double-check the flags here. Dante might not spawn.
            inst("COMM",0x60), #remove player control
            inst("PUSHIS",0x567), #Don't fight Thor in here again.
            inst("COMM",8),
            inst("PUSHIS",0x840), #??? Flag on
            inst("COMM",8),
            inst("PUSHIS",0x549), #Dante Flag. 0x100 needs to not be set for this to work correctly.
            inst("COMM",8),
            inst("PUSHIS",0x581), #Kabukicho terminal so Dante 1 doesn't softlock
            inst("COMM",8),
            inst("COMM",1), #display message window
            inst("PUSHIS",97), #Magatama get message
            inst("COMM",0),
            inst("COMM",2), #close message window
            inst("PUSHIS",0x21),
            inst("COMM",0x20f)#warp
        ]+ self.get_flag_reward_insts("Thor 1",world)
        
        #flag insertion
        #this will be a headache
        #0x565 is Orthrus fought.
        #0x566 is Yaksini fought. Cutscnee is 406-485 inclusive
        #0x567 is Thor fought.
        precut1 = 125
        postcut1 = 335
        precut1p5 = 404
        postcut1p5 = 486
        precut2 = 549 
        postcut2 = 649
        precut3 = 726
        postcut3 = 881
        diff1 = (postcut1 - precut1) - len(f024_10_insert_insts)
        diff1p5 = (postcut1p5 - precut1p5) - len(f024_10_insert_insts_yaksini)
        diff2 = (postcut2 - precut2) - len(f024_10_insert_insts_thor_pre)
        diff3 = (postcut3 - precut3) - len(f024_10_insert_insts_thor_post)

        f024_10_insts = f024_10_insts[:precut1] + f024_10_insert_insts + f024_10_insts[postcut1:precut1p5] + f024_10_insert_insts_yaksini + f024_10_insts[postcut1p5:precut2] + f024_10_insert_insts_thor_pre + f024_10_insts[postcut2:precut3] + f024_10_insert_insts_thor_post + f024_10_insts[postcut3:]

        for l in f024_10_labels:
            if l.label_offset > precut1:
                if l.label_offset < postcut1:
                    l.label_offset=1
                else:
                    if l.label_offset > precut1p5:
                        if l.label_offset < postcut1p5:
                            l.label_offset=1
                        else:
                            if l.label_offset > precut2:
                                if l.label_offset < postcut2:
                                    l.label_offset = 1
                                else:
                                    if l.label_offset > precut3:
                                        if l.label_offset < postcut3:
                                            l.label_offset = 1
                                        else:
                                            l.label_offset-=diff3
                                    l.label_offset-=diff2
                            l.label_offset-=diff1p5
                    l.label_offset-=diff1
                if l.label_offset < 0:
                    l.label_offset = 1
                    #TODO: Do better than just move the labels

        f024_obj.changeProcByIndex(f024_10_insts, f024_10_labels, f024_10_room)
        
        #f024_names = f024_obj.sections[3].names.names
        #f024_yaksini_name_index = f024_names.index("Yaksini")
        #f024_names[f024_yaksini_name_index] = self.get_checks_boss_name("Yaksini",world)
        #f024_yaksini_name_len_diff = len(self.get_checks_boss_name("Yaksini",world)) - 7
        #f024_names_pointers = f024_obj.sections[3].names.names_pointers
        #for i in range(f024_yaksini_name_index + 1, len(f024_names_pointers)):
        #    f024_names_pointers[i] = f024_names_pointers[i] + f024_yaksini_name_len_diff
        #f024_obj.sections[3].m_size += f024_yaksini_name_len_diff
        #f024_obj.sections[3].rolling_pointer += f024_yaksini_name_len_diff
        #f024_obj.sections[4].offset += f024_yaksini_name_len_diff
        f024_obj.changeNameByLookup("Orthrus", self.get_checks_boss_name("Orthrus",world, immersive=True))
        f024_obj.changeNameByLookup("Yaksini", self.get_checks_boss_name("Yaksini",world, immersive=True))
        f024_obj.changeNameByLookup("Thor", self.get_checks_boss_name("Thor 1",world, immersive=True))
        f024_yaksini_name_id = f024_obj.sections[3].messages[0x59].name_id
        f024_yaksini_message = assembler.message("Just beating "+self.get_checks_boss_name("Orthrus",world, immersive=True)+" isn't going to^noverturn the decision.^n^xYour sentence is death...^nAhh... I want to cut you up right now!^n^xBut, I'll give you some time.^nMake it fun for me." ,"K_TARA_01")
        f024_yaksini_message.name_id = f024_yaksini_name_id
        f024_obj.changeMessageByIndex(f024_yaksini_message,0x59)
        f024_thor_name_id = f024_obj.sections[3].messages[0x5b].name_id
        f024_thor_message = assembler.message("I am "+self.get_checks_boss_name("Thor 1",world, immersive=True)+".^n^xI commend your ability to fight.^n^xBut...^n^xWill your power work against me?^n^xMy hammer shall be the judge.^n^xI will give you time to prepare." ,"K_TORU_01")
        f024_thor_message.name_id = f024_thor_name_id
        f024_obj.changeMessageByIndex(f024_thor_message,0x5b)  


        f024_lb = self.push_bf_into_lb(f024_obj, 'f024')

        self.dds3.add_new_file(custom_vals.LB0_PATH['f024'], f024_lb)
        self.dds3.add_new_file(custom_vals.LB0_PATH['f024b'], f024_lb) #for some reason there's regular, b and c
        self.dds3.add_new_file(custom_vals.LB0_PATH['f024c'], f024_lb)

        if SCRIPT_DEBUG:
            self.script_debug_out(f024_obj,'f024.bf')

        #Cutscene removal in East Nihilo f020
        #Shorten Koppa & Incubus encounter
        #Fix visual puzzle bug.
        #Shorten Berith cutscene - Add text box for Berith reward. (0xf4 in f020.wap)
        #How to do Kaiwans??? - Automatically have all switches already hit?
        #Shorten spiral staircase down cutscene
        #Shorten Ose
        #018 is 1st block maze
        #019 is 2nd block maze
        #020 is 3rd block maze with kaiwans

        #001_start, 002_start, 014_start - cut these completely. They turn on the 0x4e0 flag for initializing the block puzzles. 001 works (which is vanilla behavior) but has a cutscene associated with it. 002 and 014 also set the flag but don't do the stuff needed. The stuff done with the 4e0 flag also appears in 018 so we'll just use that code (it'd be ideal to insert it there, but it's already there).
        f020_obj = self.get_script_obj_by_name('f020')
        f020_01_room = f020_obj.getProcIndexByLabel("001_start")
        f020_01_insts = [
            inst("PROC",f020_01_room),
            inst("END")
        ]
        f020_02_room = f020_obj.getProcIndexByLabel("002_start")
        f020_02_insts = [
            inst("PROC",f020_02_room),
            inst("END")
        ]
        f020_14_room = f020_obj.getProcIndexByLabel("014_start")
        f020_14_insts = [
            inst("PROC",f020_14_room),
            inst("END")
        ]
        no_labels = []
        f020_obj.changeProcByIndex(f020_01_insts, no_labels, f020_01_room)
        f020_obj.changeProcByIndex(f020_02_insts, no_labels, f020_02_room)
        f020_obj.changeProcByIndex(f020_14_insts, no_labels, f020_14_room)

        #008_start - koppa / incubus. cut 47 - 179
        f020_08_room = f020_obj.getProcIndexByLabel("008_start")
        f020_08_insts, f020_08_labels = f020_obj.getProcInstructionsLabelsByIndex(f020_08_room)
        precut = 48
        postcut = 179
        diff = postcut-precut

        #turn on 4eb, submerge the floor, display message saying the kilas were inserted
        #kilas: 3d2, 3d3, 3d4, 3d5
        #inserted kilas: 4ea, 4e7, 4e8, 4e9
        #start poplix with 0x58
        f020_08_auto_kila_label_index = len(f020_08_labels)
        f020_08_insert_insts_autokilacheck = [
            #if (4e7 or 3d2) and (4ea or 3d3) and (4e8 or 3d4) and (4e9 or 3d5):
            inst("PUSHIS",0x4e7), #Kila 1 inserted or in inventory
            inst("COMM",7),
            inst("PUSHREG"),
            inst("POPLIX",0x58),
            inst("PUSHIS",0x3d2),
            inst("COMM",7),
            inst("PUSHREG"),
            inst("PUSHLIX",0x58),
            inst("OR"),
            inst("POPLIX",0x60),

            inst("PUSHIS",0x4ea), #Kila 2 inserted or in inventory
            inst("COMM",7),
            inst("PUSHREG"),
            inst("POPLIX",0x5a),
            inst("PUSHIS",0x3d3),
            inst("COMM",7),
            inst("PUSHREG"),
            inst("PUSHLIX",0x5a),
            inst("OR"),
            inst("POPLIX",0x61),

            inst("PUSHIS",0x4e8), #Kila 3 inserted or in inventory
            inst("COMM",7),
            inst("PUSHREG"),
            inst("POPLIX",0x5c),
            inst("PUSHIS",0x3d4),
            inst("COMM",7),
            inst("PUSHREG"),
            inst("PUSHLIX",0x5c),
            inst("OR"),
            inst("POPLIX",0x62),

            inst("PUSHIS",0x4e9), #Kila 4 inserted or in inventory
            inst("COMM",7),
            inst("PUSHREG"),
            inst("POPLIX",0x5e),
            inst("PUSHIS",0x3d5),
            inst("COMM",7),
            inst("PUSHREG"),
            inst("PUSHLIX",0x5e),
            inst("OR"),
            inst("POPLIX",0x63),

            inst("PUSHIS",0x4eb), #Haven't completed insertion yet
            inst("COMM",7),
            inst("PUSHREG"),
            inst("PUSHIS",0),
            inst("EQ"),
            inst("POPLIX",0x64),
            
            inst("PUSHIS",0x4e3), #4e3 set and 6d9 unset. For Koppa / Incubus. (Note: Possibly doesn't work, but doesn't seem to harm things either way. It's also a super edge-case scenario for randomizing kilas in with other stuff.)
            inst("COMM",7),
            inst("PUSHREG"),
            inst("PUSHIS",0x6d9),
            inst("COMM",7),
            inst("PUSHREG"),
            inst("PUSHIS",0),
            inst("EQ"),
            inst("AND"),
            inst("PUSHIS",0),
            inst("EQ"),
            inst("POPLIX",0x65),

            #58 := 4e7, 59 := 3d2, 5a := 4ea, 5b := 3d3, 5c := 4e8, 5d := 3d4, 5e := 4e9, 5f := 3d5
            inst("PUSHLIX",0x60),
            inst("PUSHLIX",0x61),
            inst("AND"),
            inst("PUSHLIX",0x62),
            inst("AND"),
            inst("PUSHLIX",0x63),
            inst("AND"),
            inst("PUSHLIX",0x64),
            inst("AND"),
            inst("PUSHLIX",0x65),
            inst("AND"),
            inst("PUSHIS",0),
            inst("EQ"),
            inst("IF",f020_08_auto_kila_label_index)
        ]
        for l in f020_08_labels:
            if l.label_offset > precut:
                l.label_offset-=diff
                if l.label_offset < 0:
                    l.label_offset = 1
            l.label_offset += len(f020_08_insert_insts_autokilacheck)
        f020_08_auto_kila_label_offset = len(f020_08_insts) + len(f020_08_insert_insts_autokilacheck) - diff
        f020_08_labels.append(assembler.label("AUTO_INSERT_KILA",f020_08_auto_kila_label_offset))
        auto_kila_text = f020_obj.appendMessage("Kilas automatically inserted.", "AUTO_KILA")
        f020_08_insert_insts_autokila_do = [
            inst("END"),#My math is off by one so instead of making it correct I'm adding what's supposed to be the instruction before to here to make it work. :)
            inst("COMM",0x60),
            inst("COMM",1),
            inst("PUSHIS",auto_kila_text),
            inst("COMM",0),
            inst("COMM",2),#first display a the message

            inst("PUSHIS",0), #Mostly copied code. It works but I don't even know what half of this does.
            inst("PUSHSTR",1457), #path_hoji_01
            inst("COMM",0x94), 
            inst("PUSHREG"),
            inst("PUSHSTR",1443), #atari_hoji_01
            inst("COMM",0x94),
            inst("PUSHREG"),
            inst("COMM",0x6b),
            inst("PUSHSTR",1470), #atari_hoji_02
            inst("PUSHIS",0),
            inst("PUSHIS",0),
            inst("COMM",0x107),
            inst("PUSHIS",0),
            inst("PUSHSTR",1484), #md_hoji_03
            inst("PUSHIS",0),
            inst("PUSHIS",0),
            inst("COMM",0x104),
            inst("PUSHIS",0x64),
            inst("COMM",0x215),
            inst("PUSHIS",1),
            inst("PUSHSTR",1495), #md_hoji_04
            inst("PUSHIS",0),
            inst("PUSHIS",0),
            inst("COMM",0x103),
            inst("PUSHIS",1),
            inst("PUSHIS",8),
            inst("PUSHIS",0),
            inst("COMM",0x112),
            inst("PUSHIS",3),
            inst("PUSHIS",8),
            inst("PUSHIS",0),
            inst("COMM",0x111),
            inst("PUSHIS",0x4eb),
            inst("COMM",8),
            
            inst("COMM",0x61),
            inst("END")
        ]

        f020_08_insts = [f020_08_insts[0]] + f020_08_insert_insts_autokilacheck + f020_08_insts[1:precut] + f020_08_insts[postcut:-1] + f020_08_insert_insts_autokila_do
        #TODO: make sure 4e0 is NOT set in e506, or replace it altogether.
        f020_obj.changeProcByIndex(f020_08_insts, f020_08_labels, f020_08_room)
        #Cut waits on switches. These numbers are the index of the pushis instruction with the next one being the comm e (wait) instruction. 
        f020_18_01_waits = [47,58,67,76,146,215,220, 234, 246]
        f020_18_02_waits = [47,58,64,69,78,135,191,196,210,222]
        f020_19_01_waits = [47,58,67,76,130,183,188,202,214]
        f020_19_02_waits = [47,58,67,76,121,165,170,184,196]
        f020_19_03_waits = [47,58,67,76,130,183,188,202,214]
        #20 room kaiwan flags are: 4f4,4f5,4f6
        #28 room kaiwan flags are: 6c5,6c6,6c7
        f020_20_01_waits = [24,50,59,79,98,124,140,146,155,225,243,257,262,279] 
        f020_20_02_waits = [24,50,59,79,98,124,140,146,155,225,243,257,262,279]
        f020_20_03_waits = [24,50,59,79,98,129,145,156,165,210,228,242,247,264]
        f020_20_04_waits = [24,50,59,79,98,124,140,146,155,216,234,248,253,270]
        f020_20_05_waits = [61,72,81,90,164,237,242,256,268]
        f020_20_06_waits = [61,72,81,90,139,187,192,206,218]
        f020_20_07_waits = [61,72,81,90,155,219,224,238,250]
        f020_proc_waits = [("018_01eve_01",f020_18_01_waits), ("018_01eve_02",f020_18_02_waits), ("019_01eve_01",f020_19_01_waits), ("019_01eve_02",f020_19_02_waits), ("019_01eve_03",f020_19_03_waits), ("020_01eve_01",f020_20_01_waits), ("020_01eve_02",f020_20_02_waits), ("020_01eve_03",f020_20_03_waits), ("020_01eve_04",f020_20_04_waits), ("020_01eve_05",f020_20_05_waits), ("020_01eve_06",f020_20_06_waits), ("020_01eve_07",f020_20_07_waits)]
        for p_name, p_waits in f020_proc_waits:
            p_proc = f020_obj.getProcIndexByLabel(p_name)
            p_insts, p_labels = f020_obj.getProcInstructionsLabelsByIndex(p_proc)
            new_insts = []
            curr_cut = 0
            for p_wait in p_waits:
                new_insts.extend(p_insts[curr_cut:p_wait])
                curr_cut = p_wait+2 #2 because a wait is 2 instructions
                for label in p_labels:
                    if label.label_offset > len(new_insts):
                        label.label_offset-=2
            new_insts.extend(p_insts[curr_cut:])
            f020_obj.changeProcByIndex(new_insts,p_labels,p_proc)

        #Shorten Ose.
        #Door event is 013_01eve_01
        #Cut out 50-58 (inclusive both)
        #Ose ID is 117
        precut = 50
        postcut = 59
        diff = postcut - precut
        f020_13_proc = f020_obj.getProcIndexByLabel("013_01eve_01")
        f020_13_insts, f020_13_labels = f020_obj.getProcInstructionsLabelsByIndex(f020_13_proc)
        f020_13_insert_insts = [
            inst("PUSHIS",0x56c),#I don't know what these flags do, but they are set here.
            inst("COMM",8),
            inst("PUSHIS",0x56d),
            inst("COMM",8),
            inst("PUSHIS",0x27a),
            inst("PUSHIS",0x14),
            inst("PUSHIS",1),
            inst("COMM",0x97), #Call next
            inst("PUSHIS",117),
            inst("COMM",0x67) #Fight Ose
        ]
        #Callback: f020.wap at 0x7fc
        for l in f020_13_labels:
            if l.label_offset > precut:
                l.label_offset-=diff
                l.label_offset+=len(f020_13_insert_insts)
        f020_13_insts = f020_13_insts[:precut] + f020_13_insert_insts + f020_13_insts[postcut:]
        f020_obj.changeProcByIndex(f020_13_insts,f020_13_labels,f020_13_proc)

        f020_berith_rwms_index = f020_obj.appendMessage(self.get_reward_str("Berith",world),"BERITH_REWARD")
        f020_berith_rwms_insts = [
            inst("PROC",len(f020_obj.p_lbls().labels)),
            inst("COMM",0x60),
            inst("COMM",1),
            inst("PUSHIS",f020_berith_rwms_index),
            inst("COMM",0),
            inst("COMM",2),
            inst("COMM",0x61),
        ] + self.get_flag_reward_insts("Berith",world) + [    
            inst("END"),
        ]
        f020_berith_callback_str = "BERITH_CB"
        f020_obj.appendProc(f020_berith_rwms_insts, [], f020_berith_callback_str)
        self.insert_callback('f020',0xf4,f020_berith_callback_str)

        f020_kaiwan_rwms_index = f020_obj.appendMessage(self.get_reward_str("Kaiwan",world),"KAIWAN_REWARD")
        f020_kaiwan_rwms_insts = [
            inst("PROC",len(f020_obj.p_lbls().labels)),
            inst("PUSHIS",0x3d4),
            inst("COMM",0x8), 
            inst("COMM",0x60),
            inst("COMM",1),
            inst("PUSHIS",f020_kaiwan_rwms_index),
            inst("COMM",0),
            inst("COMM",2),
            inst("COMM",0x61),
        ] + self.get_flag_reward_insts("Kaiwan",world) + [    
            inst("END"),
        ]
        f020_kaiwan_callback_str = "KAIWAN_CB"
        f020_obj.appendProc(f020_kaiwan_rwms_insts, [], f020_kaiwan_callback_str)
        self.insert_callback('f020',0x158,f020_kaiwan_callback_str) #0x158 is the Kaiwan callback index
        
        f020_berith_proc = f020_obj.getProcIndexByLabel("024_01eve_01") #Change berith model to new boss
        f020_berith_insts, f020_berith_labels = f020_obj.getProcInstructionsLabelsByIndex(f020_berith_proc)
        f020_berith_insts[25] = inst("PUSHIS",self.get_checks_boss_id("Berith",world))
        f020_obj.changeProcByIndex(f020_berith_insts, f020_berith_labels, f020_berith_proc)
        f020_eligor_name_id = f020_obj.sections[3].messages[0x16].name_id
        f020_eligor_message = assembler.message("^r"+self.get_checks_boss_name("Berith",world)+"^p says that's enough..." ,"HEISHI01")
        f020_eligor_message.name_id = f020_eligor_name_id
        f020_obj.changeMessageByIndex(f020_eligor_message,0x16)        
        #Unsure if this is the correct door, look carefully

        f020_kaiwan_proc = f020_obj.getProcIndexByLabel("027_start") #Change kaiwan model to new boss
        f020_kaiwan_insts, f020_kaiwan_labels = f020_obj.getProcInstructionsLabelsByIndex(f020_kaiwan_proc)
        f020_kaiwan_insts[311] = inst("PUSHIS",self.get_checks_boss_id("Kaiwan",world)) #Middle Kaiwan
        f020_kaiwan_insts[323] = inst("PUSHIS",self.get_checks_boss_id("Kaiwan",world, index = 1)) #Kaiwan on the left
        f020_kaiwan_insts[335] = inst("PUSHIS",self.get_checks_boss_id("Kaiwan",world, index=2)) #Kaiwan on the right
        f020_obj.changeProcByIndex(f020_kaiwan_insts, f020_kaiwan_labels, f020_kaiwan_proc)
        f020_obj.changeMessageByIndex(assembler.message("> ^r"+self.get_checks_boss_name("Kaiwan",world)+"^p unlocked the door.^n^x> Will you enter?" ,"F020_KIUNDOOR02"),0x6e)        

        #Ose hint message, may be the wrong door
        f020_obj.changeMessageByIndex(assembler.message("> You sense ^r"+self.get_checks_boss_name("Ose",world)+"^p^nbeyond the door.^n^x> Will you enter?" ,"HON_ENT"),0x4c)        
        
        f020_obj.changeNameByLookup("Berith", self.get_checks_boss_name("Berith",world, immersive=True))
        f020_obj.changeNameByLookup("Kaiwan", self.get_checks_boss_name("Kaiwan",world, immersive=True))
        f020_berith_name_id = f020_obj.sections[3].messages[0x22].name_id
        f020_berith_message = assembler.message("Halt...^n^xI am "+self.get_checks_boss_name("Berith",world, immersive=True)+", the great duke of hell.^n^xInsolent scoundrel, put down^nthe Kila and begone!" ,"BERI01")
        f020_berith_message.name_id = f020_berith_name_id
        f020_obj.changeMessageByIndex(f020_berith_message,0x22)

        f020_lb = self.push_bf_into_lb(f020_obj, 'f020')
        self.dds3.add_new_file(custom_vals.LB0_PATH['f020'], f020_lb)

        if SCRIPT_DEBUG:
            self.script_debug_out(f020_obj,'f020.bf')

        f003_obj = self.get_script_obj_by_name('f003')
        f003_proclen = len(f003_obj.p_lbls().labels)

        f003_ose_callback_message = f003_obj.appendMessage(self.get_reward_str("Ose",world),"OSE_REWARD")
        f003_ose_callback_proc_str = "OSE_CB"
        f003_ose_callback_insts = [
            inst("PROC",len(f003_obj.p_lbls().labels)),
            inst("COMM",0x60),
            inst("COMM",1),
            inst("PUSHIS",f003_ose_callback_message),
            inst("COMM",0),
            inst("COMM",2),
            inst("COMM",0x61),
        ] + self.get_flag_reward_insts("Ose",world) + [
            inst("END"),
        ]
        f003_obj.appendProc(f003_ose_callback_insts,[],f003_ose_callback_proc_str)
        f003_lb = self.push_bf_into_lb(f003_obj, 'f003')
        self.dds3.add_new_file(custom_vals.LB0_PATH['f003'], f003_lb)
        self.insert_callback('f020', 0x7fc, f003_ose_callback_proc_str)

        #The callback is in f020, but the proc is in f003 (outside Ginza).
        #interesting note: 001_01eve_08 happens going from Rainbow Bridge to Shiba, 001_01eve_07 happens going from Shiba to Rainbow Bridge. Probably responsible for changing encounter tables.

        if SCRIPT_DEBUG:
            self.script_debug_out(f003_obj,'f003.bf')

        #kilas: 3d2, 3d3, 3d4, 3d5
        #inserted kilas: 4ea, 4e7, 4e8, 4e9
        #probably just want to do path_hoji_01 and other stuff.
        #4e7 - 3d2, 4ea - 3d3, 4e8 - 3d4, 4e9 - 3d5
        #best way to auto-insert kilas is to have the respective flags also set.
        #change 008_start to include a fast version of descending the floor to reveal the spiral down to ose. It will only happen if 4e7, 4ea, 4e8 and 4e9 are set (kila insertion flags).
        #Kaiwan flags: 0x700, 0x6c5, 0x6c6, 0x6c7
        #013_01eve_01 is event that calls ose, which is e634.
        #e634:
        #0x16, 0x56c, 0x56d on - 0x4e1 off. 0x29 also on, but is only used here.

        #Cutscene removal for Hell Biker f004
        f004_obj = self.get_script_obj_by_name('f004')
        f004_biker_event = f004_obj.getProcIndexByLabel("001_01eve_03")
        f004_biker_insts = [
            inst("PROC",f004_biker_event),
            inst("PUSHIS",0),
            inst("PUSHIS",0x754),#Didn't already run away.
            inst("COMM",7),
            inst("PUSHREG"),
            inst("EQ"),
            inst("PUSHIS",0),
            inst("PUSHIS",0x10a),#Didn't already fight.
            inst("COMM",7),
            inst("PUSHREG"),
            inst("EQ"),
            inst("AND"),
            inst("IF",0),#End label
            inst("COMM",0x60),
            inst("COMM",1),
            inst("PUSHIS",5), #Do you want to stay here?
            inst("COMM",0),
            inst("PUSHIS",0),
            inst("PUSHIS",6), #Yes/no
            inst("COMM",3),
            inst("PUSHREG"),
            inst("EQ"),
            inst("COMM",2),
            inst("IF",1),
            inst("PUSHIS",0x10a), #turn on fought flag.
            inst("COMM",8),
            inst("PUSHIS",0x922), #turn on ???
            inst("COMM",8),
            inst("PUSHIS",0x3e8), #give candelabra
            inst("COMM",8),
            inst("PUSHIS",0x2e5),
            inst("PUSHIS",4),
            inst("PUSHIS",1),
            inst("COMM",0x97), #call next
            inst("PUSHIS",1029),
            inst("COMM",0x67), #fight biker
            inst("END"),
            inst("PUSHIS",0x754),
            inst("COMM",0x8),
            inst("COMM",0x61),
            inst("END")
        ]
        f004_biker_labels = [
            assembler.label("BIKER_RAN",40),
            assembler.label("BIKER_FOUGHT",37)
        ]
        if config_settings.menorah_groups: #Remove candelabra if randomized
            del f004_biker_insts[28:30]
            f004_biker_labels = [
                assembler.label("BIKER_RAN",38),
                assembler.label("BIKER_FOUGHT",35)
            ]
        f004_obj.changeProcByIndex(f004_biker_insts,f004_biker_labels,f004_biker_event)
        f004_biker_callback_proc_str = "HBIKER_CB"
        f004_biker_callback_msg = f004_obj.appendMessage(self.get_reward_str("Hell Biker",world),"HBIKER_REWARD")
        f004_obj.changeMessageByIndex(assembler.message("You sense the presence of^n^r"+self.get_checks_boss_name("Hell Biker",world)+"^p.","HBIKER_HINT"),4)
        f004_biker_callback_insts = [
            inst("PROC",len(f004_obj.p_lbls().labels)),
            inst("COMM",0x60),
            inst("COMM",1),
            inst("PUSHIS",f004_biker_callback_msg),
            inst("COMM",0),
            inst("COMM",2),
            inst("COMM",0x61),
        ] + self.get_flag_reward_insts("Hell Biker",world) + [
            inst("END")
        ]
        f004_obj.appendProc(f004_biker_callback_insts,[],f004_biker_callback_proc_str)
        self.insert_callback('f004', 0x540, f004_biker_callback_proc_str)
        
        #Ongyo-Key hint
        f004_obj.changeMessageByIndex(assembler.message("> East Ikebukuro Station.^n^x> The key is stashed in^n^g"+self.get_flag_reward_location_string(0x3f7,world)+"^p.","SUBWAY"),0x0)
        
        #Swap the 0x24 flag for Ikebukuro Tunnel to the 0x3f7 Ongyo-Key
        f004_wap = bytearray(self.dds3.get_file_from_path(custom_vals.WAP_PATH['f004']).read())
        f004_wap[0x35e] = 0xf7
        f004_wap[0x35f] = 0x03

        f004_lb_data = self.dds3.get_file_from_path(custom_vals.LB0_PATH['f004'])
        f004_lb = LB_FS(f004_lb_data)
        f004_lb.read_lb()
        f004_lb = f004_lb.export_lb({'WAP': BytesIO(f004_wap), 'BF': BytesIO(bytes(f004_obj.toBytes()))})
        
        #f004_lb = self.push_bf_into_lb(f004_obj, 'f004')
        self.dds3.add_new_file(custom_vals.LB0_PATH['f004'], f004_lb)

        if SCRIPT_DEBUG:
            self.script_debug_out(f004_obj,'f004.bf')

        #Cutscene removal in Kabukicho Prison f025
        #Shorten forced Naga
        #Shorten Mizuchi
        #First Umugi stone usage flag
        #Shorten Black Frost (low priority)
        #set 0x583, 0x594
        #change mizuchi intro to not set 0x59c. (Might as well also shorten it). It also sets 0x595
        #Mizuchi is in 025_start
        #0x589 is spoon cutscene.
        f025_obj = self.get_script_obj_by_name("f025")
        f025_mizuchi_room = f025_obj.getProcIndexByLabel("025_start")
        f025_mizuchi_room_insts, f025_mizuchi_room_labels = f025_obj.getProcInstructionsLabelsByIndex(f025_mizuchi_room)
        #28 - 87 both inclusive. Insert 595 and 863.
        #Probably don't need to change labels, but if you don't _443 is OoB, but it doesn't seem like it does anything since it was compiler made.
        precut = 28
        postcut = 88
        f025_mizuchi_room_insert_insts = [
            inst("PUSHIS",0x595),
            inst("COMM",8),
            inst("PUSHIS",0x863),
            inst("COMM",8)
        ] + self.get_flag_reward_insts("Mizuchi",world)
        f025_mizuchi_room_labels[-1].label_offset = 0 #fixes _443 OoB warning.
        f025_mizuchi_room_insts = f025_mizuchi_room_insts[:precut] + f025_mizuchi_room_insert_insts + f025_mizuchi_room_insts[postcut:]
        f025_obj.changeProcByIndex(f025_mizuchi_room_insts, f025_mizuchi_room_labels, f025_mizuchi_room)
        f025_obj.changeMessageByIndex(assembler.message(self.get_reward_str("Mizuchi",world),"MIZUCHI_REWARD"),0x62)
        f025_obj.changeMessageByIndex(assembler.message("> You sense ^r"+self.get_checks_boss_name("Mizuchi",world)+"^p^nbeyond the door.^n^x> Will you enter?" ,"F025_DOOR01"),0xb4)        
        

        f025_021_05 = f025_obj.getProcIndexByLabel("021_01eve_05") #I don't think this gets executed, but I was frustrated when I chose the wrong LB file and this also has the Mizuchi text.
        f025_021_insts = [
            inst("PROC",f025_021_05),
            inst("END")
        ]
        f025_obj.changeProcByIndex(f025_021_insts,[],f025_021_05)

        f025_lb = self.push_bf_into_lb(f025_obj, 'f025b')
        self.dds3.add_new_file(custom_vals.LB0_PATH['f025b'], f025_lb)

        if SCRIPT_DEBUG:
            self.script_debug_out(f025_obj,'f025.bf')

        #Cutscene removal in Ikebukuro Tunnel (anything at all?) f026
        #Kin-ki: 015_01eve_02. Area is 015_start obviously.
        #Callback: 0x158
        #Sui-ki: 014_01eve_02
        #Callback: 0xf4
        #Fuu-ki: 016_01eve_02
        #Callback: 0x1bc
        #Ongyo-ki: 017_start
        #Callback: 0x220
        
        #patch ikebukuro tunnel entrance to use new key item
        #f004_inf_patched = BytesIO(bytes(open(path.join(PATCHES_PATH,'F004_tunnel_key.INF'),'rb').read()))
        #self.dds3.add_new_file('/fld/f/f004/F004.INF', f004_inf_patched)
        f026_obj = self.get_script_obj_by_name('f026')
        f026_kinki_rwms_index = f026_obj.appendMessage(self.get_reward_str("Kin-Ki",world),"KINKI_REWARD")
        f026_kinki_rwms_insts = [
            inst("PROC",len(f026_obj.p_lbls().labels)),
            inst("COMM",0x60),
            inst("COMM",1),
            inst("PUSHIS",f026_kinki_rwms_index),
            inst("COMM",0),
            inst("COMM",2),
            inst("COMM",0x61),
        ] + self.get_flag_reward_insts("Kin-Ki",world) + [    
            inst("END")
        ]
        f026_kinki_callback_str = "KINKI_CB"
        f026_obj.appendProc(f026_kinki_rwms_insts, [], f026_kinki_callback_str)
        self.insert_callback('f026',0x158,f026_kinki_callback_str)
        
        #Change Kin-ki model to check boss
        f026_15_room = f026_obj.getProcIndexByLabel("015_start")
        f026_15_room_insts, f026_15_room_labels = f026_obj.getProcInstructionsLabelsByIndex(f026_15_room)
        f026_15_room_insts[7] = inst("PUSHIS",self.get_checks_boss_id("Kin-Ki",world))
        f026_obj.changeProcByIndex(f026_15_room_insts, f026_15_room_labels, f026_15_room)
        
        f026_suiki_rwms_index = f026_obj.appendMessage(self.get_reward_str("Sui-Ki",world),"SUIKI_REWARD")
        f026_suiki_rwms_insts = [
            inst("PROC",len(f026_obj.p_lbls().labels)),
            inst("COMM",0x60),
            inst("COMM",1),
            inst("PUSHIS",f026_suiki_rwms_index),
            inst("COMM",0),
            inst("COMM",2),
            inst("COMM",0x61),
        ] + self.get_flag_reward_insts("Sui-Ki",world) + [    
            inst("END")
        ]
        f026_suiki_callback_str = "SUIKI_CB"
        f026_obj.appendProc(f026_suiki_rwms_insts, [], f026_suiki_callback_str)
        self.insert_callback('f026',0xf4,f026_suiki_callback_str)
        
        f026_14_room = f026_obj.getProcIndexByLabel("014_start")
        f026_14_room_insts, f026_14_room_labels = f026_obj.getProcInstructionsLabelsByIndex(f026_14_room)
        f026_14_room_insts[7] = inst("PUSHIS",self.get_checks_boss_id("Sui-Ki",world))
        f026_obj.changeProcByIndex(f026_14_room_insts, f026_14_room_labels, f026_14_room)
        
        f026_fuuki_rwms_index = f026_obj.appendMessage(self.get_reward_str("Fuu-Ki",world),"FUUKI_REWARD")
        f026_fuuki_rwms_insts = [
            inst("PROC",len(f026_obj.p_lbls().labels)),
            inst("COMM",0x60),
            inst("COMM",1),
            inst("PUSHIS",f026_fuuki_rwms_index),
            inst("COMM",0),
            inst("COMM",2),
            inst("COMM",0x61),
        ] + self.get_flag_reward_insts("Fuu-Ki",world) + [    
            inst("END")
        ]
        f026_fuuki_callback_str = "FUUKI_CB"
        f026_obj.appendProc(f026_fuuki_rwms_insts, [], f026_fuuki_callback_str)
        self.insert_callback('f026',0x1bc,f026_fuuki_callback_str)

        f026_16_room = f026_obj.getProcIndexByLabel("016_start")
        f026_16_room_insts, f026_16_room_labels = f026_obj.getProcInstructionsLabelsByIndex(f026_16_room)
        f026_16_room_insts[7] = inst("PUSHIS",self.get_checks_boss_id("Fuu-Ki",world))
        f026_obj.changeProcByIndex(f026_16_room_insts, f026_16_room_labels, f026_16_room)

        f026_ongyoki_rwms_index = f026_obj.appendMessage(self.get_reward_str("Ongyo-Ki",world),"ONGYOKI_REWARD")
        f026_ongyoki_rwms_insts = [
            inst("PROC",len(f026_obj.p_lbls().labels)),
            inst("COMM",0x60),
            inst("COMM",1),
            inst("PUSHIS",f026_ongyoki_rwms_index),
            inst("COMM",0),
            inst("COMM",2),
            inst("COMM",0x61),
        ] + self.get_flag_reward_insts("Ongyo-Ki",world) + [    
            inst("END")
        ]
        f026_ongyoki_callback_str = "ONGYOKI_CB"
        f026_obj.appendProc(f026_ongyoki_rwms_insts, [], f026_ongyoki_callback_str)
        self.insert_callback('f026',0x220,f026_ongyoki_callback_str)
        
        f026_ongyo_proc = f026_obj.getProcIndexByLabel("017_start") #Change ongyo-ki model to new boss and add hint message
        f026_ongyo_insts, f026_ongyo_labels = f026_obj.getProcInstructionsLabelsByIndex(f026_ongyo_proc)
        f026_ongyo_insts[17] = inst("PUSHIS",self.get_checks_boss_id("Ongyo-Ki",world))
        f026_obj.changeProcByIndex(f026_ongyo_insts, f026_ongyo_labels, f026_ongyo_proc)
        f026_obj.changeMessageByIndex(assembler.message("> You sense ^r"+self.get_checks_boss_name("Ongyo-Ki",world)+"^p^nbeyond the door..." ,"F26_FUIN_YOKI"),0x2b)
        
        f026_obj.changeNameByLookup("Kin-ki", self.get_checks_boss_name("Kin-Ki",world, immersive=True))
        f026_obj.changeNameByLookup("Sui-ki", self.get_checks_boss_name("Sui-Ki",world, immersive=True))
        f026_obj.changeNameByLookup("Fuu-ki", self.get_checks_boss_name("Fuu-Ki",world, immersive=True))
        f026_obj.changeNameByLookup("Ongyo-ki", self.get_checks_boss_name("Ongyo-Ki",world, immersive=True))
        

        f026_kinki_name_id = f026_obj.sections[3].messages[0x10].name_id
        f026_kinki_message = assembler.message("............^n^x...WHAT DO YOU WANT?^n^xI AM "+self.get_checks_boss_name("Kin-Ki",world, immersive=True).upper()+". YOU FILTHY DOG..." ,"F26_KINKI")
        f026_kinki_message.name_id = f026_kinki_name_id
        f026_obj.changeMessageByIndex(f026_kinki_message,0x10) 
        f026_obj.changeMessageByIndex(assembler.message("> "+self.get_checks_boss_name("Kin-Ki",world, immersive=True)+" is not listening. What will^nyou do?" ,"F26_KINKI_2"),0x11)
        f026_obj.changeMessageByIndex(assembler.message("> "+self.get_checks_boss_name("Kin-Ki",world, immersive=True)+"'s breathing is getting heavier." ,"F26_KINKI_HANA"),0x15)
        f026_suiki_name_id = f026_obj.sections[3].messages[0x16].name_id
        f026_suiki_message = assembler.message("...I've never seen you before.^n^xI'm "+self.get_checks_boss_name("Sui-Ki",world, immersive=True)+".^n^xI'm a cold demon." ,"F26_SUIKI")
        f026_suiki_message.name_id = f026_suiki_name_id
        f026_obj.changeMessageByIndex(f026_suiki_message,0x16) 
        f026_fuuki_name_id = f026_obj.sections[3].messages[0x1f].name_id
        f026_fuuki_message = assembler.message("Yee-haw!^n^xI'm "+self.get_checks_boss_name("Fuu-Ki",world, immersive=True)+".^n^xYou must have some time on your^nhands, making it all the way down^nhere." ,"F26_FUUKI")
        f026_fuuki_message.name_id = f026_fuuki_name_id
        f026_obj.changeMessageByIndex(f026_fuuki_message,0x1f) 
        f026_ongyoki_name_id = f026_obj.sections[3].messages[0x2c].name_id
        f026_ongyoki_message = assembler.message("My name is "+self.get_checks_boss_name("Ongyo-Ki",world, immersive=True)+"...^n^xAre you the one who slew my^npartners and awakened me!?" ,"F26_ONGYO")
        f026_ongyoki_message.name_id = f026_ongyoki_name_id
        f026_obj.changeMessageByIndex(f026_ongyoki_message,0x2c)      
        
        f026_lb = self.push_bf_into_lb(f026_obj,'f026')
        self.dds3.add_new_file(custom_vals.LB0_PATH['f026'],f026_lb)

        if SCRIPT_DEBUG:
            self.script_debug_out(f026_obj,'f026.bf')

        #Cutscene removal in Asakusa (Hijiri?) f027
        #Shorten Pale Rider
        #Move Black Frost to Sakahagi room.
        f027_obj = self.get_script_obj_by_name('f027')

        #Pale Rider
        f027_pr_proc = f027_obj.getProcIndexByLabel('016_p_rider')
        f027_pr_insts, f027_pr_labels = f027_obj.getProcInstructionsLabelsByIndex(f027_pr_proc)
        f027_pr_insts[12] = inst("PUSHIS",0x3f4) #Change rider trigger check from 7b8 to key item
        f027_obj.changeProcByIndex(f027_pr_insts, f027_pr_labels, f027_pr_proc)

        f027_obj.changeMessageByIndex(assembler.message("You sense the presence of^n^r"+self.get_checks_boss_name("Pale Rider",world)+"^p.","FIRE_YURE"),0x13)

        f027_16_proc = f027_obj.getProcIndexByLabel('016_01eve_01')
        f027_16_insts = [
            inst("PROC",f027_16_proc),
            inst("PUSHIS",0x109), #Black Rider dead
            inst("COMM",7),
            inst("PUSHREG"),
            inst("PUSHIS",0x3f4), #Key item to enable Riders
            inst("COMM",7),
            inst("PUSHREG"),
            inst("PUSHIS",0),
            inst("PUSHIS",0x758), #Didn't already run away
            inst("COMM",7),
            inst("PUSHREG"),
            inst("EQ"),
            inst("PUSHIS",0),
            inst("PUSHIS",0x113), #Didn't already beat him
            inst("COMM",7),
            inst("PUSHREG"),
            inst("EQ"),
            inst("AND"),
            inst("AND"), 
            inst("AND"),
            inst("IF",0), #End label
            inst("COMM",0x60),
            inst("COMM",1),
            inst("PUSHIS",0x14), #"Stay here?"
            inst("COMM",0),
            inst("PUSHIS",0),
            inst("PUSHIS",0x15), #">Yes/no"
            inst("COMM",3),
            inst("PUSHREG"),
            inst("EQ"),
            inst("IF",1), #Not quite end label
            inst("PUSHIS",0x113), #Fought flag
            inst("COMM",8),
            inst("PUSHIS",0x3e1), #Candelabra
            inst("COMM",8),
            inst("PUSHIS",0x91d), #Fusion flag
            inst("COMM",8),
            inst("PUSHIS",0x2ea),
            inst("PUSHIS",0x1b),
            inst("PUSHIS",1),
            inst("COMM",0x97), #Call next
            inst("PUSHIS",0x400),
            inst("COMM",0x67), #Fight Pale Rider
            inst("END"),
            inst("PUSHIS",0x758),
            inst("COMM",8),
            inst("COMM",0x61),
            inst("END")
        ]
        f027_16_labels = [
            assembler.label("PRIDER_FOUGHT",47),
            assembler.label("PRIDER_RAN",44)
        ]
        if config_settings.menorah_groups: #Remove candelabra if randomized
            del f027_16_insts[33:35]
            f027_16_labels = [
                assembler.label("PRIDER_FOUGHT",45),
                assembler.label("PRIDER_RAN",42)
            ]
        f027_obj.changeProcByIndex(f027_16_insts, f027_16_labels, f027_16_proc)

        f027_prider_callback_str = "PR_CB"
        f027_prider_rwms_index = f027_obj.appendMessage(self.get_reward_str("Pale Rider",world), "PR_REWARD")
        f027_pr_rwms_insts = [
            inst("PROC",len(f027_obj.p_lbls().labels)),
            inst("COMM",0x60),
            inst("COMM",1),
            inst("PUSHIS",f027_prider_rwms_index),
            inst("COMM",0),
            inst("COMM",2),
            inst("COMM",0x61),
        ] + self.get_flag_reward_insts("Pale Rider",world) + [    
            inst("END")
        ]
        f027_obj.appendProc(f027_pr_rwms_insts, [], f027_prider_callback_str)
        self.insert_callback('f027',0xf4,f027_prider_callback_str)

        f027_bfrost_callback_str = "BFROST_CB"
        f027_bfrost_rwms_index = f027_obj.appendMessage(self.get_reward_str("Black Frost",world), "BFROST_REWARD")
        f027_bfrost_rwms_insts = [
            inst("PROC",len(f027_obj.p_lbls().labels)),
            inst("COMM",0x60),
            inst("COMM",1),
            inst("PUSHIS",f027_bfrost_rwms_index),
            inst("COMM",0),
            inst("COMM",2),
            inst("COMM",0x61),
        ] + self.get_flag_reward_insts("Black Frost",world) + [
            inst("END")
        ]
        f027_obj.appendProc(f027_bfrost_rwms_insts, [], f027_bfrost_callback_str)
        self.insert_callback('f027',0x1ddc,f027_bfrost_callback_str)
        
        #Black frost hint message
        f027_obj.changeMessageByIndex(assembler.message("> You sense ^r"+self.get_checks_boss_name("Black Frost",world)+"^p^nbeyond the door.^n^x> Will you enter?" ,"F027_DOOR01"),0x4e)        

        #Remove white rider from Asakusa always
        f027_rider_flame_proc = f027_obj.getProcIndexByLabel("001_w_rider")
        f027_rider_flame_insts, f027_rider_flame_labels = f027_obj.getProcInstructionsLabelsByIndex(f027_rider_flame_proc)
        f027_rider_flame_insts[6] = inst("PUSHIS",0x113) #Switch flag to pale rider fought so it's never relevant
        f027_obj.changeProcByIndex(f027_rider_flame_insts, f027_rider_flame_labels, f027_rider_flame_proc)
        f027_rider_fight1_proc = f027_obj.getProcIndexByLabel("001_01eve_01")
        f027_rider_fight1_insts, f027_rider_fight1_labels = f027_obj.getProcInstructionsLabelsByIndex(f027_rider_fight1_proc)
        f027_rider_fight1_insts[1] = inst("PUSHIS",0x113) #Switch flag to pale rider fought so it's never relevant
        f027_obj.changeProcByIndex(f027_rider_fight1_insts, f027_rider_fight1_labels, f027_rider_fight1_proc)
        f027_rider_fight2_proc = f027_obj.getProcIndexByLabel("001_01eve_02")
        f027_rider_fight2_insts, f027_rider_fight2_labels = f027_obj.getProcInstructionsLabelsByIndex(f027_rider_fight2_proc)
        f027_rider_fight2_insts[1] = inst("PUSHIS",0x113) #Switch flag to pale rider fought so it's never relevant
        f027_obj.changeProcByIndex(f027_rider_fight2_insts, f027_rider_fight2_labels, f027_rider_fight2_proc)
        f027_rider_fight3_proc = f027_obj.getProcIndexByLabel("001_01eve_03") #There are 3 Asakusa rider battles because why?
        f027_rider_fight3_insts, f027_rider_fight3_labels = f027_obj.getProcInstructionsLabelsByIndex(f027_rider_fight3_proc)
        f027_rider_fight3_insts[1] = inst("PUSHIS",0x113) #Switch flag to pale rider fought so it's never relevant
        f027_obj.changeProcByIndex(f027_rider_fight3_insts, f027_rider_fight3_labels, f027_rider_fight3_proc)

        f027_lb = self.push_bf_into_lb(f027_obj,'f027')
        self.dds3.add_new_file(custom_vals.LB0_PATH['f027'],f027_lb)

        if SCRIPT_DEBUG:
            self.script_debug_out(f027_obj,'f027.bf')

        #Change e644 to fight Black Frost. Normally it's the Sakahagi cutscene in Asakusa, but we're repurposing it so no two bosses are in the same location.
        #Flag is 2e
        #Callback is 0x1ddc in f027
        e644_obj = self.get_script_obj_by_name('e644')
        e644_insts = [
            inst("PROC",0),
            inst("PUSHIS",0),
            inst("PUSHIS",0x2e),
            inst("COMM",7),
            inst("PUSHREG"),
            inst("EQ"),
            inst("IF",0),
            inst("PUSHIS",0x2e),
            inst("COMM",8),
            inst("PUSHIS",644),#Should work???
            inst("PUSHIS",0x2ca),#Black Frost battle ID
            inst("COMM",0x28),
            inst("END"),
            inst("PUSHIS",644),
            inst("PUSHIS",27),
            inst("PUSHIS",1),
            inst("COMM",0x97),
            inst("COMM",0x23),
            inst("COMM",0x2e),
            inst("END")
        ]
        e644_labels = [
            assembler.label("BFROST_FOUGHT",13)
        ]
        e644_obj.changeProcByIndex(e644_insts, e644_labels, 0)
        self.dds3.add_new_file(custom_vals.SCRIPT_OBJ_PATH['e644'],BytesIO(bytes(e644_obj.toBytes())))

        if SCRIPT_DEBUG:
            self.script_debug_out(e644_obj,'e644.bf')

        #Bishamonten scene f039
        f039_obj = self.get_script_obj_by_name('f039')
        f039_obj.changeNameByLookup("Bishamon", self.get_checks_boss_name("Bishamon 1",world, immersive=True))
        f039_obj.changeMessageByIndex(assembler.message("Well done.","SHORTER_B_TEXT"),0x11)
        f039_obj.changeMessageByIndex(assembler.message(self.get_reward_str("Bishamon 1",world),"BISHA_REWARD"),0x13)
        f039_obj.changeMessageByIndex(assembler.message("> Do you accept "+self.get_checks_boss_name("Bishamon 1",world, immersive=True)+"'s^nchallenge?","f039_BOSS01_03"),0xd)
        f039_obj.changeMessageByIndex(assembler.message("> "+self.get_checks_boss_name("Bishamon 1",world, immersive=True)+" disappeared.","BOSS03"),0x16)
        f039_rwms_proc = f039_obj.getProcIndexByLabel('039_B_AFTER')
        f039_rwms_insts, f039_rwms_labels = f039_obj.getProcInstructionsLabelsByIndex(f039_rwms_proc)

        f039_keys_insts = [
            inst("PUSHIS",0x3f1), #Black Key (testing purposes)
            inst("COMM",8),
            inst("PUSHIS",0x3f2), #White Key (testing purposes)
            inst("COMM",8),
            inst("PUSHIS",0x3f3), #Red Key (testing purposes)
            inst("COMM",8),   
        ]#Insert these if Bishamon should be a backup for softlocks

        f039_rwms_insts[23] = inst("PUSHIS",self.get_checks_boss_id("Bishamon 1",world))
        f039_rwms_insts = f039_rwms_insts[0:2] + self.get_flag_reward_insts("Bishamon 1",world) + f039_rwms_insts[2:-1] + [inst("END")]
        f039_obj.changeProcByIndex(f039_rwms_insts,[],f039_rwms_proc) #No labels in the proc
        f039_02_proc = f039_obj.getProcIndexByLabel("002_start")
        f039_02_insts, f039_02_labels = f039_obj.getProcInstructionsLabelsByIndex(f039_02_proc)
        f039_02_insts[41] = inst("PUSHIS",self.get_checks_boss_id("Bishamon 1",world))
        f039_02_insts[166] = inst("PUSHIS",self.get_checks_boss_id("Bishamon 1",world))
        f039_obj.changeProcByIndex(f039_02_insts, f039_02_labels, f039_02_proc)
        f039_lb = self.push_bf_into_lb(f039_obj, 'f039')
        self.dds3.add_new_file(custom_vals.LB0_PATH['f039'], f039_lb)
        #Model lines: 41, 166 of 002_start, 23 of 039_B_AFTER
        
        if SCRIPT_DEBUG:
            self.script_debug_out(f039_obj,'f039.bf')
        
        #inst("PUSHIS",0x56),
        #inst("COMM",8),
        #inst("PUSHIS",0x2a2), #0x2a1 is archangels
        #inst("COMM",0x67)

        #Cutscene removal in Mifunashiro f035
        #Shorten and add decision on boss
        #6e2,6e3,6e7 - Mifunashiro splash/entrance
        #6e5 - Angels asking for opinion
        #009_01eve_01 is platform that takes you to boss decision.
        #156-157 inclusive is removed. Put in setting 0x56 then calling Futomimi fight. Return is already included.
        #Insert callback for reward message. 0xf68
        #Fight Futomimi always.
        f035_obj = self.get_script_obj_by_name('f035')
        
        f035_09_index = f035_obj.getProcIndexByLabel('009_01eve_01')
        f035_09_insts, f035_09_labels = f035_obj.getProcInstructionsLabelsByIndex(f035_09_index)
        f035_futomimi_insert_insts = [
            inst("PUSHIS",0x56),
            inst("COMM",8),
            inst("PUSHIS",0x2a2), #0x2a1 is archangels
            inst("COMM",0x67)
        ]
        precut = 156
        postcut = 158
        diff = postcut-precut
        for l in f035_09_labels:
            if l.label_offset > precut:
                l.label_offset -= diff
                l.label_offset += len(f035_futomimi_insert_insts)
        f035_09_insts = f035_09_insts[:precut] + f035_futomimi_insert_insts + f035_09_insts[postcut:]
        if config_settings.open_yurakucho: #Use flag that we know is off until after both fights
            f035_09_insts[109] = inst("PUSHIS",0x81)
        f035_obj.changeProcByIndex(f035_09_insts, f035_09_labels, f035_09_index)

        #f035_angel_rwms_index = f035_obj.appendMessage(self.get_reward_str("Archangels",world),"ANGEL_REWARD")
        #f035_angel_rwms_insts = [
        #    inst("PROC",len(f035_obj.p_lbls().labels)),
        #    inst("COMM",0x60),
        #    inst("COMM",1),
        #    inst("PUSHIS",f035_angel_rwms_index),
        #    inst("COMM",0),
        #    inst("COMM",2),
        #    inst("COMM",0x61),
        #] + self.get_flag_reward_insts("Archangels",world) + [    
        #    inst("END"),
        #]
        #f035_angel_callback_str = "ANGEL_CB"
        #f035_obj.appendProc(f035_angel_rwms_insts, [], f035_angel_callback_str)
        
        #Futomimi/Archangels hint
        f035_obj.changeMessageByIndex(assembler.message("> The mirror's reflection shows^n^r"+self.get_checks_boss_name("Futomimi",world)+"^p and ^r"+self.get_checks_boss_name("Archangels",world)+"^p.^n^x> Will you step into the light?" ,"HIKARI"),0xa)        


        f035_futomimi_rwms_index = f035_obj.appendMessage(self.get_reward_str("Futomimi",world),"FUTO_RWMS")
        f035_angel_rwms_index = f035_obj.appendMessage(self.get_reward_str("Archangels",world),"ANGE_RWMS")
        f035_futomimi_callback_insts = [
            inst("PROC",len(f035_obj.p_lbls().labels)),
            inst("PUSHIS",0x0),
            inst("PUSHIS",0x81), #Use Agree with Chiaki flag because it is not needed elsewhere
            inst("COMM",0x7),
            inst("PUSHREG"),
            inst("EQ"),
            inst("IF", 0),
            inst("COMM",0x60),
            inst("COMM",1),
            inst("PUSHIS",f035_futomimi_rwms_index),
            inst("COMM",0),
            inst("COMM",2),
            
        ] + self.get_flag_reward_insts("Futomimi",world) + [
            inst("COMM",0x61),
            inst("PUSHIS", 0x81),
            inst("COMM", 0x8),
            inst("PUSHIS",0x2be),
            inst("PUSHIS",0x23), #Set a callback to self but check the Chiaki agree flag to prevent an infinite loop
            inst("PUSHIS",1),
            inst("COMM",0x97),
            inst("PUSHIS",0x2a1),#This is awkward, but it is the best I can do for now. Archangels are boss rush after futomimi
            inst("COMM",0x67),
            inst("END"),
            
            inst("COMM",0x60), #If this is after the angel fight, show the reward message and exit
            inst("COMM",1),
            inst("PUSHIS",f035_angel_rwms_index),
            inst("COMM",0),
            inst("COMM",2),
            inst("COMM",0x61),
            #inst("PUSHIS", 0x81), If anything is wierd because agree with chiaki is on, uncomment this
            #inst("COMM", 0x9),
        ] + self.get_flag_reward_insts("Archangels",world) + [
            inst("END")
        ]
        f035_futomimi_callback_labels = [
            assembler.label("ANGEL_FOUGHT",22 + len(self.get_flag_reward_insts("Futomimi",world)))
        ]
        f035_futomimi_callback_str = "FUTO_CB"
        f035_obj.appendProc(f035_futomimi_callback_insts,f035_futomimi_callback_labels,f035_futomimi_callback_str)
        f035_lb = self.push_bf_into_lb(f035_obj, 'f035')
        self.dds3.add_new_file(custom_vals.LB0_PATH['f035'], f035_lb)
        self.insert_callback('f035',0xf68,f035_futomimi_callback_str)

        if SCRIPT_DEBUG:
            self.script_debug_out(f035_obj,'f035.bf')

        #Cutscene removal in Obelisk f031
        #Anything? Could probably do everything with flags.
        #000_dh_plus is sisters callback. Any added flags can be put there.
        f031_obj = self.get_script_obj_by_name("f031")
        f031_obj.changeMessageByIndex(assembler.message(self.get_reward_str("Sisters",world),"SIS_REWARD"),0x2d)
        
        f031_rwms_proc = f031_obj.getProcIndexByLabel('000_dh_plus')
        f031_rwms_insts, f031_rwms_labels = f031_obj.getProcInstructionsLabelsByIndex(f031_rwms_proc)
        f031_rwms_insts = f031_rwms_insts[:-1] + self.get_flag_reward_insts("Sisters",world) + [inst("END")]
        f031_obj.changeProcByIndex(f031_rwms_insts,[],f031_rwms_proc)
        
        f031_sisters_proc = f031_obj.getProcIndexByLabel("012_start") #Change sisters models to new boss and add hint message
        f031_sisters_insts, f031_sisters_labels = f031_obj.getProcInstructionsLabelsByIndex(f031_sisters_proc)
        f031_sisters_insts[100] = inst("PUSHIS",self.get_checks_boss_id("Sisters",world))
        f031_sisters_insts[112] = inst("PUSHIS",self.get_checks_boss_id("Sisters",world, index=2))
        f031_sisters_insts[124] = inst("PUSHIS",self.get_checks_boss_id("Sisters",world, index=1))
        f031_obj.changeProcByIndex(f031_sisters_insts, f031_sisters_labels, f031_sisters_proc)
        f031_obj.changeMessageByIndex(assembler.message("> You sense ^r"+self.get_checks_boss_name("Sisters",world)+"^p^non the floor above.^n^x> Will you go up?" ,"BOSS_ROOM_IN"),0x32)        
        f031_obj.changeNameByLookup("Clotho", self.get_checks_boss_name("Sisters",world, immersive=True))
        f031_obj.changeNameByLookup("Lachesis", self.get_checks_boss_name("Sisters",world, immersive=True))
        f031_obj.changeNameByLookup("Atropos", self.get_checks_boss_name("Sisters",world, immersive=True))
        
        f031_lb = self.push_bf_into_lb(f031_obj,'f031')
        self.dds3.add_new_file(custom_vals.LB0_PATH['f031'],f031_lb)
        #relevant story flags:
        #Obelisk Yuko turns on: 0x46, 0x4e, 0x4c3. Turns off 0x48f.
        #0x50 is the cutscene with Hijiri after Obelisk.

        if SCRIPT_DEBUG:
            self.script_debug_out(f031_obj,'f031.bf')

        #Cutscene removal in Amala Network 2 f028
        #Shorten Specter 2 and add reward message
        #Remove waits on that dude?
        #Flag ending cutscene with Isamu as already viewed.
        #0x5eb
        #001_start has code for 
        #011_01eve_02 is specter 2. remove 7 - 162 inclusive
        f028_obj = self.get_script_obj_by_name("f028")
        f028_011_index = f028_obj.getProcIndexByLabel("011_01eve_02")
        f028_011_insts, f028_011_labels = f028_obj.getProcInstructionsLabelsByIndex(f028_011_index)
        precut = 7
        postcut = 163
        diff = postcut - precut
        #nothing to insert.
        f028_011_insts = f028_011_insts[:precut] + f028_011_insts[postcut:]
        #only one label.
        f028_011_labels[0].label_offset -= diff
        f028_obj.changeProcByIndex(f028_011_insts, f028_011_labels, f028_011_index)
        f028_specter2_rwms_index = f028_obj.appendMessage(self.get_reward_str("Specter 2",world),"SPEC2_RWMS")
        f028_specter2_callback_insts = [
            inst("PROC",len(f028_obj.p_lbls().labels)),
            inst("COMM",0x60),
            inst("COMM",1),
            inst("PUSHIS",f028_specter2_rwms_index),
            inst("COMM",0),
            inst("COMM",2),
            inst("COMM",0x61),
            #inst("PUSHIS",0x44), #Needs to be set at some time so why not now? Flag for Hijiri to not take you back into Network 2.
            #inst("COMM",8),
        ] + self.get_flag_reward_insts("Specter 2",world) + [
            inst("END")
        ]
        f028_specter2_callback_str = "SPEC2_CB"
        f028_obj.appendProc(f028_specter2_callback_insts,[],f028_specter2_callback_str)
        f028_lb = self.push_bf_into_lb(f028_obj, 'f028')
        self.dds3.add_new_file(custom_vals.LB0_PATH['f028'], f028_lb)
        self.insert_callback('f028',0xf4,f028_specter2_callback_str)
        
        if SCRIPT_DEBUG:
            self.script_debug_out(f028_obj,'f028.bf')

        
        #set 0x43, 0x5ed
        #0x5f9 gets set on finish of network 2.

        

        #e652 - e652_trm
        #0-30 init
        #{
        #   Transfer to Network 2? 32-64
        #   {
        #       Go into Network 2. Set bit 0x41. 66-90
        #       return
        #   }{
        #       Say no. 92-122
        #   }{
        #       blah blah blah 123-152
        #   }
        #}
        #155-156 end

        #Write as:
        #0-30 init
        #   Check 0x5f9.
        #   Unset {
        #       Transfer to Network 2?
        #       Yes {
        #           Go into Network 2. Set bit 0x41. Return.
        #       }
        #   }Set{
        #       Check 0x4a.
        #       Unset {
        #           "Come back after you've completed yoyogi park."
        #       } Set {
        #           Transfer to Network 3?
        #           Yes {
        #               Go into Network 3. Set 0x53 to make Hikawa in Asakusa disappear.
        #           }
        #       }
        #   }
        #   Go to TERMINAL

        #So uh, because of new flags set, we're getting a different event script. I'm just going to copy this code for e660 as the same trm modification should work just the same.
        e652_obj = self.get_script_obj_by_name('e652')
        e652_proc = e652_obj.getProcIndexByLabel('e652_trm')
        e652_insts, e652_labels = e652_obj.getProcInstructionsLabelsByIndex(e652_proc)
        e652_terminal_label_index = 0 #relative index for TERMINAL label. Absolute is 13
        e652_kept_insts = e652_insts[:52] #0-31 is terminal code. 32-51 has camera to hijiri code.
        e652_network2_msg = e652_obj.appendMessage("I think a "+self.get_checks_boss_name("Specter 2",world)+ " is in Amala Network 2. Go?","NETWORK2_MSG")
        e652_network3_msg = e652_obj.appendMessage(self.get_checks_boss_name("Specter 3",world) + " is pulling me in! ...Save Hijiri?","NETWORK3_MSG")
        e652_locked_msg = e652_obj.appendMessage("Come back after you've completed Yoyogi Park and I will take you to Amala Network 3.","LOCKED_MSG")
        e652_gl_msg = e652_obj.appendMessage("Good luck!","GL_MSG")
        e652_insert_insts = [
            inst("PUSHIS",0),
            inst("PUSHIS",0x5f9), #Check if gone in Network 2
            inst("COMM",7),
            inst("PUSHREG"),
            inst("EQ"),
            inst("IF",1), #0x5f9 check (Network 2) scope
            inst("COMM",1),
            inst("PUSHIS",e652_network2_msg),
            inst("COMM",0),
            inst("PUSHIS",7), #Sure/No thanks
            inst("COMM",3), #MSG_DEC
            inst("PUSHREG"),
            inst("POPIX"),
            inst("COMM",2),
            inst("PUSHIS",0),
            inst("PUSHIX"),
            inst("EQ"),
            inst("IF",3), #Go to Network 2 scope. If not return to terminal.
            inst("COMM",1),
            inst("PUSHIS",e652_gl_msg),
            inst("COMM",0),
            inst("COMM",2),
            inst("PUSHIS",0x41), #turn on flag 0x41. Not sure why but eh.
            inst("COMM",8),
            inst("COMM",0x45),
            inst("COMM",0x23),
            inst("PUSHIS",0x28c),
            inst("PUSHIS",0x1c),
            inst("PUSHIS",1),
            inst("COMM",0x97),
            inst("END"), #End go to Network 2 scope
            inst("PUSHIS",0),#Start Network 3 locked check scope.
            inst("PUSHIS",0x4a), 
            inst("COMM",7),
            inst("PUSHREG"),
            inst("EQ"),
            inst("IF",2), #Network 3 Locked scope
            inst("COMM",1),
            inst("PUSHIS",e652_locked_msg),
            inst("COMM",0),
            inst("COMM",2),
            inst("GOTO",0),
            inst("COMM",1), #Network 3 Unlocked scope
            inst("PUSHIS",e652_network3_msg),
            inst("COMM",0),
            inst("PUSHIS",7),
            inst("COMM",3),
            inst("PUSHREG"),
            inst("POPIX"),
            inst("COMM",2),
            inst("PUSHIS",0),
            inst("PUSHIX"),
            inst("EQ"),
            inst("IF",3),
            inst("COMM",1),
            inst("PUSHIS",e652_gl_msg),
            inst("COMM",0),
            inst("COMM",2),
            inst("PUSHIS",0x53), #Change Asakusa terminal to not have Hijiri.
            inst("COMM",8),
            inst("COMM",0x45),
            inst("COMM",0x23),
            inst("PUSHIS",0x296),
            inst("PUSHIS",0x1e),
            inst("PUSHIS",1),
            inst("COMM",0x97),
            inst("END"),
            inst("PUSHIS",8),#Returning to beginning code. Resetting camera.
            inst("PUSHIX"),
            inst("COMM",0x4b),
            inst("PUSHIS",0),
            inst("PUSHIS",0xa),
            inst("PUSHIS",0),
            inst("PUSHIS",0xb),
            inst("PUSHIX"),
            inst("COMM",0x73),
            inst("PUSHSTR",344),
            inst("COMM",0x94),
            inst("PUSHREG"),
            inst("COMM",0x12),
            inst("PUSHSTR",356),
            inst("COMM",0x94),
            inst("PUSHREG"),
            inst("PUSHSTR",350),
            inst("COMM",0x94),
            inst("PUSHREG"),
            inst("COMM",0x13),
            inst("GOTO",0),
            inst("END") #end label location. Also here to not trip off a warning in the assembler.
        ]
        e652_kept_insts[31] = inst("IF",4) #END label for the kept portion.
        e652_labels = [
            e652_labels[e652_terminal_label_index], #TERMINAL label.
            assembler.label("NETWORK2_SCOPE",len(e652_kept_insts) + 31),
            assembler.label("NETWORK3_SCOPE",len(e652_kept_insts) + 42),
            assembler.label("NETWORK3_SCOPE",len(e652_kept_insts) + 67),
            assembler.label("END_LABEL",len(e652_kept_insts) + 88)
        ]
        e652_obj.changeProcByIndex(e652_kept_insts + e652_insert_insts, e652_labels, e652_proc)
        self.dds3.add_new_file(custom_vals.SCRIPT_OBJ_PATH['e652'],BytesIO(bytes(e652_obj.toBytes())))
 
        if SCRIPT_DEBUG:
            self.script_debug_out(e652_obj,'e652.bf')

        #e660 version.
        #Issue is there is no yes/no decision text :(
        e660_obj = self.get_script_obj_by_name('e660')
        e660_proc = e660_obj.getProcIndexByLabel('e660_trm')
        e660_insts, e660_labels = e660_obj.getProcInstructionsLabelsByIndex(e660_proc)
        e660_terminal_label_index = 0 #relative index for TERMINAL label. Absolute is 13
        e660_kept_insts = e660_insts[:52] #0-31 is terminal code. 32-51 has camera to hijiri code.
        e660_network2_msg = e660_obj.appendMessage("I think a "+self.get_checks_boss_name("Specter 2",world)+ " is in Amala Network 2. Go?","NETWORK2_MSG")
        e660_network3_msg = e660_obj.appendMessage(self.get_checks_boss_name("Specter 3",world) + " is pulling me in! ...Save Hijiri?","NETWORK3_MSG")
        e660_locked_msg = e660_obj.appendMessage("Come back after you've completed Yoyogi Park and I will take you to Amala Network 3.","LOCKED_MSG")
        e660_gl_msg = e660_obj.appendMessage("Good luck!","GL_MSG")
        e660_yesno_msg = e660_obj.appendMessage("Yes^t^.No^t","YES_NO_SEL",is_decision=True)
        e660_insert_insts = [
            inst("PUSHIS",0),
            inst("PUSHIS",0x5f9), #Check if gone in Network 2
            inst("COMM",7),
            inst("PUSHREG"),
            inst("EQ"),
            inst("IF",1), #0x5f9 check (Network 2) scope
            inst("COMM",1),
            inst("PUSHIS",e660_network2_msg),
            inst("COMM",0),
            inst("PUSHIS",e660_yesno_msg), #Sure/No thanks
            inst("COMM",3), #MSG_DEC
            inst("PUSHREG"),
            inst("POPIX"),
            inst("COMM",2),
            inst("PUSHIS",0),
            inst("PUSHIX"),
            inst("EQ"),
            inst("IF",3), #Go to Network 2 scope. If not return to terminal.
            inst("COMM",1),
            inst("PUSHIS",e660_gl_msg),
            inst("COMM",0),
            inst("COMM",2),
            inst("PUSHIS",0x41), #turn on flag 0x41. Not sure why but eh.
            inst("COMM",8),
            inst("COMM",0x45),
            inst("COMM",0x23),
            inst("PUSHIS",0x28c),
            inst("PUSHIS",0x1c),
            inst("PUSHIS",1),
            inst("COMM",0x97),
            inst("END"), #End go to Network 2 scope
            inst("PUSHIS",0),#Start Network 3 locked check scope.
            inst("PUSHIS",0x4a), 
            inst("COMM",7),
            inst("PUSHREG"),
            inst("EQ"),
            inst("IF",2), #Network 3 Locked scope
            inst("COMM",1),
            inst("PUSHIS",e660_locked_msg),
            inst("COMM",0),
            inst("COMM",2),
            inst("GOTO",0),
            inst("COMM",1), #Network 3 Unlocked scope
            inst("PUSHIS",e660_network3_msg),
            inst("COMM",0),
            inst("PUSHIS",e660_yesno_msg),
            inst("COMM",3),
            inst("PUSHREG"),
            inst("POPIX"),
            inst("COMM",2),
            inst("PUSHIS",0),
            inst("PUSHIX"),
            inst("EQ"),
            inst("IF",3),
            inst("COMM",1),
            inst("PUSHIS",e660_gl_msg),
            inst("COMM",0),
            inst("COMM",2),
            inst("PUSHIS",0x53), #Change Asakusa terminal to not have Hijiri.
            inst("COMM",8),
            inst("COMM",0x45),
            inst("COMM",0x23),
            inst("PUSHIS",0x296),
            inst("PUSHIS",0x1e),
            inst("PUSHIS",1),
            inst("COMM",0x97),
            inst("END"),
            inst("PUSHIS",8),#Returning to beginning code. Resetting camera.
            inst("PUSHIX"),
            inst("COMM",0x4b),
            inst("PUSHIS",0),
            inst("PUSHIS",0xa),
            inst("PUSHIS",0),
            inst("PUSHIS",0xb),
            inst("PUSHIX"),
            inst("COMM",0x73),
            inst("PUSHSTR",24), #cam05
            inst("COMM",0x94),
            inst("PUSHREG"),
            inst("COMM",0x12),
            inst("PUSHSTR",36), #cam05_MOTION
            inst("COMM",0x94),
            inst("PUSHREG"),
            inst("PUSHSTR",24), #cam05
            inst("COMM",0x94),
            inst("PUSHREG"),
            inst("COMM",0x13),
            inst("GOTO",0),
            inst("END") #end label location. Also here to not trip off a warning in the assembler.
        ]
        e660_kept_insts[31] = inst("IF",4) #END label for the kept portion.
        e660_labels = [
            e660_labels[e660_terminal_label_index], #TERMINAL label.
            assembler.label("NETWORK2_SCOPE",len(e660_kept_insts) + 31),
            assembler.label("NETWORK3_SCOPE",len(e660_kept_insts) + 42),
            assembler.label("NETWORK4_SCOPE",len(e660_kept_insts) + 67),
            assembler.label("END_LABEL",len(e660_kept_insts) + 88)
        ]
        e660_obj.changeProcByIndex(e660_kept_insts + e660_insert_insts, e660_labels, e660_proc)
        self.dds3.add_new_file(custom_vals.SCRIPT_OBJ_PATH['e660'],BytesIO(bytes(e660_obj.toBytes())))

        if SCRIPT_DEBUG:
            self.script_debug_out(e660_obj,'e660.bf')

        #Cutscene removal in Asakusa Tunnel (anything at all?) f029

        #Cutscene removal in Yoyogi Park f016
        #TODO: Shorten Pixie stay/part scene to not have splash: Low Priority
        #Shorten Girimekhala and Sakahagi
        #Shorten Mother Harlot
        #Flags for each short cutscene in the area
        #set: 0x464, 0x465, 0x466, 0x467, 0x474
        #set: 0x4b. 0x3dd is yoyogi key.
        #0x4a is gary fight. e658. Door is 01d_10
        #wap entry of 0x1b94 in 
        #e701_main is Yuko differentiator in Yoyogi park. 
        e658_obj = self.get_script_obj_by_name("e658")
        e658_insts = [
            inst("PROC",0),
            inst("PUSHIS",0),
            inst("PUSHIS",0x4a),
            inst("COMM",7),
            inst("PUSHREG"),
            inst("EQ"),
            inst("IF",0),
            inst("PUSHIS",0x4a),
            inst("COMM",8),
            inst("PUSHIS",658),
            inst("PUSHIS",0x133),
            inst("COMM",0x28),#CALL_EVENT_BATTLE
            inst("END"),
            inst("PUSHIS",658),
            inst("PUSHIS",16),
            inst("PUSHIS",1),
            inst("COMM",0x97),
            inst("COMM",0x23),
            inst("COMM",0x2e),
            inst("END")
        ]
        e658_labels = [
            assembler.label("GARY_FOUGHT",13)
        ]
        e658_obj.changeProcByIndex(e658_insts,e658_labels,0)
        self.dds3.add_new_file(custom_vals.SCRIPT_OBJ_PATH['e658'],BytesIO(bytes(e658_obj.toBytes())))

        if SCRIPT_DEBUG:
            self.script_debug_out(e658_obj,'e658.bf')

        f016_obj = self.get_script_obj_by_name("f016")
        #018_start has pixie cutscene.
        f016_gary_reward_msg = f016_obj.appendMessage(self.get_reward_str("Girimehkala",world),"GARY_MSG")
        f016_gary_reward_insts = [
            inst("PROC",len(f016_obj.p_lbls().labels)),
            inst("COMM",0x60),
            inst("COMM",1),
            inst("PUSHIS",f016_gary_reward_msg),
            inst("COMM",0),
            inst("COMM",2),
            inst("COMM",0x61),
        ] + self.get_flag_reward_insts("Girimehkala",world) + [
            inst("END")
        ]
        f016_gary_reward_proc_str = "GARY_CB"
        f016_obj.appendProc(f016_gary_reward_insts, [], f016_gary_reward_proc_str)
        #Gary hint
        f016_obj.changeMessageByIndex(assembler.message("> You sense ^r"+self.get_checks_boss_name("Girimehkala",world)+"^p^nbeyond the door.^n^x> Will you enter?" ,"F016_DOOR01"),0x8a)        

        f016_mh_proc = f016_obj.getProcIndexByLabel('019_mother')
        f016_mh_insts, f016_mh_labels = f016_obj.getProcInstructionsLabelsByIndex(f016_mh_proc)
        f016_mh_insts[1] = inst("PUSHIS",0x3f5) #Change Harlot trigger from a story trigger to a key item
        f016_obj.changeProcByIndex(f016_mh_insts, f016_mh_labels, f016_mh_proc)

        f016_19_proc = f016_obj.getProcIndexByLabel('019_01eve_01')

        f016_19_insts = [
            inst("PROC",f016_19_proc),
            inst("PUSHIS",0x3f5), #Key item to enable Harlot
            inst("COMM",7),
            inst("PUSHREG"),
            inst("PUSHIS",0),
            inst("PUSHIS",0x759), #Didn't already run away
            inst("COMM",7),
            inst("PUSHREG"),
            inst("EQ"),
            inst("PUSHIS",0),
            inst("PUSHIS",0x116), #Didn't already beat her
            inst("COMM",7),
            inst("PUSHREG"),
            inst("EQ"),
            inst("AND"),
            inst("AND"),
            inst("IF",0), #End label
            inst("COMM",0x60),
            inst("COMM",1),
            inst("PUSHIS",0x4b), #"Stay here?"
            inst("COMM",0),
            inst("PUSHIS",0),
            inst("PUSHIS",0x4c), #">Yes/no"
            inst("COMM",3),
            inst("PUSHREG"),
            inst("EQ"),
            inst("IF",1), #Not quite end label
            inst("PUSHIS",0x116), #Fought flag
            inst("COMM",8),
            inst("PUSHIS",0x3e6), #Candelabra
            inst("COMM",8),
            inst("PUSHIS",0x924), #Fusion flag
            inst("COMM",8),
            inst("PUSHIS",0x2eb),
            inst("PUSHIS",0x10),
            inst("PUSHIS",1),
            inst("COMM",0x97), #Call next
            inst("PUSHIS",0x407),
            inst("COMM",0x67), #Fight Harlot
            inst("END"),
            inst("PUSHIS",0x759),
            inst("COMM",8),
            inst("COMM",0x61),
            inst("END")
        ]
        f016_19_labels = [
            assembler.label("HARLOT_FOUGHT",43),
            assembler.label("HARLOT_RAN",40)
        ]
        if config_settings.menorah_groups: #Remove candelabra if randomized
            del f016_19_insts[29:31]
            f016_19_labels = [
                assembler.label("HARLOT_FOUGHT",41),
                assembler.label("HARLOT_RAN",38)
            ]
        f016_obj.changeProcByIndex(f016_19_insts, f016_19_labels, f016_19_proc)

        f016_harlot_callback_str = "HARLOT_CB"
        f016_harlot_rwms_index = f016_obj.appendMessage(self.get_reward_str("The Harlot",world), "HARLOT_REWARD")
        f016_harlot_rwms_insts = [
            inst("PROC",len(f016_obj.p_lbls().labels)),
            inst("COMM",0x60),
            inst("COMM",1),
            inst("PUSHIS",f016_harlot_rwms_index),
            inst("COMM",0),
            inst("COMM",2),
            inst("COMM",0x61),
        ] + self.get_flag_reward_insts("The Harlot",world) + [
            inst("END")
        ]
        f016_obj.appendProc(f016_harlot_rwms_insts, [], f016_harlot_callback_str)
        self.insert_callback('f016',0xf4,f016_harlot_callback_str)

        f016_obj.changeMessageByIndex(assembler.message("You sense the presence of^n^r"+self.get_checks_boss_name("The Harlot",world)+"^p.","FIRE_YURE"),0x4a)

        #Golden goblet hint
        f016_demon_name_id = f016_obj.sections[3].messages[0x98].name_id
        f016_demon_message = assembler.message("I want a golden goblet!^n^xI hear you can find one^nat ^g"+self.get_flag_reward_location_string(0x3f5,world)+"^p.","F016_DEVIL03")
        f016_demon_message.name_id = f016_demon_name_id
        f016_obj.changeMessageByIndex(f016_demon_message,0x98)

        f016_lb = self.push_bf_into_lb(f016_obj,'f016')
        self.dds3.add_new_file(custom_vals.LB0_PATH['f016'],f016_lb)
        self.insert_callback('f016', 0x1b84, f016_gary_reward_proc_str)

        if SCRIPT_DEBUG:
            self.script_debug_out(f016_obj,'f016.bf')

        #Cutscene removal in Amala Network 3 f030
        #Shorten the one thing - if even because it's tiny. Add reward message
        f030_obj = self.get_script_obj_by_name("f030")
        #callback: 0xf4
        f030_specter3_callback_str = "SPEC3_CB"
        f030_specter3_rwms_index = f030_obj.appendMessage(self.get_reward_str("Specter 3",world), "SPECTER3_REWARD")
        f030_specter3_rwms_insts = [
            inst("PROC",len(f030_obj.p_lbls().labels)),
            inst("COMM",0x60),
            inst("COMM",1),
            inst("PUSHIS",f030_specter3_rwms_index),
            inst("COMM",0),
            inst("COMM",2),
            inst("COMM",0x61),
        ] + self.get_flag_reward_insts("Specter 3",world) + [
            inst("END")
        ]
        f030_obj.appendProc(f030_specter3_rwms_insts, [], f030_specter3_callback_str)
        self.insert_callback('f030',0xf4,f030_specter3_callback_str)
        
        f030_specter_proc = f030_obj.getProcIndexByLabel("002_01eve_01") #Change specter model to new boss
        f030_specter_insts, f030_specter_labels = f030_obj.getProcInstructionsLabelsByIndex(f030_specter_proc)
        f030_specter_insts[23] = inst("PUSHIS",self.get_checks_boss_id("Specter 3",world))
        f030_specter_insts[129] = inst("PUSHIS",4) #Change crashing animation to "spell"
        f030_obj.changeProcByIndex(f030_specter_insts, f030_specter_labels, f030_specter_proc)
        f030_obj.changeNameByLookup("Specter", self.get_checks_boss_name("Specter 3",world, immersive=True))
        
        f030_lb = self.push_bf_into_lb(f030_obj,'f030')
        self.dds3.add_new_file(custom_vals.LB0_PATH['f030'],f030_lb)
        
        if SCRIPT_DEBUG:
            self.script_debug_out(f030_obj,'f030.bf')

        #Cutscene removal in Amala Temple f034
        #Remove Intro and Fix Red Temple.
        #Shorten pre and post cutscenes. Make sure there are reward messages and a separate message for defeating all 3 that brings down the central pyramid.
        #Shorten ToK cutscene.
        #Look into for future versions: Have doors to temples locked by particular flags.
        #f034_obj = get_script_obj_by_name(iso,'f034')
        #In the procedure that sets the flag 6a0 and displays messages 1f - 25
        #002_start is outside.
        #lots of comm 104 and 103
        #002 -> 001 is entrance
        #002 -> 012 is red entrance
        #002 -> 004 is black entrance
        #002 -> 021 is white entrance
        f034_obj = self.get_script_obj_by_name("f034")
        #Bit checks in 001_start:
        #6ac, 6ae, 6ad, 6a0, 63. 6a7 off.
        #possibly cut 202-298 inclusive
        f034_02_proc = f034_obj.getProcIndexByLabel("002_start")
        f034_02_insts, f034_02_labels = f034_obj.getProcInstructionsLabelsByIndex(f034_02_proc)
        precut = 151
        postcut = 299
        diff = postcut - precut
        f034_02_insert_insts = [
            inst("PUSHIS",0x4a0),
            inst("COMM",8)
        ]
        f034_02_insts = f034_02_insts[:precut] + f034_02_insert_insts + f034_02_insts[postcut:]
        for l in f034_02_labels:
            if l.label_offset > precut:
                if l.label_offset < postcut:
                    l.label_offset = 0
                else:
                    l.label_offset -= diff
                    l.label_offset += len(f034_02_insert_insts)
        f034_obj.changeProcByIndex(f034_02_insts, f034_02_labels, f034_02_proc)

        #Plan: Completely gut the 002_01 events. The underground magatsuhi flows into the center won't show, but who gives a shit.
        #6aX:
        #   9 - Aciel spawn
        #   a - Skadi spawn
        #   b - Albion spawn
        #   c - Aciel callback (defeat confirmed)
        #   d - Skadi callback (defeat confirmed)
        #   e - Albion callback (defeat confirmed)
        #   f - Gets set after all 3 defeats are confirmed (cde), then enables 003_start in the center instead of 002_start.

        #Temp plan. Gut out 002_01 events and see what happens.
        f034_02_1_proc = f034_obj.getProcIndexByLabel('002_01eve_01')
        f034_02_2_proc = f034_obj.getProcIndexByLabel('002_01eve_02')
        f034_02_3_proc = f034_obj.getProcIndexByLabel('002_01eve_03')
        f034_obj.changeProcByIndex([inst("PROC",f034_02_1_proc),inst("END")], [], f034_02_1_proc)
        f034_obj.changeProcByIndex([inst("PROC",f034_02_2_proc),inst("END")], [], f034_02_2_proc)
        f034_obj.changeProcByIndex([inst("PROC",f034_02_3_proc),inst("END")], [], f034_02_3_proc)

        f034_wap_file_path = custom_vals.WAP_PATH['f034']
        f034_wap_file = bytes(self.dds3.get_file_from_path(f034_wap_file_path).read())
        wap_empty_entry = bytes([0]*0x38) + bytes(assembler.ctobb("01pos_01",8)) + bytes([0]*6) + bytes(assembler.ctobb("01cam_01",8)) + bytes([0,0,0,0,1,1]) + bytes([0]*0x10)

        #"Deleting" 2nd, 4th and 6th wap entries.
        f034_wap_file = f034_wap_file[:0xa0 + 0x64] + wap_empty_entry + f034_wap_file[0xa0 + (0x64*2):0xa0 + (0x64*3)] + wap_empty_entry + f034_wap_file[0xa0 + (0x64*4):0xa0 + (0x64*5)] + wap_empty_entry + f034_wap_file[0xa0 + (0x64*6):]
        #Thankfully there aren't any callbacks that need to be inserted.

        #Consider: The text called by 031_start "No one's here", change it to "You need the Himorogi"

        self.dds3.add_new_file(f034_wap_file_path,BytesIO(f034_wap_file)) #Write in normal WAP spot, but this isn't what we 'really' need.
        #What we really need to do is to write the WAP into all 4 LB files.
        f034a_lb_data = self.dds3.get_file_from_path(custom_vals.LB0_PATH['f034'])
        f034b_lb_data = self.dds3.get_file_from_path(custom_vals.LB0_PATH['f034b'])
        f034c_lb_data = self.dds3.get_file_from_path(custom_vals.LB0_PATH['f034c'])
        f034d_lb_data = self.dds3.get_file_from_path(custom_vals.LB0_PATH['f034d'])
        f034a_lb = LB_FS(f034a_lb_data)
        f034b_lb = LB_FS(f034b_lb_data)
        f034c_lb = LB_FS(f034c_lb_data)
        f034d_lb = LB_FS(f034d_lb_data)
        f034a_lb.read_lb()
        f034b_lb.read_lb()
        f034c_lb.read_lb()
        f034d_lb.read_lb()
        #f034a_lb = f034a_lb.export_lb({'WAP': BytesIO(f034_wap_file)})
        #f034b_lb = f034b_lb.export_lb({'WAP': BytesIO(f034_wap_file)})
        #f034c_lb = f034c_lb.export_lb({'WAP': BytesIO(f034_wap_file)})
        #f034d_lb = f034d_lb.export_lb({'WAP': BytesIO(f034_wap_file)})
        #dds3.add_new_file(custom_vals.LB0_PATH['f034'], f034a_lb)
        #dds3.add_new_file(custom_vals.LB0_PATH['f034b'], f034b_lb)
        #dds3.add_new_file(custom_vals.LB0_PATH['f034c'], f034c_lb)
        #dds3.add_new_file(custom_vals.LB0_PATH['f034d'], f034d_lb)

        #6aX:
        #   9 - Aciel spawn
        #   a - Skadi spawn
        #   b - Albion spawn
        #   c - Aciel callback (defeat confirmed)
        #   d - Skadi callback (defeat confirmed)
        #   e - Albion callback (defeat confirmed)
        #   f - Gets set after all 3 defeats are confirmed (cde), then enables 

        f034_temple_bosses_done_msg = f034_obj.appendMessage("All temple bosses defeated.^nThe central temple is now open.","CENTER_TEMPLE_MSG")

        #Albion callback
        f034_25_2_proc = f034_obj.getProcIndexByLabel('025_01eve_02')
        #Set 6ae, check 6ac and 6ad. If both are set then set 6af
        f034_albion_rwms = f034_obj.appendMessage(self.get_reward_str("Albion",world),"ALBION_RWMS") #Could change a message, but this is just easier.
        f034_25_2_insts = [
            inst("PROC",f034_25_2_proc),
            inst("PUSHIS",0x6ae),
            inst("COMM",8),
            inst("COMM",0x60),
            inst("COMM",1),
            inst("PUSHIS",f034_albion_rwms),
            inst("COMM",0),
            inst("PUSHIS",0x6ac),
            inst("COMM",7),
            inst("PUSHREG"),
            inst("PUSHIS",0x6ad),
            inst("COMM",7),
            inst("PUSHREG"),
            inst("AND"),
            inst("IF",0),#Check if other two bosses defeated.
            inst("PUSHIS",f034_temple_bosses_done_msg),
            inst("COMM",0),
            inst("PUSHIS",0x6af),
            inst("COMM",8),
            inst("COMM",2),#Label here. 19
            inst("COMM",0x61),
        ] + self.get_flag_reward_insts("Albion",world) + [
            inst("END")
        ]
        f034_25_2_labels = [
            assembler.label("ALBION_TO_CENTER",19)
        ]
        f034_obj.changeProcByIndex(f034_25_2_insts, f034_25_2_labels, f034_25_2_proc)

        f034_albion_hint_msg = f034_obj.appendMessage("You sense the presence of^n^r"+self.get_checks_boss_name("Albion",world)+"^p.","ALBION_HINT")
        f034_25_start_proc = f034_obj.getProcIndexByLabel("025_start")
        f034_25_start_insts, f034_25_start_labels = f034_obj.getProcInstructionsLabelsByIndex(f034_25_start_proc)
        f034_25_start_insts[100] = inst("PUSHIS",f034_albion_hint_msg)
        f034_obj.changeProcByIndex(f034_25_start_insts, f034_25_start_labels, f034_25_start_proc)

        #Skadi callback
        #Set 6ad, check 6ac and 6ae. If both are set then set 6af
        f034_18_2_proc = f034_obj.getProcIndexByLabel('018_01eve_02')
        f034_skadi_rwms = f034_obj.appendMessage(self.get_reward_str("Skadi",world), "SKADI_RWMS")
        f034_18_2_insts = [
            inst("PROC",f034_18_2_proc),
            inst("PUSHIS",0x6ad),
            inst("COMM",8),
            inst("COMM",0x60),
            inst("COMM",1),
            inst("PUSHIS",f034_skadi_rwms),
            inst("COMM",0),
            inst("PUSHIS",0x6ac),
            inst("COMM",7),
            inst("PUSHREG"),
            inst("PUSHIS",0x6ae),
            inst("COMM",7),
            inst("PUSHREG"),
            inst("AND"),
            inst("IF",0),#Check if other two bosses defeated.
            inst("PUSHIS",f034_temple_bosses_done_msg),
            inst("COMM",0),
            inst("PUSHIS",0x6af),
            inst("COMM",8),
            inst("COMM",2),#Label here. 19
            inst("COMM",0x61),
        ] + self.get_flag_reward_insts("Skadi",world) + [
            inst("END")
        ]
        f034_18_2_labels = [
            assembler.label("SKADI_TO_CENTER",19)
        ]
        f034_obj.changeProcByIndex(f034_18_2_insts, f034_18_2_labels, f034_18_2_proc)

        f034_skadi_hint_msg = f034_obj.appendMessage("You sense the presence of^n^r"+self.get_checks_boss_name("Skadi",world)+"^p.","SKADI_HINT")
        f034_18_start_proc = f034_obj.getProcIndexByLabel("018_start")
        f034_18_start_insts, f034_18_start_labels = f034_obj.getProcInstructionsLabelsByIndex(f034_18_start_proc)
        f034_18_start_insts[116] = inst("PUSHIS",f034_skadi_hint_msg)
        f034_obj.changeProcByIndex(f034_18_start_insts, f034_18_start_labels, f034_18_start_proc)

        #Aciel callback
        f034_10_2_proc = f034_obj.getProcIndexByLabel('010_01eve_02')
        #Set 6ac, check 6ae and 6ad. If both are set then set 6af
        f034_aciel_rwms = f034_obj.appendMessage(self.get_reward_str("Aciel",world),"ACIEL_RWMS")
        f034_10_2_insts = [
            inst("PROC",f034_10_2_proc),
            inst("PUSHIS",0x6ac),
            inst("COMM",8),
            inst("COMM",0x60),
            inst("COMM",1),
            inst("PUSHIS",f034_aciel_rwms),
            inst("COMM",0),
            inst("PUSHIS",0x6ad),
            inst("COMM",7),
            inst("PUSHREG"),
            inst("PUSHIS",0x6ae),
            inst("COMM",7),
            inst("PUSHREG"),
            inst("AND"),
            inst("IF",0),#Check if other two bosses defeated.
            inst("PUSHIS",f034_temple_bosses_done_msg),
            inst("COMM",0),
            inst("PUSHIS",0x6af),
            inst("COMM",8),
            inst("COMM",2),#Label here. 19
            inst("COMM",0x61),
        ] + self.get_flag_reward_insts("Aciel",world) + [
            inst("END")
        ]
        f034_10_2_labels = [
            assembler.label("ACIEL_TO_CENTER",19)
        ]
        f034_obj.changeProcByIndex(f034_10_2_insts, f034_10_2_labels, f034_10_2_proc)

        f034_aciel_hint_msg = f034_obj.appendMessage("You sense the presence of^n^r"+self.get_checks_boss_name("Aciel",world)+"^p.","ACIEL_HINT")
        f034_10_start_proc = f034_obj.getProcIndexByLabel("010_start")
        f034_10_start_insts, f034_10_start_labels = f034_obj.getProcInstructionsLabelsByIndex(f034_10_start_proc)
        f034_10_start_insts[96] = inst("PUSHIS",f034_aciel_hint_msg)
        f034_obj.changeProcByIndex(f034_10_start_insts, f034_10_start_labels, f034_10_start_proc)
        
        f034_aciel_proc = f034_obj.getProcIndexByLabel("010_01eve_01") #Change aciel model to new boss
        f034_aciel_insts, f034_aciel_labels = f034_obj.getProcInstructionsLabelsByIndex(f034_aciel_proc)
        f034_aciel_insts[55] = inst("PUSHIS",self.get_checks_boss_id("Aciel",world))
        f034_obj.changeProcByIndex(f034_aciel_insts, f034_aciel_labels, f034_aciel_proc)
        f034_obj.changeNameByLookup("Aciel", self.get_checks_boss_name("Aciel",world, immersive=True))
        
        f034_skadi_proc = f034_obj.getProcIndexByLabel("018_01eve_01") #Change skadi model to new boss
        f034_skadi_insts, f034_skadi_labels = f034_obj.getProcInstructionsLabelsByIndex(f034_skadi_proc)
        f034_skadi_insts[55] = inst("PUSHIS",self.get_checks_boss_id("Skadi",world))
        f034_obj.changeProcByIndex(f034_skadi_insts, f034_skadi_labels, f034_skadi_proc)
        f034_obj.changeNameByLookup("Skadi", self.get_checks_boss_name("Skadi",world, immersive=True))
        
        f034_albion_proc = f034_obj.getProcIndexByLabel("025_01eve_01") #Change albion model to new boss
        f034_albion_insts, f034_albion_labels = f034_obj.getProcInstructionsLabelsByIndex(f034_albion_proc)
        f034_albion_insts[57] = inst("PUSHIS",self.get_checks_boss_id("Albion",world))
        f034_obj.changeProcByIndex(f034_albion_insts, f034_albion_labels, f034_albion_proc)
        f034_obj.changeNameByLookup("Albion", self.get_checks_boss_name("Albion",world, immersive=True))

        #Center temple: 1st scene sets 0x864 and 0x52. 0x51 is the check. Keeping 0x51 set is probably safe.
        #   2nd scene checks 0x73. We want it to check Pyramidion instead.
        f034_03_01_proc = f034_obj.getProcIndexByLabel('003_01eve_01')
        f034_03_01_insts, f034_03_01_labels = f034_obj.getProcInstructionsLabelsByIndex(f034_03_01_proc)
        f034_03_01_insts[61] = inst("PUSHIS",0x3da) #Change flag check to key item (Himorogi)
        f034_obj.changeProcByIndex(f034_03_01_insts, f034_03_01_labels, f034_03_01_proc)
        
        #Pyramidion hint
        f034_obj.changeMessageByIndex(assembler.message("> What you seek is at^n^g"+self.get_flag_reward_location_string(0x3da,world)+"^p.","CENTER_DONE"),0x26)

        #Swap out Markro's INF.
        #Black Temple - Checks flag 0x03C0
        #    MSG 1 - 0x10
        #    MSG 2 - 0x13
        #White Temple - Checks flag 0x03C1
        #    MSG 1 - 0x11
        #    MSG 2 - 0x13
        #Red Temple - Checks flag 0x03C2
        #    MSG 1 - 0x12
        #    MSG 2 - 0x13
        f034_inf_patched = BytesIO(bytes(open(path.join(PATCHES_PATH,'Doors_F034.INF'),'rb').read()))
        self.dds3.add_new_file('/fld/f/f034/F034.INF', f034_inf_patched)
        f034_obj.changeMessageByIndex(assembler.message("This door is locked by the^n^bblack temple key^p,^nwhich is found in ^g"+self.get_flag_reward_location_string(0x3f1,world)+"^p.","BLACK_LOCK"),0x10)
        #get_flag_reward_location_string
        f034_obj.changeMessageByIndex(assembler.message("This door is locked by the^n^ywhite temple key^p,^nwhich is found in ^g"+self.get_flag_reward_location_string(0x3f2,world)+"^p.","WHITE_LOCK"),0x11)
        f034_obj.changeMessageByIndex(assembler.message("This door is locked by the^n^rred temple key^p,^nwhich is found in ^g"+self.get_flag_reward_location_string(0x3f3,world)+"^p.","RED_LOCK"),0x12)
        f034_obj.changeMessageByIndex(assembler.message("You have opened the locked door.","DOOR_OPEN"),0x13)
        #f034_lb = push_bf_into_lb(f034_obj, 'f034')
        #f034b_lb = push_bf_into_lb(f034_obj, 'f034b')
        #f034c_lb = push_bf_into_lb(f034_obj, 'f034c')
        #f034d_lb = push_bf_into_lb(f034_obj, 'f034d')

        f034_amb_a = self.dds3.get_file_from_path('/fld/f/f034/f034.amb')
        f034_amb_b = self.dds3.get_file_from_path('/fld/f/f034/f034b.amb')
        f034_amb_c = self.dds3.get_file_from_path('/fld/f/f034/f034c.amb')
        f034_amb_d = self.dds3.get_file_from_path('/fld/f/f034/f034d.amb')

        f034a_lb = f034a_lb.export_lb({'WAP': BytesIO(f034_wap_file), 'BF': BytesIO(bytes(f034_obj.toBytes())), 'ATMP': f034_amb_a, 'INF': f034_inf_patched})
        f034b_lb = f034b_lb.export_lb({'WAP': BytesIO(f034_wap_file), 'BF': BytesIO(bytes(f034_obj.toBytes())), 'ATMP': f034_amb_b, 'INF': f034_inf_patched})
        f034c_lb = f034c_lb.export_lb({'WAP': BytesIO(f034_wap_file), 'BF': BytesIO(bytes(f034_obj.toBytes())), 'ATMP': f034_amb_c, 'INF': f034_inf_patched})
        f034d_lb = f034d_lb.export_lb({'WAP': BytesIO(f034_wap_file), 'BF': BytesIO(bytes(f034_obj.toBytes())), 'ATMP': f034_amb_d, 'INF': f034_inf_patched})
        #Modified WAP is to remove the warping outside when you defeat one of the bosses (because internally you get warped outside, view the cutscene, then warped back in).
        #Modified BF as usual.
        #Modified ATMP/AMB because if I don't the map stays on the outside one whenever you go into a temple.
        #Modified INF for locked doors (though probably fine as just a_lb).

        self.dds3.add_new_file(custom_vals.LB0_PATH['f034'], f034a_lb)
        self.dds3.add_new_file(custom_vals.LB0_PATH['f034b'], f034b_lb)
        self.dds3.add_new_file(custom_vals.LB0_PATH['f034c'], f034c_lb)
        self.dds3.add_new_file(custom_vals.LB0_PATH['f034d'], f034d_lb)
        #set 0x51

        if SCRIPT_DEBUG:
            self.script_debug_out(f034_obj,'f034.bf')

        e703_obj = self.get_script_obj_by_name('e703')
        e703_msg = e703_obj.appendMessage("The Tower of ^r"+self.get_checks_boss_name("Kagutsuchi",world)+"^p has been lowered onto the Obelisk.^nThe Labyrinth of Amala is now closed.","TOK_LOWERED")
        ending_flag = 0x95 #Freedom
        if config_settings.yosuga:
            ending_flag = 0x91
        elif config_settings.shijima:
            ending_flag = 0x92
        elif config_settings.musubi:
            ending_flag = 0x93
        e703_insts = [
            inst("PROC",0),
            inst("PUSHIS",0x10),
            inst("PUSHIS",1),
            inst("COMM",0xf),
            inst("COMM",1),
            inst("PUSHIS",e703_msg),
            inst("COMM",0),
            inst("COMM",2),
            inst("PUSHIS",0x96),
            inst("COMM",8),
            inst("PUSHIS",0x4e2), #Unlock Nihilo Marunochi Terminal
            inst("COMM",8),
            inst("PUSHIS", ending_flag),
            inst("COMM",8),
            inst("COMM",0x23),#FLD_EVENT_END2
            inst("COMM",0x2e),
            inst("END")
        ]
        e703_TDE_insts = [
            inst("PUSHIS",0x126),
            inst("COMM",8),
            inst("PUSHIS",0x8c1),
            inst("COMM",8),
        ]
        if config_settings.fight_lucifer:
            e703_insts = e703_insts[:-3] + e703_TDE_insts + e703_insts[-3:]    

        e703_obj.changeProcByIndex(e703_insts,[],0)
        self.dds3.add_new_file(custom_vals.SCRIPT_OBJ_PATH['e703'], BytesIO(bytes(e703_obj.toBytes())))

        if SCRIPT_DEBUG:
            self.script_debug_out(e703_obj,'e703.bf')

        #Cutscene removal in Yurakucho Tunnel f021
        #Shorten Trumpeter
        #add archangels to room north of bead of life chest
        f021_obj = self.get_script_obj_by_name("f021")
        #Trumpeter is 001_01eve_04
        f021_toot_proc = f021_obj.getProcIndexByLabel("001_01eve_04")
        f021_toot_insts = [
            inst("PROC",f021_toot_proc),
            inst("PUSHIS",0),
            inst("PUSHIS",0x75a),#Didn't already run away
            inst("COMM",7),
            inst("PUSHREG"),
            inst("EQ"),
            inst("PUSHIS",0),
            inst("PUSHIS",0x118),#Didn't already fight
            inst("COMM",7),
            inst("PUSHREG"),
            inst("EQ"),
            inst("AND"),
            inst("IF",0),#End label
            inst("COMM",0x60),
            inst("COMM",1),
            inst("PUSHIS",0x39),#Do you want to stay here?
            inst("COMM",0),
            inst("PUSHIS",0),
            inst("PUSHIS",0x3a),#Yes/no
            inst("COMM",3),
            inst("PUSHREG"),
            inst("EQ"),
            inst("COMM",2),
            inst("IF",1),
            inst("PUSHIS",0x118), #turn on fought flag.
            inst("COMM",8),
            inst("PUSHIS",0x3e5), #give candelabra
            inst("COMM",8),
            inst("PUSHIS",0x925), #Fusion flag???
            inst("COMM",8),
            inst("PUSHIS",0x2ec),
            inst("PUSHIS",0x15),
            inst("PUSHIS",1),
            inst("COMM",0x97),
            inst("PUSHIS",0x408),
            inst("COMM",0x67),
            inst("END"),
            inst("PUSHIS",0x75a),
            inst("COMM",0x8),
            inst("COMM",0x61),
            inst("END")
        ]
        f021_toot_labels = [
            assembler.label("TOOT_RAN",40),
            assembler.label("TOOT_FOUGHT",37)
        ]
        if config_settings.menorah_groups: #Remove candelabra if randomized
            del f021_toot_insts[26:28]
            f021_toot_labels = [
                assembler.label("TOOT_RAN",38),
                assembler.label("TOOT_FOUGHT",35)
            ]
        f021_obj.changeProcByIndex(f021_toot_insts,f021_toot_labels,f021_toot_proc)

        f021_toot_rwms = f021_obj.appendMessage(self.get_reward_str("Trumpeter",world),"TOOT_RWMS")
        f021_toot_rwms_insts = [
            inst("PROC",len(f021_obj.p_lbls().labels)),
            inst("COMM",0x60),
            inst("COMM",1),
            inst("PUSHIS",f021_toot_rwms),
            inst("COMM",0),
            inst("COMM",2),
            inst("COMM",0x61),
        ] + self.get_flag_reward_insts("Trumpeter",world) + [
            inst("END")
        ]
        f021_toot_reward_proc_str = "TOOT_CB"
        f021_obj.appendProc(f021_toot_rwms_insts,[],f021_toot_reward_proc_str)
        self.insert_callback('f021', 0xf4, f021_toot_reward_proc_str)

        f021_obj.changeMessageByIndex(assembler.message("You sense the presence of^n^r"+self.get_checks_boss_name("Trumpeter",world)+"^p.","FIRE_YURE"),0x38)
        #f021_obj.changeMessageByIndex(assembler.message("At the Northern Temple,^nyou can get back lost keys^nwith this Kimon Stone I found.^nCheck it out if one of your^ntemple keys failed to drop!^n^xIt's just a backup though.^nDon't use it to cheat.","SIGE_04"),0x14) If bishamon drops all 3 keys use this

        f021_lb = self.push_bf_into_lb(f021_obj, 'f021')
        self.dds3.add_new_file(custom_vals.LB0_PATH['f021'], f021_lb)

        #TODO
        #Insert archangels in the same room that has "009_01eve_08"
        #Plan: Move 009_01eve_08 over to the door, and have the normal door opening moved OoB. At that point we have BF control.

        if SCRIPT_DEBUG:
            self.script_debug_out(f021_obj,'f021.bf')

        #Cutscene removal in Diet Building f033
        #Shorten Mada and Mithra. Add reward messages for all bosses.
        #Shorten Samael cutscene, as well as force Samael.
        #001_01eve_01 is Surt cutscene. No shortnening needed, but a callback is needed.
        #   Location value is: 0x226
        #0x694 set going into 007_start is Mada. No shortening needed, but a callback is needed.
        #   Location value is: 0x227
        #024_01eve_01 - 08 is Mot. "> Mot's magic is coming undone." can be used as reward message in 018_start.
        #   Message ID is: 0xd
        #029_01eve_01 is Mithra. Shortening possibly needed, but pretty low priority. 029_start has callback on the text: "O Kagutsuchi... Hath the destroyer (ry"
        #   Message ID is: 0x2d
        #e674_main is event with Samael. Shorten like Gary.
        f033_obj = self.get_script_obj_by_name("f033")

        f033_surt_rwms = f033_obj.appendMessage(self.get_reward_str("Surt",world),"SURT_RWMS")
        f033_surt_rwms_insts = [
            inst("PROC",len(f033_obj.p_lbls().labels)),
            inst("COMM",0x60),
            inst("COMM",1),
            inst("PUSHIS",f033_surt_rwms),
            inst("COMM",0),
            inst("COMM",2),
            inst("COMM",0x61),
        ] + self.get_flag_reward_insts("Surt",world) + [
            inst("END")
        ]

        f033_surt_reward_proc_str = "SURT_CB"
        f033_obj.appendProc(f033_surt_rwms_insts,[],f033_surt_reward_proc_str)
        self.insert_callback('f033', 0x37a4, f033_surt_reward_proc_str)
        
        #Diet building hints
        f033_obj.changeMessageByIndex(assembler.message("> There is a statue of ^r"+self.get_checks_boss_name("Surt",world)+"^p." ,"F033_DOZO01_02"),0x57)
        
        f033_surt_name_id = f033_obj.sections[3].messages[0x3].name_id
        f033_surt_message = assembler.message("I am the guardian of this building.^n^xThou shan't reach ^r"+self.get_checks_boss_name("Mada",world)+"^p." ,"ITAGAKI_DOUZOU_1")
        f033_surt_message.name_id = f033_surt_name_id
        f033_obj.changeMessageByIndex(f033_surt_message,0x3)
        
        f033_mada_name_id = f033_obj.sections[3].messages[0x7].name_id
        f033_mada_message = assembler.message("...But, I cannot let you get to^n^r"+self.get_checks_boss_name("Mot",world)+"^p.^n^xThe Magatsuhi in this building is^nalready ours.^n^xAll we have to do now is summon^nour god, and we will receive^nthe Reason of Shijima!^nI will not allow you to meddle with^nour commander.^n^xI, "+self.get_checks_boss_name("Mada",world, immersive=True)+", will personally hand you^na ticket to hell!" ,"OOKUMA_DOUZOU")
        f033_mada_message.name_id = f033_mada_name_id
        f033_obj.changeMessageByIndex(f033_mada_message,0x7)
        
        f033_mot_name_id = f033_obj.sections[3].messages[0x1b].name_id
        f033_mot_message = assembler.message("Curse thee...^n^xCurse thee, knave...!^n^xI shall smite thee down myself!^n^xThou shan't see^n^r"+self.get_checks_boss_name("Mithra",world)+"^p nor ^r"+self.get_checks_boss_name("Samael",world)+"^p!" ,"MITUKETANODA")
        f033_mot_message.name_id = f033_mot_name_id
        f033_obj.changeMessageByIndex(f033_mot_message,0x1b)

        f033_mot_proc = f033_obj.getProcIndexByLabel("024_moto_on") #Change mot model to new boss
        f033_mot_insts, f033_mot_labels = f033_obj.getProcInstructionsLabelsByIndex(f033_mot_proc)
        f033_mot_insts[12] = inst("PUSHIS",self.get_checks_boss_id("Mot",world))
        f033_mot_insts[38] = inst("PUSHIS",self.get_checks_boss_id("Mot",world))
        f033_mot_insts[64] = inst("PUSHIS",self.get_checks_boss_id("Mot",world))
        f033_mot_insts[90] = inst("PUSHIS",self.get_checks_boss_id("Mot",world)) #mot is loaded 4 times, unsure which is correct
        f033_obj.changeProcByIndex(f033_mot_insts, f033_mot_labels, f033_mot_proc)
        f033_obj.changeNameByLookup("Mot", self.get_checks_boss_name("Mot",world, immersive=True))
        
        f033_mada_rwms = f033_obj.appendMessage(self.get_reward_str("Mada",world),"MADA_RWMS")
        f033_mada_rwms_insts = [
            inst("PROC",len(f033_obj.p_lbls().labels)),
            inst("COMM",0x60),
            inst("COMM",1),
            inst("PUSHIS",f033_mada_rwms),
            inst("COMM",0),
            inst("COMM",2),
            inst("COMM",0x61),
        ] + self.get_flag_reward_insts("Mada",world) + [
            inst("END")
        ]

        f033_mada_reward_proc_str = "MADA_CB"
        f033_obj.appendProc(f033_mada_rwms_insts,[],f033_mada_reward_proc_str)
        self.insert_callback('f033', 0x3808, f033_mada_reward_proc_str)

        f033_obj.changeMessageByIndex(assembler.message(self.get_reward_str("Mot",world),"MOT_REWARD"),0xd)

        #Flag insertion for Mot after line 44. Need to move labels.
        f033_18_proc = f033_obj.getProcIndexByLabel('018_start')
        f033_18_insts, f033_18_labels = f033_obj.getProcInstructionsLabelsByIndex(f033_18_proc)
        f033_18_insert_insts = self.get_flag_reward_insts("Mot",world)
        f033_18_insts = f033_18_insts[:45] + f033_18_insert_insts + f033_18_insts[45:]
        for l in f033_18_labels:
            if l.label_offset > 45:
                l.label_offset += len(f033_18_insert_insts)
        f033_obj.changeProcByIndex(f033_18_insts, f033_18_labels, f033_18_proc)

        f033_29_proc = f033_obj.getProcIndexByLabel('029_01eve_01') #Mithra
        f033_29_insts = [
            inst("PROC",f033_29_proc),
            inst("PUSHIS",0),
            inst("PUSHIS",0x691),
            inst("COMM",0x7),
            inst("PUSHREG"),
            inst("EQ"),
            inst("IF",0),
            inst("PUSHIS",0x691),
            inst("COMM",0x8),
            inst("PUSHIS",0x919), #Fusion flag I think. Probably not necessary
            inst("COMM",0x8),
            inst("PUSHIS",0x22a),
            inst("PUSHIS",0x21),
            inst("PUSHIS",1),
            inst("COMM",0x97),
            inst("PUSHIS",0x3ca),
            inst("COMM",0x67),
            inst("END")
        ]
        f033_29_labels = [
            assembler.label("MITHRA_FOUGHT",17)
        ]

        f033_obj.changeProcByIndex(f033_29_insts, f033_29_labels, f033_29_proc)
        f033_obj.changeMessageByIndex(assembler.message(self.get_reward_str("Mithra",world),"MITHRA_REWARD"),0x2d)
        
        f033_29_start_proc = f033_obj.getProcIndexByLabel('029_start') #Mithra reward, DELETE if doesn't work right
        f033_29_start_insts, f033_29_start_labels = f033_obj.getProcInstructionsLabelsByIndex(f033_29_start_proc)
        f033_29_start_insts = f033_29_start_insts[0:28] + self.get_flag_reward_insts("Mithra",world) + f033_29_start_insts[28:]
        f033_29_start_labels[0].label_offset = f033_29_start_labels[0].label_offset + len(self.get_flag_reward_insts("Mithra",world))
        f033_29_start_labels[1].label_offset = f033_29_start_labels[1].label_offset + len(self.get_flag_reward_insts("Mithra",world))
        f033_obj.changeProcByIndex(f033_29_start_insts, f033_29_start_labels, f033_29_start_proc)

        f033_samael_rwms = f033_obj.appendMessage(self.get_reward_str("Samael",world),"SAMAEL_RWMS")
        f033_samael_rwms_insts = [
            inst("PROC",len(f033_obj.p_lbls().labels)),
            inst("COMM",0x60),
            inst("COMM",1),
            inst("PUSHIS",f033_samael_rwms),
            inst("COMM",0),
            inst("COMM",2),
            inst("COMM",0x61),
        ] + self.get_flag_reward_insts("Samael",world) + [
            inst("END")
        ]
        f033_samael_reward_proc_str = "SAMAEL_CB"
        f033_obj.appendProc(f033_samael_rwms_insts,[],f033_samael_reward_proc_str)
        self.insert_callback('f033', 0x3998, f033_samael_reward_proc_str)
        f033_lb = self.push_bf_into_lb(f033_obj, 'f033')
        self.dds3.add_new_file(custom_vals.LB0_PATH['f033'], f033_lb)

        if SCRIPT_DEBUG:
            self.script_debug_out(f033_obj,'f033.bf')

        #e674_main
        #set bits: 0x904, 0x72 (then calls battle 0x2a0). 0x73 (closes door), 0x3da, 0x870, 0x6b7 (off), 0x76, 0x70, 0x71, 
        e674_obj = self.get_script_obj_by_name('e674')
        e674_insts = [
            inst("PROC",0),
            inst("PUSHIS",0),
            inst("PUSHIS",0x73),
            inst("COMM",7),
            inst("PUSHREG"),
            inst("EQ"),
            inst("IF",0),
            inst("PUSHIS",0x73),
            inst("COMM",8),
            inst("PUSHIS",0x2a2),
            inst("PUSHIS",0x2a0),
            inst("COMM",0x28),
            inst("END"),
            inst("PUSHIS",0x2a2),#guess
            inst("PUSHIS",33),
            inst("PUSHIS",1),
            inst("COMM",0x97),
            inst("COMM",0x23),#FLD_EVENT_END2
            inst("COMM",0x2e),
            inst("END")
        ]
        e674_labels = [
            assembler.label("SAMAEL_DEFEATED",13)
        ]
        e674_obj.changeProcByIndex(e674_insts,e674_labels,0)
        self.dds3.add_new_file(custom_vals.SCRIPT_OBJ_PATH['e674'], BytesIO(bytes(e674_obj.toBytes())))

        if SCRIPT_DEBUG:
            self.script_debug_out(e674_obj,'e674.bf')

        #Going into ToK is 015_01eve_02 of Obelisk
        #With 0x660 set it's super quick.

        #Cutscene removal in ToK1 f032
        #Shorten Ahriman
        #If possible, have block puzzle already solved
        #Block puzzle to ahriman is in 017. Probably initialized with 017_start.
        #9&10 is middle block. 5&7 is front block. 6&8 is far block.
        #e681 is Ahriman. e678 is Ahriman dead.
        e681_obj = self.get_script_obj_by_name('e681')
        e681_insts = [
            inst("PROC",0),
            inst("PUSHIS",0x75),
            inst("COMM",8),
            inst("PUSHIS",0x74),
            inst("COMM",8),
            inst("PUSHIS",0x2a6),
            inst("PUSHIS", 0x3e0), #Ahriman mysterious 2nd appearance
            #inst("PUSHIS", 0x1c2), #Beelzebub
            #inst("PUSHIS",0x14e),
            inst("COMM",0x28),
            inst("PUSHIS",0x3df),
            inst("COMM",8),
            inst("PUSHIS",0x2a9),
            inst("PUSHIS",32),
            inst("PUSHIS",1),
            inst("COMM",0x97),
            inst("COMM",0x23),#FLD_EVENT_END2
            inst("COMM",0x2e),
            inst("END")
        ]
        if not config_settings.shijima: #Don't fight Ahriman in Shijima
           e681_obj.changeProcByIndex(e681_insts,[],0)
           self.dds3.add_new_file(custom_vals.SCRIPT_OBJ_PATH['e681'], BytesIO(bytes(e681_obj.toBytes())))
        #Could probably blank out e678

        if SCRIPT_DEBUG:
            self.script_debug_out(e681_obj,'e681.bf')

        f032_obj = self.get_script_obj_by_name('f032')
        
        #Ahriman hint
        f032_obj.changeMessageByIndex(assembler.message("I saw an incredible demon up ahead.^nIt's big! It's red!^n^xIt's ^r"+self.get_checks_boss_name("Ahriman",world)+"^p!" ,"F032_MANE07"),0x76)
        
        f032_lb = self.push_bf_into_lb(f032_obj, 'f032')
        self.dds3.add_new_file(custom_vals.LB0_PATH['f032'], f032_lb)
            
        if SCRIPT_DEBUG:
            self.script_debug_out(f032_obj,'f032.bf')

        #Cutscene removal in ToK2 f036
        #Shorten Noah
        #013_01eve_09 is block. (inverse is 10)
        #e680 is noah. e677 is noah dead.
        e680_obj = self.get_script_obj_by_name('e680')
        e680_insts = [
            inst("PROC",0),
            inst("PUSHIS",0x62),
            inst("COMM",8),
            inst("PUSHIS",0x61),
            inst("COMM",8),
            inst("PUSHIS",0x2a5),
            inst("PUSHIS", 0x3e1), #Noah mysterious 2nd appearance
            #inst("PUSHIS", 0x1c1), #Metatron
            #inst("PUSHIS",0x1d8),
            inst("COMM",0x28),
            inst("PUSHIS",0x3e0),
            inst("COMM",8),
            inst("PUSHIS",680),
            inst("PUSHIS",36),
            inst("PUSHIS",1),
            inst("COMM",0x97),
            inst("COMM",0x23),#FLD_EVENT_END2
            inst("COMM",0x2e),
            inst("END")
        ]
        if not config_settings.musubi: #Don't fight Noah in Musubi
            e680_obj.changeProcByIndex(e680_insts,[],0)
            self.dds3.add_new_file(custom_vals.SCRIPT_OBJ_PATH['e680'], BytesIO(bytes(e680_obj.toBytes())))

        if SCRIPT_DEBUG:
            self.script_debug_out(e680_obj,'e680.bf')

        #By setting 0x660, some stuff doesn't properly work. We'd like to keep 0x660 on, so we'll change the flag (using new flags, a30 and a31). This also allows direct ToK2 and ToK3 to work properly.
        #Change 012_start to use the 0xa30 flag and 013_start to be a duplicate (013 doesn't exist as a proc, but it's still referenced, and it's exactly where we want it).
        #There's a super duper corner-case scenario where you unlock ToK2 terminal externally, warp directly to ToK2, which doesn't trigger 012_start, then you go into 014 or 015 and it'll look weird. You still can't progress or lock yourself, and going back into 012 will call 012_start and fix it, so as far as I'm concerned there is no issue whatsoever. If someone submits a bug report for this situation, point them to this comment and say it is known and does not need to be fixed.
        f036_obj = self.get_script_obj_by_name('f036')
        f036_12_proc = f036_obj.getProcIndexByLabel('012_start')
        f036_12_insts, f036_12_labels = f036_obj.getProcInstructionsLabelsByIndex(f036_12_proc)
        f036_12_insts[2] = inst("PUSHIS",0xa30)
        f036_12_insts[227] = inst("PUSHIS",0xa30)

        f036_13_insts = copy.deepcopy(f036_12_insts)
        f036_13_labels = copy.deepcopy(f036_12_labels) #Need to deepcopy the labels because changeProcByIndex changes the label offsets from relative to absolute, and I didn't think of this situation when I wrote the assembler.

        f036_obj.changeProcByIndex(f036_12_insts, f036_12_labels, f036_12_proc)

        #Repurpose for 013, then append it.
        f036_13_labels[0].label_str = "_13_START_LABEL"
        f036_13_insts[0] = inst("PROC",len(f036_obj.p_lbls().labels))
        f036_obj.appendProc(f036_13_insts, f036_13_labels, "013_start")
        
        #Noah hint
        if not config_settings.vanilla_tok:
            f036_obj.changeMessageByIndex(assembler.message("............^n^xI see......^n^xThen, go in. ^r"+self.get_checks_boss_name("Noah",world)+"^p^nis waiting..." ,"F036_SINEN03_YES"),0x32)

        f036_lb = self.push_bf_into_lb(f036_obj, 'f036')
        self.dds3.add_new_file(custom_vals.LB0_PATH['f036'], f036_lb)

        if SCRIPT_DEBUG:
            self.script_debug_out(f036_obj,'f036.bf')

        #Cutscene removal in ToK3 f037
        #Shorten Thor 2
        #Shorten Baal
        #Shorten Kagutsuchi and Lucifer
        #If possible, have block puzzle after Thor 2 already solved
        #Thor 2 is 007_01eve_05. 007_THOR_AFTER exists.
        #007_01eve_03 is center block. (inverse is 04)
        #Baal is e682. e679 is baal dead.
        #0x665 is ToK3 top splash.
        #027_01eve_04 is left pillar, 05 is middle, 06 is right. 07 is central pillar to Kagutsuchi.
        #e705?
        e682_obj = self.get_script_obj_by_name('e682')
        e682_insts = [
            inst("PROC",0),
            inst("PUSHIS",0x83),
            inst("COMM",8),
            inst("PUSHIS",0x84),
            inst("COMM",8),
            inst("PUSHIS",0x2a7),
            inst("PUSHIS",0x14d),
            inst("COMM",0x28),
            inst("PUSHIS",0x3d3),
            inst("COMM",8),
            inst("PUSHIS",682),
            inst("PUSHIS",37),
            inst("PUSHIS",1),
            inst("COMM",0x97),
            inst("COMM",0x23),#FLD_EVENT_END2
            inst("COMM",0x2e),
            inst("END")
        ]
        e682_obj.changeProcByIndex(e682_insts,[],0)
        self.dds3.add_new_file(custom_vals.SCRIPT_OBJ_PATH['e682'], BytesIO(bytes(e682_obj.toBytes())))

        if SCRIPT_DEBUG:
            self.script_debug_out(e682_obj,'e682.bf')
            self.script_debug_out(self.get_script_obj_by_name('e718'),'e718.bf')
            self.script_debug_out(self.get_script_obj_by_name('e719'),'e719.bf')

        f037_obj = self.get_script_obj_by_name('f037')
        #Same 0x660 problem as ToK2. Use 0xa31, a32, a33, a34 instead.
        f037_19_proc = f037_obj.getProcIndexByLabel('019_start')
        f037_19_insts, f037_19_labels = f037_obj.getProcInstructionsLabelsByIndex(f037_19_proc)
        f037_19_insts[2] = inst("PUSHIS",0xa31)
        f037_19_insts[67] = inst("PUSHIS",0xa31)
        f037_obj.changeProcByIndex(f037_19_insts, f037_19_labels, f037_19_proc)

        f037_20_proc = f037_obj.getProcIndexByLabel('020_start')
        f037_20_insts, f037_20_labels = f037_obj.getProcInstructionsLabelsByIndex(f037_20_proc)
        f037_20_insts[2] = inst("PUSHIS",0xa32)
        f037_20_insts[27] = inst("PUSHIS",0xa32)
        f037_obj.changeProcByIndex(f037_20_insts, f037_20_labels, f037_20_proc)

        #37 for 21
        f037_21_proc = f037_obj.getProcIndexByLabel('021_start')
        f037_21_insts, f037_21_labels = f037_obj.getProcInstructionsLabelsByIndex(f037_21_proc)
        f037_21_insts[2] = inst("PUSHIS",0xa33)
        f037_21_insts[37] = inst("PUSHIS",0xa33)
        f037_obj.changeProcByIndex(f037_21_insts, f037_21_labels, f037_21_proc)

        #47 for 23
        f037_23_proc = f037_obj.getProcIndexByLabel('023_start')
        f037_23_insts, f037_23_labels = f037_obj.getProcInstructionsLabelsByIndex(f037_23_proc)
        f037_23_insts[2] = inst("PUSHIS",0xa34)
        f037_23_insts[47] = inst("PUSHIS",0xa34)
        f037_obj.changeProcByIndex(f037_23_insts, f037_23_labels, f037_23_proc)
        
        #Thor 2 hint and reward message
        f037_obj.changeMessageByIndex(assembler.message("You can see ^r"+self.get_checks_boss_name("Thor 2",world)+"^p^nat the end of the hall." ,"THOR00"),0x2)
        f037_thor_name_id = f037_obj.sections[3].messages[0x5].name_id
        f037_thor_message = assembler.message("...I am ^r"+self.get_checks_boss_name("Thor 2",world, immersive=True)+"^p. Our paths have not^ncrossed since the fall of the Mantra." ,"THOR03")
        f037_thor_message.name_id = f037_thor_name_id
        f037_obj.changeMessageByIndex(f037_thor_message,0x5)
        f037_obj.changeMessageByIndex(assembler.message(self.get_reward_str("Thor 2",world),"THOR04"),0x10)
        
        f037_thorafter_proc = f037_obj.getProcIndexByLabel("007_THOR_AFTER") #Change Thor 2 model to new boss before and after fight
        f037_thorafter_insts, f037_thorafter_labels = f037_obj.getProcInstructionsLabelsByIndex(f037_thorafter_proc)
        f037_thorafter_insts[8] = inst("PUSHIS",self.get_checks_boss_id("Thor 2",world))
        f037_obj.changeProcByIndex(f037_thorafter_insts, f037_thorafter_labels, f037_thorafter_proc)
        
        if not config_settings.vanilla_tok:
            f037_thor_proc = f037_obj.getProcIndexByLabel("007_01eve_05") #model is loaded differently here, beware of explosion
            f037_thor_insts, f037_thor_labels = f037_obj.getProcInstructionsLabelsByIndex(f037_thor_proc)
            f037_thor_insts[18] = inst("PUSHIS",self.get_checks_boss_id("Thor 2",world))
            f037_thor_insts[19] = inst("PUSHIS",6) #Same number as other model loads
            f037_obj.changeProcByIndex(f037_thor_insts, f037_thor_labels, f037_thor_proc)
        
        f037_obj.changeNameByLookup("Thor", self.get_checks_boss_name("Thor 2",world, immersive=True))
        
        #Baal hint for normal and Yosuga
        if not config_settings.vanilla_tok:
            f037_dominion_name_id = f037_obj.sections[3].messages[0x4d].name_id
            f037_dominion_message1 = assembler.message("If it isn't the Demi-fiend...^n^xWe've been waiting for you,^nand that stone you have in^nyour hands.^xLady ^r"+self.get_checks_boss_name("Baal Avatar",world)+"^p is waiting for^nyou up ahead. Please go on through." ,"F037_DEVIL03_01")
            f037_dominion_message1.name_id = f037_dominion_name_id
            f037_obj.changeMessageByIndex(f037_dominion_message1,0x4d)
            f037_dominion_message2 = assembler.message("If it isn't the Demi-fiend...^n^xI'm surprised you have the nerve to^neven see us!^n^xLady ^r"+self.get_checks_boss_name("Baal Avatar",world)+"^p^nis up ahead.^n^xYosuga shall take that stone^nyou have in your hands.^n...And your life." ,"F037_DEVIL03_02")
            f037_dominion_message2.name_id = f037_dominion_name_id
            f037_obj.changeMessageByIndex(f037_dominion_message2,0x4e)

        f037_lb = self.push_bf_into_lb(f037_obj, 'f037')
        self.dds3.add_new_file(custom_vals.LB0_PATH['f037'], f037_lb)

        if SCRIPT_DEBUG:
            self.script_debug_out(f037_obj,'f037.bf')
           
        f038_obj = self.get_script_obj_by_name('f038')
        f038_zouchou_proc = f038_obj.getProcIndexByLabel("001_01eve_10") #Zoucho model swap
        f038_zouchou_insts, f038_zouchou_labels = f038_obj.getProcInstructionsLabelsByIndex(f038_zouchou_proc)
        f038_zouchou_insts[116] = inst("PUSHIS",self.get_checks_boss_id("Zouchou",world))
        f038_obj.changeProcByIndex(f038_zouchou_insts, f038_zouchou_labels, f038_zouchou_proc)
        f038_jikoku_proc = f038_obj.getProcIndexByLabel("001_01eve_11") #Jikoku model swap
        f038_jikoku_insts, f038_jikoku_labels = f038_obj.getProcInstructionsLabelsByIndex(f038_jikoku_proc)
        f038_jikoku_insts[116] = inst("PUSHIS",self.get_checks_boss_id("Jikoku",world))
        f038_obj.changeProcByIndex(f038_jikoku_insts, f038_jikoku_labels, f038_jikoku_proc)
        f038_koumoku_proc = f038_obj.getProcIndexByLabel("001_01eve_12") #Koumoku model swap
        f038_koumoku_insts, f038_koumoku_labels = f038_obj.getProcInstructionsLabelsByIndex(f038_koumoku_proc)
        f038_koumoku_insts[116] = inst("PUSHIS",self.get_checks_boss_id("Koumoku",world))
        f038_obj.changeProcByIndex(f038_koumoku_insts, f038_koumoku_labels, f038_koumoku_proc)
        f038_bishamon_proc = f038_obj.getProcIndexByLabel("001_01eve_13") #Bishamon model swap
        f038_bishamon_insts, f038_bishamon_labels = f038_obj.getProcInstructionsLabelsByIndex(f038_bishamon_proc)
        f038_bishamon_insts[116] = inst("PUSHIS",self.get_checks_boss_id("Bishamon 2",world))
        f038_obj.changeProcByIndex(f038_bishamon_insts, f038_bishamon_labels, f038_bishamon_proc)
        
        f038_obj.changeNameByLookup("Zouchou", self.get_checks_boss_name("Zouchou",world, immersive=True))
        f038_obj.changeNameByLookup("Jikoku", self.get_checks_boss_name("Jikoku",world, immersive=True))
        f038_obj.changeNameByLookup("Koumoku", self.get_checks_boss_name("Koumoku",world, immersive=True))
        f038_obj.changeNameByLookup("Bishamon", self.get_checks_boss_name("Bishamon 2",world, immersive=True))
        
        f038_lb = self.push_bf_into_lb(f038_obj, 'f038')
        self.dds3.add_new_file(custom_vals.LB0_PATH['f038'], f038_lb)

        if SCRIPT_DEBUG:
            self.script_debug_out(f038_obj,'f038.bf')
        
        #LoA Kalpa Tunnel Skips
        f040_obj = self.get_script_obj_by_name('f040')
        f040_kalpa1_tunnel_proc = f040_obj.getProcIndexByLabel("001_01eve_02")
        f040_kalpa1_tunnel_insts, f040_kalpa1_tunnel_labels = f040_obj.getProcInstructionsLabelsByIndex(f040_kalpa1_tunnel_proc)
        f040_kalpa1_tunnel_insert_insts = [
            inst("PUSHIS",0x3e9),
            inst("PUSHIS",0x29),
            inst("PUSHIS",0x1),
            inst("COMM",0x97),
            inst("PUSHIS",0x2c7), #Call a null event (LoA Lobby 2 Cutscene)
            inst("COMM",0x66)
        ]
        f040_kalpa1_tunnel_insts = f040_kalpa1_tunnel_insts[0:64] + f040_kalpa1_tunnel_insert_insts + f040_kalpa1_tunnel_insts[66:-1] + [inst("END")]
        for l in f040_kalpa1_tunnel_labels:
            if l.label_offset > 64:
                l.label_offset += 4
        f040_obj.changeProcByIndex(f040_kalpa1_tunnel_insts, f040_kalpa1_tunnel_labels, f040_kalpa1_tunnel_proc)
        
        f040_kalpa2_tunnel_proc = f040_obj.getProcIndexByLabel("001_01eve_03")
        f040_kalpa2_tunnel_insts, f040_kalpa2_tunnel_labels = f040_obj.getProcInstructionsLabelsByIndex(f040_kalpa2_tunnel_proc)
        f040_kalpa2_tunnel_insert_insts = [
            inst("PUSHIS",0x3eb),
            inst("PUSHIS",0x2a),
            inst("PUSHIS",0x1),
            inst("COMM",0x97),
            inst("PUSHIS",0x2c7), #Call a null event (LoA Lobby 2 Cutscene)
            inst("COMM",0x66)
        ]
        f040_kalpa2_tunnel_insts = f040_kalpa2_tunnel_insts[0:64] + f040_kalpa2_tunnel_insert_insts + f040_kalpa2_tunnel_insts[66:-1] + [inst("END")]
        for l in f040_kalpa2_tunnel_labels:
            if l.label_offset > 64:
                l.label_offset += 4
        f040_obj.changeProcByIndex(f040_kalpa2_tunnel_insts, f040_kalpa2_tunnel_labels, f040_kalpa2_tunnel_proc)
        
        f040_kalpa3_tunnel_proc = f040_obj.getProcIndexByLabel("001_01eve_04")
        f040_kalpa3_tunnel_insts, f040_kalpa3_tunnel_labels = f040_obj.getProcInstructionsLabelsByIndex(f040_kalpa3_tunnel_proc)
        f040_kalpa3_tunnel_insert_insts = [
            inst("PUSHIS",0x3ed),
            inst("PUSHIS",0x2b),
            inst("PUSHIS",0x1),
            inst("COMM",0x97),
            inst("PUSHIS",0x2c7), #Call a null event (LoA Lobby 2 Cutscene)
            inst("COMM",0x66)
        ]
        f040_kalpa3_tunnel_insts = f040_kalpa3_tunnel_insts[0:64] + f040_kalpa3_tunnel_insert_insts + f040_kalpa3_tunnel_insts[66:-1] + [inst("END")]
        for l in f040_kalpa3_tunnel_labels:
            if l.label_offset > 64:
                l.label_offset += 4
        f040_obj.changeProcByIndex(f040_kalpa3_tunnel_insts, f040_kalpa3_tunnel_labels, f040_kalpa3_tunnel_proc)
        
        f040_kalpa4_tunnel_proc = f040_obj.getProcIndexByLabel("001_01eve_05")
        f040_kalpa4_tunnel_insts, f040_kalpa4_tunnel_labels = f040_obj.getProcInstructionsLabelsByIndex(f040_kalpa4_tunnel_proc)
        f040_kalpa4_tunnel_insert_insts = [
            inst("PUSHIS",0x3ef),
            inst("PUSHIS",0x2c),
            inst("PUSHIS",0x1),
            inst("COMM",0x97),
            inst("PUSHIS",0x2c7), #Call a null event (LoA Lobby 2 Cutscene)
            inst("COMM",0x66)
        ]
        f040_kalpa4_tunnel_insts = f040_kalpa4_tunnel_insts[0:64] + f040_kalpa4_tunnel_insert_insts + f040_kalpa4_tunnel_insts[66:-1] + [inst("END")]
        for l in f040_kalpa4_tunnel_labels:
            if l.label_offset > 64:
                l.label_offset += 4
        f040_obj.changeProcByIndex(f040_kalpa4_tunnel_insts, f040_kalpa4_tunnel_labels, f040_kalpa4_tunnel_proc)
        
        f040_kalpa5_tunnel_proc = f040_obj.getProcIndexByLabel("001_01eve_06")
        f040_kalpa5_tunnel_insts, f040_kalpa5_tunnel_labels = f040_obj.getProcInstructionsLabelsByIndex(f040_kalpa5_tunnel_proc)
        f040_kalpa5_tunnel_insert_insts = [
            inst("PUSHIS",0x3f1),
            inst("PUSHIS",0x2d),
            inst("PUSHIS",0x1),
            inst("COMM",0x97),
            inst("PUSHIS",0x2c7), #Call a null event (LoA Lobby 2 Cutscene)
            inst("COMM",0x66)
        ]
        f040_kalpa5_tunnel_insts = f040_kalpa5_tunnel_insts[0:64] + f040_kalpa5_tunnel_insert_insts + f040_kalpa5_tunnel_insts[66:-1] + [inst("END")]
        for l in f040_kalpa5_tunnel_labels:
            if l.label_offset > 64:
                l.label_offset += 4
        f040_obj.changeProcByIndex(f040_kalpa5_tunnel_insts, f040_kalpa5_tunnel_labels, f040_kalpa5_tunnel_proc)
        
        f040_lb = self.push_bf_into_lb(f040_obj, 'f040')
        self.dds3.add_new_file(custom_vals.LB0_PATH['f040'], f040_lb)
        
        f041_obj = self.get_script_obj_by_name('f041')

        f041_kalpa2_tunnel_proc = f041_obj.getProcIndexByLabel("002_01eve_02")
        f041_kalpa2_tunnel_insts, f041_kalpa2_tunnel_labels = f041_obj.getProcInstructionsLabelsByIndex(f041_kalpa2_tunnel_proc)
        f041_kalpa2_tunnel_insert_insts = [
            inst("PUSHIS",0x3ea),
            inst("PUSHIS",0x2a),
            inst("PUSHIS",0x1),
            inst("COMM",0x97),
            inst("PUSHIS",0x2c7), #Call a null event (LoA Lobby 2 Cutscene)
            inst("COMM",0x66)
        ]
        f041_kalpa2_tunnel_insts = f041_kalpa2_tunnel_insts[0:60] + f041_kalpa2_tunnel_insert_insts + f041_kalpa2_tunnel_insts[62:-1] + [inst("END")]
        for l in f041_kalpa2_tunnel_labels:
            if l.label_offset > 60:
                l.label_offset += 4
        f041_obj.changeProcByIndex(f041_kalpa2_tunnel_insts, f041_kalpa2_tunnel_labels, f041_kalpa2_tunnel_proc)
        
        f041_lobby_tunnel_proc = f041_obj.getProcIndexByLabel("001_01eve_02")
        f041_lobby_tunnel_insts, f041_lobby_tunnel_labels = f041_obj.getProcInstructionsLabelsByIndex(f041_lobby_tunnel_proc)
        f041_lobby_tunnel_insert_insts = [
            inst("PUSHIS",0x3e9),
            inst("PUSHIS",0x28),
            inst("PUSHIS",0x1),
            inst("COMM",0x97),
            inst("PUSHIS",0x2c7), #Call a null event (LoA Lobby 2 Cutscene)
            inst("COMM",0x66)
        ]
        f041_lobby_tunnel_insts = f041_lobby_tunnel_insts[0:60] + f041_lobby_tunnel_insert_insts + f041_lobby_tunnel_insts[62:-1] + [inst("END")]
        for l in f041_lobby_tunnel_labels:
            if l.label_offset > 60:
                l.label_offset += 4
        f041_obj.changeProcByIndex(f041_lobby_tunnel_insts, f041_lobby_tunnel_labels, f041_lobby_tunnel_proc)

        f041_lb = self.push_bf_into_lb(f041_obj, 'f041')
        self.dds3.add_new_file(custom_vals.LB0_PATH['f041'], f041_lb)
        
        f042_obj = self.get_script_obj_by_name('f042')

        f042_kalpa1_tunnel_proc = f042_obj.getProcIndexByLabel("001_01eve_02")
        f042_kalpa1_tunnel_insts, f042_kalpa1_tunnel_labels = f042_obj.getProcInstructionsLabelsByIndex(f042_kalpa1_tunnel_proc)
        f042_kalpa1_tunnel_insert_insts = [
            inst("PUSHIS",0x3ea),
            inst("PUSHIS",0x29),
            inst("PUSHIS",0x1),
            inst("COMM",0x97),
            inst("PUSHIS",0x2c7), #Call a null event (LoA Lobby 2 Cutscene)
            inst("COMM",0x66)
        ]
        f042_kalpa1_tunnel_insts = f042_kalpa1_tunnel_insts[0:60] + f042_kalpa1_tunnel_insert_insts + f042_kalpa1_tunnel_insts[62:-1] + [inst("END")]
        for l in f042_kalpa1_tunnel_labels:
            if l.label_offset > 60:
                l.label_offset += 4
        f042_obj.changeProcByIndex(f042_kalpa1_tunnel_insts, f042_kalpa1_tunnel_labels, f042_kalpa1_tunnel_proc)
        
        f042_lobby_tunnel_proc = f042_obj.getProcIndexByLabel("001_01eve_03")
        f042_lobby_tunnel_insts, f042_lobby_tunnel_labels = f042_obj.getProcInstructionsLabelsByIndex(f042_lobby_tunnel_proc)
        f042_lobby_tunnel_insert_insts = [
            inst("PUSHIS",0x3eb),
            inst("PUSHIS",0x28),
            inst("PUSHIS",0x1),
            inst("COMM",0x97),
            inst("PUSHIS",0x2c7), #Call a null event (LoA Lobby 2 Cutscene)
            inst("COMM",0x66)
        ]
        f042_lobby_tunnel_insts = f042_lobby_tunnel_insts[0:60] + f042_lobby_tunnel_insert_insts + f042_lobby_tunnel_insts[62:-1] + [inst("END")]
        for l in f042_lobby_tunnel_labels:
            if l.label_offset > 60:
                l.label_offset += 4
        f042_obj.changeProcByIndex(f042_lobby_tunnel_insts, f042_lobby_tunnel_labels, f042_lobby_tunnel_proc)  
        
        f042_kalpa3_tunnel_proc = f042_obj.getProcIndexByLabel("002_01eve_02")
        f042_kalpa3_tunnel_insts, f042_kalpa3_tunnel_labels = f042_obj.getProcInstructionsLabelsByIndex(f042_kalpa3_tunnel_proc)
        f042_kalpa3_tunnel_insert_insts = [
            inst("PUSHIS",0x3ec),
            inst("PUSHIS",0x2b),
            inst("PUSHIS",0x1),
            inst("COMM",0x97),
            inst("PUSHIS",0x2c7), #Call a null event (LoA Lobby 2 Cutscene)
            inst("COMM",0x66)
        ]
        f042_kalpa3_tunnel_insts = f042_kalpa3_tunnel_insts[0:60] + f042_kalpa3_tunnel_insert_insts + f042_kalpa3_tunnel_insts[62:-1] + [inst("END")]
        for l in f042_kalpa3_tunnel_labels:
            if l.label_offset > 60:
                l.label_offset += 4
        f042_obj.changeProcByIndex(f042_kalpa3_tunnel_insts, f042_kalpa3_tunnel_labels, f042_kalpa3_tunnel_proc)
        
        #Apoc stone hint
        f042_arahabaki_name_id = f042_obj.sections[3].messages[0x84].name_id
        f042_arahabaki_message = assembler.message("The riders are not here.^n^xThey left while sayeth their stone^nis at ^g"+self.get_flag_reward_location_string(0x3f4,world)+"^p.","MSG_F42_A2_AKUMA01")
        f042_arahabaki_message.name_id = f042_arahabaki_name_id
        f042_obj.changeMessageByIndex(f042_arahabaki_message,0x84)
        
        if config_settings.menorah_groups: #Menorah hint
            f042_obj.changeMessageByIndex(assembler.message("> Retrieve these candelabra^nfrom ^g"+self.get_flag_reward_location_string(0x3e7,world)+"^p.", "MSG_001_2"),0x6)
            
        f042_lb = self.push_bf_into_lb(f042_obj, 'f042')
        self.dds3.add_new_file(custom_vals.LB0_PATH['f042'], f042_lb)
        
        #LoA peephole cutscene skips
        e711_obj = self.get_script_obj_by_name('e711')
        e711_main_proc = e711_obj.getProcIndexByLabel("e711_main")
        e711_main_insts, e711_main_labels = e711_obj.getProcInstructionsLabelsByIndex(e711_main_proc)
        e711_main_insts = [e711_main_insts[0]] + [
            inst("PUSHIS",0x10b),
            inst("COMM",0x8),
            inst("COMM",0x23),
            inst("COMM",0x2e),
            inst("END")
        ]
        e711_obj.changeProcByIndex(e711_main_insts, [], e711_main_proc)
        self.dds3.add_new_file(custom_vals.SCRIPT_OBJ_PATH['e711'], BytesIO(bytes(e711_obj.toBytes())))
        
        e712_obj = self.get_script_obj_by_name('e712')
        e712_main_proc = e712_obj.getProcIndexByLabel("e712_main")
        e712_main_insts, e712_main_labels = e712_obj.getProcInstructionsLabelsByIndex(e712_main_proc)
        e712_main_insts = [e712_main_insts[0]] + [
            inst("PUSHIS",0x10d),
            inst("COMM",0x8),
            inst("PUSHIS",0x10e),
            inst("COMM",0x8),
            inst("COMM",0x23),
            inst("COMM",0x2e),
            inst("END")
        ]
        e712_obj.changeProcByIndex(e712_main_insts, [], e712_main_proc)
        self.dds3.add_new_file(custom_vals.SCRIPT_OBJ_PATH['e712'], BytesIO(bytes(e712_obj.toBytes())))
        
        e713_obj = self.get_script_obj_by_name('e713')
        e713_main_proc = e713_obj.getProcIndexByLabel("e713_main")
        e713_main_insts, e713_main_labels = e713_obj.getProcInstructionsLabelsByIndex(e713_main_proc)
        e713_main_insts = [e713_main_insts[0]] + [
            inst("PUSHIS",0x11a),
            inst("COMM",0x8),
            inst("COMM",0x23),
            inst("COMM",0x2e),
            inst("END")
        ]
        e713_obj.changeProcByIndex(e713_main_insts, [], e713_main_proc)
        self.dds3.add_new_file(custom_vals.SCRIPT_OBJ_PATH['e713'], BytesIO(bytes(e713_obj.toBytes())))
        
        e714_obj = self.get_script_obj_by_name('e714')
        e714_main_proc = e714_obj.getProcIndexByLabel("e714_main")
        e714_main_insts, e714_main_labels = e714_obj.getProcInstructionsLabelsByIndex(e714_main_proc)
        e714_main_insts = [e714_main_insts[0]] + [
            inst("PUSHIS",0x11b),
            inst("COMM",0x8),
            inst("COMM",0x23),
            inst("COMM",0x2e),
            inst("END")
        ]
        e714_obj.changeProcByIndex(e714_main_insts, [], e714_main_proc)
        self.dds3.add_new_file(custom_vals.SCRIPT_OBJ_PATH['e714'], BytesIO(bytes(e714_obj.toBytes())))
        
        e715_obj = self.get_script_obj_by_name('e715')
        e715_main_proc = e715_obj.getProcIndexByLabel("e715_main")
        e715_main_insts, e715_main_labels = e715_obj.getProcInstructionsLabelsByIndex(e715_main_proc)
        e715_main_insts = [e715_main_insts[0]] + [
            inst("PUSHIS",0x11c),
            inst("COMM",0x8),
            inst("PUSHIS",0x11e),
            inst("COMM",0x8),
            inst("COMM",0x23),
            inst("COMM",0x2e),
            inst("END")
        ]
        e715_obj.changeProcByIndex(e715_main_insts, [], e715_main_proc)
        self.dds3.add_new_file(custom_vals.SCRIPT_OBJ_PATH['e715'], BytesIO(bytes(e715_obj.toBytes())))
        
        #Shorten Dante 2 Fight
        e728_obj = self.get_script_obj_by_name('e728')
        
        e729_obj = self.get_script_obj_by_name('e729')
        e729_main_proc = e729_obj.getProcIndexByLabel("e729_main")
        e729_main_insts, e729_main_labels = e729_obj.getProcInstructionsLabelsByIndex(e729_main_proc)
        e729_main_insts = [e729_main_insts[0]] + [
            inst("PUSHIS",0),
            inst("PUSHIS",0x105),
            inst("COMM",7),
            inst("PUSHREG"),
            inst("EQ"),
            inst("IF",0),
            inst("PUSHIS",0x105),
            inst("COMM",0x8),
            inst("PUSHIS",0x2d9),
            inst("PUSHIS",0x40b),
            inst("COMM",0x28),
            inst("END"),
            inst("PUSHIS",0x2d9),
            inst("PUSHIS",0x2b),
            inst("PUSHIS",0x1),
            inst("COMM",0x97),
            inst("COMM",0x23),
            inst("COMM",0x2e),
            inst("END")
        ]
        e729_main_labels = [
            assembler.label("DANTE_FOUGHT",13)
        ]
        e729_obj.changeProcByIndex(e729_main_insts, e729_main_labels, e729_main_proc)
        self.dds3.add_new_file(custom_vals.SCRIPT_OBJ_PATH['e729'], BytesIO(bytes(e729_obj.toBytes())))
        
        
        #Dante 2 reward
        f043_obj = self.get_script_obj_by_name('f043')
        f043_dante_callback_proc = f043_obj.getProcIndexByLabel("012_battle_aft")
        f043_dante_callback_insts, f043_dante_callback_labels = f043_obj.getProcInstructionsLabelsByIndex(f043_dante_callback_proc)
        if config_settings.menorah_groups:
            f043_dante_callback_insts = f043_dante_callback_insts[0:8] + self.get_flag_reward_insts("Dante 2",world) + f043_dante_callback_insts[8:-1] + [inst("END")]
        else:
            f043_dante_menorah_insts = [
                inst("PUSHIS",0x3eb),
                inst("COMM",0x8),
            ]
            f043_dante_callback_insts = f043_dante_callback_insts[0:8] + self.get_flag_reward_insts("Dante 2",world) + f043_dante_menorah_insts + f043_dante_callback_insts[8:-1] + [inst("END")]
        f043_obj.changeProcByIndex(f043_dante_callback_insts, f043_dante_callback_labels, f043_dante_callback_proc)
        f043_obj.changeMessageByIndex(assembler.message(self.get_reward_str("Dante 2",world),"MSG_012_BATTLE_AFTER"),0x25)
        f043_obj.changeMessageByIndex(assembler.message("You sense the presence of^n^r"+self.get_checks_boss_name("Dante 2",world)+"^p.","FIRE_YURE"),0x31)

        #Fix doors in Dante chase sequence
        f043_door7_proc = f043_obj.getProcIndexByLabel("007_door_open")
        f043_door7_insts, f043_door7_labels = f043_obj.getProcInstructionsLabelsByIndex(f043_door7_proc)
        f043_door7_insts[2] = inst("PUSHIS", 0x12b) #Agree with riders flag for now
        f043_obj.changeProcByIndex(f043_door7_insts, f043_door7_labels, f043_door7_proc)
        f043_door5_proc = f043_obj.getProcIndexByLabel("005_door_open")
        f043_door5_insts, f043_door5_labels = f043_obj.getProcInstructionsLabelsByIndex(f043_door5_proc)
        f043_door5_insts[2] = inst("PUSHIS", 0x12b) #Agree with riders flag for now
        f043_obj.changeProcByIndex(f043_door5_insts, f043_door5_labels, f043_door5_proc)
        
        #Kalpa 3 tunnels
        f043_kalpa2_tunnel_proc = f043_obj.getProcIndexByLabel("001_01eve_02")
        f043_kalpa2_tunnel_insts, f043_kalpa2_tunnel_labels = f043_obj.getProcInstructionsLabelsByIndex(f043_kalpa2_tunnel_proc)
        f043_kalpa2_tunnel_insert_insts = [
            inst("PUSHIS",0x3ec),
            inst("PUSHIS",0x2a),
            inst("PUSHIS",0x1),
            inst("COMM",0x97),
            inst("PUSHIS",0x2c7), #Call a null event (LoA Lobby 2 Cutscene)
            inst("COMM",0x66)
        ]
        f043_kalpa2_tunnel_insts = f043_kalpa2_tunnel_insts[0:60] + f043_kalpa2_tunnel_insert_insts + f043_kalpa2_tunnel_insts[62:-1] + [inst("END")]
        for l in f043_kalpa2_tunnel_labels:
            if l.label_offset > 60:
                l.label_offset += 4
        f043_obj.changeProcByIndex(f043_kalpa2_tunnel_insts, f043_kalpa2_tunnel_labels, f043_kalpa2_tunnel_proc)
        
        f043_lobby_tunnel_proc = f043_obj.getProcIndexByLabel("001_01eve_03")
        f043_lobby_tunnel_insts, f043_lobby_tunnel_labels = f043_obj.getProcInstructionsLabelsByIndex(f043_lobby_tunnel_proc)
        f043_lobby_tunnel_insert_insts = [
            inst("PUSHIS",0x3ed),
            inst("PUSHIS",0x28),
            inst("PUSHIS",0x1),
            inst("COMM",0x97),
            inst("PUSHIS",0x2c7), #Call a null event (LoA Lobby 2 Cutscene)
            inst("COMM",0x66)
        ]
        f043_lobby_tunnel_insts = f043_lobby_tunnel_insts[0:60] + f043_lobby_tunnel_insert_insts + f043_lobby_tunnel_insts[62:-1] + [inst("END")]
        for l in f043_lobby_tunnel_labels:
            if l.label_offset > 60:
                l.label_offset += 4
        f043_obj.changeProcByIndex(f043_lobby_tunnel_insts, f043_lobby_tunnel_labels, f043_lobby_tunnel_proc)
        
        f043_kalpa4_tunnel_proc = f043_obj.getProcIndexByLabel("002_01eve_02")
        f043_kalpa4_tunnel_insts, f043_kalpa4_tunnel_labels = f043_obj.getProcInstructionsLabelsByIndex(f043_kalpa4_tunnel_proc)
        f043_kalpa4_tunnel_insert_insts = [
            inst("PUSHIS",0x3ee),
            inst("PUSHIS",0x2c),
            inst("PUSHIS",0x1),
            inst("COMM",0x97),
            inst("PUSHIS",0x2c7), #Call a null event (LoA Lobby 2 Cutscene)
            inst("COMM",0x66)
        ]
        f043_kalpa4_tunnel_insts = f043_kalpa4_tunnel_insts[0:60] + f043_kalpa4_tunnel_insert_insts + f043_kalpa4_tunnel_insts[62:-1] + [inst("END")]
        for l in f043_kalpa4_tunnel_labels:
            if l.label_offset > 60:
                l.label_offset += 4
        f043_obj.changeProcByIndex(f043_kalpa4_tunnel_insts, f043_kalpa4_tunnel_labels, f043_kalpa4_tunnel_proc)
        
        f043_star_tunnel_proc = f043_obj.getProcIndexByLabel("029_01eve_01")
        f043_star_tunnel_insts, f043_star_tunnel_labels = f043_obj.getProcInstructionsLabelsByIndex(f043_star_tunnel_proc)
        f043_star_tunnel_insert_insts = [
            inst("PUSHIS",0x3f2),
            inst("PUSHIS",0x2c),
            inst("PUSHIS",0x1),
            inst("COMM",0x97),
            inst("PUSHIS",0x2c7), #Call a null event (LoA Lobby 2 Cutscene)
            inst("COMM",0x66)
        ]
        f043_star_tunnel_insts = f043_star_tunnel_insts[0:60] + f043_star_tunnel_insert_insts + f043_star_tunnel_insts[62:-1] + [inst("END")]
        for l in f043_star_tunnel_labels:
            if l.label_offset > 60:
                l.label_offset += 4
        f043_obj.changeProcByIndex(f043_star_tunnel_insts, f043_star_tunnel_labels, f043_star_tunnel_proc)
        
        if config_settings.menorah_groups: #Menorah hint
            f043_obj.changeMessageByIndex(assembler.message("> Retrieve these candelabra^nfrom ^g"+self.get_flag_reward_location_string(0x3e4,world)+"^p.", "MSG_001_2"),0xc)
        
        f043_lb = self.push_bf_into_lb(f043_obj, 'f043')
        self.dds3.add_new_file(custom_vals.LB0_PATH['f043'], f043_lb)
        
        #Shorten Beelzebub
        e749_obj = self.get_script_obj_by_name('e749')
        e749_main_proc = e749_obj.getProcIndexByLabel("e749_main")
        e749_main_insts, e749_main_labels = e749_obj.getProcInstructionsLabelsByIndex(e749_main_proc)
        e749_main_insts = [e749_main_insts[0]] + [
            inst("PUSHIS",0),
            inst("PUSHIS",0x114),
            inst("COMM",7),
            inst("PUSHREG"),
            inst("EQ"),
            inst("IF",0),
            inst("PUSHIS",0x114),
            inst("COMM",0x8),
            inst("PUSHIS",0x928),
            inst("COMM",0x8),
            inst("PUSHIS",0x2ed),
            inst("PUSHIS",0x1c2),
            inst("COMM",0x28),
            inst("END"),
            inst("PUSHIS",0x2ed),
            inst("PUSHIS",0x2c),
            inst("PUSHIS",0x1),
            inst("COMM",0x97),
            inst("COMM",0x23),
            inst("COMM",0x2e),
            inst("END")
        ]
        e749_main_labels = [
            assembler.label("BELZ_FOUGHT",15)
        ]
        e749_obj.changeProcByIndex(e749_main_insts, e749_main_labels, e749_main_proc)
        self.dds3.add_new_file(custom_vals.SCRIPT_OBJ_PATH['e749'], BytesIO(bytes(e749_obj.toBytes())))

        #Beelzebub callback is 0x2e8 don't forget it
        f044_obj = self.get_script_obj_by_name('f044')

        f044_belz_rwms = f044_obj.appendMessage(self.get_reward_str("Beelzebub",world),"BELZ_RWMS")
        f044_belz_rwms_insts = [
            inst("PROC",len(f044_obj.p_lbls().labels)),
            inst("COMM",0x60),
            inst("COMM",1),
            inst("PUSHIS",f044_belz_rwms),
            inst("COMM",0),
            inst("COMM",2),
            inst("COMM",0x61),
        ] + self.get_flag_reward_insts("Beelzebub",world) + [
            inst("END")
        ]

        f044_belz_reward_proc_str = "BELZ_CB"
        f044_obj.appendProc(f044_belz_rwms_insts,[],f044_belz_reward_proc_str)
        self.insert_callback('f044', 0x2e8, f044_belz_reward_proc_str)
        
        f044_obj.changeMessageByIndex(assembler.message("> ^r"+self.get_checks_boss_name("Beelzebub",world)+"^p can be felt^nbehind the door.^n^x> Will you enter?" ,"F044_DOOR03"),0x83)

        #Skip kalpa 4 tunnels
        f044_kalpa3_tunnel_proc = f044_obj.getProcIndexByLabel("001_01eve_02")
        f044_kalpa3_tunnel_insts, f044_kalpa3_tunnel_labels = f044_obj.getProcInstructionsLabelsByIndex(f044_kalpa3_tunnel_proc)
        f044_kalpa3_tunnel_insert_insts = [
            inst("PUSHIS",0x3ee),
            inst("PUSHIS",0x2b),
            inst("PUSHIS",0x1),
            inst("COMM",0x97),
            inst("PUSHIS",0x2c7), #Call a null event (LoA Lobby 2 Cutscene)
            inst("COMM",0x66)
        ]
        f044_kalpa3_tunnel_insts = f044_kalpa3_tunnel_insts[0:60] + f044_kalpa3_tunnel_insert_insts + f044_kalpa3_tunnel_insts[62:-1] + [inst("END")]
        for l in f044_kalpa3_tunnel_labels:
            if l.label_offset > 60:
                l.label_offset += 4
        f044_obj.changeProcByIndex(f044_kalpa3_tunnel_insts, f044_kalpa3_tunnel_labels, f044_kalpa3_tunnel_proc)
        
        f044_lobby_tunnel_proc = f044_obj.getProcIndexByLabel("001_01eve_03")
        f044_lobby_tunnel_insts, f044_lobby_tunnel_labels = f044_obj.getProcInstructionsLabelsByIndex(f044_lobby_tunnel_proc)
        f044_lobby_tunnel_insert_insts = [
            inst("PUSHIS",0x3ef),
            inst("PUSHIS",0x28),
            inst("PUSHIS",0x1),
            inst("COMM",0x97),
            inst("PUSHIS",0x2c7), #Call a null event (LoA Lobby 2 Cutscene)
            inst("COMM",0x66)
        ]
        f044_lobby_tunnel_insts = f044_lobby_tunnel_insts[0:60] + f044_lobby_tunnel_insert_insts + f044_lobby_tunnel_insts[62:-1] + [inst("END")]
        for l in f044_lobby_tunnel_labels:
            if l.label_offset > 60:
                l.label_offset += 4
        f044_obj.changeProcByIndex(f044_lobby_tunnel_insts, f044_lobby_tunnel_labels, f044_lobby_tunnel_proc)
        
        f044_kalpa5_tunnel_proc = f044_obj.getProcIndexByLabel("002_01eve_02")
        f044_kalpa5_tunnel_insts, f044_kalpa5_tunnel_labels = f044_obj.getProcInstructionsLabelsByIndex(f044_kalpa5_tunnel_proc)
        f044_kalpa5_tunnel_insert_insts = [
            inst("PUSHIS",0x3f0),
            inst("PUSHIS",0x2d),
            inst("PUSHIS",0x1),
            inst("COMM",0x97),
            inst("PUSHIS",0x2c7), #Call a null event (LoA lobby 2 Cutscene)
            inst("COMM",0x66)
        ]
        f044_kalpa5_tunnel_insts = f044_kalpa5_tunnel_insts[0:60] + f044_kalpa5_tunnel_insert_insts + f044_kalpa5_tunnel_insts[62:-1] + [inst("END")]
        for l in f044_kalpa5_tunnel_labels:
            if l.label_offset > 60:
                l.label_offset += 4
        f044_obj.changeProcByIndex(f044_kalpa5_tunnel_insts, f044_kalpa5_tunnel_labels, f044_kalpa5_tunnel_proc)
        
        f044_star_tunnel_proc = f044_obj.getProcIndexByLabel("030_01eve_01")
        f044_star_tunnel_insts, f044_star_tunnel_labels = f044_obj.getProcInstructionsLabelsByIndex(f044_star_tunnel_proc)
        f044_star_tunnel_insert_insts = [
            inst("PUSHIS",0x3f2),
            inst("PUSHIS",0x2b),
            inst("PUSHIS",0x1),
            inst("COMM",0x97),
            inst("PUSHIS",0x2c7), #Call a null event (LoA lobby 2 Cutscene)
            inst("COMM",0x66)
        ]
        f044_star_tunnel_insts = f044_star_tunnel_insts[0:60] + f044_star_tunnel_insert_insts + f044_star_tunnel_insts[62:-1] + [inst("END")]
        for l in f044_star_tunnel_labels:
            if l.label_offset > 60:
                l.label_offset += 4
        f044_obj.changeProcByIndex(f044_star_tunnel_insts, f044_star_tunnel_labels, f044_star_tunnel_proc)
        
        if config_settings.menorah_groups: #Menorah hint
            f044_obj.changeMessageByIndex(assembler.message("> Retrieve these candelabra^nfrom ^g"+self.get_flag_reward_location_string(0x3e1,world)+"^p.", "MSG_001_2"),0x7)

        f044_lb = self.push_bf_into_lb(f044_obj, 'f044')
        self.dds3.add_new_file(custom_vals.LB0_PATH['f044'], f044_lb)
        
        #Shorten Metatron
        e750_obj = self.get_script_obj_by_name('e750')
        e750_main_proc = e750_obj.getProcIndexByLabel("e750_main")
        e750_main_insts, e750_main_labels = e750_obj.getProcInstructionsLabelsByIndex(e750_main_proc)
        e750_main_insts = [e750_main_insts[0]] + [
            inst("PUSHIS",0),
            inst("PUSHIS",0x115),
            inst("COMM",7),
            inst("PUSHREG"),
            inst("EQ"),
            inst("IF",0),
            inst("PUSHIS",0x115),
            inst("COMM",0x8),
            inst("PUSHIS",0x91b),
            inst("COMM",0x8),
            inst("PUSHIS",0x2ee),
            inst("PUSHIS",0x1c1),
            inst("COMM",0x28),
            inst("END"),
            inst("PUSHIS",0x2ee),
            inst("PUSHIS",0x2d),
            inst("PUSHIS",0x1),
            inst("COMM",0x97),
            inst("COMM",0x23),
            inst("COMM",0x2e),
            inst("END")
        ]
        e750_main_labels = [
            assembler.label("META_FOUGHT",15)
        ]
        e750_obj.changeProcByIndex(e750_main_insts, e750_main_labels, e750_main_proc)
        self.dds3.add_new_file(custom_vals.SCRIPT_OBJ_PATH['e750'], BytesIO(bytes(e750_obj.toBytes())))
        
        #Metatron callback is 0x1bc, don't forget it
        f045_obj = self.get_script_obj_by_name('f045')

        f045_meta_rwms = f045_obj.appendMessage(self.get_reward_str("Metatron",world),"META_RWMS")
        f045_meta_rwms_insts = [
            inst("PROC",len(f045_obj.p_lbls().labels)),
            inst("COMM",0x60),
            inst("COMM",1),
            inst("PUSHIS",f045_meta_rwms),
            inst("COMM",0),
            inst("COMM",2),
            inst("COMM",0x61),
        ] + self.get_flag_reward_insts("Metatron",world) + [
            inst("END")
        ]

        f045_meta_reward_proc_str = "META_CB"
        f045_obj.appendProc(f045_meta_rwms_insts,[],f045_meta_reward_proc_str)
        self.insert_callback('f045', 0x1bc, f045_meta_reward_proc_str)
        
        f045_obj.changeMessageByIndex(assembler.message("> You sense ^r"+self.get_checks_boss_name("Metatron",world)+"^p^nbeyond the door.^n^x> Will you enter?" ,"F045_DOOR02"),0x98)

        #Change magic and agility stat doors to require 15 instead of 25 (20 for agility in vanilla?)
        f045_magic1_proc = f045_obj.getProcIndexByLabel("014_01eve_02")
        f045_magic1_insts, f045_magic1_labels = f045_obj.getProcInstructionsLabelsByIndex(f045_magic1_proc)
        f045_magic1_insts[61] = inst("PUSHIS", 0xe)
        f045_obj.changeProcByIndex(f045_magic1_insts, f045_magic1_labels, f045_magic1_proc)
        f045_magic2_proc = f045_obj.getProcIndexByLabel("014_01eve_03")
        f045_magic2_insts, f045_magic2_labels = f045_obj.getProcInstructionsLabelsByIndex(f045_magic2_proc)
        f045_magic2_insts[61] = inst("PUSHIS", 0xe)
        f045_obj.changeProcByIndex(f045_magic2_insts, f045_magic2_labels, f045_magic2_proc)
        f045_agility1_proc = f045_obj.getProcIndexByLabel("014_01eve_01")
        f045_agility1_insts, f045_agility1_labels = f045_obj.getProcInstructionsLabelsByIndex(f045_agility1_proc)
        f045_agility1_insts[61] = inst("PUSHIS", 0xe)
        f045_obj.changeProcByIndex(f045_agility1_insts, f045_agility1_labels, f045_agility1_proc)
        f045_agility2_proc = f045_obj.getProcIndexByLabel("019_01eve_01")
        f045_agility2_insts, f045_agility2_labels = f045_obj.getProcInstructionsLabelsByIndex(f045_agility2_proc)
        f045_agility2_insts[61] = inst("PUSHIS", 0xe)
        f045_obj.changeProcByIndex(f045_agility2_insts, f045_agility2_labels, f045_agility2_proc)
        
        #Skip kalpa 5 tunnels
        f045_kalpa4_tunnel_proc = f045_obj.getProcIndexByLabel("001_01eve_02")
        f045_kalpa4_tunnel_insts, f045_kalpa4_tunnel_labels = f045_obj.getProcInstructionsLabelsByIndex(f045_kalpa4_tunnel_proc)
        f045_kalpa4_tunnel_insert_insts = [
            inst("PUSHIS",0x3f0),
            inst("PUSHIS",0x2c),
            inst("PUSHIS",0x1),
            inst("COMM",0x97),
            inst("PUSHIS",0x2c7), #Call a null event (LoA lobby 2 Cutscene)
            inst("COMM",0x66)
        ]
        f045_kalpa4_tunnel_insts = f045_kalpa4_tunnel_insts[0:60] + f045_kalpa4_tunnel_insert_insts + f045_kalpa4_tunnel_insts[62:-1] + [inst("END")]
        for l in f045_kalpa4_tunnel_labels:
            if l.label_offset > 60:
                l.label_offset += 4
        f045_obj.changeProcByIndex(f045_kalpa4_tunnel_insts, f045_kalpa4_tunnel_labels, f045_kalpa4_tunnel_proc)
        
        f045_lobby_tunnel_proc = f045_obj.getProcIndexByLabel("001_01eve_03")
        f045_lobby_tunnel_insts, f045_lobby_tunnel_labels = f045_obj.getProcInstructionsLabelsByIndex(f045_lobby_tunnel_proc)
        f045_lobby_tunnel_insert_insts = [
            inst("PUSHIS",0x3f1),
            inst("PUSHIS",0x28),
            inst("PUSHIS",0x1),
            inst("COMM",0x97),
            inst("PUSHIS",0x2c7), #Call a null event (LoA lobby 2 Cutscene)
            inst("COMM",0x66)
        ]
        f045_lobby_tunnel_insts = f045_lobby_tunnel_insts[0:60] + f045_lobby_tunnel_insert_insts + f045_lobby_tunnel_insts[62:-1] + [inst("END")]
        for l in f045_lobby_tunnel_labels:
            if l.label_offset > 60:
                l.label_offset += 4
        f045_obj.changeProcByIndex(f045_lobby_tunnel_insts, f045_lobby_tunnel_labels, f045_lobby_tunnel_proc)
        
        f045_lb = self.push_bf_into_lb(f045_obj, 'f045')
        self.dds3.add_new_file(custom_vals.LB0_PATH['f045'], f045_lb)

        if SCRIPT_DEBUG:
            self.script_debug_out( f040_obj,'f040.bf')
            self.script_debug_out( f041_obj,'f041.bf')
            self.script_debug_out( f042_obj,'f042.bf')
            self.script_debug_out( f043_obj,'f043.bf')
            self.script_debug_out( f044_obj,'f044.bf')
            self.script_debug_out( f045_obj,'f045.bf')
            self.script_debug_out( self.get_script_obj_by_name('e710'),'e710.bf')
            self.script_debug_out( e711_obj,'e711.bf')
            self.script_debug_out( e712_obj,'e712.bf')
            self.script_debug_out( e713_obj,'e713.bf')
            self.script_debug_out( e714_obj,'e714.bf')
            self.script_debug_out( e715_obj,'e715.bf')
            self.script_debug_out( e729_obj,'e729.bf')
            self.script_debug_out( self.get_script_obj_by_name('e731'),'e731.bf')
            self.script_debug_out( e728_obj,'e728.bf')
            self.script_debug_out( self.get_script_obj_by_name('e730'),'e730.bf')
            self.script_debug_out( e749_obj,'e749.bf')
            self.script_debug_out( e750_obj,'e750.bf')
            self.script_debug_out( self.get_script_obj_by_name('e718'),'e718.bf')
            self.script_debug_out( self.get_script_obj_by_name('e719'),'e719.bf')
            #self.script_debug_out( self.get_script_obj_by_name('e751'),'e751.bf') This causes an error because no text
            #self.script_debug_out( self.get_script_obj_by_name('e752'),'e752.bf')
            #self.script_debug_out( self.get_script_obj_by_name('e753'),'e753.bf')
            #self.script_debug_out( self.get_script_obj_by_name('e754'),'e754.bf')
            #self.script_debug_out( self.get_script_obj_by_name('e755'),'e755.bf')

        #Cutscene removal in LoA Lobby f040
        #If possible, have each hole with 3 options. Jump, Skip, Cancel
        #Don't get put in LoA Lobby after Network 1. Have door always open.
        #Network 1 1st time is 001_start. Sets 0x756
        #Interacting with peekhole is 001_01eve_01, which calls e710_main. Sets 0x3ea (candelabra), 0x1f, 0x1c. 0x1f is flag that disallows seeing the cutscene again.

        #Cutscene removal in LoA K1 f041
        #Candelabra door, tunnel door.

        #Cutscene removal in LoA K2 f042
        #Candelabra door, tunnel door.
        #If possible, have an NPC that is easy to access unlock White Rider

        #Cutscene removal in LoA K3 f043
        #SHORTEN DANTE
        #Candelabra door, tunnel door.

        #Cutscene removal in LoA K4 f044
        #Shorten Beelzebub. Look into the door unlocking cutscene.
        #Candelabra door, tunnel door.

        #Cutscene removal in LoA K5 f045
        #Intro
        #Look into stat requirements.
        #Dante hire - have flags set as if you already said no to him. Shorten the yes.
        #Metatron
        #030_voice - Tutorial 1. 
        #031_01eve_02 - Tutorial 2. Can be removed with flags.
        #027_lui - Tutorial 3

        #Hint message testing
        ''' Commented out, but still works. Mostly here to show how modifying text works.
        script_objs = {}
        for i,hint_msg in enumerate(custom_vals.hint_msgs):
            script_name = hint_msg[0]
            message_label = hint_msg[1]
            #print "Parsing",message_label
            if script_name not in script_objs:
                s_o = get_script_obj_by_name(iso,script_name)
                script_objs[script_name] = (s_o,len(s_o.toBytes())) #Using a tuple for a size check. Otherwise don't need it.
            index = script_objs[script_name][0].getMessageIndexByLabel(message_label)
            if index != -1:
                new_message_str = "Label: "+message_label+"^nHint index: "+str(i)+"^x2nd text box because ^bwhy not?^p"
                script_objs[script_name][0].changeMessageByIndex(assembler.message(new_message_str,message_label),index)
            else:
                print "ERROR: Message not found. Message label:",message_label
                
        for s_name,s_obj in script_objs.iteritems():
            iso.seek(custom_vals.customizer_offsets[s_name])
            print "Packing script:",s_name
            #if s_name == 'f024':
            #    print s_obj.toBytes()
            ba = bytearray(s_obj[0].toBytes())
            
            if len(ba) > custom_vals.stack_sizes + s_obj[1]:
                print "ERROR: New script for",s_name,"is too big"
            else:
                iso.write(ba)
                open("piped_scripts/"+s_name+".bf","wb").write(ba)
        iso.close()
        '''

if __name__ == '__main__':
    print ("Parsing ISO")
    # open the ISO and parse it
    iso = IsoFS('rom/input.iso')
    iso.read_iso()

    print ("Getting DDT")
    # get the ddt and write it out to disk
    ddt_file = iso.get_file_from_path('DDS3.DDT;1')

    #if not os.path.isfile('rom/old_DDS3.IMG'): #save some dev time
    with open('rom/old_DDS3.DDT', 'wb') as file:
        file.write(ddt_file.read())

    print ("Getting Atlus FileSystem IMG")
    # get the img and write it out to disk in chucks due to size
    with open('rom/old_DDS3.IMG', 'wb') as file:
        for chunk in iso.read_file_in_chunks('DDS3.IMG;1'):
            file.write(chunk)

    print ("Parsing Atlus FileSystem IMG")
    # parse the dds3 fs
    dds3 = DDS3FS('rom/old_DDS3.DDT', 'rom/old_DDS3.IMG')
    dds3.read_dds3()

    print ("Patching scripts")
    script_modifier = Script_Modifier(dds3)
    script_modifier.run()

    #Clean up
    print("Writing new ISO")
    # export the new DDS3 FS
    dds3.export_dds3('rom/DDS3.DDT', 'rom/DDS3.IMG')

    # remove the DUMMY file to save disk space and write back the iso
    iso.rm_file("DUMMY.DAT;1")
    with open('rom/DDS3.DDT', 'rb') as ddt, open('rom/DDS3.IMG', 'rb') as img:
        iso.export_iso('rom/modified_scripts.iso', {'DDS3.DDT;1': ddt, 'DDS3.IMG;1': img})

    # remove the temp DDS3 files
    #os.remove('rom/old_DDS3.DDT')
    #os.remove('rom/old_DDS3.IMG')
    #os.remove('rom/DDS3.DDT')
    #os.remove('rom/DDS3.IMG')
