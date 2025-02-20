import random
from typing import Optional

import discord
from discord import app_commands

from io import BytesIO
import modules.queue
from modules.card_game import Rarity, Collection, Card, SCQuestion, MCQuestion, idx_to_card, idx_to_collection, \
    QuestionType
from modules.data import Role, ICEDOUTSERVER, OWNERS_3PLEAGUE, pop, weights, Emoji, Tier
from modules.functions import defer, is_mod, is_icy, send_permission_message, check_backup, save_image, save_week, \
    get_nickname, contained
from modules.initializer import manager, card_game_manager, tree, config_manager, queue_manager, profile_manager
from modules.logger import logger, log_errors
from modules.pagination import paginate
from modules.ui_classes import ResetPicksUI


def get_autocomplete(names: list, values: list = None):
    if values is None:
        values = names.copy()
    if values is not None and len(values) != len(names):
        raise ValueError('Name and value lists of different sizes')

    async def autocomplete(interaction: discord.Interaction, inp: str) -> list[app_commands.Choice[str]]:
        lst = []
        for name, value in zip(names, values):
            if name.lower().find(inp.lower()) == 0:
                lst.append(app_commands.Choice(name=name, value=value))
        for name, value in zip(names, values):
            if name.lower().find(inp.lower()) != 0 and contained(inp.lower(), name.lower()):
                lst.append(app_commands.Choice(name=name, value=value))
        if len(lst) > 25:
            lst = lst[:25:]
        return lst
    return autocomplete


async def collection_autocomplete(interaction: discord.Interaction, inp: str) -> list[app_commands.Choice[str]]:
    collection_list = [x[0] for x in card_game_manager.get_collections_reprs_list()]
    lst = [app_commands.Choice(name=collection, value=collection)
           for collection in collection_list if contained(inp.lower(), collection.lower())]
    if len(lst) > 25:
        lst = lst[:25:]
    return lst


async def grade_autocomplete(interaction: discord.Interaction, card: str) -> list[app_commands.Choice[str]]:
    cards_list = card_game_manager.get_card_reprs_list(interaction.user, only_ungraded=True)
    lst = [app_commands.Choice(name=_card_name, value=f'{idx}_12c76c7711c67894c34c234c7098642c0b7')
           for _card_name, idx in cards_list if contained(card.lower(), _card_name.lower())]
    if len(lst) > 25:
        lst = lst[:25:]
    return lst


async def card_autocomplete(interaction: discord.Interaction, card: str) -> list[app_commands.Choice[str]]:
    cards_list = card_game_manager.get_card_reprs_list(interaction.user, only_ungraded=False)
    lst = [app_commands.Choice(name=_card_name, value=f'{idx}_12c76c7711c67894c34c234c7098642c0b7')
           for _card_name, idx in cards_list if contained(card.lower(), _card_name.lower())]
    if len(lst) > 25:
        lst = lst[:25:]
    return lst


async def queue_name_autocomplete(interaction: discord.Interaction, q: str) -> list[app_commands.Choice[str]]:
    queue_list = queue_manager.get_queue_reprs_list()
    lst = [app_commands.Choice(name=_queue_name, value=_queue_name) for _queue_name in queue_list
           if contained(q.lower(), _queue_name.lower())]
    if len(lst) > 25:
        lst = lst[:25:]
    return lst


async def progress_autocomplete(interaction: discord.Interaction, collection: str) -> list[app_commands.Choice[str]]:
    collection_list = card_game_manager.get_collections_reprs_list()
    lst = [app_commands.Choice(name='All', value=f'All')]
    lst += [app_commands.Choice(name=_collection_name, value=f'{idx}_12c76c7711c67894c34c234c7098642c0b7')
            for _collection_name, idx in collection_list if contained(collection.lower(), _collection_name.lower())]
    if len(lst) > 25:
        lst = lst[:25:]
    return lst


async def cards_autocomplete(interaction: discord.Interaction, card: str) -> list[app_commands.Choice[str]]:
    cards_list = card_game_manager.cards_list
    lst = [app_commands.Choice(name=str(_card), value=_card.id) for _card in cards_list
           if contained(card.lower(), str(_card).lower())]
    if len(lst) > 25:
        lst = lst[:25:]
    return lst


