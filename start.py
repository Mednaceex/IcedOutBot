from __future__ import annotations

import json
from pathlib import Path

import discord

# noinspection PyUnresolvedReferences
import modules.commands
from modules.data import THRESHOLD, TOKEN, SERVER, CardChannelIDs, CardChannelWeights, ICEDOUTSERVER_ID
from modules.functions import get_channel_by_id, set_up_config, talk
from modules.initializer import client, manager, registrator, card_game_manager, tree, config_manager
from modules.logger import logger
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
    if await talk(message, client):
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


@client.event
async def on_ready():
    manager.set_current_week(config_manager.CURRENT_WEEK)
    manager.open_picks()
    manager.open_matches()
    card_game_manager.set_channels([await get_channel_by_id(client, chid) for chid in CardChannelIDs],
                                   CardChannelWeights)
    await tree.sync(guild=SERVER)
    logger.info('Bot is ready.')

if __name__ == '__main__':
    client.run(TOKEN)
