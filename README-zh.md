# 遗忘之塔 · Jev Magic Tower

[English](README.md) | **中文**

一款用于观察 TypeSafe Jev 策略判断的三层魔塔。玩家可以手动探索，也可以让 Jev 在每个合法移动之间选择。界面会实时展示完整概率分布、置信度、模型名和耗时。

![Jev 魔塔游戏与实时决策视图](assets/jev-magic-tower-gameplay.jpeg)

项目采用分层架构：确定性游戏规则、用例编排、Jev 适配器和 Web 交付层相互独立。游戏状态只由领域规则修改，Jev 专注于有边界的策略判断，便于测试、替换和持续扩展。

## 玩法与测试目标

- 三层 11×11 地图，包含门、钥匙、药水、宝石、普通敌人和最终 Boss。
- 代码先计算所有合法移动及其确定性后果；Jev 只负责在候选中选择，不负责修改状态。
- 每个候选说明会包含资源变化和访问次数，用于测试 Jev 对生命、永久成长、稀缺钥匙、探索和绕路的权衡。
- 连续推演采用响应驱动：上一轮 Jev 结果应用到游戏状态后，立即用新状态发起下一轮，不添加固定决策间隔。
- 连续推演期间会显示真实墙钟用时，其中包含 Jev API 响应时间；停止、失败或通关时计时冻结。
- 内置中文与英文。首次访问根据浏览器语言自动选择，也可在“Jev 设置”中固定为中文、English，或恢复自动识别。
- 没有 API Key 或请求失败时自动使用明确标记的本地基线，方便先验收 UI；它不会伪装成 Jev 结果。
- 手动操作支持方向键或 `WASD`，也可点击相邻格子。

## 一条命令启动

安装 [uv](https://docs.astral.sh/uv/) 后，在项目目录执行：

```bash
uv run jev-magic-tower
```

`uv` 会自动创建隔离环境、安装锁定依赖并启动服务，无需手动创建虚拟环境。打开 <http://127.0.0.1:8093> 即可。

点击页面右上角的“Jev 设置”可以填写 API Key、API 地址、模型和界面语言。页面配置仅保存在当前服务进程内存中，不写入浏览器或磁盘；重新启动时仍优先读取 `TYPESAFE_API_KEY`、`TYPESAFE_BASE_URL` 和 `TYPESAFE_MODEL` 环境变量。没有 Key 时也可以把“决策源”切换为“本地基线”离线体验。

运行测试：

```bash
uv run --extra dev pytest
uv run --extra dev ruff check .
```

## 目录

```text
src/magic_tower/
├── domain/                  # 实体、楼层定义、战斗与移动规则
├── application/             # 用例服务、本地化及决策引擎端口
├── infrastructure/          # TypeSafe SDK、环境和 HTTP 适配器
├── web/static/              # 无构建步骤的浏览器界面
└── main.py                  # 组合根
tests/                       # 领域、应用、配置与本地化测试
```

## Jev 请求边界

`JevDecisionEngine` 使用一个 `Choice` 问题：

- `state`：英雄资源、楼层、最近事件、回合和长期目标。
- `criteria`：当前每个合法方向，以及进入该格后的确定性资源变化和历史访问次数。
- 返回值：所选动作、所有动作的概率和 confidence。

门能否打开、敌人是否可击败、战斗扣血、拾取和换层全部由领域规则处理。这保证了模型输出永远只能触发当前合法动作，也使 Jev 与本地基线可以在同一套游戏状态上公平比较。

## 配置

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `TYPESAFE_API_KEY` | 无 | TypeSafe API Key |
| `TYPESAFE_BASE_URL` | `https://api.typesafe.ai` | API 地址 |
| `TYPESAFE_MODEL` | `jev-latest` | System One 模型 |
| `HOST` | `127.0.0.1` | Web 监听地址 |
| `PORT` | `8093` | Web 监听端口 |
