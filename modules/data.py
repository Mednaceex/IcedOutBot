from __future__ import annotations
from enum import Enum
import discord
import numpy
from pathlib import Path
import json

THRESHOLD = 16  # How many messages for 1 card needs to be sent
MAX_THRESHOLD = 1000000  # Number of messages stored before the count resets
BUTTON_LIFETIME = 600
TIMEOUT = 300  # Minimum timeout in seconds between two cards can be sent
ITEMS_PER_PAGE = 15
ANSWER_TIMEOUT = 60

pic_ext = ['.jpg', '.png', '.jpeg', '.webp']
with open(Path('data', 'config.json'), 'r') as file:
    dct = json.load(file)
TOKEN = dct['token']

pop = numpy.arange(6, 10.1, 0.1)
sigma, mean = 1, 8
weights = (1 / (sigma * numpy.sqrt(2 * numpy.pi))) * numpy.exp(-(pop - mean) ** 2 / (2 * sigma ** 2))

WORLD_MAP_PICKS_COUNT = 1
WORLD_MAP_VETOES_COUNT = 1
COUNTRY_MAP_PICKS_COUNT = 0
COUNTRY_MAP_VETOES_COUNT = 0
FORCE_DISTINCT_WORLD_MAPS = False
FORCE_DISTINCT_COUNTRY_MAPS = False
MODE_REDEMPTION = True
FORCE_DISTINCT_GAMEMODES = False
A_TIER_COUNT = 2
B_TIER_COUNT = 2
C_TIER_COUNT = 1

APPR_CHANNELS = {'suggestions': 837844906458349580,
                 'lounge': 784928734213570613,
                 'travel_pics': 1080181009846386748,
                 'gaming': 1124989630471737374,
                 'music': 1134236714131521597,
                 'geoguessr': 837845604784406578,
                 'insane_scores': 1055773446358974524,
                 'guess_the_location': 1049287427451260958,
                 'records': 1067927193881149471,
                 'an_icy_world': 1054333828119920651,
                 'tournament_signup': 1070664198838812723,
                 'tournament_discussion': 1050398589333012500,
                 '3p_league_chat': 1119662605393465405,
                 'avw_signup': 1096353269728677908,
                 'location_suggestions': 1096435188692684832,
                 'general_varied': 1096372959934943242,
                 'completed': 1096396752581578752,
                 'memes': 784946869595668521,
                 'left_or_right': 811357316292411404,
                 'chess_and_sports': 1110678051752251432,
                 'self_promo': 826620859782266881,
                 'extra_spam': 1073915143634821170,
                 'rank_ups': 811365464818843688,
                 'tip_of_the_day': 1180945028969926776,
                 'medcord_general': 1116721698243350631,
                 }

ICEDOUTSERVER_ID = 784928734213570610
MEDCORD_ID = 773927468519260170
ICEDOUTSERVER = discord.Object(id=ICEDOUTSERVER_ID)
MEDCORD = discord.Object(id=MEDCORD_ID)


class Gamemode(Enum):
    MOVING = 1
    NM = 2
    NMPZ = 3


DEFAULT_GAMEMODE = Gamemode.NM


class MapTier(Enum):
    A = 1
    B = 2
    C = 3


class Map:
    def __init__(self, name: str, link: str):
        self.name = name
        self.link = link

    def __eq__(self, other: Map):
        return self.name == other.name

    def __str__(self):
        return self.name


class WorldMap(Map):
    def __init__(self, name: str, link: str):
        super(WorldMap, self).__init__(name, link)


class CountryMap(Map):
    def __init__(self, name: str, link: str, tier: MapTier):
        super(CountryMap, self).__init__(name, link)
        self.tier = tier


