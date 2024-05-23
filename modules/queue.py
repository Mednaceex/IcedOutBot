from __future__ import annotations

import json
from pathlib import Path

with open(Path('data', 'queue.json'), 'r') as data:
    queue = json.load(data)

ids = queue["ids"]
pos = queue["position"]


def join(user_id: int) -> bool:
    if user_id not in ids[pos:]:
        ids.append(user_id)
        return True
    return False


def leave(user_id: int) -> bool:
    if user_id not in ids[pos::]:
        return False
    for i, uid in enumerate(ids[pos::]):
        if uid == user_id:
            ids.pop(i)
            return True


def is_empty() -> bool:
    return pos >= len(ids)


def info() -> list[str]:
    if pos < len(ids):
        msg = []
        for i in range(pos, len(ids)):
            msg += [f'{i-pos+1}. <@{ids[i]}>']
        return msg
    else:
        raise ValueError('Queue is empty.')


def push() -> int | None:
    global pos
    if pos >= len(ids):
        return None
    pos += 1
    return ids[pos-1]


def undo_push() -> bool:
    global pos
    if pos > 0:
        pos -= 1
        return True
    return False


def save():
    dct = {"position": pos, "ids": ids}
    with open(Path('data', 'queue.json'), 'w') as file:
        json.dump(dct, file)
