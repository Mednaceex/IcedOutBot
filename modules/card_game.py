from __future__ import annotations
import asyncio
import random
import discord
import json
import hashlib
from typing import Dict
from enum import IntEnum
from pathlib import Path, PureWindowsPath
from datetime import datetime, timedelta
import modules.functions as funcs
from modules.data import TIMEOUT, BUTTON_LIFETIME, Emoji, ANSWER_TIMEOUT
from modules.logger import logger


class ElementNotFoundError(Exception):
    def __init__(self, msg: str):
        super(ElementNotFoundError, self).__init__(msg)


class WrongRarityError(Exception):
    def __init__(self):
        super(WrongRarityError, self).__init__('Wrong rarity!')


class UserHasNoCardsError(Exception):
    def __init__(self):
        super(UserHasNoCardsError, self).__init__('This user has no cards!')


class Rarity(IntEnum):
    # ULTRACOMMON = 5
    COMMON = 15
    RARE = 25
    EPIC = 35


def get_rarity(rarity: str | int) -> Rarity:
    if type(rarity) == int:
        r = Rarity(rarity)
    # elif rarity == 'ULTRACOMMON':
    # r = Rarity.ULTRACOMMON
    elif rarity == 'COMMON':
        r = Rarity.COMMON
    elif rarity == 'RARE':
        r = Rarity.RARE
    elif rarity == 'EPIC':
        r = Rarity.EPIC
    else:
        raise WrongRarityError
    return r


class Collection:
    def __init__(self, name: str, emoji: str, chance: float, collection_id: int = None):
        self.name = name
        self.emoji = emoji
        self.chance = chance
        self.id = self.get_id() if collection_id is None else collection_id

    def __eq__(self, other: Collection):
        return isinstance(other, Collection) and self.name == other.name \
               and self.emoji == other.emoji and self.chance == other.chance and self.id == other.id

    def __lt__(self, other: Collection):
        if not isinstance(other, Collection):
            raise TypeError('Given object is not of type Collection!')
        return self.id < other.id

    def __le__(self, other: Collection):
        if not isinstance(other, Collection):
            raise TypeError('Given object is not of type Collection!')
        return self.id <= other.id

    def __gt__(self, other: Collection):
        if not isinstance(other, Collection):
            raise TypeError('Given object is not of type Collection!')
        return self.id > other.id

    def __ge__(self, other: Collection):
        if not isinstance(other, Collection):
            raise TypeError('Given object is not of type Collection!')
        return self.id >= other.id

    @staticmethod
    def get_id() -> int:
        with open(Path('data', 'config.json'), 'r') as file:
            dct = json.load(file)
        _id = dct['current_collection_id']
        dct['current_collection_id'] += 1
        with open(Path('data', 'config.json'), 'w+') as file:
            json.dump(dct, file)
        return _id


class QuestionType(IntEnum):
    SINGLECHOICE = 1
    MULTIPLECHOICE = 2


class Question:
    def __init__(self, _type: QuestionType):
        self.type = _type
        self.text = None
        self.answer = None
        self.answer_repr = None
        self.correct_answer = ''
        self.incorrect_answers = []

    def check_answer(self, given: str) -> bool:
        pass


class SCQuestion(Question):
    def __init__(self, text: str, answer: str):
        super(SCQuestion, self).__init__(QuestionType.SINGLECHOICE)
        self.text = text
        self.answer_repr = answer
        self.correct_answers = answer.split(';')

    def check_answer(self, given: str) -> bool:
        return given.lower() in [i.lower() for i in self.correct_answers]


class MCQuestion(Question):
    def __init__(self, text: str, answer: str):
        super(MCQuestion, self).__init__(QuestionType.MULTIPLECHOICE)
        self.answer_repr = answer
        answers = answer.split(';')
        for i in answers:
            while i[0] == ' ':
                i = i[1:]
        self.text = text
        self.correct_answer = answers[0]
        self.incorrect_answers = answers[1:]
        self.answer = self.correct_answer
        for i in self.incorrect_answers:
            self.answer += f';{i}'

    def check_answer(self, given: str) -> bool:
        return self.correct_answer.lower() == given.lower()