WORLD_MAP_LIST = (WorldMap('A Community World', 'https://www.geoguessr.com/maps/62a44b22040f04bd36e8a914'),
                  WorldMap('A Tweaked World', 'https://www.geoguessr.com/maps/64205c50e014cf9bb1a04e01'),
                  WorldMap('A Varied World', 'https://www.geoguessr.com/maps/64ce812adc7614680516ff8c'),
                  WorldMap('AI Generated World', 'https://www.geoguessr.com/maps/5dbaf08ed0d2a478444d2e8e'),
                  WorldMap('An Arbitrary Rural World', 'https://www.geoguessr.com/maps/643dbc7ccc47d3a344307998'),
                  WorldMap('An Improved World', 'https://www.geoguessr.com/maps/5b0a80f8596695b708122809'),
                  WorldMap('Less-Extreme Regionguessing', 'https://www.geoguessr.com/maps/658a3ef12255cca9e7f39c06'),
                  WorldMap('The World at Equilibrium', 'https://www.geoguessr.com/maps/64a33494a05ac4fecb6b9e8a'),
                  )


COUNTRY_MAP_DICT = {'A Balanced Turkey': 'https://www.geoguessr.com/maps/61fb2314990720000141ecc9',
                    'AI Generated Nigeria': 'https://www.geoguessr.com/maps/63715d43261c845960550585',
                    'AI Generated United Kingdom': 'https://www.geoguessr.com/maps/5ba862d12c0173524cd9327a',
                    'Sweden (AI Generated)': 'https://www.geoguessr.com/maps/62555d8d7a51f14b3a1a6203',
                    'AI gen - Thailand': 'https://www.geoguessr.com/maps/638777aabd4e538d5e52d4f9',
                    'A Balanced AI Generated India': 'https://www.geoguessr.com/maps/62e10035c97fc44e29bd8e0e',
                    'AI Generated Philippines': 'https://www.geoguessr.com/maps/633212badd3606b32cf7f7d2',
                    'A Balanced Spain': 'https://www.geoguessr.com/maps/62f439cfe46df79befe5c5f8',
                    'A Balanced Colombia': 'https://www.geoguessr.com/maps/63c0a65c985b2d9d2425c6a1',
                    'An Arbitrary Japan': 'https://www.geoguessr.com/maps/63e5ecc3ca384c72d0bd9bc4',
                    'A Balanced Malaysia': 'https://www.geoguessr.com/maps/634050c7fc09dbb1e6c107c6',
                    'AI Gen - New Zealand': 'https://www.geoguessr.com/maps/61f3f49330ad7100010d56c2',
                    'A Community USA': 'https://www.geoguessr.com/maps/635c797dac045a96b9333016',
                    'A Balanced AI Generated Chile': 'https://www.geoguessr.com/maps/6430f6ae803b91d398056286',
                    'AI Gen - Italy': 'https://www.geoguessr.com/maps/63e21bd5e43795374f8400e1'}

