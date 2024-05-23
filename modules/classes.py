from __future__ import annotations

import itertools
import json
import random
import typing
from dataclasses import dataclass
from pathlib import Path

import discord
import jsonpickle

import modules.data as data
import modules.functions as functions
import modules.ui_classes as ui_classes
from modules.logger import logger


Vetoable = data.Map | data.Gamemode


class Match3PLeague:
    def __init__(self, id_1: int, id_2: int, tier: data.Tier,
                 week: int, backup_1=False, backup_2=False, announced=False):
        self.id_1 = id_1
        self.id_2 = id_2
        self.tier = tier
        self.week = week
        self.backup = [backup_1, backup_2]
        self.announced = announced

    def __str__(self) -> str:
        return f'<@{self.id_1}> vs <@{self.id_2}>'

    def __eq__(self, other) -> bool:
        if not isinstance(other, Match3PLeague):
            return False
        return self.id_1 == other.id_1 and self.id_2 == other.id_2 and self.tier == other.tier and \
               self.week == other.week


class ArbitraryPick:
    def __init__(self, world_map_picks: list[data.Map],
                 world_map_vetoes: list[data.Map], country_map_picks: list[data.Map],
                 country_map_vetoes: list[data.Map], redeemed_mode: data.Gamemode | None,
                 vetoed_modes: list[data.Gamemode] | None):
        self.redeemed_mode = data.DEFAULT_GAMEMODE if redeemed_mode is None else redeemed_mode
        self.vetoed_modes = vetoed_modes if vetoed_modes is not None else []
        self.world_map_picks = world_map_picks
        self.world_map_vetoes = world_map_vetoes
        self.country_map_picks = country_map_picks
        self.country_map_vetoes = country_map_vetoes

    def __str__(self) -> str:
        s = "World map picks:"
        for _map in self.world_map_picks:
            s += f"\n{_map.name}"
        s += "\nCountry map picks:"
        for _map in self.country_map_picks:
            s += f"\n{_map.name}"
        s += "\nWorld map vetoes:"
        for _map in self.world_map_vetoes:
            s += f"\n{_map.name}"
        s += "\nCountry map vetoes:"
        for _map in self.country_map_vetoes:
            s += f"\n{_map.name}"
        s += f"\nRedeemed gamemode: {self.redeemed_mode.name}"
        return s


class Pick:
    def __init__(self, user_id: int, match: Match3PLeague, arbitrary_pick: ArbitraryPick,
                 known_vetoes: list[Vetoable] | None = None):
        self.user_id = user_id
        self.match = match
        self.redeemed_mode = data.DEFAULT_GAMEMODE if arbitrary_pick.redeemed_mode is None else \
            arbitrary_pick.redeemed_mode
        self.vetoed_modes = arbitrary_pick.vetoed_modes
        self.world_map_picks = arbitrary_pick.world_map_picks
        self.world_map_vetoes = arbitrary_pick.world_map_vetoes
        self.country_map_picks = arbitrary_pick.country_map_picks
        self.country_map_vetoes = arbitrary_pick.country_map_vetoes
        self.known_vetoes = known_vetoes if known_vetoes is not None else []

    def set_arbitrary_pick(self, arbitrary_pick: ArbitraryPick):
        self.redeemed_mode = data.DEFAULT_GAMEMODE if arbitrary_pick.redeemed_mode is None else \
            arbitrary_pick.redeemed_mode
        self.vetoed_modes = arbitrary_pick.vetoed_modes
        self.world_map_picks = arbitrary_pick.world_map_picks
        self.world_map_vetoes = arbitrary_pick.world_map_vetoes
        self.country_map_picks = arbitrary_pick.country_map_picks
        self.country_map_vetoes = arbitrary_pick.country_map_vetoes

    def __str__(self) -> str:
        s = f"Pick by {self.user_id} for match {self.match.id_1} vs {self.match.id_2}:\n"
        s += "World map picks:"
        for _map in self.world_map_picks:
            s += f"\n{_map.name}"
        s += "\nCountry map picks:"
        for _map in self.country_map_picks:
            s += f"\n{_map.name}"
        s += "\nWorld map vetoes:"
        for _map in self.world_map_vetoes:
            s += f"\n{_map.name}"
        s += "\nCountry map vetoes:"
        for _map in self.country_map_vetoes:
            s += f"\n{_map.name}"
        s += f"\nRedeemed gamemode: {self.redeemed_mode.name}"
        s += f"\nKnown vetoes:\n"
        for _map in self.known_vetoes:
            s += f"{_map.name}\n"
        return s

    def __eq__(self, other: Pick) -> bool:
        if not isinstance(other, Pick):
            raise TypeError('Comparison Pick to unknown object')
        return self.user_id == other.user_id and self.match == other.match


