import discord

from modules.card_game import CardGameManager
from modules.classes import PickManager, MessageRegistrator, ConfigManager
from modules.data import MAX_THRESHOLD, THRESHOLD
from modules.queue import QueueManager

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)
manager = PickManager(client)
registrator = MessageRegistrator(MAX_THRESHOLD)
card_game_manager = CardGameManager(message_threshold=THRESHOLD)
config_manager = ConfigManager()
queue_manager = QueueManager()
