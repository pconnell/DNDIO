import argparse, shlex
from functools import partial
from src.aio.parser_consts import *

'''
Parser: Defines the arguments passed by the client to the ingress controller.

We will also need to translate these from the Discord command itself passed to the bot.
'''
####################### Argparse overrides ######################

add_parser = argparse._SubParsersAction.add_parser

def add_parser_dont_exit(self, name, **kwargs):
    if 'exit_on_error' not in kwargs:
        kwargs['exit_on_error'] = False
    return add_parser(self, name, **kwargs)

argparse._SubParsersAction.add_parser = add_parser_dont_exit


# This is horrible please delete this
def error_to_string(self, message):
    raise argparse.ArgumentError(None, message)

argparse.ArgumentParser.error = error_to_string

####################### Class definitions #######################
class SetValueSplitter(argparse.Action):
    def __init__(self, valid_stats, valid_values, return_values=False, roll=False, **kwargs):
        self.return_values = "values" if return_values else "stats"
        self.roll = roll

        if valid_stats:
            self.valid_stats = [str(s) for s in valid_stats]
        if valid_values:
            self.valid_values = valid_values
        super().__init__(**kwargs)
    
    def __call__(self, parser, namespace, args, opt_string=False): #idk what opt_string is but it breaks if it's not there

        if self.roll:
            args = self._convert_roll(args)

        if self.nargs in ["*", "?"] or type(self.nargs) == int:
            setattr(namespace, self.dest, args)
            return
        
        if len(args) % 2 != 0:
            raise ValueError("Values must be in key-value pairs.")

        it = [iter(args)] * 2

        stats = dict(zip(*it))

        if self.valid_stats and self.valid_values:
            for stat in stats:
                if not (
                    str(stat) in self.valid_stats and int(stats[stat]) in self.valid_values
                ):
                    raise ValueError(f"{stat}, {stats[stat]}.\nValid categories are {self.valid_stats}, with values ranging from {self.valid_values[0]} to {self.valid_values[-1]}.")

        setattr(namespace, self.dest, eval(self.return_values))
        return
    
    def _convert_roll(self, args):
        rolls = []
        for roll in args:
            roll_temp = roll.split('d')
            roll_temp.reverse()
            rolls+= roll_temp
        
        return rolls
    
####################### ARGPARSER DEFINITIONS #######################

parser = argparse.ArgumentParser(prog='dndio', exit_on_error=False)

subparsers = parser.add_subparsers(
    dest='command',
    help='subcommand help'
)

##########################################################################
#                             Init Commands                              #
##########################################################################
#add for the following cases if we can
# just add an individual that's come to the party late 
# maybe  (not required) - option for removing users.
parser_init = subparsers.add_parser('init', help='channel initialization')

parser_init.add_argument("-u", "--users", nargs="+")
parser_init.add_argument("-o", "--owner", nargs="+")

##########################################################################
#                            Lookup Commands                             #
##########################################################################

lookup_parser = subparsers.add_parser("lookup", 
                              help="Look up information from the Player's Handbook.",
                              aliases=['lookup'])

lookup_sub = lookup_parser.add_subparsers(dest='subcommand')

spell_parser = lookup_sub.add_parser("spells", aliases=["spell"])

spell_parser.add_argument("class", nargs="?")
spell_parser.add_argument("name", nargs="?")
spell_parser.add_argument("-r", "--restrict", nargs=1, help="TODO")

lookup_type = lookup_parser.add_mutually_exclusive_group()
lookup_type.add_argument("-b", "--backgrounds", action="store_true")
lookup_type.add_argument("-f", "--feats", action="store_true")
lookup_type.add_argument("-w", "--weapons", action="store_true")
lookup_type.add_argument("-a", "--armor", action="store_true")

search_type = lookup_parser.add_mutually_exclusive_group()
search_type.add_argument("-r", "--restrict", nargs=1)
search_type.add_argument("-n", "--name", nargs=1)

##########################################################################
#                             Roll Commands                              #
##########################################################################

roll_parser = subparsers.add_parser("roll")

adv_mod = roll_parser.add_mutually_exclusive_group()
adv_mod.add_argument("-a", "--advantage")
adv_mod.add_argument("-d", "--disadvantage")

roll_sub = roll_parser.add_subparsers(dest="subcommand")

raw_parser = roll_sub.add_parser("raw")

raw_parser.add_argument(
    "rolls", 
    nargs="+", 
    action=SetValueSplitter, 
    valid_stats=[4, 6, 8, 10, 12, 20, 100], 
    valid_values=range(0, 101),
    roll=True
)

spell_parser = roll_sub.add_parser("spell")
spell_parser.add_argument("name")
spell_parser.add_argument("level")