COUNTRY_MAP_LIST = (CountryMap('A Balanced Australia',
                               'https://www.geoguessr.com/maps/60afb9b2dcdbe60001438fa6', MapTier.A),
                    CountryMap('A Balanced Brazil',
                               'https://www.geoguessr.com/maps/61df8477a94f5d0001ef9f2c', MapTier.A),
                    CountryMap('A Balanced Canada',
                               'https://www.geoguessr.com/maps/61067f9608061c000157a851', MapTier.A),
                    CountryMap('A Balanced South Africa',
                               'https://www.geoguessr.com/maps/62eb2b6e9e3a000003c039ad', MapTier.A),
                    CountryMap('An Arbitrary Argentina',
                               'https://www.geoguessr.com/maps/63a3cef9571dcbb3660427c4', MapTier.A),
                    CountryMap('AI Gen - Indonesia',
                               'https://www.geoguessr.com/maps/619086606e5572000185a1db', MapTier.A),
                    CountryMap('AI gen - Mexico',
                               'https://www.geoguessr.com/maps/63382d2cc00816fde6cd69b6', MapTier.A),
                    CountryMap('An Arbitrary Russia',
                               'https://www.geoguessr.com/maps/645fee824b5a2a4652553378', MapTier.A),
                    CountryMap('An Arbitrary United States',
                               'https://www.geoguessr.com/maps/61dfb63654e4730001e8faf5', MapTier.A),
                    CountryMap('A Balanced AI Generated Chile',
                               'https://www.geoguessr.com/maps/6430f6ae803b91d398056286', MapTier.B),
                    CountryMap('A Balanced AI Generated India',
                               'https://www.geoguessr.com/maps/62e10035c97fc44e29bd8e0e', MapTier.B),
                    CountryMap('A Balanced Malaysia',
                               'https://www.geoguessr.com/maps/634050c7fc09dbb1e6c107c6', MapTier.B),
                    CountryMap('A Balanced Peru',
                               'https://www.geoguessr.com/maps/63e7e2184c0ca2dca3723ca2', MapTier.B),
                    CountryMap('A Balanced Philippines',
                               'https://www.geoguessr.com/maps/64f4959080229b9a3d429041', MapTier.B),
                    CountryMap('A Balanced Spain',
                               'https://www.geoguessr.com/maps/62f439cfe46df79befe5c5f8', MapTier.B),
                    CountryMap('AI Degenerated Türkiye',
                               'https://www.geoguessr.com/maps/65c401ff733920eb83c44174', MapTier.B),
                    CountryMap('AI Gen - New Zealand',
                               'https://www.geoguessr.com/maps/61f3f49330ad7100010d56c2', MapTier.B),
                    CountryMap('AI Gen - Thailand',
                               'https://www.geoguessr.com/maps/638777aabd4e538d5e52d4f9', MapTier.B),
                    CountryMap('An Arbitrary Japan',
                               'https://www.geoguessr.com/maps/63e5ecc3ca384c72d0bd9bc4', MapTier.B),
                    CountryMap('A Balanced Colombia',
                               'https://www.geoguessr.com/maps/63c0a65c985b2d9d2425c6a1', MapTier.C),
                    CountryMap('A Balanced Germany',
                               'https://www.geoguessr.com/maps/617d2526ed0f750001c24b21', MapTier.C),
                    CountryMap('A Balanced Italy',
                               'https://www.geoguessr.com/maps/63e40449e42ff95dc1d652ae', MapTier.C),
                    CountryMap('A Balanced Kenya',
                               'https://www.geoguessr.com/maps/638188a2ce5dad8d44eb9cae', MapTier.C),
                    CountryMap('A Balanced Sweden',
                               'https://www.geoguessr.com/maps/632994cb83652ed2e2009029', MapTier.C),
                    CountryMap('AI Gen - France',
                               'https://www.geoguessr.com/maps/6383cdd0be0d9b60a5ab2e5d', MapTier.C),
                    CountryMap('AI Gen - Norway',
                               'https://www.geoguessr.com/maps/6256b73b244c43c4448b6e45', MapTier.C),
                    CountryMap('AI Generated United Kingdom',
                               'https://www.geoguessr.com/maps/5ba862d12c0173524cd9327a', MapTier.C),
                    CountryMap('A Diverse Kazakhstan',
                               'https://www.geoguessr.com/maps/65fda213210c988a99251730', MapTier.C),
                    )


class LocPhrase:
    def __init__(self, opening_phrase: str, closing_phrase: str | None = None, exclam=True):
        self.opening_phrase = opening_phrase
        self.closing_phrase = closing_phrase
        self.exclam = exclam

    def write(self, country_name: str) -> str:
        text = self.opening_phrase + ' ' + country_name
        if self.closing_phrase is not None:
            text += self.closing_phrase
        if self.exclam:
            text += '!'
        else:
            text += '.'
        return text


class Tier(str, Enum):
    S_TIER = 's_tier'
    A_TIER = 'a_tier'
    B_TIER = 'b_tier'
    C_TIER = 'c_tier'
    D_TIER = 'd_tier'
    E_TIER = 'e_tier'
    ROTTWEILER_TIER = 'rottweiler_tier'