class Card:
    def __init__(self, name: str, rarity: Rarity, collection: Collection, image_path: Path, question: Question,
                 card_id: int | None, chance: float | None):
        self.name = name
        self.rarity = rarity
        self.collection = collection
        self.image_path = image_path
        self.question = question
        self.chance = 1. if chance is None else chance
        if rarity == Rarity.COMMON:
            val = "COMMON"
        elif rarity == Rarity.RARE:
            val = "RARE"
        elif rarity == Rarity.EPIC:
            val = "EPIC"
        # elif rarity == Rarity.ULTRACOMMON:
        # val = "ULTRACOMMON"
        else:
            val = rarity.value
        self.id = hashlib.sha3_256(f'{name}-{val}-{collection.id}'.encode('utf-8')).hexdigest() if card_id is None \
            else card_id

    def __eq__(self, other: Card):
        return isinstance(other, Card) and other.id == self.id

    def __str__(self):
        return f'{self.name} ({self.collection.name} Collection, {self.rarity.name.capitalize()})'


class CollectedCard:
    def __init__(self, card: Card, date: datetime, grade: str | float):
        self.card = card
        self.id = card.id
        self.date = date
        self.grade = grade

    def __eq__(self, other: CollectedCard):
        return isinstance(other, CollectedCard) and other.card == self.card \
               and other.grade == self.grade and other.date == self.date