check_parser = roll_sub.add_parser("check")
check_parser.add_argument("ability", choices=ABILITY_SCORES + SKILLS, nargs="+")

check_parser = roll_sub.add_parser("save")
check_parser.add_argument("ability", choices=ABILITY_SCORES, nargs="+")

attack_parser = roll_sub.add_parser("attack", aliases=["atk"])
attack_parser.add_argument("action", type=str.lower)

dmg_parser = roll_sub.add_parser("damage", aliases=["dmg"])
dmg_parser.add_argument("action", type=str.lower)

init_parser = roll_sub.add_parser("initiative", aliases=["init"])

roll_parser.add_argument("mod", nargs="?")

##########################################################################
#                          Character Commands                            #
##########################################################################

parser_char = subparsers.add_parser('char',help='Character Commands')

char_sub = parser_char.add_subparsers(help='/char Subcommands', dest='subcommand')

##########################################################################
#                            Char Get Commands                           #
##########################################################################
get_sub = char_sub.add_parser("get", 
                              help="Get a piece of information from your, another player's, or an NPC's character sheet.",
                              aliases=['get'])

get_sub.add_argument(
                        "info", 
                        choices=['ability', 'skills', 'combat', 'equipped', 'inv', 'spellmod', 'spells', 'feats', 'all'],
                        nargs="*", 
                        default='all',
                        type=str.lower,
                        help=
                        '''
                            The type of information you want to pull from the character sheet.
                                                
                            Choices:
                            - ability:     Ability Scores
                            - skills:      Skills and Proficiencies
                            - combat:      HP, AC, and Initiative
                            - equipped:    Currently Equipped Items
                            - inv:         Inventory
                            - spellmod:    Spell Slots and Modifiers
                            - spells:      Known Spells
                            - feats:       Feats
                            - all:         All Character Sheet Information
                        '''
                    )  

get_sub.add_argument("-b", "--base", action='store_true', 
                        help='Get the base stat as it appears on the character sheet.',
                        default=False
                    )

get_sub.add_argument("-c", "--char", default=None,
                        help="The name or numerical ID of the character to look up. Defaults to the player sending the command."
                    )


##########################################################################
#                            Char Set Commands                           #
##########################################################################

######### The following are for multiple skills that can be set. #########

def create_set_value_parser(parser, name, valid_stats: list, valid_values: list[int]):
    parser.add_argument(
        name, 
        nargs="+", 
        action=SetValueSplitter, 
        valid_stats=valid_stats, 
        valid_values=valid_values
    )

    return parser

# Create parsers

char_set = char_sub.add_parser('set', 
                               help="Modify a value on your, another player's, or an NPC's character sheet.", 
                               aliases=['set'])
set_sub = char_set.add_subparsers()

########## The following can take multiple values of type (string, int). ##########

char_set_parsers = {
    "ability": 
        (
            ABILITY_SCORES, 
            list(range(1, 21))
        ),
    "equipped":
        (
            'weapon', 
            [
                'morningstar', 'blowgun', 'halberd', 'light crossbow', 'longsword', 'net', 'greatclub', 'shortsword', 'flail', 'quarterstaff', 'spear', 'club', 'glaive', 'lance', 
                'battleaxe', 'dart', 'trident', 'javelin', 'greatsword', 'warhammer', 'sickle', 'mace', 'whip', 'light hammer', 'war pick', 'pike', 'rapier', 'greataxe', 'hand crossbow', 
                'scimitar', 'dagger', 'heavy crossbow', 'sling', 'longbow', 'shortbow', 'maul', 'handaxe'
            ]
        )
}


for target in char_set_parsers:
    value_sub = set_sub.add_parser(target)
    create_set_value_parser(
        value_sub, 
        target,
        char_set_parsers[target][0],
        char_set_parsers[target][1]        
    )

########## The following take one or more values of a single type. ##########

char_set_arguments = {
        "skill":
        SKILLS
}

for stat in char_set_arguments:
    value_sub = set_sub.add_parser(stat)
    value_sub.add_argument(
        stat,
        choices = char_set_arguments[stat],
        nargs="+",
        type = str
    )


########## The following take one value. ##########

char_set_arguments = {
    "AC":
        list(
            range(0, 51)
            ),
    "Class":
        CLASSES,
    "race":
        RACES,
    "size":
        SIZES,
    "level":
        list(
            range(21)
        ),
    "name":
        None
}

for stat in char_set_arguments:
    value_sub = set_sub.add_parser(stat)
    value_sub.add_argument(
        stat,
        choices = char_set_arguments[stat],
        type = str if char_set_arguments[stat] is None else type(char_set_arguments[stat][0])
    )

##########################################################################
#                            Char Add Commands                           #
##########################################################################

