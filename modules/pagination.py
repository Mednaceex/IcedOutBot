from typing import Callable, Optional

import discord

from modules.data import ITEMS_PER_PAGE, BUTTON_LIFETIME


class Pagination(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, get_page: Callable):
        self.interaction = interaction
        self.get_page = get_page
        self.total_pages: Optional[int] = None
        self.index = 1
        self.message = None
        super().__init__(timeout=BUTTON_LIFETIME)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user == self.interaction.user:
            return True
        else:
            emb = discord.Embed(
                description=f"Only the author of the command can perform this action.",
                color=16711680
            )
            await interaction.response.send_message(embed=emb, ephemeral=True)
            return False

    async def navigate(self):
        emb, self.total_pages = await self.get_page(self.index)
        if self.total_pages == 1:
            self.message = await self.interaction.followup.send(embed=emb)
        elif self.total_pages > 1:
            self.update_buttons()
            self.message = await self.interaction.followup.send(embed=emb, view=self)

    async def edit_page(self, interaction: discord.Interaction):
        emb, self.total_pages = await self.get_page(self.index)
        self.update_buttons()
        await interaction.response.edit_message(embed=emb, view=self)

    def update_buttons(self):
        if self.index > self.total_pages // 2:
            self.children[2].emoji = "⏮️"
        else:
            self.children[2].emoji = "⏭️"
        self.children[0].disabled = self.index == 1
        self.children[1].disabled = self.index == self.total_pages

    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.blurple)
    async def previous(self, interaction: discord.Interaction, button: discord.Button):
        self.index -= 1
        await self.edit_page(interaction)

    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.blurple)
    async def next(self, interaction: discord.Interaction, button: discord.Button):
        self.index += 1
        await self.edit_page(interaction)

    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.blurple)
    async def end(self, interaction: discord.Interaction, button: discord.Button):
        if self.index <= self.total_pages//2:
            self.index = self.total_pages
        else:
            self.index = 1
        await self.edit_page(interaction)

    async def on_timeout(self):
        # remove buttons on timeout
        await self.message.edit(view=None)


def compute_total_pages(total_results: int, results_per_page: int) -> int:
    return ((total_results - 1) // results_per_page) + 1 if total_results > 0 else 1


async def paginate(interaction: discord.Interaction, lst: list, title: str, name: str = None, numbered: bool = False):
    async def get_page(page: int):
        emb = discord.Embed(title=title, description="")
        offset = (page-1) * ITEMS_PER_PAGE
        for idx, elem in enumerate(lst[offset:offset+ITEMS_PER_PAGE]):
            if numbered:
                emb.description += f'{idx + offset + 1}. '
            emb.description += f"{elem}\n"
        emb.set_author(name=name if name is not None else f"")
        n = compute_total_pages(len(lst), ITEMS_PER_PAGE)
        emb.set_footer(text=f"Page {page} from {n}")
        return emb, n

    await Pagination(interaction, get_page).navigate()