class CardGameManager:
    def __init__(self, message_threshold: int):
        self.channels = None
        self.channel_weights = None
        self.collections_list = self.open_collections_list()
        self.cards_list = self.open_cards()
        self.message_threshold = message_threshold
        self.collections = self.open_collections()
        self.timeout = datetime.now()
        self.cooldowns: list[Cooldown] = []

    @staticmethod
    def open_collections_list() -> list[Collection]:
        lst = []
        with open(Path('data', 'collections_list.json'), 'r') as file:
            collections = json.load(file)
        for collection in collections:
            lst.append(Collection(collection['name'], collection['emoji'], collection['chance'], collection['id']))
        return lst

    def save_collections_list(self):
        lst = []
        for collection in self.collections_list:
            lst.append({'name': collection.name, 'emoji': collection.emoji, 'chance': collection.chance,
                        'id': collection.id})
        with open(Path('data', 'collections_list.json'), 'w+') as file:
            json.dump(lst, file)

    def get_collection(self, name: str) -> Collection:
        for collection in self.collections_list:
            if collection.name.lower() == name.lower():
                return collection
        raise ElementNotFoundError('Collection not found')

    def open_cards(self) -> list[Card]:
        with open(Path('data', 'cards.json'), 'r') as file:
            cards = json.load(file)
        lst = []
        for card in cards:
            if QuestionType(card['question_type']) == QuestionType.SINGLECHOICE:
                q = SCQuestion(card['question'], card['answer'])
            elif QuestionType(card['question_type']) == QuestionType.MULTIPLECHOICE:
                q = MCQuestion(card['question'], card['answer'])
            else:
                raise ElementNotFoundError('Question type not found')
            try:
                card_id = card['id']
            except KeyError:
                card_id = None
            try:
                chance = card['chance']
            except KeyError:
                chance = 1.
            lst.append(Card(card['name'], get_rarity(card['rarity']), self.get_collection(card['collection']),
                            Path(PureWindowsPath(card['path'])), q, chance=chance, card_id=card_id))
        return lst

    def check_collection_exists(self, name: str) -> bool:
        return name in [n.name for n in self.collections_list]

    def check_card_exists(self, card_id: int) -> bool:
        return card_id in [n.id for n in self.cards_list]

    def configure_prob_list(self) -> list[float]:
        lst = []
        for card in self.cards_list:
            prob = 60. if card.rarity == Rarity.COMMON else \
                30. if card.rarity == Rarity.RARE else \
                10. if card.rarity == Rarity.EPIC else 0
            # 100. if card.rarity == Rarity.ULTRACOMMON else \
            lst.append(prob*card.chance*card.collection.chance)
        return lst

    async def send_card(self, card: Card, question: Question):
        if self.timeout_check():
            view = CollectButtonView(question, self, card)
            channel = random.choices(population=self.channels, weights=self.channel_weights, k=1)[0]
            cnt = 'A new card appeared!'
            view.set_message(await channel.send(file=discord.File(card.image_path), content=cnt, view=view))
            self.timeout = datetime.now() + timedelta(seconds=TIMEOUT)
            await self.start_timer(view)

    def timeout_check(self):
        return self.timeout <= datetime.now()

    @staticmethod
    async def start_timer(view: CollectButtonView):
        async def disable_button():
            await asyncio.sleep(BUTTON_LIFETIME)
            await view.button.deactivate()
            view.timedout = True

        await asyncio.create_task(disable_button())

    async def play(self):
        try:
            card = self.choose_card()
            await self.send_card(card, card.question)
        except ValueError as e:
            logger.error(e)

    def choose_card(self) -> Card:
        prob_list = self.configure_prob_list()
        for prob in prob_list:
            if prob < 0:
                raise ValueError('Probability less than zero!')
            if prob > 1e-7:
                return random.choices(population=self.cards_list, weights=prob_list, k=1)[0]
        raise ValueError('All probabilities are too small!')

    def set_channels(self, channels: list[discord.TextChannel], weights: list[float]):
        self.channels = channels
        self.channel_weights = weights

    def add_collected_card(self, card: Card, owner_id: int):
        if owner_id not in self.collections.keys():
            self.collections[owner_id] = []
        self.collections[owner_id].append(CollectedCard(card, datetime.now(), 'UNGRADED'))
        self.save_collections()

    def open_collections(self) -> Dict[int, list[CollectedCard]]:
        with open(Path('data', 'collections.json'), 'r') as file:
            d = json.load(file)
        dct = {}
        for key, value in d.items():
            dct[int(key)] = []
            for item in value:
                dct[int(key)].append(CollectedCard(self.get_card_by_id(str(item['id'])),
                                                   datetime.fromisoformat(item['date']), item['grade']))
        return dct

    def save_collections(self):
        dct = {}
        for key, value in self.collections.items():
            dct[key] = []
            for item in value:
                dct[key].append({'id': item.id, 'date': item.date.isoformat(), 'grade': item.grade})
        with open(Path('data', 'collections.json'), 'w+') as file:
            json.dump(dct, file)

    async def display_collections(self, client: discord.Client) -> str:
        s = f'List of all of the collected cards:\n\n'
        lst = sorted(self.collections, key=lambda x: len(self.collections.get(x)), reverse=True)
        for user_id in lst:
            card_list = self.collections[user_id]
            user = await funcs.get_user_by_id(client, user_id)
            s += f'**<@{user.id}>\'s collection:**\n'
            for collected_card in card_list:
                card = collected_card.card
                s += f'{card.name} ({card.rarity.name.capitalize()})\n'
            s += '\n'
        return s

    def display_collection(self, user: discord.User, sorting: str = None) -> list[str]:
        if user.id in self.collections:
            count = 0
            s = []

            def key(_collected_card: CollectedCard):
                if sorting == 'Grade':
                    return _collected_card.grade if type(_collected_card.grade) != str else 0
                elif sorting == 'Rarity':
                    return _collected_card.card.rarity
                elif sorting == 'Collection':
                    return _collected_card.card.collection
                else:
                    return _collected_card.date

            lst = sorted(self.collections[user.id], key=key, reverse=(sorting != 'Oldest first'))
            for collected_card in lst:
                card = collected_card.card
                grade = f'{collected_card.grade.capitalize()})' if collected_card.grade == 'UNGRADED' \
                    else f'{get_grade_emoji(collected_card.grade)} Grade: {"{:.1f}".format(collected_card.grade)})'
                s += [f'***{card.name}*** | {get_collection_emoji(card.collection)} {card.collection.name}'
                      f' Collection | {get_rarity_emoji(card.rarity)} {card.rarity.name.capitalize()} | {grade}']
                count += 1
            if count > 0:
                return s
        return [f'<@{user.id}>\'s collection is empty! :(']

    def get_card_reprs_list(self, user: discord.User, only_ungraded: bool = True) -> list[[str, int]]:
        lst = []
        if user.id in self.collections:
            for idx, collected_card in enumerate(self.collections[user.id]):
                if not only_ungraded or collected_card.grade == 'UNGRADED':
                    card = collected_card.card
                    name = [f'{card.name} ({card.collection.name} Collection, '
                            f'{card.rarity.name.capitalize()})', idx]
                    if not only_ungraded:
                        name[0] += ', Grade: ' if collected_card.grade != 'UNGRADED' else ', '
                        name[0] += f'{collected_card.grade}'
                    lst.append(name)
        return lst

    def get_collections_reprs_list(self) -> list[(str, int)]:
        lst = []
        for idx, collection in enumerate(self.collections_list):
            lst.append((collection.name, idx))
        return lst

    def get_card_by_id(self, card_id: str) -> Card:
        for card in self.cards_list:
            if card.id == card_id:
                return card
        raise ElementNotFoundError('No card with this ID is found.')

    def save_cards(self):
        lst = [{'name': card.name, 'rarity': card.rarity, 'path': str(PureWindowsPath(card.image_path)),
                'collection': card.collection.name, 'question_type': card.question.type.value,
                'question': card.question.text, 'answer': card.question.answer_repr,
                'chance': card.chance, 'id': card.id} for card in self.cards_list]
        with open(Path('data', 'cards.json'), 'w+') as file:
            json.dump(lst, file)

    def upload_card(self, card: Card):
        self.cards_list.append(card)
        self.save_cards()

    def edit_card(self, old_card: Card, new_name: str, new_rarity: int, new_question: Question, new_path: Path):
        for idx, c in enumerate(self.cards_list):
            if old_card == c:
                self.cards_list[idx].name = new_name
                self.cards_list[idx].rarity = new_rarity
                self.cards_list[idx].question = new_question
                self.cards_list[idx].image_path = new_path
                self.save_cards()
                return
        raise ElementNotFoundError('Old card not found!')

    def set_card_chance(self, card: Card, chance: float):
        for idx, c in enumerate(self.cards_list):
            if card == c:
                self.cards_list[idx].chance = chance
                self.save_cards()
                return
        raise ElementNotFoundError('Card not found!')

    def set_all_cards_chance(self, chance: float):
        for idx, c in enumerate(self.cards_list):
            self.cards_list[idx].chance = chance
        self.save_cards()

    def add_collection(self, collection: Collection):
        self.collections_list.append(collection)
        self.save_collections_list()

    def edit_collection(self, old_collection: Collection, new_name: str, new_emoji: str, new_chance: float):
        for idx, c in enumerate(self.collections_list):
            if old_collection == c:
                self.collections_list[idx].name = new_name
                self.collections_list[idx].emoji = new_emoji
                self.collections_list[idx].chance = new_chance
                self.save_collections_list()
                self.save_cards()
                return
        raise ElementNotFoundError('Old collection not found!')

    def delete_collection(self, collection: Collection):
        for idx, c in enumerate(self.collections_list):
            if collection == c:
                self.collections_list.pop(idx)
                self.cards_list = [card for card in self.cards_list if card.collection != collection]
                self.save_collections_list()
                self.save_cards()
                return
        raise ElementNotFoundError('Collection not found!')

    def save_grade(self, user_id: int, card: CollectedCard, grade: str | float):
        if user_id not in self.collections:
            raise UserHasNoCardsError()
        if card not in self.collections[user_id]:
            raise ElementNotFoundError('Card not found!')
        for _card in self.collections[user_id]:
            if card == _card:
                _card.grade = grade
                self.save_collections()

    def get_overall_progress(self, user_id: int) -> list[str]:
        collected_list = []
        missing_list = self.cards_list.copy()
        for card in self.collections[user_id]:
            if card.card in missing_list:
                missing_list.remove(card.card)
                collected_list.append(card.card)
        total_progress = self.get_total_progress(collected_list)
        collection_progress_list = self.get_collection_progress(collected_list, missing_list)
        return [f'**Overall:**', total_progress, '', '**Collections:**'] + collection_progress_list

    def get_total_progress(self, collected_list: list[Card]) -> str:
        collected = len(collected_list)
        total = len(self.cards_list)
        percentage = collected * 100 / total if total != 0 else 0
        return f'{format(percentage, ".1f")}% ({collected}/{total})'

    def get_collection_progress(self, collected_list: list[Card], missing_list: list[Card]) -> list[str]:
        output = []
        for collection in self.collections_list:
            collected = 0
            missing = 0
            for card in collected_list:
                if card.collection == collection:
                    collected += 1
            for card in missing_list:
                if card.collection == collection:
                    missing += 1
            percentage = collected * 100 / (missing + collected) if missing + collected != 0 else 0
            s = f' {Emoji.CHECKMARK}' if 0 == missing else ''
            output.append(f'{collection.emoji}{collection.name}: {format(percentage, ".1f")}% '
                          f'({collected}/{missing + collected}){s}')
        return output

    def get_progress(self, user_id: int, collection: Collection) -> list[str]:
        collected_list = []
        missing_list = list(filter(lambda x: x.collection == collection, self.cards_list))
        total = len(missing_list)
        try:
            for card in self.collections[user_id]:
                if card.card in missing_list:
                    missing_list.remove(card.card)
                    collected_list.append(card.card)
        except KeyError:
            pass
        missing_list.sort(key=lambda x: x.rarity.value, reverse=True)
        collected_list.sort(key=lambda x: x.rarity.value, reverse=True)
        percentage = len(collected_list) * 100 / total if total != 0 else 0
        s = f' {Emoji.CHECKMARK}' if total == len(collected_list) else ''
        output = [f'**{collection.emoji}{collection.name} collection progress:**',
                  f'{format(percentage, ".1f")}% ({len(collected_list)}/{total}){s}']
        for lst, title in ((collected_list, '**Collected cards:**'), (missing_list, '**Missing cards:**')):
            output += ['', title]
            length = len(lst)
            if length == 0:
                output[-1] += ' None'
            else:
                idx, ref = 0, 0
                for rarity in sorted(Rarity, key=lambda x: x.value, reverse=True):
                    output.append(f'{get_rarity_emoji(rarity)} **{rarity.name}**:')
                    while idx < length and lst[idx].rarity == rarity:
                        output.append(f'*{lst[idx].name}*')
                        idx += 1
                    if idx == ref:
                        output[-1] += ' None'
                    ref = idx
        return output

    def add_cooldown(self, user_id: int, collect_button: CollectButton, time: datetime, length: int = ANSWER_TIMEOUT):
        # length in seconds
        self.cooldowns.append(Cooldown(user_id, collect_button, time, length))

    def get_remaining_cooldown(self, user_id: int, collect_button: CollectButton):
        for cooldown in reversed(self.cooldowns):
            if cooldown.id == user_id and cooldown.collect_button == collect_button:
                return cooldown.length - (datetime.now() - cooldown.start).total_seconds()
        return 0


