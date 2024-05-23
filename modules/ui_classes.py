from __future__ import annotations

import itertools
import typing

import discord

import modules.classes as classes
import modules.data as data
import modules.functions as functions
from modules.logger import logger


class MapSelectMenu(discord.ui.Select):
    def __init__(self, map_list: typing.Iterable[data.Map], label: str,
                 command_name: str = 'MapSelectMenu'):
        super(MapSelectMenu, self).__init__()
        self.command_name = command_name
        self.map_list = list(map_list)
        for _map in map_list:
            self.add_option(label=label + _map.name)

    async def callback(self, interaction: discord.Interaction):
        await functions.defer(interaction, command_name=self.command_name)


class VetoSelectMenu(MapSelectMenu):
    def __init__(self, map_list: list[data.Map]):
        super(VetoSelectMenu, self).__init__(map_list, 'Veto ', 'VetoSelectMenu')


class PickSelectMenu(MapSelectMenu):
    def __init__(self, map_list: list[data.Map]):
        super(PickSelectMenu, self).__init__(map_list, 'Pick ', 'PickSelectMenu')


class SendButton(discord.ui.Button):
    def __init__(self, pick_ui: PickUI):
        super(SendButton, self).__init__()
        self.label = 'Send picks'
        self.pick_ui = pick_ui

    async def callback(self, interaction: discord.Interaction):
        await self.pick_ui.send(interaction)


class RedeemModeMenu(discord.ui.Select):
    def __init__(self, gamemode_list: list[data.Gamemode]):
        super(RedeemModeMenu, self).__init__()
        for mode in gamemode_list:
            self.add_option(label='Pick ' + mode.name)

    async def callback(self, interaction: discord.Interaction):
        await functions.defer(interaction, command_name='RedeemMode')


class RedeemButton(discord.ui.Button):
    def __init__(self, pick_ui: PickUI, label: str, active_label: str, activate_message: str, deactivate_message: str):
        super(RedeemButton, self).__init__()
        self.inactive_label = label
        self.active_label = active_label
        self.pick_ui = pick_ui
        self.label = label
        self.active = False
        self.activate_message = activate_message
        self.deactivate_message = deactivate_message
        self.inactive_style = discord.ButtonStyle.green
        self.active_style = discord.ButtonStyle.red
        self.style = self.inactive_style

    async def callback(self, interaction: discord.Interaction):
        if self.active:
            self.active = False
            self.style = self.inactive_style
            self.label = self.inactive_label
            await interaction.response.send_message(content=self.deactivate_message, ephemeral=True)
        else:
            self.active = True
            self.style = self.active_style
            self.label = self.active_label
            await interaction.response.send_message(content=self.activate_message, ephemeral=True)


class RedeemNMPZButton(RedeemButton):
    def __init__(self, pick_ui: PickUI):
        super(RedeemNMPZButton, self).__init__(pick_ui, 'Redeem NMPZ', 'Unredeem NMPZ',
                                               'You redeemed NMPZ on your world map.',
                                               'You unredeemed NMPZ on your world map.')


class RedeemMovingButton(RedeemButton):
    def __init__(self, pick_ui: PickUI):
        super(RedeemMovingButton, self).__init__(pick_ui, 'Redeem Moving', 'Unredeem Moving',
                                                 'You redeemed Moving on your world map.',
                                                 'You unredeemed Moving on your world map.')


class ResetPicksSelectMenu(discord.ui.Select):
    def __init__(self):
        super(ResetPicksSelectMenu, self).__init__()
        for tier in data.TIER_CHANNELS.keys():
            self.add_option(label=tier.value)
        self.add_option(label='All tiers')

    async def callback(self, interaction: discord.Interaction):
        await functions.defer(interaction, command_name='ResetPicksSelectMenu')


class ResetPicksSendButton(discord.ui.Button):
    def __init__(self, pick_ui: ResetPicksUI, pick_manager: classes.PickManager):
        super(ResetPicksSendButton, self).__init__()
        self.pick_ui = pick_ui
        self.pick_manager = pick_manager
        self.approved = False
        self.label = 'Reset matches'

    async def callback(self, interaction: discord.Interaction):
        if len(self.pick_ui.select_menu.values) == 0:
            await interaction.response.send_message('Please select tier or cancel.', ephemeral=True)
        elif self.approved:
            tier = self.pick_ui.select_menu.values[0]
            if tier == 'All tiers':
                self.pick_manager.reset_all_tiers()
            else:
                self.pick_manager.reset_tier(data.Tier(tier))
            logger.info('%s reset matches in %s.', interaction.user.name, tier)
            await interaction.response.edit_message(content=f'You reset matches in {tier}.', view=None)
        else:
            self.approved = True
            await interaction.response.send_message(f'All matches in {self.pick_ui.select_menu.values[0]} will be '
                                                    f'reset! Press the button again to confirm.', ephemeral=True)