async def all_cards_autocomplete(interaction: discord.Interaction, card: str) -> list[app_commands.Choice[str]]:
    cards_list = card_game_manager.cards_list
    lst = [app_commands.Choice(name='All', value='All')] + \
          [app_commands.Choice(name=str(_card), value=_card.id)
           for _card in cards_list if contained(card.lower(), str(_card).lower())]
    if len(lst) > 25:
        lst = lst[:25:]
    return lst


async def tier_autocomplete(interaction: discord.Interaction, tier: str) -> list[app_commands.Choice[str]]:
    lst = [app_commands.Choice(name=_tier, value=_tier) for _tier in Tier if contained(tier.lower(), _tier.lower())]
    if len(lst) > 25:
        lst = lst[:25:]
    return lst


@log_errors
@tree.command(name='pick', guild=ICEDOUTSERVER)
async def send_pick_menu(interaction: discord.Interaction):
    await defer(interaction, '/pick')
    match = manager.get_match(interaction.user.id)
    if match is None:
        await interaction.followup.send(f'You don\'t have any more matches this week!', ephemeral=True)
        logger.info('%s ran /pick, no more matches found.', interaction.user.name)
        return
    backup = check_backup(interaction.user.id, match)
    pick_ui = manager.configure_playoffs_pick_ui(interaction.user.id, match)
    if backup:
        await pick_ui.send_ui(interaction, f'Please make your backup pick for {str(pick_ui.match)} match:')
        logger.info('%s ran /pick for backup picks.', interaction.user.name)
    else:
        await pick_ui.send_ui(interaction, f'Please make your picks for {str(pick_ui.match)} match:')
        logger.info('%s ran /pick for main picks.', interaction.user.name)


@log_errors
@app_commands.checks.has_any_role(Role.ICY_ROLE, Role.MOD)
@app_commands.autocomplete(tier=tier_autocomplete)
@tree.command(name='whopicked', guild=ICEDOUTSERVER)
async def who_picked(interaction: discord.Interaction, tier: str):
    await defer(interaction, '/whopicked')
    if not is_mod(interaction.user.roles):
        await send_permission_message(interaction)
        logger.info('%s ran /whopicked, permission denied', interaction.user.name)
        return
    try:
        message = manager.get_who_picked_message(Tier(tier))
    except ValueError:
        message = manager.get_who_picked_message(None)
    await interaction.followup.send(message, ephemeral=True)
    logger.info('%s ran /whopicked, permission allowed', interaction.user.name)


@log_errors
@app_commands.checks.has_any_role(Role.ICY_ROLE, Role.MOD)
@tree.command(name='maps_of_the_week', guild=ICEDOUTSERVER)
async def maps_of_the_week(interaction: discord.Interaction):
    await defer(interaction, '/maps_of_the_week')
    if not is_mod(interaction.user.roles):
        await send_permission_message(interaction)
        logger.info('%s ran /maps_of_the_week, permission denied', interaction.user.name)
        return
    message = 'Current week\'s country maps:\n\n**' + '\n'.join([_map.name for _map in manager.country_map_list]) + '**'
    await interaction.followup.send(message, ephemeral=True)
    logger.info('%s ran /maps_of_the_week, permission allowed', interaction.user.name)


@log_errors
@app_commands.checks.has_any_role(Role.ICY_ROLE, Role.MOD)
@tree.command(name='resetmatches', guild=ICEDOUTSERVER)
async def reset_picks(interaction: discord.Interaction):
    await defer(interaction, '/resetmatches')
    if interaction.user.id not in OWNERS_3PLEAGUE:
        await send_permission_message(interaction)
        logger.info('%s ran /resetmatches, permission denied', interaction.user.name)
        return
    reset_picks_ui = ResetPicksUI(pick_manager=manager)
    await interaction.followup.send('Choose the tier to reset matches in:', view=reset_picks_ui, ephemeral=True)
    logger.info('%s ran /resetmatches, permission allowed', interaction.user.name)


