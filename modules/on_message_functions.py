from modules.data import *
from modules.logger import logger
from modules.initializer import manager, config_manager
from modules.functions import check_countries, check_picture, check_geo_link, check_country_tournament, is_pod,\
    check_word, extract_rank, check_bot_mention, is_counting_ruiner
import random
from typing import Union


async def _react_fmbot(message: discord.Message) -> bool:
    if message.channel.id == APPR_CHANNELS['music']:
        if message.author.id == UserID.FMBOT:
            if await react_multiple(message, (Emoji.FIRE, Emoji.SKULL, None),
                                    (Chance.FMBOT_FIRE, Chance.FMBOT_SKULL), 'fmbot'):
                return True
    return False


async def _react_rankup(message: discord.Message) -> bool:
    if message.channel.id == APPR_CHANNELS['rank_ups']:
        if message.author.id == UserID.MEE6 and message.content.find('you just advanced to level') != -1:
            if await react_rankup(message):
                return True
    return False


async def _react_welcome(message: discord.Message) -> bool:
    if message.channel.id == ChannelID.WELCOME:
        if message.is_system() and message.type == discord.MessageType.new_member:
            await message.add_reaction(Emoji.GEOWAVE)
            return True
        if message.author.id == UserID.MEE6:
            await message.add_reaction(Emoji.SKULL)
            return True
    return False


async def _react_introduce(message: discord.Message) -> bool:
    if message.channel.id == ChannelID.INTRODUCE_YOURSELF:
        await message.add_reaction(Emoji.GEOWAVE)
        return True
    return False


async def _react_geonews(message: discord.Message) -> bool:
    if message.channel.id in (ChannelID.GEONEWS, ChannelID.ANNOUNCEMENTS_3PLEAGUE):
        checked = check_countries(message.content)
        await react_countries(message, checked)
        return True
    return False


async def _react_country_tournament(message: discord.Message) -> bool:
    if message.channel.id == ChannelID.COUNTRY_TOURNAMENT:
        if message.author.id == UserID.ICY:
            checked = check_country_tournament(message.content)
            if checked is not None:
                await react_countries(message, checked)
                return True
    return False


async def _deal_with_bots(message: discord.Message) -> bool:
    return message.author.bot


async def _add_matches(message: discord.Message) -> bool:
    if message.author.id in OWNERS_3PLEAGUE:
        if message.channel.id in TIER_CHANNELS.values():
            return manager.add_matches(message, config_manager.CURRENT_WEEK)
    return False


async def _deal_with_ping(message: discord.Message) -> bool:
    if await check_bot_mention(message):
        logger.info('%s pinged!', message.author.name)
        await message.channel.send('Don\'t ping unless urgent!')
        return True
    return False


async def _react_video_stream(message: discord.Message) -> bool:
    if message.channel.id == ChannelID.VIDEO_STREAM:
        if message.author.id == UserID.ICY:
            if await react_single(message, Emoji.THEGOAT, Chance.VIDEO_STREAM_GOAT, 'Video Goat'):
                return True
    return False


async def _filter_appr_channels(message: discord.Message) -> bool:
    return message.channel.id not in APPR_CHANNELS.values()


async def _guess_loc(message: discord.Message) -> bool:
    if message.channel.id == APPR_CHANNELS['guess_the_location']:
        is_picture = check_picture(message, True)
        if is_picture:
            await guess_loc(message)
            return True
    return False


async def _react_left_right(message: discord.Message) -> bool:
    if message.channel.id == APPR_CHANNELS['left_or_right']:
        is_picture = check_picture(message, False)
        if is_picture:
            await message.add_reaction(Emoji.LEFT)
            await message.add_reaction(Emoji.RIGHT)
            return True
    return False


async def _react_tip_of_the_day(message: discord.Message) -> bool:
    if message.channel.id == APPR_CHANNELS['tip_of_the_day']:
        if message.content.find('https://') == -1:
            await message.add_reaction(Emoji.CHECKMARK)
            await message.add_reaction(Emoji.CROSS)
            return True
    return False


async def _react_insane_score(message: discord.Message) -> bool:
    if message.channel.id == APPR_CHANNELS['insane_scores']:
        is_picture = check_picture(message, False)
        has_link = check_geo_link(message)
        if is_picture or has_link:
            if await react_multiple(message, (Emoji.MINDBLOWN, Emoji.GOAT, None),
                                    (Chance.INSANE_MINDBLOWN, Chance.INSANE_GOAT), 'Insane score'):
                return True
    return False


async def _react_memes(message: discord.Message) -> bool:
    if message.channel.id == APPR_CHANNELS['memes']:
        is_picture = check_picture(message, False)
        if is_picture:
            if await respond_single(message, 'Skulls and bones.', Chance.SKULLS_AND_BONES, 'Skulls and bones'):
                return True
    return False


async def _react_kanav_gm(message: discord.Message) -> bool:
    if message.channel.id == APPR_CHANNELS['chess_and_sports'] and message.author.id == UserID.KANAV:
        if await respond_single(message, 'Kanav you\'re gonna become a grandmaster soon!', Chance.KANAV_GM, 'Kanav GM'):
            return True
    return False


async def _deal_with_simon(message: discord.Message) -> bool:
    if message.author.id == UserID.SIMONGOOSE:
        if await respond_single(message, '#Simongoose4WorldCup (it\'s never too late!)', Chance.SIMON, 'Simon'):
            return True
    return False


