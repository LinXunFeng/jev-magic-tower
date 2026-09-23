from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import ceil
from typing import Any


class TileKind(str, Enum):
    FLOOR = "floor"
    WALL = "wall"
    YELLOW_DOOR = "yellow_door"
    BLUE_DOOR = "blue_door"
    YELLOW_KEY = "yellow_key"
    BLUE_KEY = "blue_key"
    RED_POTION = "red_potion"
    BLUE_POTION = "blue_potion"
    ATTACK_GEM = "attack_gem"
    DEFENSE_GEM = "defense_gem"
    ENEMY = "enemy"
    STAIRS = "stairs"
    BOSS = "boss"


@dataclass(frozen=True, slots=True)
class Enemy:
    name: str
    hp: int
    attack: int
    defense: int
    gold: int
    icon: str


@dataclass(frozen=True, slots=True)
class Tile:
    kind: TileKind
    label: str
    icon: str
    enemy: Enemy | None = None


@dataclass(slots=True)
class Hero:
    hp: int = 1000
    attack: int = 28
    defense: int = 16
    gold: int = 0
    yellow_keys: int = 1
    blue_keys: int = 0


@dataclass(frozen=True, slots=True)
class Position:
    row: int
    col: int

    def moved(self, dr: int, dc: int) -> Position:
        return Position(self.row + dr, self.col + dc)


@dataclass(frozen=True, slots=True)
class ActionPreview:
    action_id: str
    direction: str
    destination: Position
    tile: Tile
    hp_delta: int = 0
    attack_delta: int = 0
    defense_delta: int = 0
    gold_delta: int = 0
    yellow_key_delta: int = 0
    blue_key_delta: int = 0
    visit_count: int = 0

@dataclass(frozen=True, slots=True)
class GameEvent:
    code: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class GameState:
    hero: Hero
    floor_index: int
    position: Position
    consumed: set[tuple[int, int, int]] = field(default_factory=set)
    visits: dict[tuple[int, int, int], int] = field(default_factory=dict)
    turn: int = 0
    won: bool = False
    lost: bool = False
    recent_events: list[GameEvent] = field(default_factory=list)

    def visit_count(self, floor_index: int, position: Position) -> int:
        return self.visits.get((floor_index, position.row, position.col), 0)

    def record_visit(self) -> None:
        key = (self.floor_index, self.position.row, self.position.col)
        self.visits[key] = self.visits.get(key, 0) + 1

    def add_event(self, code: str, **params: Any) -> None:
        self.recent_events.append(GameEvent(code, params))
        del self.recent_events[:-6]


def combat_damage(hero: Hero, enemy: Enemy) -> int | None:
    """Return damage taken, or None when the enemy cannot be damaged."""
    hero_hit = hero.attack - enemy.defense
    if hero_hit <= 0:
        return None
    enemy_hit = max(0, enemy.attack - hero.defense)
    retaliation_count = max(0, ceil(enemy.hp / hero_hit) - 1)
    return retaliation_count * enemy_hit


def serialize_enemy(enemy: Enemy | None) -> dict[str, Any] | None:
    if enemy is None:
        return None
    return {
        "name": enemy.name,
        "hp": enemy.hp,
        "attack": enemy.attack,
        "defense": enemy.defense,
        "gold": enemy.gold,
        "icon": enemy.icon,
    }