class PickManager:
    def __init__(self, client: discord.Client):
        self.players = []
        self.picks: list[Pick] = []
        self.matches: list[Match3PLeague] = []
        self.CURRENT_WEEK = 0
        self.client = client
        self.world_map_list = []
        self.country_map_list = []
        self.set_up_map_lists(self.CURRENT_WEEK)
        self.locks = []

    def set_current_week(self, value: int) -> None:
        self.CURRENT_WEEK = value
        self.set_up_map_lists(self.CURRENT_WEEK)

    @staticmethod
    def configure_world_map_list() -> list[data.WorldMap]:
        return data.WORLD_MAP_LIST

    @staticmethod
    def check_adjacent_weeks(country_map_list: list[data.CountryMap], week: int) -> bool:
        s = set([_map.name for _map in country_map_list])
        if (prv := functions.open_country_map_list(week-1)) is not None:
            if s & set([_map.name for _map in prv]):
                return False
        if (nxt := functions.open_country_map_list(week+1)) is not None:
            if s & set([_map.name for _map in nxt]):
                return False
        return True

    def configure_country_map_list(self, week: int) -> list[data.CountryMap]:
        lst = random.sample(list(filter(lambda x: x.tier == data.MapTier.A, data.COUNTRY_MAP_LIST)),
                            k=data.A_TIER_COUNT) + \
              random.sample(list(filter(lambda x: x.tier == data.MapTier.B, data.COUNTRY_MAP_LIST)),
                            k=data.B_TIER_COUNT) + \
              random.sample(list(filter(lambda x: x.tier == data.MapTier.C, data.COUNTRY_MAP_LIST)),
                            k=data.C_TIER_COUNT)
        if self.check_adjacent_weeks(lst, week):
            return lst
        else:
            return self.configure_country_map_list(week)

    async def send_picks(self, interaction: discord.Interaction, match: Match3PLeague, arbitrary_pick: ArbitraryPick):
        user = interaction.user
        pick = Pick(user.id, match, arbitrary_pick)
        if pick in self.picks:
            await interaction.response.edit_message(content='You already made picks for this match!', view=None)
            logger.warn('Already existing pick sent!\n Player %s (%d) sent picks for match %s vs %s in %s in week %d. '
                        '%s.', user.name, user.id, match.id_1, match.id_2, match.tier.value, match.week, arbitrary_pick)
            return
        self.picks.append(pick)
        logger.info('Player %s (%d) sent picks for match %s vs %s in %s in week %d. %s.', user.name, user.id,
                    match.id_1, match.id_2, match.tier.value, match.week, arbitrary_pick)
        self.save_picks()
        checked = functions.check_match_ready(match, self.picks)
        if checked:
            await self.set_up_match(match, send_backup_message=True)

    async def send_backup_pick(self, interaction: discord.Interaction, match: Match3PLeague,
                               backup_arbitrary_pick: ArbitraryPick):
        user = interaction.user
        if not await self.handle_lock(interaction, match):
            return
        logger.info('Player %s (%d) sent backup pick for match %s vs %s in %s in week %d. %s.', user.name, user.id,
                    match.id_1, match.id_2, match.tier.value, match.week, backup_arbitrary_pick)
        for pick in self.picks:
            if pick.user_id == user.id and pick.match == match:
                self.update_pick(pick.user_id, match, backup_arbitrary_pick, pick)

        if user.id == match.id_1:
            match.backup[0] = False
        elif user.id == match.id_2:
            match.backup[1] = False

        self.save_picks()
        self.save_matches()
        checked = functions.check_match_ready(match, self.picks)
        if checked:
            await self.set_up_match(match, send_backup_message=False)

    async def handle_lock(self, interaction: discord.Interaction, match: Match3PLeague) -> bool:
        user = interaction.user
        if self.check_lock(user, match):
            await interaction.response.edit_message(content='You already made picks for this match!', view=None)
            return False
        self.lock_pick(user, match)
        return True

    def update_pick(self, user_id: int, match: Match3PLeague, backup_arbitrary_pick: ArbitraryPick,
                           initial_pick: Pick):
        opponent_pick = None
        for pick in self.picks:
            if pick.user_id != user_id and pick.match == match:
                opponent_pick = pick
                break
        i = 0
        for idx, _map in enumerate(initial_pick.world_map_picks):
            if _map in opponent_pick.world_map_vetoes:
                if len(backup_arbitrary_pick.world_map_picks) <= i:
                    logger.warn("Not all vetoed world map picks are sent in backup!")
                    break
                initial_pick.world_map_picks[idx] = backup_arbitrary_pick.world_map_picks[i]
                i += 1
        for idx, _map in enumerate(initial_pick.country_map_picks):
            if _map in opponent_pick.country_map_vetoes:
                if len(backup_arbitrary_pick.country_map_picks) <= i:
                    logger.warn("Not all vetoed country map picks are sent in backup!")
                    break
                initial_pick.country_map_picks[idx] = backup_arbitrary_pick.country_map_picks[i]
                i += 1
        if initial_pick.redeemed_mode in opponent_pick.vetoed_modes:
            if backup_arbitrary_pick.redeemed_mode is None:
                logger.warn("Vetoed gamemode is not sent in backup!")
            initial_pick.redeemed_mode = backup_arbitrary_pick.redeemed_mode

    def save_picks(self):
        lst = []
        for pick in self.picks:
            lst.append({'user_id': pick.user_id,
                        'match': {'id_1': pick.match.id_1,
                                  'id_2': pick.match.id_2,
                                  'tier': pick.match.tier,
                                  'week': pick.match.week,
                                  'backup': pick.match.backup,
                                  'announced': pick.match.announced},
                        'world_map_picks': list(map(jsonpickle.encode, pick.world_map_picks)),
                        'world_map_vetoes': list(map(jsonpickle.encode, pick.world_map_vetoes)),
                        'country_map_picks': list(map(jsonpickle.encode, pick.country_map_picks)),
                        'country_map_vetoes': list(map(jsonpickle.encode, pick.country_map_vetoes)),
                        'redeemed_mode': pick.redeemed_mode.value,
                        'vetoed_modes': [mode.value for mode in pick.vetoed_modes],
                        'known_vetoes': list(map(jsonpickle.encode, pick.known_vetoes)),
                        })

        with open(Path('data', 'picks.json'), 'w+') as file:
            json.dump(lst, file)

    def open_picks(self):
        with open(Path('data', 'picks.json'), 'r') as file:
            picks = json.load(file)
        self.picks = []
        for pick in picks:
            known_vetoes = list(map(jsonpickle.decode, pick['known_vetoes']))
            vetoed_modes = [data.Gamemode(i) for i in pick['vetoed_modes']]
            match = Match3PLeague(pick['match']['id_1'], pick['match']['id_2'], data.Tier(pick['match']['tier']),
                                  pick['match']['week'], pick['match']['backup'][0], pick['match']['backup'][1],
                                  pick['match']['announced'])
            arbitrary_pick = ArbitraryPick(list(map(jsonpickle.decode, pick['world_map_picks'])),
                                           list(map(jsonpickle.decode, pick['world_map_vetoes'])),
                                           list(map(jsonpickle.decode, pick['country_map_picks'])),
                                           list(map(jsonpickle.decode, pick['country_map_vetoes'])),
                                           data.Gamemode(pick['redeemed_mode']),
                                           vetoed_modes)
            self.picks.append(Pick(pick['user_id'], match, arbitrary_pick, known_vetoes))

    def save_matches(self):
        lst = []
        for match in self.matches:
            lst.append({'id_1': match.id_1, 'id_2': match.id_2, 'tier': match.tier, 'week': match.week,
                        'backup': match.backup, 'announced': match.announced})

        with open(Path('data', 'matches.json'), 'w+') as file:
            json.dump(lst, file)
        self.save_picks()

    def open_matches(self):
        with open(Path('data', 'matches.json'), 'r') as file:
            matches = json.load(file)
        self.matches = []
        for match in matches:
            self.matches.append(Match3PLeague(match['id_1'], match['id_2'], data.Tier(match['tier']), match['week'],
                                              match['backup'][0], match['backup'][1], match['announced']))

    @staticmethod
    def check_vetoes(pick_player1: Pick, pick_player2: Pick) -> bool:
        """
        Checks if player 1's picks were vetoed by player 2 and adds the vetoed map to known vetoes lists if they were
        """
        for _map in pick_player1.world_map_picks:
            if _map in pick_player2.world_map_vetoes:
                pick_player1.known_vetoes.append(_map)
                return True
        for _map in pick_player1.country_map_picks:
            if _map in pick_player2.country_map_vetoes:
                pick_player1.known_vetoes.append(_map)
                return True
        if pick_player1.redeemed_mode in pick_player2.vetoed_modes:
            pick_player1.known_vetoes.append(pick_player1.redeemed_mode)
            return True
        return False

    async def set_up_match(self, match: Match3PLeague, send_backup_message=True):
        picks: list[Pick] = [None, None]
        ids = (match.id_1, match.id_2)
        for idx, player in enumerate(ids):
            for pick in self.picks:
                if pick.user_id == player and pick.match == match:
                    picks[idx] = pick
                    break
        checked = True
        for i in (0, 1):
            if self.check_vetoes(picks[i], picks[1 - i]):
                self.unlock_pick(ids[i], match)
                if send_backup_message:
                    await self.send_backup_message(picks[i].user_id)
                match.backup[i] = True
                self.save_matches()
                checked = False
        if checked:
            await self.send_match(match, picks)

    async def send_backup_message(self, user_id: int):
        user = await functions.get_user_by_id(self.client, user_id)
        try:
            await user.send('Your picks have been vetoed, please run */pick* on the Iced Out Server again.')
        except discord.errors.Forbidden:
            logger.warn(f"{user.name} seems to have blocked their DMs!")
        except Exception as e:
            logger.error(e)

    @staticmethod
    def get_random_map(map_list: typing.Iterable[data.Map], vetoed_maps: list[data.Map]) -> data.Map:
        lst = list(map_list)
        for vetoed_map in vetoed_maps:
            if vetoed_map in lst:
                lst.remove(vetoed_map)
        return random.choice(lst)

    @staticmethod
    def assemble_announcement_message(match: Match3PLeague, picks: list[Pick, Pick]) -> str:
        lst = list(data.WORLD_MAP_LIST)
        for m in (picks[0].world_map_picks[0], picks[0].world_map_vetoes[0],
                  picks[1].world_map_picks[0], picks[1].world_map_vetoes[0]):
            if m in lst:
                lst.remove(m)
        random_map = random.choice(lst)
        country_map_1 = random.choice(picks[0].country_map_picks[0:5:1])
        country_map_2 = random.choice(picks[1].country_map_picks[0:5:1])
        message = f'Match:\n{str(match)}\n' \
                  f'Game 1: {picks[0].world_map_picks[0]} {picks[0].redeemed_mode.name} ' \
                  f'{picks[0].world_map_picks[0].link}\n' \
                  f'Game 2: {picks[1].world_map_picks[0]} {picks[1].redeemed_mode.name} ' \
                  f'{picks[1].world_map_picks[0].link}\n' \
                  f'Game 3: {country_map_1} NM {country_map_1.link}\n' \
                  f'Game 4 (if needed): {country_map_2} NM ' \
                  f'{country_map_2.link}\n' \
                  f'Game 5 (if needed): {random_map} NM ' \
                  f'{random_map.link}\n'
        return message

    async def send_match(self, match: Match3PLeague, picks: list[Pick, Pick]):
        message = self.assemble_announcement_message(match, picks)
        match.announced = True
        self.save_matches()
        channel = await functions.get_tier_channel(self.client, match.tier)
        await channel.send(message)

    def add_match(self, match: Match3PLeague):
        for m in self.matches:
            if m == match:
                return
        logger.info('Added match: %d vs %d in %s for week %d', match.id_1, match.id_2, match.tier.value, match.week)
        self.matches.append(match)
        self.save_matches()

    def reset_all_tiers(self):
        new_matches = []
        for match in self.matches:
            if match.week != self.CURRENT_WEEK:
                new_matches.append(match)
        self.matches = new_matches
        self.save_matches()

    def reset_tier(self, tier: data.Tier):
        new_matches = []
        for match in self.matches:
            if match.week != self.CURRENT_WEEK or match.tier != tier:
                new_matches.append(match)
        self.matches = new_matches
        self.save_matches()

    def check_if_picked(self, user_id: int, match: Match3PLeague) -> bool:
        for pick in self.picks:
            if match == pick.match and user_id == pick.user_id:
                if user_id == match.id_1 and not match.backup[0]:
                    return True
                elif user_id == match.id_2 and not match.backup[1]:
                    return True
        return False

    def get_match(self, user_id: int) -> Match3PLeague | None:
        for match in self.matches:
            if not match.announced and match.week == self.CURRENT_WEEK:
                if match.id_1 == user_id or match.id_2 == user_id:
                    if not self.check_if_picked(user_id, match):
                        return match
        return None

    def get_vetoed_maps(self, user_id: int, match: Match3PLeague) -> list[data.Map]:
        if user_id not in (match.id_1, match.id_2):
            raise AttributeError("Player is not found among the match participants!")
        if user_id == match.id_1:
            for pick in self.picks:
                if match == pick.match and pick.user_id == match.id_2:
                    return list(itertools.chain(pick.world_map_vetoes, pick.country_map_vetoes))
        if user_id == match.id_2:
            for pick in self.picks:
                if match == pick.match and pick.user_id == match.id_1:
                    return list(itertools.chain(pick.world_map_vetoes, pick.country_map_vetoes))

    def get_who_picked_message(self, _tier: data.Tier | None) -> str:
        message = f'Picks for week {self.CURRENT_WEEK}:\n\n'
        for tier in data.TIER_CHANNELS.keys():
            if _tier is not None and tier != _tier:
                continue
            name = tier.value
            message += f'{name}:\n'
            for match in self.matches:
                if match.tier == tier and match.week == self.CURRENT_WEEK:
                    player1 = data.Emoji.CROSS
                    player2 = data.Emoji.CROSS
                    for pick in self.picks:
                        if pick.match == match:
                            if pick.user_id == match.id_1:
                                player1 = data.Emoji.GREEN_CIRCLE
                            elif pick.user_id == match.id_2:
                                player2 = data.Emoji.GREEN_CIRCLE
                    if match.announced:
                        player1 = player2 = data.Emoji.CHECKMARK
                    else:
                        if match.backup[0]:
                            player1 = data.Emoji.RED_CIRCLE
                        if match.backup[1]:
                            player2 = data.Emoji.RED_CIRCLE
                    message += f'{player1} <@{match.id_1}> vs <@{match.id_2}> {player2}\n'
            message += f'\n'
        message += f'{data.Emoji.CROSS} — picks not sent\n{data.Emoji.RED_CIRCLE} — only main picks sent, need to ' \
                   f'send the backup pick\n{data.Emoji.GREEN_CIRCLE} — picks sent\n{data.Emoji.CHECKMARK} — ' \
                   f'both players sent picks, match already announced'
        return message

    def configure_pick_ui(self, user_id: int, match: Match3PLeague) -> ui_classes.PickUI:
        initial_pick = None
        other_picks: list[Pick] = []
        world_maps_list = list(self.world_map_list)
        country_maps_list = list(self.country_map_list)
        for pick in self.picks:
            if pick.match == match:
                if pick.user_id == user_id:
                    initial_pick = pick
            elif pick.user_id == user_id and pick.match.week == self.CURRENT_WEEK:
                other_picks.append(pick)
        redeemable_modes = list(data.Gamemode)
        if data.FORCE_DISTINCT_GAMEMODES:
            for pick in other_picks:
                if pick.redeemed_mode in redeemable_modes:
                    redeemable_modes.remove(pick.redeemed_mode)
        if initial_pick is None:
            world_map_vetoes_lists = [world_maps_list] * data.WORLD_MAP_VETOES_COUNT
            country_map_vetoes_lists = [country_maps_list] * data.COUNTRY_MAP_VETOES_COUNT
            self.remove_repetitions(other_picks, world_maps_list, country_maps_list)
            world_maps_lists = [world_maps_list] * data.WORLD_MAP_PICKS_COUNT
            country_maps_lists = [country_maps_list] * data.COUNTRY_MAP_PICKS_COUNT
            pick_ui = ui_classes.PickUI(match, self, False, world_maps_lists, world_map_vetoes_lists,
                                        country_maps_lists, country_map_vetoes_lists, data.MODE_REDEMPTION,
                                        match.tier in data.MOVING_TIERS, match.tier in data.NMPZ_TIERS,
                                        redeemable_modes)
        else:
            vetoed_world_maps = 0
            vetoed_country_maps = 0
            for _map in initial_pick.world_map_picks:
                if _map in initial_pick.known_vetoes:
                    vetoed_world_maps += 1
                    if _map in world_maps_list:
                        world_maps_list.remove(_map)
            for _map in initial_pick.country_map_picks:
                if _map in initial_pick.known_vetoes:
                    vetoed_country_maps += 1
                    if _map in country_maps_list:
                        country_maps_list.remove(_map)
            has_mode_redemption = initial_pick.redeemed_mode in initial_pick.known_vetoes
            if has_mode_redemption:
                for gamemode in initial_pick.known_vetoes:
                    if gamemode in redeemable_modes:
                        redeemable_modes.remove(gamemode)

            self.remove_repetitions(other_picks, world_maps_list, country_maps_list)
            world_maps_lists = [world_maps_list] * vetoed_world_maps
            country_maps_lists = [country_maps_list] * vetoed_country_maps
            pick_ui = ui_classes.PickUI(match, self, True, world_maps_lists, [], country_maps_lists, [],
                                        has_mode_redemption, match.tier in data.MOVING_TIERS and
                                        len(world_maps_lists) > 0, match.tier in data.NMPZ_TIERS and
                                        len(world_maps_lists) > 0, redeemable_modes)
            logger.debug(f'vetoed_world_maps: {vetoed_world_maps}, vetoed_country_maps: {vetoed_country_maps}, '
                         f'world_maps_lists: {world_maps_lists}, country_maps_lists: {country_maps_lists}, '
                         f'has_mode_redemption: {has_mode_redemption}, known: {initial_pick.known_vetoes}, '
                         f'wmp: {initial_pick.world_map_picks}')
        # TODO: gamemode vetoes
        return pick_ui

    def configure_playoffs_pick_ui(self, user_id: int, match: Match3PLeague) -> ui_classes.PickUI:
        initial_pick = None
        other_picks: list[Pick] = []
        world_maps_list = list(self.world_map_list)
        country_maps_list = list(self.country_map_list)
        a_tier_list = list(filter(lambda x: x.tier == data.MapTier.A, data.COUNTRY_MAP_LIST))
        b_tier_list = list(filter(lambda x: x.tier == data.MapTier.B, data.COUNTRY_MAP_LIST))
        c_tier_list = list(filter(lambda x: x.tier == data.MapTier.C, data.COUNTRY_MAP_LIST))
        for pick in self.picks:
            if pick.match == match:
                if pick.user_id == user_id:
                    initial_pick = pick
            elif pick.user_id == user_id and pick.match.week == self.CURRENT_WEEK:
                other_picks.append(pick)
        redeemable_modes = list(data.Gamemode)
        if data.FORCE_DISTINCT_GAMEMODES:
            for pick in other_picks:
                if pick.redeemed_mode in redeemable_modes:
                    redeemable_modes.remove(pick.redeemed_mode)
        if initial_pick is None:
            world_map_vetoes_lists = [world_maps_list] * data.WORLD_MAP_VETOES_COUNT
            country_map_vetoes_lists = [country_maps_list] * data.COUNTRY_MAP_VETOES_COUNT
            self.remove_repetitions(other_picks, world_maps_list, country_maps_list)
            world_maps_lists = [world_maps_list] * data.WORLD_MAP_PICKS_COUNT
            country_maps_lists = [a_tier_list, a_tier_list, b_tier_list, b_tier_list, c_tier_list]
            pick_ui = ui_classes.PickUI(match, self, False, world_maps_lists, world_map_vetoes_lists,
                                        country_maps_lists, country_map_vetoes_lists, data.MODE_REDEMPTION,
                                        match.tier in data.MOVING_TIERS, match.tier in data.NMPZ_TIERS,
                                        redeemable_modes)
        else:
            vetoed_world_maps = 0
            vetoed_country_maps = 0
            for _map in initial_pick.world_map_picks:
                if _map in initial_pick.known_vetoes:
                    vetoed_world_maps += 1
                    if _map in world_maps_list:
                        world_maps_list.remove(_map)
            for _map in initial_pick.country_map_picks:
                if _map in initial_pick.known_vetoes:
                    vetoed_country_maps += 1
                    if _map in country_maps_list:
                        country_maps_list.remove(_map)
            has_mode_redemption = initial_pick.redeemed_mode in initial_pick.known_vetoes
            if has_mode_redemption:
                for gamemode in initial_pick.known_vetoes:
                    if gamemode in redeemable_modes:
                        redeemable_modes.remove(gamemode)

            self.remove_repetitions(other_picks, world_maps_list, country_maps_list)
            world_maps_lists = [world_maps_list] * data.WORLD_MAP_PICKS_COUNT
            country_maps_lists = []
            pick_ui = ui_classes.PickUI(match, self, True, world_maps_lists, [], country_maps_lists, [],
                                        has_mode_redemption, match.tier in data.MOVING_TIERS and
                                        len(world_maps_lists) > 0, match.tier in data.NMPZ_TIERS and
                                        len(world_maps_lists) > 0, redeemable_modes)
            logger.debug(f'vetoed_world_maps: {vetoed_world_maps}, vetoed_country_maps: {vetoed_country_maps}, '
                         f'world_maps_lists: {world_maps_lists}, country_maps_lists: {country_maps_lists}, '
                         f'has_mode_redemption: {has_mode_redemption}, known: {initial_pick.known_vetoes}, '
                         f'wmp: {initial_pick.world_map_picks}')
        # TODO: gamemode vetoes
        return pick_ui

    @staticmethod
    def remove_repetitions(other_picks: list[Pick], world_maps_list: list[data.Map],
                           country_maps_list: list[data.Map]):
        if data.FORCE_DISTINCT_WORLD_MAPS:
            for pick in other_picks:
                for _map in pick.world_map_picks:
                    if _map in world_maps_list:
                        world_maps_list.remove(_map)
        if data.FORCE_DISTINCT_COUNTRY_MAPS:
            for pick in other_picks:
                for _map in pick.country_map_picks:
                    if _map in country_maps_list:
                        country_maps_list.remove(_map)

    def add_matches(self, message: discord.Message, week: int) -> bool:
        text = message.content.split('\n')
        found = False
        for line in text:
            if line.find('vs') != -1 and line.find('<@') != -1:
                players = functions.get_players(line)
                if len(players) == 2:
                    tier = functions.get_tier(message.channel.id)
                    match = Match3PLeague(players[0], players[1], tier, week)
                    self.add_match(match)
                    found = True
        return found

    def set_up_map_lists(self, week: int):
        if (lst := functions.open_world_map_list(week)) is None:
            self.world_map_list = self.configure_world_map_list()
        else:
            self.world_map_list = lst
        if (lst := functions.open_country_map_list(week)) is None:
            self.country_map_list = self.configure_country_map_list(week)
        else:
            self.country_map_list = lst
        self.save_map_lists()

    def save_map_lists(self):
        with open(Path('data', 'map_lists.json'), 'r') as file:
            lst = json.load(file)
        for week in lst:
            if week['week'] == self.CURRENT_WEEK:
                return
        lst.append({'week': self.CURRENT_WEEK,
                    'world_maps': list(map(jsonpickle.encode, self.world_map_list)),
                    'country_maps': list(map(jsonpickle.encode, self.country_map_list))})
        with open(Path('data', 'map_lists.json'), 'w+') as file:
            json.dump(lst, file)

    def lock_pick(self, user: discord.User, match: Match3PLeague):
        self.locks.append((user.id, match))

    def check_lock(self, user: discord.User, match: Match3PLeague):
        return (user.id, match) in self.locks

    def unlock_pick(self, user_id: int, match: Match3PLeague):
        if (user_id, match) in self.locks:
            self.locks.remove((user_id, match))