async def _handle_reactions(message: discord.Message) -> bool:
    reaction = random.choices((True, False), (Chance.GOAT, 1 - Chance.GOAT))[0]
    logger.info('Special: %s', reaction)
    try:
        if reaction:
            await message.add_reaction(Emoji.THEGOAT)
            return True
        if message.author.id == UserID.KANAV:
            if await deal_with_kanav(message, Chance.KANAV_SKULL):
                return True
        if message.author.id == UserID.IAMNOTKANAV:
            if await deal_with_kanav(message, Chance.IAMNOTKANAV_SKULL):
                return True
        if message.author.id == UserID.VISH:
            if await react_single(message, Emoji.FISH, Chance.FISH, 'Fish'):
                return True
        if is_counting_ruiner(message.author.roles):
            if await react_single(message, Emoji.FISH, Chance.RUINER, 'Ruiner'):
                return True
        if is_pod(message.author.roles):
            if await react_single(message, Emoji.NPC, Chance.NPC, 'NPC'):
                return True
    finally:
        return False


async def _praise_icy(message: discord.Message) -> bool:
    if message.author.id == UserID.ICY:
        reaction = random.choices((True, False), (Chance.PRAISE_ICY, 1 - Chance.PRAISE_ICY))[0]
        logger.info('PraiseIcy: %s', reaction)
        if reaction:
            text = random.choice(icy_praisers)
            logger.info('Praiser: %s', text)
            await message.channel.send(text)
            return True
    return False


async def _berate_google_earth(message: discord.Message) -> bool:
    text = message.content
    if text.find('earth.google.com/') != -1 or text.find('earth.app.goo.gl/') != -1:
        await message.channel.send('Stop using Google Earth!')
        return True
    return False


async def _berate_soccer(message: discord.Message) -> bool:
    text = message.content
    if check_word(text, 'soccer') != -1:
        await message.channel.send('It\'s called football!')
        return True
    return False


async def guess_loc(message: discord.Message):
    country = random.choices(COUNTRY_LIST, PROB_LIST)[0]
    phrase = random.choice(loc_phrases)
    text = phrase.write(country)
    await message.channel.send(text)


async def react_multiple(message: discord.Message, emoji_list: Union[list, tuple],
                         chance_list: Union[list, tuple], debug_msg='Reaction') -> bool:
    if len(emoji_list) != len(chance_list) + 1:
        raise ValueError('Length of the given lists do not correspond.')
    reaction = random.choices(emoji_list, list(chance_list) + [1 - sum(chance_list)])[0]
    logger.info('%s: %s', debug_msg, reaction)
    if reaction is None:
        return False
    try:
        await message.add_reaction(reaction)
        return True
    except discord.errors.Forbidden:
        logger.error('%s blocked reaction %s', message.author.name, reaction)
    finally:
        return False


async def react_single(message: discord.Message, emoji: str, chance: float, debug_msg='Reaction') -> bool:
    reaction = random.choices((True, False), (chance, 1 - chance))[0]
    logger.info('%s: %s', debug_msg, reaction)
    if not reaction:
        return False
    try:
        await message.add_reaction(emoji)
        return True
    except discord.errors.Forbidden:
        logger.error('%s blocked reaction %s', message.author.name, emoji)
    finally:
        return False


async def respond_single(message: discord.Message, response: str, chance: float, debug_msg='Response') -> bool:
    reaction = random.choices((True, False), (chance, 1 - chance))[0]
    logger.info('%s: %s', debug_msg, reaction)
    if not reaction:
        return False
    try:
        await message.channel.send(response)
        return True
    except discord.errors.Forbidden:
        logger.error('Message response to %s is blocked', message.author.name)
    finally:
        return False


async def deal_with_kanav(message: discord.Message, skull_chance: float) -> bool:
    if message.content.lower() == 'l med':
        await message.add_reaction(Emoji.SKULL)
        return True
    reaction = random.choices((Emoji.SKULL, Emoji.SKULL_BONES, Emoji.SKULL_REACTION, 'Arnav', 'None'),
                              (skull_chance / 3, skull_chance / 3, skull_chance / 3,
                               Chance.ARNAV, 1 - skull_chance - Chance.ARNAV))[0]
    logger.info('Kanav: %s', reaction)
    if reaction == 'None':
        return False
    elif reaction == 'Arnav':
        await react_arnav(message)
    else:
        await message.add_reaction(reaction)
    return True


async def react_arnav(message: discord.Message):
    for emoji in (Emoji.REG_IND_A, Emoji.REG_IND_R, Emoji.REG_IND_N, Emoji.REG_IND_A_2, Emoji.REG_IND_V):
        await message.add_reaction(emoji)


async def react_countries(message: discord.Message, countries: list[str]):
    for country in countries:
        await message.add_reaction(ALL_COUNTRY_DICT[country])


async def react_rankup(message: discord.Message) -> bool:
    reaction = random.choices((True, False), (Chance.RANKUP, 1 - Chance.RANKUP))[0]
    logger.info('Rank up: %s', reaction)
    if reaction:
        number = extract_rank(message.content)
        await message.channel.send(number)
        return True
    return False


func_list = (_react_fmbot, _react_rankup, _react_welcome, _react_introduce, _react_geonews, _guess_loc,
             _react_left_right, _react_tip_of_the_day, _react_country_tournament, _deal_with_bots, _add_matches,
             _deal_with_ping, _react_video_stream, _filter_appr_channels, _react_insane_score, _react_memes,
             _berate_google_earth, _berate_soccer, _react_kanav_gm, _deal_with_simon, _handle_reactions, _praise_icy)