class Emoji(str):
    ICY2P = '<:ICY2P:1123323759537967205>'
    SKULL = '💀'
    SKULL_BONES = '☠️'
    MOAI = '🗿'
    SKULL_REACTION = '<:Skull_Reaction:1096086132476883035>'
    THEGOAT = '<:the_goat:1138815924540031047>'
    REG_IND_A = '🅰️'
    REG_IND_R = '🇷'
    REG_IND_N = '🇳'
    REG_IND_A_2 = '🇦'
    REG_IND_V = '🇻'
    LEFT = '⬅️'
    RIGHT = '➡️'
    FIRE = '🔥'
    GOAT = '🐐'
    MINDBLOWN = '<:mindblown:1081199314711355453>'
    FISH = '🐟'
    NPC = '<:npc:1141157776685539358>'
    WAVE = '👋'
    GEOWAVE = '<:geoWave:1157237410380390502>'
    CHECKMARK = '✅'
    CROSS = '❌'
    RED_CIRCLE = '🔴'
    GREEN_CIRCLE = '🟢'
    YELLOW_CIRCLE = '🟡'
    ORANGE_CIRCLE = '🟠'
    HUNDRED = '💯'
    TRASH = '🗑️'
    SNOWFLAKE = '<:ice:1157148795788857427>'
    PENCIL = '✏️'
    RED_DIAMOND = '♦️'
    YELLOW_DIAMOND = '🔸'
    BLUE_DIAMOND = '🔹'
    SNOWY_BABY = '<:SnowyBaby:1192229604488908820>'
    SNOWY_RARE = '<:SnowyRare:1201613904762118184>'
    SNOWY_GODMODE = '<:SnowyGODMODE:1192229757555847228>'
    PARTYING = '🥳'


class UserID(int):
    MEDNACEEX = 699706359846928425
    MEDNACEEX2 = 979949104396382208
    KANAV = 750435367865548860
    IAMNOTKANAV = 1101339184893022259
    FMBOT = 356268235697553409
    ICY = 401602034781913099
    VISH = 754722119568457759
    SIMONGOOSE = 381955416885821451
    MEE6 = 159985870458322944
    SELF_ID = 1138621846904905758


class ChannelID(int):
    VIDEO_STREAM = 994332678751015042
    COUNTRY_TOURNAMENT = 1137882434445266985
    WELCOME = 784938861440532521
    INTRODUCE_YOURSELF = 1058053930887676004
    WEEKLY_CHALLENGE_SUGGESTIONS = 1131607113018376394
    GEONEWS = 1088399288071102475
    ANNOUNCEMENTS_3PLEAGUE = 1203486603721314344
    MEDCORD_GENERAL = 1116721698243350631
    TEST_ICYCORD = 1140405951451631647


class Role(str):
    RUINER = 'Counting Ruiner'
    MOD = 'Mod'
    ICY_ROLE = 'The One Time Explorer League Champ'
    POD = 'POD'
    VIP = 'VIP'
    BOOSTER = 'Server Booster 🐐'
    TWITCH_SUB = 'Twitch Sub 🐐'
    CINNAMON = 'Cinnamon Role'


class Chance(float):
    ARNAV = 0.002
    GOAT = 0.001
    KANAV_SKULL = 0.063
    IAMNOTKANAV_SKULL = 0.063
    FMBOT_FIRE = 0.05
    FMBOT_SKULL = 0.05
    INSANE_GOAT = 0.075
    INSANE_MINDBLOWN = 0.3
    PRAISE_ICY = 0.007
    SKULLS_AND_BONES = 0.05
    FISH = 0.005
    RUINER = 0.02
    NPC = 0.01
    SIMON = 0.00
    VIDEO_STREAM_GOAT = 0.1
    KANAV_GM = 0.03
    RANKUP = 1


loc_phrases = (LocPhrase('Come on, every toddler knows this is'),
               LocPhrase('What an easy loc, it\'s clearly in'),
               LocPhrase('Such an obvious'),
               LocPhrase('Is there anyone who doesn\'t know this? Clearly'),
               LocPhrase('I bet 10 million dollars that this is'),
               LocPhrase('Easiest', ' of my virtual life', exclam=False),
               LocPhrase('This is always', exclam=False),
               LocPhrase('Bro this is such an elementary', ', give us something harder next time'),
               LocPhrase('Easy', ', call me a cheater'),
               LocPhrase('Voices in my head tell me this is', exclam=False),
               LocPhrase('Imagine not knowing that this is', exclam=False),
               LocPhrase('What a beautiful location! Has to be', exclam=False),
               LocPhrase('I would 5k this with my eyes closed, it\'s'),
               LocPhrase('My guess is', exclam=False),
               LocPhrase('I\'ll go', ' here', exclam=False),
               LocPhrase('Let\'s plonk in', ' here'),
               LocPhrase('I have seen this location millions of times, it is in'),
               LocPhrase('Interesting one! I\'ll go with', exclam=False),
               LocPhrase('Nice location! Let me guess', exclam=False),
               LocPhrase('I know this road, it\'s in')
               )
