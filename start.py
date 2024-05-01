from __future__ import annotations
import json
from pathlib import Path

import discord

import modules.queue
from modules.data import THRESHOLD, TOKEN, SERVER, CardChannelIDs, CardChannelWeights, ICEDOUTSERVER_ID, MEDCORD_ID
from modules.initializer import client, manager, registrator, card_game_manager, tree, config_manager
import modules.commands
from modules.logger import logger
from modules.functions import get_channel_by_id, set_up_config
from modules.on_message_functions import func_list

set_up_config(('week', 'playoffs', 'message_count'), (0, True, 0))
with open(Path('data', 'config.json'), 'r') as config:
    _dct = json.load(config)
    config_manager.CURRENT_WEEK = _dct['week']
    config_manager.PLAYOFFS = _dct['playoffs']


@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return
    try:
        logger.info('Message by %s in %s: \"%s\"', message.author.name, message.channel.name, message.content)
    except AttributeError:
        logger.info('Message by %s in DMs: \"%s\"', message.author.name, message.content)
        return
    for func in func_list:
        try:
            if await func(message):
                break
        except Exception as e:
            logger.error(e)
    if message.guild.id == ICEDOUTSERVER_ID:
        registrator.increase_count()
        if registrator.check_message_count(THRESHOLD):
            await card_game_manager.play()
    if message.guild.id == MEDCORD_ID:
        lst = message.content.split(' ')
        if lst[0] == '!send':
            try:
                channel = await get_channel_by_id(client, int(lst[1]))
                await channel.send(f'{" ".join(lst[2:])}')
            except Exception as e:
                await message.channel.send(str(e))


@client.event
async def on_ready():
    manager.set_current_week(config_manager.CURRENT_WEEK)
    manager.open_picks()
    manager.open_matches()
    card_game_manager.set_channels([await get_channel_by_id(client, chid) for chid in CardChannelIDs],
                                   CardChannelWeights)
    await tree.sync(guild=SERVER)
    # client.add_view(CollectButtonView())
    logger.info('Bot is ready.')
    modules.queue.save()


client.run(TOKEN)