@log_errors
@app_commands.checks.has_any_role(Role.ICY_ROLE, Role.MOD)
@tree.command(name='changeweek', guild=ICEDOUTSERVER)
async def change_week(interaction: discord.Interaction, week: int):
    await defer(interaction, '/changeweek')
    if interaction.user.id not in OWNERS_3PLEAGUE:
        await send_permission_message(interaction)
        logger.info('%s ran /changeweek, permission denied', interaction.user.name)
        return
    logger.info('%s ran /changeweek, permission allowed', interaction.user.name)
    manager.set_current_week(week)
    config_manager.CURRENT_WEEK = week
    save_week(week)
    await interaction.followup.send(f'It\'s week {week} now!')
    logger.info('%s changed the week to %d.', interaction.user.name, week)


@log_errors
@app_commands.autocomplete(sort_by=get_autocomplete(['Rarity', 'Grade', 'Collection', 'Newest first', 'Oldest first']))
@tree.command(name='cards', guild=ICEDOUTSERVER)
async def cards(interaction: discord.Interaction, user: Optional[discord.Member] = None, sort_by: Optional[str] = None):
    await interaction.response.defer()
    lst = ['Specify the user or leave the field blank.']
    if user is None:
        # message = await card_game_manager.display_collections(client)
        user = interaction.user
    if isinstance(user, discord.Member):
        lst = card_game_manager.display_collection(user, sorting=sort_by)
    else:
        logger.error('The user %s ran /cards and is not a discord Member object!', interaction.user.name)
    nick = get_nickname(interaction.user)
    await paginate(interaction, lst, f'**{nick}\'s collection:**\n')
    logger.info('%s ran /cards, permission allowed', interaction.user.name)


@log_errors
@app_commands.autocomplete(collection=collection_autocomplete)
@app_commands.autocomplete(rarity=get_autocomplete(['Common', 'Rare', 'Epic'], [15, 25, 35]))
@app_commands.autocomplete(multiple_choice=get_autocomplete(['Yes', 'No'], [1, 0]))
@app_commands.checks.has_any_role(Role.ICY_ROLE, Role.MOD)
@tree.command(name='add_card', guild=ICEDOUTSERVER)
async def add_card(interaction: discord.Interaction, name: str, collection: str, rarity: int,
                   question: str, multiple_choice: int, answer: str, image: discord.Attachment):
    await defer(interaction, 'add_card')
    message = 'The card is successfully added!'
    try:
        _rarity = Rarity(rarity)
    except ValueError:
        await interaction.followup.send('This rarity doesn\'t exist!')
        return
    try:
        _collection = card_game_manager.get_collection(collection.upper())
    except AttributeError:
        await interaction.followup.send('This collection doesn\'t exist!')
        return
    except Exception as e:
        logger.error(e)
        return
    try:
        path = save_image(image, name)
    except IOError:
        await interaction.followup.send('The image is invalid! (.png format is preferred.)')
        return
    q = MCQuestion(question, answer) if multiple_choice else SCQuestion(question, answer)
    card = Card(name, _rarity, _collection, path, q, None, 1.)
    card_game_manager.upload_card(card)
    await interaction.followup.send(message)
    logger.info('%s added a card, permission allowed', interaction.user.name)


@log_errors
@app_commands.autocomplete(card=cards_autocomplete)
@app_commands.autocomplete(rarity=get_autocomplete(['Common', 'Rare', 'Epic'], [15, 25, 35]))
@app_commands.autocomplete(multiple_choice=get_autocomplete(['Yes', 'No'], [1, 0]))
@app_commands.checks.has_any_role(Role.ICY_ROLE, Role.MOD)
@tree.command(name='edit_card', guild=ICEDOUTSERVER)
async def edit_card(interaction: discord.Interaction, card: str, name: str = None, rarity: int = None,
                    question: str = None, multiple_choice: int = None, answer: str = None,
                    image: discord.Attachment = None):
    await defer(interaction, 'edit_card')
    if not card_game_manager.check_card_exists(card):
        await interaction.followup.send('This is not a valid existing card!')
        return
    card = card_game_manager.get_card_by_id(card)
    message = 'The edits are successfully saved!'
    if name is None:
        name = card.name
    if rarity is None:
        _rarity = card.rarity
    else:
        try:
            _rarity = Rarity(rarity)
        except ValueError:
            await interaction.followup.send('This rarity doesn\'t exist!')
            return
        except Exception as e:
            logger.error(e)
            return
    if image is None:
        path = card.image_path
    else:
        try:
            path = save_image(image, name)
        except IOError:
            await interaction.followup.send('The image is invalid! (.png format is preferred.)')
            return
    if question is None:
        question = card.question.text
    if multiple_choice is None:
        multiple_choice = card.question.type == QuestionType.MULTIPLECHOICE
    if answer is None:
        answer = card.question.answer_repr
    q = MCQuestion(question, answer) if multiple_choice else SCQuestion(question, answer)
    card_game_manager.edit_card(card, name, _rarity, q, path)
    await interaction.followup.send(message)
    logger.info('%s edited a card, permission allowed', interaction.user.name)


