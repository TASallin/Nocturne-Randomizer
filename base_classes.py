import nocturne

# Resist/Null/Absorb/Repel Phys to leave out of SMC
PHYS_INVALID_BOSSES = ['Ongyo-Ki', 'Aciel', 'Girimehkala', 'Skadi', 'Mada', 'Mot', 'The Harlot', 'Black Frost', 'Lucifer', 'Noah']
# other banned smc bosses 
BANNED_SMC_BOSSES = ['Kin-Ki', 'Matador', 'Mithra', 'Samael', 'Beelzebub', 'Metatron']

BANNED_FINAL_BOSSES = ['Specter 1','Troll', 'Orthrus', 'Yaksini', 'Thor 1', 'Kaiwan']

class World(object):
    def __init__(self):
        self.areas = {}
        self.flags = {}
        self.checks = {}
        self.magatamas = {}
        self.bosses = {}
        self.state = Progression(self)

        # new objects used for writing to binary
        self.demons = {}
        self.battles = {}
        self.demon_generator = None
        self.demon_map = {}

        self.bonus_magatama = None

    def add_area(self, name):
        self.areas[name] = Area(name)
        return self.areas[name]

    def add_flag(self, name, flag_id):
        self.flags[name] = Flag(name, flag_id)
        return self.flags[name]

    def add_terminal(self, area, flag_id):
        t = Flag(area.name + " Terminal", flag_id)
        t.is_terminal = True
        self.flags[t.name] = t
        self.areas[area.name].terminal_flag = t
        return t

    def add_check(self, name, area, offset):
        c = Check(name, area)
        c.offset = offset
        self.checks[name] = c
        
        b = Boss(name)
        b.battle = nocturne.all_battles.get(offset)
        b.smc_banned = name in PHYS_INVALID_BOSSES or name in BANNED_SMC_BOSSES
        b.final_banned = name in BANNED_FINAL_BOSSES
        self.bosses[name] = b
        return c

    def add_magatama(self, name, resistances, id):
        self.magatamas[name] = Magatama(name)
        self.magatamas[name].resistances = resistances
        self.magatamas[name].id = id
        return self.magatamas[name]

    def get_area(self, area):
        return self.areas.get(area)

    def get_check(self, check):
        return self.checks.get(check)

    def get_flag(self, flag):
        return self.flags.get(flag)

    def get_magatama(self, magatama):
        return self.magatamas.get(magatama)

    def get_boss(self, boss):
        return self.bosses.get(boss)

    def get_areas(self):
        return list(self.areas.values())

    def get_checks(self):
        return list(self.checks.values())

    def get_flags(self):
        return list(self.flags.values())

    def get_magatamas(self):
        return list(self.magatamas.values())

    def get_bosses(self):
        return list(self.bosses.values())

    def add_demons(self, demons):
        for d in demons:
            self.demons[d.ind] = d

    def add_battles(self, battles):
        for b in battles:
            self.battles[b.offset] = b

    def add_magatamas(self, magatamas):
        for m in magatamas:
            if self.magatamas.get(m.name):
                self.magatamas[m.name].offset = m.offset
                self.magatamas[m.name].stats = m.stats
                self.magatamas[m.name].skills = m.skills

class Area(object):
    def __init__(self, name):
        self.name = name
        self.rule = lambda state: True
        self.boss_rule = lambda boss: True
        self.terminal_flag = None
        self.checks = []
        self.changed = False

    def can_reach(self, state):
        return self.rule(state) or state.has_terminal(self.name)

    def can_place(self, boss):
        return self.boss_rule(boss)


# Checks are boss locations, not the bosses themselves
class Check(object):
    def __init__(self, name, parent):
        self.name = name
        self.rule = lambda state: True
        self.area = parent
        self.offset = None
        self.boss = None
        self.flag_rewards = []
        self.area.checks.append(self)

    def can_reach(self, state):
        return self.rule(state) and self.area.can_reach(state)

    def can_place(self, boss):
        return self.area.can_place(boss)