COUNTRIES = {'Albania': '🇦🇱', 'Andorra': '🇦🇩', 'Argentina': '🇦🇷', 'Australia': '🇦🇺', 'Austria': '🇦🇹',
             'Bangladesh': '🇧🇩', 'Belgium': '🇧🇪', 'Bhutan': '🇧🇹', 'Bolivia': '🇧🇴', 'Botswana': '🇧🇼',
             'Brazil': '🇧🇷', 'Bulgaria': '🇧🇬', 'Cambodia': '🇰🇭', 'Canada': '🇨🇦', 'Chile': '🇨🇱',
             'Colombia': '🇨🇴', 'Croatia': '🇭🇷', 'Czechia': '🇨🇿', 'Denmark': '🇩🇰', 'Dominican Republic': '🇩🇴',
             'Ecuador': '🇪🇨', 'Estonia': '🇪🇪', 'Eswatini': '🇸🇿', 'Finland': '🇫🇮', 'France': '🇫🇷',
             'Germany': '🇩🇪', 'Ghana': '🇬🇭', 'Greece': '🇬🇷', 'Guatemala': '🇬🇹', 'Hungary': '🇭🇺',
             'Iceland': '🇮🇸', 'India': '🇮🇳', 'Indonesia': '🇮🇩', 'Ireland': '🇮🇪', 'Israel': '🇮🇱',
             'Italy': '🇮🇹', 'Japan': '🇯🇵', 'Jordan': '🇯🇴', 'Kenya': '🇰🇪', 'South Korea': '🇰🇷',
             'Kyrgyzstan': '🇰🇬',
             'Laos': '🇱🇦', 'Latvia': '🇱🇻', 'Lesotho': '🇱🇸', 'Lithuania': '🇱🇹', 'Luxembourg': '🇱🇺',
             'Malaysia': '🇲🇾',
             'Malta': '🇲🇹', 'Mexico': '🇲🇽', 'Monaco': '🇲🇨', 'Mongolia': '🇲🇳', 'Montenegro': '🇲🇪',
             'Netherlands': '🇳🇱',
             'New Zealand': '🇳🇿', 'Nigeria': '🇳🇬', 'North Macedonia': '🇲🇰', 'Norway': '🇳🇴', 'Pakistan': '🇵🇰',
             'Palestine': '🇵🇸', 'Panama': '🇵🇦', 'Peru': '🇵🇪', 'Philippines': '🇵🇭', 'Poland': '🇵🇱', 'Portugal': '🇵🇹',
             'Qatar': '🇶🇦',
             'Romania': '🇷🇴', 'Russia': '🇷🇺', 'Rwanda': '🇷🇼', 'San Marino': '🇸🇲', 'Senegal': '🇸🇳',
             'Serbia': '🇷🇸',
             'Singapore': '🇸🇬', 'Slovakia': '🇸🇰', 'Slovenia': '🇸🇮', 'South Africa': '🇿🇦', 'Spain': '🇪🇸',
             'Sri Lanka': '🇱🇰', 'Sweden': '🇸🇪', 'Switzerland': '🇨🇭', 'Thailand': '🇹🇭', 'Tunisia': '🇹🇳',
             'Turkey': '🇹🇷', 'Uganda': '🇺🇬', 'Ukraine': '🇺🇦', 'United Arab Emirates': '🇦🇪',
             'United Kingdom': '🇬🇧', 'United States': '🇺🇸', 'Uruguay': '🇺🇾', 'Taiwan': '🇹🇼'}
