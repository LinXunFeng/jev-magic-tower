from __future__ import annotations

from dataclasses import replace

from .floors import FLOORS, in_bounds, tile_at
from .models import ActionPreview, GameState, Hero, Position, TileKind, combat_damage

DIRECTIONS = {
    "up": (-1, 0),
    "right": (0, 1),
    "down": (1, 0),
    "left": (0, -1),
}


class IllegalMove(ValueError):
    pass


def new_game() -> GameState:
    state = GameState(hero=Hero(), floor_index=0, position=FLOORS[0].start)
    state.record_visit()
    state.add_event("game_started")
    return state


def _preview(state: GameState, direction: str, destination: Position) -> ActionPreview | None:
    tile = tile_at(state.floor_index, destination, state.consumed)
    hero = state.hero
    values = {
        "hp_delta": 0,
        "attack_delta": 0,
        "defense_delta": 0,
        "gold_delta": 0,
        "yellow_key_delta": 0,
        "blue_key_delta": 0,
    }
    if tile.kind is TileKind.WALL:
        return None
    if tile.kind is TileKind.YELLOW_DOOR:
        if hero.yellow_keys <= 0:
            return None
        values["yellow_key_delta"] = -1
    elif tile.kind is TileKind.BLUE_DOOR:
        if hero.blue_keys <= 0:
            return None
        values["blue_key_delta"] = -1
    elif tile.kind is TileKind.YELLOW_KEY:
        values["yellow_key_delta"] = 1
    elif tile.kind is TileKind.BLUE_KEY:
        values["blue_key_delta"] = 1
    elif tile.kind is TileKind.RED_POTION:
        values["hp_delta"] = 180
    elif tile.kind is TileKind.BLUE_POTION:
        values["hp_delta"] = 360
    elif tile.kind is TileKind.ATTACK_GEM:
        values["attack_delta"] = 8
    elif tile.kind is TileKind.DEFENSE_GEM:
        values["defense_delta"] = 6
    elif tile.kind in (TileKind.ENEMY, TileKind.BOSS):
        damage = combat_damage(hero, tile.enemy)  # type: ignore[arg-type]
        if damage is None or damage >= hero.hp:
            return None
        values["hp_delta"] = -damage
        values["gold_delta"] = tile.enemy.gold  # type: ignore[union-attr]
    return ActionPreview(
        action_id=f"move_{direction}",
        direction=direction,
        destination=destination,
        tile=tile,
        visit_count=state.visit_count(state.floor_index, destination),
        **values,
    )


def legal_actions(state: GameState) -> list[ActionPreview]:
    if state.won or state.lost:
        return []
    actions = []
    for direction, (dr, dc) in DIRECTIONS.items():
        destination = state.position.moved(dr, dc)
        if not in_bounds(state.floor_index, destination):
            continue
        preview = _preview(state, direction, destination)
        if preview is not None:
            actions.append(preview)
    return actions


def apply_action(state: GameState, action_id: str) -> ActionPreview:
    preview = next((item for item in legal_actions(state) if item.action_id == action_id), None)
    if preview is None:
        raise IllegalMove(f"Action is not currently legal: {action_id}")

    hero = state.hero
    hero.hp += preview.hp_delta
    hero.attack += preview.attack_delta
    hero.defense += preview.defense_delta
    hero.gold += preview.gold_delta
    hero.yellow_keys += preview.yellow_key_delta
    hero.blue_keys += preview.blue_key_delta

    tile = preview.tile
    consumable = tile.kind not in (TileKind.FLOOR, TileKind.WALL, TileKind.STAIRS)
    if consumable:
        state.consumed.add((state.floor_index, preview.destination.row, preview.destination.col))

    state.position = preview.destination
    state.turn += 1
    state.add_event(
        "moved",
        direction=preview.direction,
        tile_kind=tile.kind.value,
        enemy_name=tile.enemy.name if tile.enemy else "",
        damage=-preview.hp_delta if preview.hp_delta < 0 else 0,
    )

    if tile.kind is TileKind.STAIRS:
        if state.floor_index < len(FLOORS) - 1:
            state.floor_index += 1
            state.position = FLOORS[state.floor_index].start
            state.add_event("reached_floor", floor_index=state.floor_index)
        else:
            state.won = True
    elif tile.kind is TileKind.BOSS:
        state.won = True
        state.add_event("won")

    state.record_visit()
    return replace(preview)
