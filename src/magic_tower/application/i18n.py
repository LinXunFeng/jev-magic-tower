from __future__ import annotations

from magic_tower.domain.models import ActionPreview, GameEvent, Tile, TileKind

SUPPORTED_LANGUAGES = {"zh", "en"}

FLOOR_TEXT = {
    "zh": (
        ("遗忘回廊", "钥匙有限，绕路也许比硬闯更划算"),
        ("镜湖地窟", "防御成长会显著降低后续战斗损耗"),
        ("王座之前", "只有击败守望者，塔顶的封印才会消散"),
    ),
    "en": (
        ("Forgotten Gallery", "Keys are scarce; a detour may be wiser than forcing a door."),
        ("Mirrorlake Cavern", "Defense upgrades greatly reduce the cost of later battles."),
        ("Before the Throne", "Defeat the Abyss Warden to break the tower's final seal."),
    ),
}

TILE_TEXT = {
    "zh": {
        TileKind.FLOOR: "空地",
        TileKind.WALL: "石墙",
        TileKind.YELLOW_DOOR: "黄门",
        TileKind.BLUE_DOOR: "蓝门",
        TileKind.YELLOW_KEY: "黄钥匙",
        TileKind.BLUE_KEY: "蓝钥匙",
        TileKind.RED_POTION: "红药水",
        TileKind.BLUE_POTION: "蓝药水",
        TileKind.ATTACK_GEM: "红宝石",
        TileKind.DEFENSE_GEM: "蓝宝石",
        TileKind.STAIRS: "通往上一层的阶梯",
    },
    "en": {
        TileKind.FLOOR: "empty floor",
        TileKind.WALL: "stone wall",
        TileKind.YELLOW_DOOR: "yellow door",
        TileKind.BLUE_DOOR: "blue door",
        TileKind.YELLOW_KEY: "yellow key",
        TileKind.BLUE_KEY: "blue key",
        TileKind.RED_POTION: "red potion",
        TileKind.BLUE_POTION: "blue potion",
        TileKind.ATTACK_GEM: "attack gem",
        TileKind.DEFENSE_GEM: "defense gem",
        TileKind.STAIRS: "stairs to the next floor",
    },
}

ENEMY_TEXT = {
    "zh": {
        "绿史莱姆": "绿史莱姆",
        "洞窟蝙蝠": "洞窟蝙蝠",
        "骷髅卫兵": "骷髅卫兵",
        "暗甲骑士": "暗甲骑士",
        "深渊守望者": "深渊守望者",
    },
    "en": {
        "绿史莱姆": "Green Slime",
        "洞窟蝙蝠": "Cave Bat",
        "骷髅卫兵": "Skeleton Guard",
        "暗甲骑士": "Dark Knight",
        "深渊守望者": "Abyss Warden",
    },
}

DIRECTION_TEXT = {
    "zh": {"up": "上", "right": "右", "down": "下", "left": "左"},
    "en": {"up": "up", "right": "right", "down": "down", "left": "left"},
}


def normalize_language(language: str | None) -> str:
    if not language:
        return "zh"
    candidate = language.lower().split("-", 1)[0]
    return candidate if candidate in SUPPORTED_LANGUAGES else "en"


def floor_text(floor_index: int, language: str) -> tuple[str, str]:
    return FLOOR_TEXT[normalize_language(language)][floor_index]


def tile_text(tile: Tile, language: str) -> str:
    language = normalize_language(language)
    if tile.enemy:
        return ENEMY_TEXT[language][tile.enemy.name]
    return TILE_TEXT[language].get(tile.kind, tile.label)


def action_description(action: ActionPreview, language: str) -> str:
    language = normalize_language(language)
    if language == "en":
        effects = _effects(action, ("HP", "attack", "defense", "gold", "yellow keys", "blue keys"), ", ")
        effect_text = effects or "no immediate resource change"
        return (
            f"Move {DIRECTION_TEXT['en'][action.direction]} to {tile_text(action.tile, 'en')}; "
            f"{effect_text}. This square has been visited {action.visit_count} time(s)."
        )
    effects = _effects(action, ("生命", "攻击", "防御", "金币", "黄钥匙", "蓝钥匙"), "，")
    effect_text = effects or "资源无即时变化"
    return (
        f"向{DIRECTION_TEXT['zh'][action.direction]}进入{tile_text(action.tile, 'zh')}；"
        f"{effect_text}；该格已访问 {action.visit_count} 次。"
    )


def event_text(event: GameEvent, language: str) -> str:
    language = normalize_language(language)
    params = event.params
    if event.code == "game_started":
        return "勇者踏入遗忘之塔。" if language == "zh" else "The hero enters the Forgotten Tower."
    if event.code == "moved":
        enemy_name = str(params.get("enemy_name", ""))
        localized_tile = (
            ENEMY_TEXT[language][enemy_name]
            if enemy_name
            else TILE_TEXT[language][TileKind(str(params["tile_kind"]))]
        )
        if language == "zh":
            suffix = f"，损失 {params['damage']} HP" if params.get("damage") else ""
            return f"向{DIRECTION_TEXT['zh'][str(params['direction'])]}移动：{localized_tile}{suffix}。"
        suffix = f", lost {params['damage']} HP" if params.get("damage") else ""
        return f"Moved {DIRECTION_TEXT['en'][str(params['direction'])]}: {localized_tile}{suffix}."
    if event.code == "reached_floor":
        name, _ = floor_text(int(params["floor_index"]), language)
        return (
            f"抵达第 {int(params['floor_index']) + 1} 层：{name}。"
            if language == "zh"
            else f"Reached floor {int(params['floor_index']) + 1}: {name}."
        )
    if event.code == "won":
        return (
            "深渊守望者倒下，遗忘之塔的封印已经解除！"
            if language == "zh"
            else "The Abyss Warden falls. The tower's seal is broken!"
        )
    if event.code == "no_moves":
        return "没有可执行的移动，冒险结束。" if language == "zh" else "No legal moves remain. The journey ends."
    return event.code


def _effects(action: ActionPreview, names: tuple[str, ...], separator: str) -> str:
    values = (
        action.hp_delta,
        action.attack_delta,
        action.defense_delta,
        action.gold_delta,
        action.yellow_key_delta,
        action.blue_key_delta,
    )
    return separator.join(f"{name} {value:+d}" for name, value in zip(names, values) if value)