TERRITORIES = {'American Samoa': '🇦🇸', 'Bermuda': '🇧🇲', 'British Indian Ocean Territory': '🇮🇴',
               'Christmas Island': '🇨🇽', 'Cocos (Keeling) Islands': '🇨🇨', 'Curacao': '🇨🇼',
               'Falkland Islands': '🇫🇰',
               'Faroe Islands': '🇫🇴', 'Gibraltar': '🇬🇮', 'Greenland': '🇬🇱', 'Hong Kong': '🇭🇰',
               'Isle of Man': '🇮🇲', 'Jersey': '🇯🇪', 'Macau': '🇲🇴', 'Martinique': '🇲🇶', 'Guam': '🇬🇺',
               'Northern Mariana Islands': '🇲🇵', 'Puerto Rico': '🇵🇷', 'Reunion': '🇷🇪',
               'Saint Pierre and Miquelon': '🇵🇲', 'South Georgia and the South Sandwich Islands': '🇬🇸',
               'Svalbard': '🇸🇯', 'Antarctica': '🇦🇶', 'United States Virgin Islands': '🇻🇮'}
RARE_COUNTRIES = {'Belarus': '🇧🇾', 'Vanuatu': '🇻🇺', 'Nepal': '🇳🇵', 'Lebanon': '🇱🇧', 'Mali': '🇲🇱',
                  'Madagascar': '🇲🇬',
                  'Egypt': '🇪🇬', 'Costa Rica': '🇨🇷', 'China': '🇨🇳', 'Tanzania': '🇹🇿'}
NOT_IN_GAME_COUNTRIES = {
    'Equatorial Guinea': '🇬🇶',
    'Saudi Arabia': '🇸🇦',
    'Mauritius': '🇲🇺',
    'Liechtenstein': '🇱🇮',
    'New Caledonia': '🇳🇨',
    'Barbados': '🇧🇧',
    'Burundi': '🇧🇮',
    'Angola': '🇦🇴',
    'Antigua': '🇦🇬',
    'Gambia': '🇬🇲',
    'Nauru': '🇳🇷',
    'Bahamas': '🇧🇸',
    'Somalia': '🇸🇴',
    'Benin': '🇧🇯',
    'Azerbaijan': '🇦🇿',
    'St. Lucia': '🇱🇨',
    'Samoa': '🇼🇸',
    'Djibouti': '🇩🇯',
    'French Guiana': '🇬🇫',
    'Algeria': '🇩🇿',
    'Zambia': '🇿🇲',
    'Tajikistan': '🇹🇯',
    'Haiti': '🇭🇹',
    'Papua New Guinea': '🇵🇬',
    'Moldova': '🇲🇩',
    'Cote d\'Ivoire': '🇨🇮',
    'Chad': '🇹🇩',
    'Kuwait': '🇰🇼',
    'Nicaragua': '🇳🇮',
    'Fiji': '🇫🇯',
    'Cabo Verde': '🇨🇻',
    'Timor-Leste': '🇹🇱',
    'Malawi': '🇲🇼',
    'Morocco': '🇲🇦',
    'Venezuela': '🇻🇪',
    'South Sudan': '🇸🇸',
    'French Polynesia': '🇵🇫',
    'Iraq': '🇮🇶',
    'Cameroon': '🇨🇲',
    'Liberia': '🇱🇷',
    'Kazakhstan': '🇰🇿',
    'Grenada': '🇬🇩',
    'Micronesia': '🇫🇲',
    'Seychelles': '🇸🇨',
    'Tobago': '🇹🇹',
    'Myanmar': '🇲🇲',
    'Burkina Faso': '🇧🇫',
    'Central African Republic': '🇨🇫',
    'Turkmenistan': '🇹🇲',
    'Turks': '🇹🇨',
    'Tuvalu': '🇹🇻',
    'Bosnia': '🇧🇦',
    'Belize': '🇧🇿',
    'Oman': '🇴🇲',
    'Guinea': '🇬🇳',
    'Guinea-Bissau': '🇬🇼',
    'Yemen': '🇾🇪',
    'El Salvador': '🇸🇻',
    'Kosovo': '🇽🇰',
    'Kiribati': '🇰🇮',
    'Cayman Islands': '🇰🇾',
    'Uzbekistan': '🇺🇿',
    'DRC': '🇨🇩',
    'Niger': '🇳🇪',
    'Vietnam': '🇻🇳',
    'Paraguay': '🇵🇾',
    'Comoros': '🇰🇲',
    'Solomon Islands': '🇸🇧',
    'Dominica': '🇩🇲',
    'Georgia': '🇬🇪',
    'Sierra Leone': '🇸🇱',
    'Gabon': '🇬🇦',
    'Iran': '🇮🇷',
    'Armenia': '🇦🇲',
    'Togo': '🇹🇬',
    'Ethiopia': '🇪🇹',
    'Syria': '🇸🇾',
    'North Korea': '🇰🇵',
    'Namibia': '🇳🇦',
    'Afghanistan': '🇦🇫',
    'Jamaica': '🇯🇲',
    'Maldives': '🇲🇻',
    'Cyprus': '🇨🇾',
    'Sudan': '🇸🇩',
    'Guyana': '🇬🇾',
    'Western Sahara': '🇪🇭',
    'Guadeloupe': '🇬🇵',
    'Sao Tome': '🇸🇹',
    'Honduras': '🇭🇳',
    'Bahrain': '🇧🇭',
    'Republic of the Congo': '🇨🇬',
    'Libya': '🇱🇾',
    'Galapagos': '🇪🇨',
    'Papua': '🇮🇩',
    'Cuba': '🇨🇺',
    'Zimbabwe': '🇿🇼',
    'Mozambique': '🇲🇿',
    'Brunei': '🇧🇳',
    'Mauritania': '🇲🇷',
    'Suriname': '🇸🇷',
    'Eritrea': '🇪🇷',
    'Tonga': '🇹🇴',
    'Vincent': '🇻🇨',
    'Saint Martin': '🇸🇽',
    'Palau': '🇵🇼',
    'Kitts': '🇰🇳',
    'Bonaire': '🇧🇶',
    'Aruba': '🇦🇼',
    'Marshall Islands': '🇲🇭'
}
OVERLAP = ('Pakistan', 'Tanzania', 'Madagascar', 'Dominican Republic', 'Vanuatu', 'Mali', 'Qatar', 'Belarus', 'Nepal',
           'Costa Rica', 'Egypt', 'Martinique', 'Rwanda', 'Laos', 'Lebanon', 'China')