class Cooldown:
    def __init__(self, user_id: int, collect_button: CollectButton, start: datetime, length: int):
        self.id = user_id
        self.collect_button = collect_button
        self.start = start
        self.length = length


class CollectButtonView(discord.ui.View):
    def __init__(self, question: Question, manager: CardGameManager, card: Card):
        super(CollectButtonView, self).__init__(timeout=None)
        self.message = None
        self.question = question
        self.manager = manager
        self.card = card
        self.button = CollectMCQButton(self) if question.type == QuestionType.MULTIPLECHOICE else CollectSCQButton(self)
        self.add_item(self.button)
        self.timedout = False

    def set_message(self, message: discord.Message):
        self.message = message


class CollectButton(discord.ui.Button):
    def __init__(self, view: CollectButtonView):
        super(CollectButton, self).__init__(label='Collect!')
        self._view = view
        self.qv = None

    async def callback(self, interaction: discord.Interaction):
        pass

    async def deactivate(self):
        self.disabled = True
        message = self._view.message
        await message.edit(view=self._view)

    async def timed_out(self):
        return self._view.timedout


class CollectSCQButton(CollectButton):
    def __init__(self, view: CollectButtonView):
        super(CollectSCQButton, self).__init__(view)

    async def callback(self, interaction: discord.Interaction):
        try:
            assert self._view.question.type == QuestionType.SINGLECHOICE
            self.qv = QuestionButtonView(self._view, interaction)
            await interaction.response.send_message(content=f'**{self._view.question.text}**',
                                                    view=self.qv, ephemeral=True)
        except Exception as e:
            logger.error(e)