# Bosses are the actual boss fights at each check
class Boss(object):
    def __init__(self, name):
        self.name = name
        self.check = None
        self.rule = lambda state: True
        self.reward = None
        self.smc_banned = False
        self.final_banned = False

        self.battle = None

    def can_beat(self, state):
        return self.rule(state)

    def can_add_reward(self, reward):
        if isinstance(reward, Magatama) and self.reward != None:
            return False
        elif isinstance(reward, Flag) and self.check.flag_rewards != []:
            return False
        elif self.name == "Kagutsuchi" or self.check.name in ["Kaiwan", "Berith", "Archangels"]:
            return False
        return True            

    def add_reward(self, reward):
        reward.boss = self
        if isinstance(reward, Magatama):
            self.reward = reward
        elif isinstance(reward, Flag):
            self.check.flag_rewards.append(reward)

class Battle(object):
    def __init__(self, offset):
        self.offset = offset
        self.is_boss = False
        self.reward = None
        self.phase_value = None
        self.demons = []
        self.arena = None
        self.goes_first = None
        self.reinforcement_value = None
        self.music = None


class Flag(object):
    def __init__(self, name, flag_id):
        self.name = name
        self.flag_id = flag_id
        self.is_terminal = False


class Magatama(object):
    def __init__(self, name):
        self.name = name
        self.boss = None
        self.resistances = []

        self.offset = None
        self.stats = None
        self.skills = None
        self.id = None


class Demon(object):
    def __init__(self, id, name):
        self.ind = id
        self.name = name
        self.offset = None

        self.race = None
        self.level = None
        self.hp = None
        self.mp = None
        self.stats = None
        self.macca_drop = None
        self.exp_drop = None

        self.battle_skills = None
        self.skills = None
        self.skill_offset = None
        self.ai_offset = None

        self.is_boss = None
        self.phys_inv = None
        self.base_demon = None
        self.shady_broker = None
        self.flag = None

        self.old_id = id


class Skill(object):
    def __init__(self, id, name, rank):
        self.ind = id
        self.name = name
        self.rank = rank

        # skill types
        # 0 = Passive
        # 1 = Attack
        # 2 = Recruitment
        self.skill_type = 1

        self.level = 1

    def __repr__(self):
        return self.name


# State of players progression in the world
class Progression(object):
    def __init__(self, parent):
        self.world = parent
        self.flags = {}
        self.checks = {}
        self.magatamas = {}

    def init_checks(self):
        for c in self.world.get_checks():
            self.checks[c.name] = False

        for f in self.world.get_flags():
            self.flags[f.name] = False

        for m in self.world.get_magatamas():
            self.magatamas[m.name] = False

    def check(self, check):
        self.checks[check] = True

    def get_flag(self, flag):
        self.flags[flag] = True

    def get_magatama(self, magatama):
        self.magatamas[magatama] = True

    def get_terminal(self, area):
        self.flags[area + ' Terminal'] = True

    def get_reward(self, reward):
        if isinstance(reward, Magatama):
            self.magatamas[reward.name] = True
        elif isinstance(reward, Flag):
            self.flags[reward.name] = True

    def remove_flags(self, flag):
        self.flags[flag] = False

    def remove_magatama(self, magatama):
        self.magatamas[magatama] = False

    def remove_reward(self, reward):
        if isinstance(reward, Magatama):
            self.magatamas[reward.name] = False
        elif isinstance(reward, Flag):
            self.flags[reward.name] = False

    def has_checked(self, check):
        return self.checks.get(check) == True

    def has_flag(self, flag):
        return self.flags.get(flag) == True

    def has_terminal(self, area):
        return self.flags.get(area + " Terminal") == True

    def has_resistance(self, resistance):
        for m in self.world.magatamas.values():
            if self.magatamas[m.name]:
                if resistance in m.resistances:
                    return True
        return False

    def can_warp(self):
        return self.has_checked('Specter 1')

    def has_all_magatamas(self):
        return all([m for i, m in self.magatamas.items() if i != 'Masakados'])