NORMAL_COUNTRIES_LIST = list(COUNTRIES.keys())
TERRITORIES_LIST = list(TERRITORIES.keys())
RARE_COUNTRIES_LIST = list(RARE_COUNTRIES.keys())

COUNTRY_LIST = NORMAL_COUNTRIES_LIST + TERRITORIES_LIST + RARE_COUNTRIES_LIST
ALL_COUNTRY_LIST = COUNTRY_LIST + list(NOT_IN_GAME_COUNTRIES.keys())
ALL_COUNTRY_DICT = COUNTRIES | TERRITORIES | RARE_COUNTRIES | NOT_IN_GAME_COUNTRIES

PROB_LIST = [1. for _ in NORMAL_COUNTRIES_LIST] + [0.3 for _ in TERRITORIES_LIST] + [0.1 for _ in RARE_COUNTRIES_LIST]
icy_praisers = ('Icy3P you are a real one!', 'I love you Icy!', 'Icy3P should have a hundred million subscribers!',
                'We love you Icy!', 'Icy\'s videos are the best thing on YouTube',
                '\'The World At Equilibrium\' is the best Geoguessr map ever!',
                #  'Congratulations on 1500 subscribers!',
                )

TEST_CHANNEL = ChannelID.TEST_ICYCORD
SERVER = ICEDOUTSERVER
OWNERS_3PLEAGUE = (UserID.ICY, UserID.MEDNACEEX)
TALK_CHANNELS = (ChannelID.MEDCORD_GENERAL, ChannelID.TEST_ICYCORD)

TIER_CHANNELS = {Tier.S_TIER: 1211401695444209805,
                 Tier.A_TIER: 1211401746883149834,
                 Tier.B_TIER: 1211401792605392926,
                 Tier.C_TIER: 1211401847915552829,
                 Tier.D_TIER: 1211401896288321566,
                 Tier.E_TIER: 1211401952559243274,
                 Tier.ROTTWEILER_TIER: 1211402037720514650,
                 }
NMPZ_TIERS = ()
MOVING_TIERS = ()
CardChannelIDs = (1206268998916775936, 1206269046232981525, 1140405951451631647, 1217584660092031007)
CardChannelWeights = (1., 1., 0.25, 0.3)