@log_errors
@app_commands.autocomplete(card=all_cards_autocomplete)
@app_commands.autocomplete(spawnable=get_autocomplete(['Yes', 'No'], [1, 0]))
@app_commands.checks.has_any_role(Role.ICY_ROLE, Role.MOD)
@tree.command(name='set_spawnable', guild=ICEDOUTSERVER)
async def set_spawnable(interaction: discord.Interaction, card: str, spawnable: int):
    await defer(interaction, 'set_spawnable')
    if card == 'All':
        if not spawnable:
            chance = 0.
            await interaction.followup.send('All cards will no longer spawn!')
        else:
            chance = 1.
            await interaction.followup.send('All cards are now spawnable!')
        card_game_manager.set_all_cards_chance(chance)
        logger.info('%s changed all cards spawnability, permission allowed', interaction.user.name)
        return
    if not card_game_manager.check_card_exists(card):
        await interaction.followup.send('This is not a valid existing card!')
        logger.warn('%s tried to change card spawnability, permission allowed,card not found', interaction.user.name)
        return
    if not spawnable:
        chance = 0.
        await interaction.followup.send('The card will no longer spawn!')
    else:
        chance = 1.
        await interaction.followup.send('The card is now spawnable!')
    card = card_game_manager.get_card_by_id(card)
    card_game_manager.set_card_chance(card, chance)
    logger.info('%s changed %s card spawnability, permission allowed', interaction.user.name, str(card))


@log_errors
@app_commands.describe(card='Choose your card that you want to grade:')
@app_commands.autocomplete(card=grade_autocomplete)
@tree.command(name='grade', guild=ICEDOUTSERVER)
async def _grade(interaction: discord.Interaction, card: str):
    if '_12c76c7711c67894c34c234c7098642c0b7' not in card:
        await interaction.response.send_message(f'This is not a valid card from your collection!', ephemeral=True)
        return
    idx = int(card.split('_')[0])
    _card = idx_to_card(card_game_manager, interaction.user.id, idx)
    num = round(random.choices(population=pop, weights=weights, k=1)[0], 1)
    if num == 6.0 or num >= 9.5:
        if num == 6.0:
            emoji = Emoji.SKULL
        elif num == 10.0:
            emoji = Emoji.MINDBLOWN
        else:
            emoji = Emoji.PARTYING
        await interaction.response.send_message(f'<@{interaction.user.id}> got a ***{_card.card.name}***'
                                                f' card with the grade {num}! {emoji}', ephemeral=False)
    else:
        await interaction.response.send_message(f'{_card.card.name}\'s grade is now {num}!', ephemeral=True)
    card_game_manager.save_grade(interaction.user.id, _card, num)


@log_errors
@app_commands.describe(name='Name of the collection (register doesn\'t matter)',
                       emoji='The emoji that will show up next to each card',
                       chance='Relative chance of choosing a card from this collection. Default value is 1.')
@app_commands.checks.has_any_role(Role.ICY_ROLE, Role.MOD)
@tree.command(name='add_collection', guild=ICEDOUTSERVER)
async def add_collection(interaction: discord.Interaction, name: str, emoji: str, chance: Optional[float] = 1.):
    await defer(interaction, 'add_collection')
    message = 'The collection is successfully added!'
    if card_game_manager.check_collection_exists(name):
        message = 'Collection with this name already exists!'
    elif chance < 0:
        message = 'Chance value can\'t be negative!'
    else:
        card_game_manager.add_collection(Collection(name, emoji.replace(' ', ''), chance))
    await interaction.followup.send(message)
    logger.info('%s added collection, permission allowed', interaction.user.name)


