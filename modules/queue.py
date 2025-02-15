from __future__ import annotations

import json
import jsonpickle
from pathlib import Path

import discord

from modules.data import Role


class QueueNotFound(Exception):
    def __init__(self, name: str):
        super(QueueNotFound, self).__init__(name)


class QueueManager:
    def __init__(self):
        self.queues: list[Queue] = []

    def get_queue_reprs_list(self) -> list[str]:
        return [str(queue) for queue in self.queues]

    def open_queues(self):
        with open(Path('data', 'queue.json'), 'r') as file:
            lst = json.load(file)
        self.queues = jsonpickle.decode(lst)

    def save_queues(self):
        lst = jsonpickle.encode(self.queues)
        with open(Path('data', 'queue.json'), 'w+') as file:
            json.dump(lst, file)

    def get_queue_by_name(self, name: str) -> Queue:
        for queue in self.queues:
            if queue.name == name:
                return queue
        raise QueueNotFound(name)

    def add_queue(self, queue: Queue):
        self.queues.append(queue)
        self.save_queues()


class Queue:
    def __init__(self, name: str, roles: tuple[Role] = None):
        self.name = name
        self.pos = 0
        self.ids = []
        self.roles = (Role.TWITCH_SUB, Role.CINNAMON, Role.BOOSTER) if roles is None else roles

    def __str__(self) -> str:
        return self.name

    def check_roles(self, user: discord.Member):
        return any(role.name in self.roles for role in user.roles)

    def join(self, user_id: int) -> None:
        self.ids.append(user_id)

    def can_join(self, user_id: int) -> bool:
        """
        Checks whether the user with this ID is not waiting in the queue or has been pushed out of it.
        """
        return user_id not in self.ids

    def in_queue(self, user_id: int) -> bool:
        """
        Checks whether the user with this ID is still waiting in the queue.
        """
        return user_id in self.ids[self.pos::]

    def leave(self, user_id: int) -> None:
        for i, uid in enumerate(self.ids[self.pos::], self.pos):
            if uid == user_id:
                self.ids.pop(i)
                return

    def is_empty(self) -> bool:
        return self.pos >= len(self.ids)

    def info(self) -> list[str]:
        if self.pos < len(self.ids):
            msg = []
            for i in range(self.pos, len(self.ids)):
                msg += [f'{i - self.pos + 1}. <@{self.ids[i]}>']
            return msg
        else:
            raise ValueError('Queue is empty.')

    def can_push(self) -> bool:
        return self.pos < len(self.ids)

    def push(self) -> int:
        self.pos += 1
        return self.ids[self.pos - 1]

    def can_undo_push(self) -> bool:
        return self.pos > 0

    def undo_push(self) -> None:
        self.pos -= 1