@dataclass
class WCSMessage:
    message: discord.Message
    checks: int
    crosses: int


class MessageRegistrator:
    def __init__(self, threshold):
        self.count = self.open_message_count()
        self.threshold = threshold

    @staticmethod
    def open_message_count() -> int:
        with open(Path('data', 'config.json'), 'r') as file:
            dct = json.load(file)
        return dct['message_count']

    @staticmethod
    def save_message_count(count: int) -> None:
        with open(Path('data', 'config.json'), 'r') as file:
            dct = json.load(file)
        dct['message_count'] = count
        with open(Path('data', 'config.json'), 'w') as file:
            json.dump(dct, file)

    def increase_count(self) -> None:
        with open(Path('data', 'config.json'), 'r') as file:
            dct = json.load(file)
        dct['message_count'] = (dct['message_count'] + 1) % self.threshold
        self.count = dct['message_count']
        with open(Path('data', 'config.json'), 'w') as file:
            json.dump(dct, file)

    def check_message_count(self, threshold: int | None = None) -> bool:
        success = random.choices((True, False), (1 / threshold, 1 - 1 / threshold))[0]
        return self.count == 0 if threshold is None else success


class ConfigManager:
    def __init__(self):
        self.CURRENT_WEEK = 0
        self.PLAYOFFS = False


class InvalidChannelError(Exception):
    def __init__(self, msg: str):
        super(InvalidChannelError, self).__init__(msg)