char_add = char_sub.add_parser("add", help="Add an item or spell to your character sheet.")

add_sub = char_add.add_subparsers()

########## The following can only take one value ##########

spell_parser = add_sub.add_parser("spell")

spell_parser.add_argument(
    "spell",
    type=str.lower,
    nargs="+"
)

feat_parser = add_sub.add_parser("feat")

feat_parser.add_argument(
    "name",
    nargs="+"
)

########## The following can take multiple values. ##########

# spellslot_parser = add_sub.add_parser("spellslot")

# spellslot_parser.add_argument(
#     "slot",
#     nargs="+",
#     action=SetValueSplitter, 
#     valid_stats=list(range(1, 10)), 
#     valid_values=list(range(1, 4))
# )

item_parser = add_sub.add_parser("item")

item_parser.add_argument(
    "item",
    nargs="*",
    action=SetValueSplitter,
    valid_stats=None,
    valid_values=None
)

##########################################################################
#                          Char Remove Commands                          #
##########################################################################

char_remove = char_sub.add_parser("remove", help="Remove an item or spell to your character sheet.")

remove_sub = char_remove.add_subparsers()

########## The following can only take one value. ##########

spell_parser = remove_sub.add_parser("spell")

spell_parser.add_argument(
    "spell",
    type=str.lower,
    nargs="+"
)

feat_parser = remove_sub.add_parser("feat")

feat_parser.add_argument(
    "name",
    nargs="+",
    type=str.lower
)

item_parser = remove_sub.add_parser("item")

item_parser.add_argument(
    "item",
    nargs="+",
    type=str.lower
)

########## The following can take multiple values. ##########

# spellslot_parser = remove_sub.add_parser("spellslot")

# spellslot_parser.add_argument(
#     "slot",
#     nargs="+",
#     action=SetValueSplitter, 
#     valid_stats=list(range(1, 10)), 
#     valid_values=list(range(1, 4))
# )


##########################################################################
#                              Command Tests                             #
##########################################################################



#examples
async def parse_str(s, debug=False):
    s = shlex.split(s)
    if debug:
        print(s)
        result = parser.parse_args(s)
        print(result)
        print('*'*80)
    try:
        result = parser.parse_args(s)
    except Exception as e:
        result = e
    
    return result

if __name__ == "__main__":
    test_commands = [
        #currently char information is in two tables - char and char map
        #thinking that since char map just stores lists and one-record per user,
        # we move that into the char table as a single reference point
        # we have a column for primary skills, weapons, armor (all lists)
        # maybe add one for feat(s) too.
        # and one for currently equipped as a map of 'weapon':value, 'armor':value, 

        ##todo on DB side - see if we can have tables and data for race, for feat(s)? (may be too much) 
        ## for 
        "char set ability CHA 20 WIS 14 STR 12 INT 15",
        "char get equipped",
        "char get -b equipped",
        #may be able to truncate these for skills.  if we set a skill as a primary skill
        #the proficiency bonus and the modifier information are already available in the DB
        "char set skill animalhandling 4",
        "char set skill animalhandling 4 arcana -2",
        #after we set level and/or class - should we do a check on the db side
        #to automatically pull class-specific info & add to the char sheet?
        "char set level 1",
        "char set name alexis",
        "char add spell \"Tasha's Hideous Laughter\"",
        "char add item \"New Super Mario Brothers Wii for the Nintendo Wii\"",
        "char add item \"Super Mario 3D World for the Nintendo Switch\" 7",
        "char add spellslot 1 2 2 1",
        #feats may be something we scrape from scope
        #I had a lot of trouble getting spells - still haven't gotten feats or races integrated
        "char add feat \"umm idk\"",
        "init",
        "lookup spells Monk -r 7",
        "lookup spells Monk",
        #for these raw rolls - can we implement on the bot side vs. sending to cloud?
        #really like the format for all of these - keeps it simple.  they can all take -a|-d arguments, right?
        "roll raw 1d6",
        "roll raw 1000d12",
        "roll raw d",
        "roll raw 7d19",
        "roll save INT",
        "roll check STR CHA WIS",
        "roll check STR CHA WIS IAS",
        "roll attack \"Greatsword\"",
        "roll initiative",
        "roll init",
        "lookup --armor -n \"simple leather\"",
        "lookup -a -n \"simple leather\"",
        "lookup -f",
        "lookup -f -r Monk",
        "init test",
        "roll -a 1d6",
        "roll 1d6 -a"
    ]

if __name__ == '__main__':
    for s in test_commands:
        try:
            parse_str(s, debug=True)
        except Exception as e:
            print("Error:", e)
        # exit()

    #### NOTES ####
    # - for `init`