@log_errors
@app_commands.describe(name='Name of the collection. Keep blank to leave unchanged.',
                       emoji='The emoji that will show up next to each card. Keep blank to leave unchanged.',
                       chance='Relative chance of choosing a card from this collection. Keep blank to leave unchanged.')
@app_commands.autocomplete(collection=collection_autocomplete)
@app_commands.checks.has_any_role(Role.ICY_ROLE, Role.MOD)
@tree.command(name='edit_collection', guild=ICEDOUTSERVER)
async def edit_collection(interaction: discord.Interaction, collection: str, name: str = '', emoji: str = '',
                          chance: float = None):
    await defer(interaction, 'edit_collection')
    if not card_game_manager.check_collection_exists(collection):
        await interaction.followup.send('This is not a valid existing collection!')
        return
    collection = card_game_manager.get_collection(collection)
    if name == '':
        name = collection.name
    if emoji == '':
        emoji = collection.emoji
    if chance is None:
        chance = collection.chance
    message = 'The edits are successfully saved!'
    if name != collection.name and card_game_manager.check_collection_exists(name):
        message = 'A different collection with this name already exists!'
    elif chance < 0:
        message = 'Chance value can\'t be negative!'
    else:
        card_game_manager.edit_collection(collection, name, emoji.replace(' ', ''), chance)
    await interaction.followup.send(message)
    logger.info('%s edited collection %s, permission allowed', interaction.user.name, collection.name)


@log_errors
@app_commands.describe(collection='Choose a collection to delete:')
@app_commands.autocomplete(collection=collection_autocomplete)
@app_commands.checks.has_any_role(Role.ICY_ROLE, Role.MOD)
@tree.command(name='delete_collection', guild=ICEDOUTSERVER)
async def delete_collection(interaction: discord.Interaction, collection: str):
    await defer(interaction, 'delete_collection')
    if not card_game_manager.check_collection_exists(collection):
        await interaction.followup.send('This is not an existing collection!')
        return
    collection = card_game_manager.get_collection(collection)
    card_game_manager.delete_collection(collection)
    message = 'The collection is successfully deleted!'
    await interaction.followup.send(message)
    logger.info('%s edited collection %s, permission allowed', interaction.user.name, collection.name)


@log_errors
@app_commands.autocomplete(action=get_autocomplete(['join', 'leave', 'info', 'push', 'undo_push']))
@app_commands.autocomplete(queue_name=queue_name_autocomplete)
@tree.command(name='queue', guild=ICEDOUTSERVER)
async def queue(interaction: discord.Interaction, action: str, queue_name: str):
    await defer(interaction, 'queue')
    try:
        q = queue_manager.get_queue_by_name(queue_name)
    except modules.queue.QueueNotFound:
        await interaction.followup.send('This is not an existing queue name!')
        return

    message = ''
    if action == 'join':
        if q.check_roles(interaction.user):
            if q.can_join(interaction.user.id):
                message = 'You successfully joined the queue!'
                q.join(interaction.user.id)
            else:
                message = 'You are already in the queue!'
        else:
            message = 'Your roles don\'t allow you to join this queue!'
    elif action == 'leave':
        if q.in_queue(interaction.user.id):
            message = 'You successfully left the queue!'
            q.leave(interaction.user.id)
        else:
            message = 'You were not in the queue!'
    elif action == 'info':
        await paginate(interaction, [], 'Queue is empty!', numbered=False) if q.is_empty()\
             else await paginate(interaction, q.info(), 'Current queue:', numbered=True)
    elif action == 'push':
        if is_icy(interaction.user):
            if q.can_push():
                user_id = q.push()
                message = f'Pushed successfully, <@{user_id}> left the queue!'
            else:
                message = 'Queue is already empty!'
        else:
            message = 'You don\'t have the permission to run this command!'
    elif action == 'undo_push':
        if is_icy(interaction.user):
            if q.can_undo_push():
                message = 'Push reverted successfully!'
                q.undo_push()
            else:
                message = 'There were no pushes yet!'
        else:
            message = 'You don\'t have the permission to run this command!'
    else:
        action = 'Undefined'
        message = 'Wrong action'
    queue_manager.save_queues()
    if action != 'info':
        await interaction.followup.send(message)
    logger.info('%s %s the queue', interaction.user.name, action)


