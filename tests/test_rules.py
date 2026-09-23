from magic_tower.domain.floors import FLOORS, SLIME, TileKind
from magic_tower.domain.models import Hero, Position, combat_damage
from magic_tower.domain.rules import apply_action, legal_actions, new_game


def test_combat_damage_counts_only_enemy_retaliations() -> None:
    hero = Hero(hp=1000, attack=28, defense=16)
    # 70 HP / 25 damage requires three hero hits, therefore two retaliations.
    assert combat_damage(hero, SLIME) == 2 * (SLIME.attack - hero.defense)


def test_new_game_exposes_only_walkable_neighbors() -> None:
    state = new_game()
    actions = {item.direction: item for item in legal_actions(state)}
    assert set(actions) == {"right", "up"}
    assert actions["right"].tile.kind is TileKind.FLOOR
    assert actions["up"].tile.kind is TileKind.FLOOR


def test_collecting_key_changes_inventory_and_consumes_tile() -> None:
    state = new_game()
    before = state.hero.yellow_keys
    apply_action(state, "move_up")
    preview = apply_action(state, "move_up")
    assert preview.tile.kind is TileKind.YELLOW_KEY
    assert state.hero.yellow_keys == before + 1
    assert (0, state.position.row, state.position.col) in state.consumed


def test_stepping_on_stairs_moves_to_next_floor() -> None:
    state = new_game()
    state.position = Position(1, 8)
    state.visits[(0, 1, 8)] = 1
    assert any(item.tile.kind is TileKind.STAIRS for item in legal_actions(state))
    apply_action(state, "move_right")
    assert state.floor_index == 1
    assert state.position == FLOORS[1].start
