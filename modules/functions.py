from __future__ import annotations, division

import json
import random
from functools import partial
from os.path import isfile
from pathlib import Path

import discord
import requests
from PIL import Image
from jsonpickle import decode

import modules.classes as classes
import modules.data as data
from modules.logger import logger


def check_match_ready(match: classes.Match3PLeague, pick_list: list[classes.Pick]) -> bool:
    player_1 = False
    player_2 = False
    for pick in pick_list:
        if pick.match == match:
            if pick.user_id == match.id_1:
                player_1 = True
            if pick.user_id == match.id_2:
                player_2 = True
    return player_1 and player_2


def extract_name(name: str) -> str:
    name = name[5:]
    # if name.find('A Skewed World') == 0:
    # name = 'A Skewed World'
    # elif name.find('World') == 0:
    # name = 'World'
    return name


async def get_channel_by_id(client: discord.Client, channel_id: int) -> discord.TextChannel:
    return await client.fetch_channel(channel_id)


async def get_channel_by_link(client: discord.Client, channel_link: str) -> discord.TextChannel:
    if channel_link.isdigit():
        return await client.fetch_channel(int(channel_link))
    if channel_link.find('https://discord.com/channels/') != -1:
        lst = channel_link.split('/')
        if lst[-1].isdigit():
            return await client.fetch_channel(int(lst[-1]))
    if channel_link.find('<#') != -1:
        channel_id = channel_link[2:-1:1]
        return await client.fetch_channel(int(channel_id))
    raise classes.InvalidChannelError('Invalid channel link or ID!')


async def get_tier_channel(client: discord.Client, tier: data.Tier) -> discord.TextChannel:
    channel_id = data.TIER_CHANNELS[tier]
    return await client.fetch_channel(channel_id)


async def get_message_by_id(channel: discord.TextChannel, message_id: int) -> discord.Message:
    return await channel.fetch_message(message_id)


async def get_user_by_id(client: discord.Client, user_id: int) -> discord.User:
    return await client.fetch_user(user_id)


async def get_member_by_id(guild: discord.Guild, user_id: int) -> discord.Member:
    return await guild.fetch_member(user_id)


async def defer(interaction: discord.Interaction, command_name='cmd', ephemeral: bool = True):
    try:
        await interaction.response.defer(ephemeral=ephemeral)
    except discord.errors.NotFound:
        logger.error('%s unsuccessfully ran the command %s, error: Not Found.', interaction.user.name, command_name)


async def find_wcs_winner(client: discord.Client) -> discord.Message:
    channel = await client.fetch_channel(data.ChannelID.WEEKLY_CHALLENGE_SUGGESTIONS)
    lst = []
    messages = [i async for i in channel.history()]
    for message in messages:
        checkmark, cross = 0, 0
        for reaction in message.reactions:
            user_ids = [user.id async for user in reaction.users()]
            if reaction.emoji == data.Emoji.CHECKMARK:
                checkmark += 1
                if data.UserID.SELF_ID in user_ids:
                    checkmark -= 1
            elif reaction.emoji == data.Emoji.CROSS:
                cross += 1
                if data.UserID.SELF_ID in user_ids:
                    cross -= 1
        if cross < 10:
            lst.append(classes.WCSMessage(message, checkmark, cross))
    m = max(lst, key=lambda x: x.checks)
    itr = filter(lambda x: x.checks == m, lst)
    m = min(itr, key=lambda x: x.crosses)
    return random.choice(tuple(filter(lambda x: x.crosses == m, itr))).message


def announce_winner(winner: discord.Message):
    pass


def has_repeats(lst: list) -> bool:
    for idx, elem in enumerate(lst):
        for i in range(idx):
            if elem == lst[i]:
                return True
    return False


def check_picture(message, force_single=False) -> bool:
    if len(message.attachments) == 1 or (not force_single and len(message.attachments) >= 1):
        for file in message.attachments:
            logger.info('Attachment: %s', file.filename)
            for ext in data.pic_ext:
                if file.filename.lower().endswith(ext):
                    return True
    return False


def is_pod(roles_list: list[discord.Role]) -> bool:
    for role in roles_list:
        if role.name == data.Role.POD:
            return True
    return False


def is_counting_ruiner(roles_list: list[discord.Role]) -> bool:
    for role in roles_list:
        if role.name == data.Role.RUINER:
            return True
    return False


def is_mod(roles_list: list[discord.Role]) -> bool:
    for role in roles_list:
        if role.name == data.Role.MOD or role.name == data.Role.ICY_ROLE:
            return True
    return False


def is_icy(user: discord.Member) -> bool:
    if user.id == data.UserID.ICY:
        return True
    for role in user.roles:
        if role.name == data.Role.ICY_ROLE:
            return True
    return False


async def check_bot_mention(message: discord.Message) -> bool:
    k = 0
    for mention in message.mentions:
        if mention.id == data.UserID.SELF_ID:
            k += 1
    return k > 0 and message.content.find(f'<@{data.UserID.SELF_ID}>') != -1


def check_geo_link(message: discord.Message) -> bool:
    text = message.content
    return text.find('https://www.geoguessr.com/') != -1 or text.find('https://geoguessr.com/') != -1


async def send_permission_message(interaction: discord.Interaction):
    await interaction.followup.send('You don\'t have the permission to run this command!', ephemeral=True)


def check_countries(text: str) -> list[str]:
    lst = []
    for name in data.ALL_COUNTRY_DICT.keys():
        pos = check_word(text, name)
        if pos != -1:
            lst.append((pos, name))
    lst.sort()
    country_list = [item[1] for item in lst]
    log_list = ''
    for country in country_list:
        log_list += f'{country}, '
    logger.info('Countries found: %s', log_list[:-2:])
    return country_list