class QuestionButtonView(discord.ui.View):
    def __init__(self, view: CollectButtonView, interaction: discord.Interaction):
        super(QuestionButtonView, self).__init__(timeout=None)
        self._view = view
        self.collect_button = view.button
        self.button = AnswerSCQButton(self)
        self.question = self._view.question
        self.manager = self._view.manager
        self.card = self._view.card
        self.add_item(self.button)
        self.interaction = interaction

    def get_message(self):
        return self._view.message

    async def deactivate_answer_button(self):
        self.button.disabled = True
        await self.interaction.delete_original_response()


class AnswerSCQButton(discord.ui.Button):
    def __init__(self, view: QuestionButtonView):
        super(AnswerSCQButton, self).__init__(label='Answer')
        self._view = view

    async def callback(self, interaction: discord.Interaction):
        try:
            assert self._view.question.type == QuestionType.SINGLECHOICE
            questionnaire = Questionnaire(self._view.question, self._view.manager, self._view.card,
                                          self._view.collect_button, self._view)
            await interaction.response.send_modal(questionnaire)
        except Exception as e:
            logger.error(e)

    async def deactivate(self):
        self.disabled = True
        message = self._view.get_message()
        await message.edit(view=self._view)


class CollectMCQButton(CollectButton):
    def __init__(self, view: CollectButtonView):
        super(CollectMCQButton, self).__init__(view)

    async def callback(self, interaction: discord.Interaction):
        try:
            assert self._view.question.type == QuestionType.MULTIPLECHOICE
            cooldown = self._view.manager.get_remaining_cooldown(interaction.user.id, self._view.button)
            if cooldown <= 0:
                questionnaire_view = QuestionnaireView(self._view.question, self._view.manager, self._view.card,
                                                       self._view.button, interaction)
                await interaction.response.send_message(questionnaire_view.title,
                                                        view=questionnaire_view, ephemeral=True)
            else:
                await interaction.response.send_message(f'You have to wait for '
                                                        f'{funcs.seconds_to_string(int(cooldown + 1))}!',
                                                        ephemeral=True)
        except Exception as e:
            logger.error(e)

    async def deactivate(self):
        self.disabled = True
        message = self._view.message
        await message.edit(view=self._view)