class ResetPicksCancelButton(discord.ui.Button):
    def __init__(self, pick_ui: ResetPicksUI):
        super(ResetPicksCancelButton, self).__init__()
        self.pick_ui = pick_ui
        self.label = 'Cancel'

    async def callback(self, interaction):
        await interaction.response.edit_message(content=f'Reset cancelled.', view=None)


class ResetPicksUI(discord.ui.View):
    def __init__(self, pick_manager: classes.PickManager):
        super(ResetPicksUI, self).__init__()
        self.select_menu = ResetPicksSelectMenu()
        self.send_button = ResetPicksSendButton(self, pick_manager)
        self.cancel_button = ResetPicksCancelButton(self)
        self.add_item(self.select_menu)
        self.add_item(self.send_button)
        self.add_item(self.cancel_button)


class PickUI:
    def __init__(self, match: classes.Match3PLeague, pick_manager: classes.PickManager, is_backup: bool,
                 world_map_picks_lists: list[list[data.WorldMap]],
                 world_map_vetoes_lists: list[list[data.WorldMap]],
                 country_map_picks_lists: list[list[data.CountryMap]],
                 country_map_vetoes_lists: list[list[data.CountryMap]],
                 has_redeem_mode_menu: bool,
                 has_redeem_nmpz_button: bool,
                 has_redeem_moving_button: bool,
                 redeemable_modes_list: list[data.Gamemode] = None):
        self.pick_manager = pick_manager
        self.match = match
        self.is_backup = is_backup
        self.world_map_pick_menus: list[MapSelectMenu] = []
        self.world_map_veto_menus: list[MapSelectMenu] = []
        self.country_map_pick_menus: list[MapSelectMenu] = []
        self.country_map_veto_menus: list[MapSelectMenu] = []
        self.has_redeem_mode_menu = has_redeem_mode_menu
        self.has_redeem_nmpz_button = has_redeem_nmpz_button
        self.has_redeem_moving_button = has_redeem_moving_button
        self.items = []
        for lst in world_map_picks_lists:
            self.world_map_pick_menus.append(PickSelectMenu(lst))
        for lst in world_map_vetoes_lists:
            self.world_map_veto_menus.append(VetoSelectMenu(lst))
        for lst in country_map_picks_lists:
            self.country_map_pick_menus.append(PickSelectMenu(lst))
        for lst in country_map_vetoes_lists:
            self.country_map_veto_menus.append(VetoSelectMenu(lst))
        for item in self.world_map_pick_menus:
            self.items.append(item)
        if has_redeem_mode_menu:
            self.redeem_mode_menu = RedeemModeMenu(redeemable_modes_list)
            self.items.append(self.redeem_mode_menu)
        for item in itertools.chain(self.world_map_veto_menus, self.country_map_pick_menus,
                                    self.country_map_veto_menus):
            self.items.append(item)
        self.send_button = SendButton(self)
        if has_redeem_nmpz_button:
            self.redeem_nmpz_button = RedeemNMPZButton(self)
            self.items.append(self.redeem_nmpz_button)
        if has_redeem_moving_button:
            self.redeem_moving_button = RedeemMovingButton(self)
            self.items.append(self.redeem_moving_button)
        self.items.append(self.send_button)
        self.approved = False
        self.views = self.get_views_list()

    def get_views_list(self) -> list[discord.ui.View]:
        views = [discord.ui.View()]
        i = 0
        for idx, elem in enumerate(self.items):
            if i >= 5:
                i = 0
                views.append(discord.ui.View())
            views[-1].add_item(elem)
            i += 1
        return views

    async def send_ui(self, interaction: discord.Interaction, message: str):
        await interaction.followup.send(message, view=self.views[0], ephemeral=True)
        for menu in self.views[1:]:
            await interaction.followup.send(view=menu, ephemeral=True)

    def __str__(self) -> str:
        s = f'Match: {self.match}\nBackup: {self.is_backup}\nWorld_map_pick_menus: {len(self.world_map_pick_menus)}\n' \
            f'World_map_veto_menus: {len(self.world_map_veto_menus)}\nCountry_map_pick_menus: ' \
            f'{len(self.country_map_pick_menus)}\nCountry_map_veto_menus: {len(self.country_map_veto_menus)}\n' \
            f'Has_redeem_mode_menu: {self.has_redeem_mode_menu}\nHas_redeem_nmpz_button: ' \
            f'{self.has_redeem_nmpz_button}\nHas_redeem_moving_button: {self.has_redeem_moving_button}'
        return s

    def check_map_repetitions(self) -> bool:
        world_maps = [functions.get_map_from_menu(menu) for menu in self.world_map_pick_menus]
        country_maps = [functions.get_map_from_menu(menu) for menu in self.country_map_pick_menus]
        if functions.has_repeats(world_maps) or functions.has_repeats(country_maps):
            return False
        return True

    async def check_pick(self, interaction: discord.Interaction) -> bool:
        for menu in itertools.chain(self.world_map_pick_menus, self.world_map_veto_menus, self.country_map_pick_menus,
                                    self.country_map_veto_menus):
            if len(menu.values) == 0:
                await interaction.response.send_message('Please complete all the picks.', ephemeral=True)
                return False
            if not self.check_map_repetitions():
                await interaction.response.send_message('You can\'t choose the same map!', ephemeral=True)
                return False
        if self.has_redeem_mode_menu and len(self.redeem_mode_menu.values) == 0:
            await interaction.response.send_message('Please pick the gamemode.', ephemeral=True)
            return False
        if not self.approved:
            self.approved = True
            await interaction.response.send_message('Be careful, you won\'t be able to change your picks later! '
                                                    'Press the button again to confirm.', ephemeral=True)
            return False
        return True

    async def send(self, interaction: discord.Interaction):
        if not await self.check_pick(interaction):
            return
        redeemed_mode = self.get_redeemed_mode(functions.extract_name(self.redeem_mode_menu.values[0])) if \
            self.has_redeem_mode_menu else None
        pick = classes.ArbitraryPick(
            [functions.get_map_from_menu(menu) for menu in self.world_map_pick_menus],
            [functions.get_map_from_menu(menu) for menu in self.world_map_veto_menus],
            [functions.get_map_from_menu(menu) for menu in self.country_map_pick_menus],
            [functions.get_map_from_menu(menu) for menu in self.country_map_veto_menus],
            redeemed_mode, None)
        if not self.is_backup:
            await self.pick_manager.send_picks(interaction, self.match, pick)
            # TODO: locking consecutive responses when command run twice at a time and there's a backup
        else:
            await self.pick_manager.send_backup_pick(interaction, self.match, pick)
        await self.respond(interaction, redeemed_mode if redeemed_mode is not None else data.DEFAULT_GAMEMODE)

    async def respond(self, interaction: discord.Interaction, mode: data.Gamemode):
        message = self.assemble_send_message(mode)
        await interaction.response.edit_message(content=message, view=None)
        checked = self.pick_manager.get_match(interaction.user.id)
        if checked is None:
            await interaction.followup.send('Thank you for submitting all picks for this week!', ephemeral=True)
        else:
            await interaction.followup.send('You have other matches this week, please run */pick* again.',
                                            ephemeral=True)

    def get_redeemed_mode(self, redeemed_mode_repr: str) -> data.Gamemode | None:
        redeemed_mode = None
        if self.has_redeem_mode_menu:
            if redeemed_mode_repr == 'MOVING':
                redeemed_mode = data.Gamemode.MOVING
            elif redeemed_mode_repr == 'NM':
                redeemed_mode = data.Gamemode.NM
            elif redeemed_mode_repr == 'NMPZ':
                redeemed_mode = data.Gamemode.NMPZ
        elif self.has_redeem_nmpz_button and self.redeem_nmpz_button.active:
            redeemed_mode = data.Gamemode.NMPZ
        elif self.has_redeem_moving_button and self.redeem_moving_button.active:
            redeemed_mode = data.Gamemode.MOVING
        return redeemed_mode

    def assemble_send_message(self, mode: data.Gamemode):
        message = 'You picked:**'
        for menu in self.world_map_pick_menus:
            message += f"\n{functions.extract_name(menu.values[0])} {mode.name}"
        for menu in self.country_map_pick_menus:
            message += f"\n{functions.extract_name(menu.values[0])}"
        if len(self.world_map_veto_menus) + len(self.country_map_veto_menus) > 0:
            message += '**\nand vetoed:**'
            for menu in self.world_map_veto_menus:
                message += f"\n{functions.extract_name(menu.values[0])}"
            for menu in self.country_map_veto_menus:
                message += f"\n{functions.extract_name(menu.values[0])}"
        return message + '**'