def check_country_tournament(text: str) -> list[str] | None:
    lst = check_countries(text)
    if len(lst) > 2:
        for short, long in (('Papua', 'Papua New Guinea'), ('Guinea', 'Guinea-Bissau'), ('Guinea', 'Equatorial Guinea'),
                            ('Guinea', 'Papua New Guinea')):
            if short in lst and long in lst:
                lst.remove(short)
            if len(lst) <= 2:
                break
    if len(lst) == 2:
        return lst
    else:
        return None


def extract_rank(text: str) -> str:
    lst = text.split(' ')
    rank = ''
    for i in lst[-1]:
        if i.isdigit():
            rank += i
    return rank


def check_word(text: str, word: str) -> int:
    text = text.lower()
    a = text.find(word.lower())
    if a == -1:
        return -1
    if a > 0:
        if text[a - 1] not in (' ', '(', '\n', '\'', '\"', '/', ','):
            return -1
    if a + len(word) < len(text):
        if text[a + len(word)] not in (' ', '\n', '?', ',', '!', '.', ';', ':', '\'', '\"', ')', '/'):
            return -1
    return a


def get_players(text: str) -> list[int]:
    lst = []
    while text.find('<@') != -1:
        a = text.find('<@') + 2
        user_id = ''
        while text[a].isdigit():
            user_id += text[a]
            a += 1
        if text[a] == '>':
            lst.append(int(user_id))
        text = text[a:]
    return lst


def get_tier(channel_id: int) -> data.Tier:
    for ch, ch_id in data.TIER_CHANNELS.items():
        if ch_id == channel_id:
            return ch


def check_backup(user_id: int, match: classes.Match3PLeague) -> bool:
    if user_id not in (match.id_1, match.id_2):
        raise
    if user_id == match.id_1:
        return match.backup[0]
    if user_id == match.id_2:
        return match.backup[1]


def set_up_config(settings: tuple | list, default_values: tuple = None):
    dct = {}
    path = Path('data', 'config.json')
    if isfile(path):
        with open(path, 'r') as file:
            dct = json.load(file)
    for idx, setting in enumerate(settings):
        if setting not in dct:
            dct[setting] = 0 if default_values is None else default_values[idx]
    with open(path, 'w+') as file:
        json.dump(dct, file)


def save_image(image: discord.Attachment, name: str):
    img = Image.open(requests.get(image.url, stream=True).raw)
    path = Path('card_images', f'{name}.png')
    count = 0
    while isfile(path):
        count += 1
        path = Path('card_images', f'{name}_{count}.png')
    img.save(path)
    return path


def seconds_to_string(seconds: int) -> str:
    if seconds == 1:
        return '1 second'
    if seconds < 60:
        return f'{seconds} seconds'
    if seconds == 60:
        return '1 minute'
    if seconds == 61:
        return '1 minute 1 second'
    if seconds < 120:
        return f'1 minute {seconds - 60} seconds'
    if seconds % 60 == 0:
        return f'{seconds // 60} minutes'
    if seconds % 60 == 1:
        return f'{seconds // 60} minutes 1 second'
    return f'{seconds // 60} minutes {seconds % 60} seconds'


def get_map_by_name(name: str) -> data.Map:
    for _map in data.COUNTRY_MAP_LIST + data.WORLD_MAP_LIST:
        if _map.name == name:
            return _map
    raise AttributeError(f"Map {name} not found!")


def save_week(week: int):
    with open(Path('data', 'config.json'), 'r') as file:
        dct = json.load(file)
    dct['week'] = week
    with open(Path('data', 'config.json'), 'w') as file:
        json.dump(dct, file)


def get_nickname(user: discord.Member) -> str:
    return user.nick if user.nick is not None else user.name


async def talk(message: discord.Message, client: discord.Client) -> bool:
    if message.channel.id not in data.TALK_CHANNELS:
        return False
    lst = message.content.split(' ')
    if lst[0] != '!send':
        return False
    try:
        channel = await get_channel_by_link(client, lst[1])
        await channel.send(f'{" ".join(lst[2:])}')
    except discord.NotFound:
        await message.channel.send('Channel with this ID is not found!')
    except discord.Forbidden:
        await message.channel.send('I can\'t see this channel!')
    except discord.HTTPException:
        await message.channel.send('Channel with this ID is not found!')
    except classes.InvalidChannelError:
        await message.channel.send('Invalid channel link! '
                                   'Please specify the channel after \"!send\" by either copying its ID or link.')
    except Exception as e:
        await message.channel.send(repr(e))
    return True


def open_map_list(week: int, name: str) -> list[data.Map] | None:
    with open(Path('data', 'map_lists.json'), 'r') as file:
        lst = json.load(file)
    for w in lst:
        if w['week'] == week:
            return list(map(decode, w[name]))
    return None


open_country_map_list: partial = partial(open_map_list, name='country_maps')
open_world_map_list: partial = partial(open_map_list, name='world_maps')


def get_map_from_menu(menu: discord.ui.Select) -> data.Map:
    return get_map_by_name(extract_name(menu.values[0]))


def contained(substring: str, source: str) -> bool:
    """
    Checks for a string containing another one. Success means every character from the substring appears in the
    source string in order. For example, "ABC" is contained in "xAxxBxCxx" and "ABAC" but not "BCAB".

    :param substring: a string that is supposed to be contained
    :param source: a source string that contains the substring
    :return: whether a substring is contained
    """
    k = -1
    for char in substring:
        idx = source[k+1::].find(char)
        if idx == -1:
            return False
        k = k + 1 + idx
    return True