@log_errors
@app_commands.describe(card='Choose your card that you want to see:')
@app_commands.autocomplete(card=card_autocomplete)
@tree.command(name='show', guild=ICEDOUTSERVER)
async def show(interaction: discord.Interaction, card: str):
    if '_12c76c7711c67894c34c234c7098642c0b7' not in card:
        await interaction.response.send_message(f'This is not a valid card from your collection!', ephemeral=True)
        return
    idx = int(card.split('_')[0])
    _card = idx_to_card(card_game_manager, interaction.user.id, idx)
    total = card_game_manager.get_total(_card.card)
    player_total = card_game_manager.get_player_total(_card.card, interaction.user.id)
    ending = "ies" if player_total > 1 else "y"
    image = card_game_manager.get_image(_card)
    with BytesIO() as image_binary:
        image.save(image_binary, 'PNG')
        image_binary.seek(0)
        await interaction.response.send_message(
            content=f'You have {player_total} cop{ending} out of {total} in total!',
            file=discord.File(fp=image_binary, filename='card.png'), ephemeral=False)


@log_errors
@app_commands.describe(collection='Choose to collection to see your progress or leave blank to '
                                  'see your overall completion:')
@app_commands.autocomplete(collection=progress_autocomplete)
@tree.command(name='progress', guild=ICEDOUTSERVER)
async def progress(interaction: discord.Interaction, collection: Optional[str] = 'All'):
    await defer(interaction, 'progress', ephemeral=False)
    logger.info('%s ran /progress, permission allowed', interaction.user.name)
    nick = get_nickname(interaction.user)
    if collection == 'All':
        lst = card_game_manager.get_overall_progress(interaction.user.id)
        await paginate(interaction, lst, f'**{nick}\'s progress:**\n')
        return
    if '_12c76c7711c67894c34c234c7098642c0b7' not in collection:
        await interaction.followup.send(f'This is not a valid collection!', ephemeral=True)
        return
    idx = int(collection.split('_')[0])
    _collection = idx_to_collection(card_game_manager, idx)
    lst = card_game_manager.get_progress(interaction.user.id, _collection)
    await paginate(interaction, lst, f'**{nick}\'s progress:**\n')


@log_errors
@app_commands.describe(link='Paste the link to your GeoGuessr profile:')
@tree.command(name='add_profile', guild=ICEDOUTSERVER)
async def add_profile(interaction: discord.Interaction, link: str):
    await defer(interaction, 'add_profile', ephemeral=True)
    logger.info('%s ran /add_profile, permission allowed', interaction.user.name)
    link = link.strip()
    if link == 'https://www.geoguessr.com/me/profile':
        message = 'Rookie mistake! The profile link is found on the bottom of the "Profile" page. Try again!'
    elif link.find('https://www.geoguessr.com/user/') == 0:
        link = link.replace('https://www.geoguessr.com/user/', '').strip(' /\\')
        if not link.isalnum():
            logger.error(f'Wrong format profile link submitted, not alphanumerical: {link}')
            message = 'Wrong link format. The profile link is found on the bottom of the "Profile" page. Try again!'
        else:
            if profile_manager.is_profile_submitted(interaction.user.id):
                message = 'Your profile is successfully updated!'
            else:
                message = 'Your profile is successfully added!'
            profile_manager.store_profile(interaction.user.id, link)
    else:
        logger.info(f'Wrong format profile link submitted: {link}')
        message = 'Wrong link format. The profile link is found on the bottom of the "Profile" page. Try again!'
    await interaction.followup.send(message)


@log_errors
@tree.command(name='view_profiles', guild=ICEDOUTSERVER)
@app_commands.checks.has_any_role(Role.ICY_ROLE, Role.MOD)
async def view_profiles(interaction: discord.Interaction, user: Optional[discord.Member] = None):
    await defer(interaction, 'add_profile', ephemeral=True)
    logger.info('%s ran /view_profiles, permission allowed', interaction.user.name)
    if user is None:
        message = profile_manager.create_profiles_message_list()
        logger.debug(f'Created profiles message list: {message}')
        await paginate(interaction, message, 'Profile links')
    else:
        message = profile_manager.get_user_profile_message(user.id)
        await interaction.followup.send(message)