class Questionnaire(discord.ui.Modal):
    def __init__(self, question: Question, manager: CardGameManager, card: Card, button: CollectSCQButton,
                 qv: QuestionButtonView):
        super(Questionnaire, self).__init__(title='Answer to collect the card!')
        self.question = question
        self.answer = discord.ui.TextInput(label=f'Enter your answer here:', style=discord.TextStyle.short)
        self.add_item(self.answer)
        self.manager = manager
        self.card = card
        self.button = button
        self.qv = qv

    async def on_submit(self, interaction: discord.Interaction):
        await funcs.defer(interaction, 'filled card game form')
        if self.button.disabled:
            await interaction.followup.send(f'Sorry <@{interaction.user.id}>, the card has already been collected.',
                                                ephemeral=False)
            await self.qv.deactivate_answer_button()
        else:
            if self.question.check_answer(str(self.answer)):
                await self.button.deactivate()
                await self.qv.deactivate_answer_button()
                await interaction.followup.send(
                    f'<@{interaction.user.id}> collected ***{self.card.name}***!', ephemeral=False)
                self.manager.add_collected_card(self.card, interaction.user.id)
            else:
                await interaction.followup.send(f'<@{interaction.user.id}> Wrong answer, try again!', ephemeral=False)
        self.stop()


class QuestionnaireSendButton(discord.ui.Button):
    def __init__(self, qview: QuestionnaireView):
        super(QuestionnaireSendButton, self).__init__()
        self.label = 'Send answer'
        self.qview = qview

    async def callback(self, interaction: discord.Interaction):
        answer = ''
        if self.qview.question.type == QuestionType.SINGLECHOICE:
            answer = str(self.qview.answer)
        elif self.qview.question.type == QuestionType.MULTIPLECHOICE:
            if len(self.qview.answer.values) == 0:
                await interaction.response.send_message('Please choose the answer!', ephemeral=True)
                return
            answer = str(self.qview.answer.values[0])
        if not self.qview.question.type == QuestionType.MULTIPLECHOICE:
            raise AttributeError('Not multiple choice!')
        await funcs.defer(interaction, 'choose card game answer')
        if self.qview.button.timed_out():
            await interaction.followup.send(f'Sorry <@{interaction.user.id}>, the card has despawned.',
                                            ephemeral=False)
        elif self.qview.button.disabled:
            await interaction.followup.send(f'Sorry <@{interaction.user.id}>, the card has already been collected.',
                                            ephemeral=False)
        else:
            cooldown = self._view.manager.get_remaining_cooldown(interaction.user.id, self.qview.button)
            if cooldown > 0:
                await interaction.followup.send(f'You have to wait for {funcs.seconds_to_string(int(cooldown + 1))}!',
                                                ephemeral=True)
            else:
                await self.collect(interaction, answer)

        self.qview.deactivate()
        await self.qview.collect_button_interaction.delete_original_response()

    async def collect(self, interaction: discord.Interaction, answer: str):
        self.qview.manager.add_cooldown(interaction.user.id, self.qview.button, datetime.now())
        if self.qview.question.check_answer(answer):
            await self.qview.button.deactivate()
            await interaction.followup.send(
                f'<@{interaction.user.id}> collected ***{self.qview.card.name}***!', ephemeral=False)
            self.qview.manager.add_collected_card(self.qview.card, interaction.user.id)
        else:
            await interaction.followup.send(f'<@{interaction.user.id}> Wrong answer, try again in '
                                            f'{funcs.seconds_to_string(ANSWER_TIMEOUT)}!', ephemeral=False)


