from __future__ import annotations

from dataclasses import dataclass

from .models import Enemy, Position, Tile, TileKind

SLIME = Enemy("绿史莱姆", hp=70, attack=30, defense=3, gold=5, icon="♟")
BAT = Enemy("洞窟蝙蝠", hp=110, attack=38, defense=7, gold=9, icon="◆")
SKELETON = Enemy("骷髅卫兵", hp=150, attack=45, defense=12, gold=14, icon="♜")
KNIGHT = Enemy("暗甲骑士", hp=210, attack=58, defense=20, gold=22, icon="♞")
WARDEN = Enemy("深渊守望者", hp=320, attack=70, defense=28, gold=80, icon="♛")

FLOOR = Tile(TileKind.FLOOR, "空地", "")
WALL = Tile(TileKind.WALL, "石墙", "")
YELLOW_DOOR = Tile(TileKind.YELLOW_DOOR, "黄门", "▥")
BLUE_DOOR = Tile(TileKind.BLUE_DOOR, "蓝门", "▥")
YELLOW_KEY = Tile(TileKind.YELLOW_KEY, "黄钥匙", "⚿")
BLUE_KEY = Tile(TileKind.BLUE_KEY, "蓝钥匙", "⚿")
RED_POTION = Tile(TileKind.RED_POTION, "红药水", "♥")
BLUE_POTION = Tile(TileKind.BLUE_POTION, "蓝药水", "♥")
ATTACK_GEM = Tile(TileKind.ATTACK_GEM, "红宝石", "♦")
DEFENSE_GEM = Tile(TileKind.DEFENSE_GEM, "蓝宝石", "♦")
STAIRS = Tile(TileKind.STAIRS, "通往上一层的阶梯", "▲")


@dataclass(frozen=True, slots=True)
class FloorDefinition:
    name: str
    subtitle: str
    layout: tuple[str, ...]
    start: Position
    palette: str


FLOORS = (
    FloorDefinition(
        "遗忘回廊",
        "钥匙有限，绕路也许比硬闯更划算",
        (
            "###########",
            "#..r#.dy.U#",
            "#.#.#.###.#",
            "#.#y#R..s.#",
            "#.###.###.#",
            "#...r...#.#",
            "###.#.#.#.#",
            "#Y..#.#...#",
            "#.###b###.#",
            "#@....D.B.#",
            "###########",
        ),
        Position(9, 1),
        "ember",
    ),
    FloorDefinition(
        "镜湖地窟",
        "防御成长会显著降低后续战斗损耗",
        (
            "###########",
            "#U..#..k.B#",
            "#.#.#.###.#",
            "#b#D#s..R.#",
            "#.#.#.###.#",
            "#...k...#.#",
            "###.#.#.#.#",
            "#Y.d#.#.r.#",
            "#.###y###.#",
            "#@....s...#",
            "###########",
        ),
        Position(9, 1),
        "frost",
    ),
    FloorDefinition(
        "王座之前",
        "只有击败守望者，塔顶的封印才会消散",
        (
            "###########",
            "#....#....#",
            "#.##.#.##.#",
            "#R.k.D.k.B#",
            "###..s..###",
            "#.d.###...#",
            "#.r.#W#.b.#",
            "#...#D#...#",
            "#Y..#y#Y..#",
            "#@........#",
            "###########",
        ),
        Position(9, 1),
        "void",
    ),
)


TILE_LEGEND: dict[str, Tile] = {
    ".": FLOOR,
    "@": FLOOR,
    "#": WALL,
    "D": YELLOW_DOOR,
    "b": BLUE_DOOR,
    "Y": YELLOW_KEY,
    "B": BLUE_KEY,
    "R": RED_POTION,
    "P": BLUE_POTION,
    "A": ATTACK_GEM,
    "y": ATTACK_GEM,
    "d": DEFENSE_GEM,
    "r": Tile(TileKind.ENEMY, SLIME.name, SLIME.icon, SLIME),
    "s": Tile(TileKind.ENEMY, SKELETON.name, SKELETON.icon, SKELETON),
    "k": Tile(TileKind.ENEMY, KNIGHT.name, KNIGHT.icon, KNIGHT),
    "m": Tile(TileKind.ENEMY, BAT.name, BAT.icon, BAT),
    "U": STAIRS,
    "W": Tile(TileKind.BOSS, WARDEN.name, WARDEN.icon, WARDEN),
}


def tile_at(floor_index: int, position: Position, consumed: set[tuple[int, int, int]]) -> Tile:
    if (floor_index, position.row, position.col) in consumed:
        return FLOOR
    return TILE_LEGEND[FLOORS[floor_index].layout[position.row][position.col]]


def in_bounds(floor_index: int, position: Position) -> bool:
    layout = FLOORS[floor_index].layout
    return 0 <= position.row < len(layout) and 0 <= position.col < len(layout[0])