class AnswerSelectMenu(discord.ui.Select):
    def __init__(self, answer_list: list[str]):
        super(AnswerSelectMenu, self).__init__()
        self.list = []
        for name in answer_list:
            self.list.append(name)
            self.add_option(label=name)

    async def callback(self, interaction: discord.Interaction):
        await funcs.defer(interaction, command_name='AnswerSelectMenu')


class QuestionnaireView(discord.ui.View):
    def __init__(self, question: Question, manager: CardGameManager, card: Card, button: CollectButton,
                 collect_button_interaction: discord.Interaction):
        super(QuestionnaireView, self).__init__()
        self.title = f'Answer to collect the card!**\n{question.text}**'
        self.question = question
        self.manager = manager
        self.card = card
        self.button = button
        if self.question.type == QuestionType.MULTIPLECHOICE:
            lst = self.question.incorrect_answers + [self.question.correct_answer]
            random.shuffle(lst)
            self.answer = AnswerSelectMenu(lst)
        self.send_button = QuestionnaireSendButton(self)
        self.add_item(self.answer)
        self.add_item(self.send_button)
        self.collect_button_interaction = collect_button_interaction

    def deactivate(self) -> None:
        self.send_button.disabled = True
        self.answer.disabled = True
        self.stop()


def card_to_str(collected_card: CollectedCard) -> str:
    card = collected_card.card
    dct = {'id': card.id, 'grade': collected_card.grade, 'date': collected_card.date.isoformat()}
    return json.dumps(dct)


def str_to_card(string: str, manager: CardGameManager) -> CollectedCard:
    dct = json.loads(string)
    card = manager.get_card_by_id(str(dct['id']))
    collected_card = CollectedCard(card, datetime.fromisoformat(dct['date']), dct['grade'])
    return collected_card


def idx_to_card(manager: CardGameManager, user_id: int, idx: int) -> CollectedCard:
    return manager.collections[user_id][idx]


def idx_to_collection(manager: CardGameManager, idx: int) -> Collection:
    return manager.collections_list[idx]


def get_grade_emoji(grade: float) -> Emoji:
    if grade <= 6:
        emoji = Emoji.TRASH
    elif grade < 7:
        emoji = Emoji.RED_CIRCLE
    elif grade < 8:
        emoji = Emoji.ORANGE_CIRCLE
    elif grade < 9:
        emoji = Emoji.YELLOW_CIRCLE
    elif grade < 10:
        emoji = Emoji.GREEN_CIRCLE
    else:
        emoji = Emoji.HUNDRED
    return emoji


def get_collection_emoji(collection: Collection) -> str:
    return collection.emoji


def get_rarity_emoji(rarity: Rarity) -> Emoji:
    if rarity == Rarity.COMMON:
        emoji = Emoji.SNOWY_BABY
    elif rarity == Rarity.RARE:
        emoji = Emoji.SNOWY_RARE
    elif rarity == Rarity.EPIC:
        emoji = Emoji.SNOWY_GODMODE
    # elif rarity == Rarity.ULTRACOMMON:
    # emoji = Emoji.BLUE_DIAMOND
    else:
        raise WrongRarityError
    return emoji
