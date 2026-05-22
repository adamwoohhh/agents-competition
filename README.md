# Terminal Dino Runner

Chrome 断网小恐龙的终端版 —— 演示「如何让 AI Agent 自动玩游戏」。

```
  ┌──────────┐     get_state()     ┌───────────┐
  │  游戏引擎  │ ──────────────────▶ │   Agent   │
  │ DinoGame │ ◀────────────────── │  (决策器)  │
  └──────────┘   jump() / duck()   └───────────┘
       │                                 │
       ▼                               ┌─┴──────────┐
  ┌──────────┐                         │ RuleAgent  │ 规则型（微秒级）
  │  渲染器   │                         │ LLMAgent   │ Claude API（秒级）
  │ Renderer │                         └────────────┘
  └──────────┘
```

## 快速开始

```bash
# 人类手动玩
python3 dino_game.py

# 看规则 AI Agent 自动玩
python3 dino_game.py --agent

# 看 Claude LLM 玩（需要 API key）
export ANTHROPIC_API_KEY=sk-ant-...
python3 dino_game.py --llm
```

**零依赖** — 只用 Python 标准库（curses），无需 pip install。

## 操控

| 按键 | 作用 |
|------|------|
| `SPACE` / `↑` | 跳跃 |
| `↓` | 蹲下（地面）/ 快速下落（空中） |
| `A` | 切换 人类 ↔ AI 模式 |
| `R` | Game Over 后重新开始 |
| `Q` | 退出 |

## 项目结构

整个项目就一个文件 `dino_game.py`，包含 5 个核心组件：

```
dino_game.py
├── 游戏常量        FPS、重力、速度等可调参数
├── 像素艺术        Unicode 字符画的精灵（恐龙、仙人掌、鸟、云）
├── Obstacle       障碍物实体（位置、类型、碰撞箱）
├── DinoGame       游戏引擎（物理、碰撞、生成、状态导出）
├── RuleAgent      规则 Agent（距离阈值判断，微秒级）
├── LLMAgent       LLM Agent（Claude Haiku API，秒级）
├── Renderer       curses 终端渲染器
└── main()         主循环（串联引擎 + 渲染 + Agent）
```

## 核心设计：让 Agent 玩游戏的 3 步

### Step 1: 暴露游戏状态（Observation）

游戏引擎通过 `get_state()` 方法把内部状态导出为结构化数据：

```python
state = game.get_state()
# {
#   "dino_y": 3.4,            # 恐龙高度 (0=地面)
#   "jumping": True,           # 是否在跳
#   "speed": 1.5,              # 当前游戏速度
#   "obstacles": [             # 前方最近 3 个障碍物
#     {"kind": "cactus_lg", "distance": 12.3, "height": 0, ...},
#   ]
# }
```

这就是 Agent 的「眼睛」。设计要点：
- 只暴露 Agent 需要的信息，不是全部内部状态
- 数值要有物理含义（距离、速度），不是像素坐标
- `obstacles` 按距离排序，Agent 不需要自己排

### Step 2: Agent 做决策（Decision）

Agent 读取状态，返回一个动作字符串：

```python
class RuleAgent:
    def decide(self, state: dict) -> str:  # → "jump" / "duck" / "none"
        nearest = state["obstacles"][0]
        if nearest["distance"] < threshold and on_ground:
            return "jump"
        return "none"
```

两种 Agent 对比：

| | RuleAgent | LLMAgent |
|---|---|---|
| 延迟 | < 1ms | 200ms~2s |
| 原理 | 距离阈值 | 自然语言推理 |
| 平均分 | ~960 | ~200 |
| 适用场景 | 实时游戏 | 复杂/慢节奏游戏 |
| 依赖 | 无 | ANTHROPIC_API_KEY |

### Step 3: 注入动作（Action）

把 Agent 的决策映射为游戏操作：

```python
action = agent.decide(game.get_state())
if action == "jump":
    game.jump()
elif action == "duck":
    game.duck(True)
```

Agent 和人类玩家共享同一套 `jump()` / `duck()` 接口。

## 物理参数一览

| 参数 | 值 | 说明 |
|------|-----|------|
| `FPS` | 20 | 每秒 20 帧 |
| `JUMP_VELOCITY` | -2.2 | 起跳初速度（负=向上） |
| `GRAVITY` | 0.25 | 每帧重力加速度 |
| 跳跃最大高度 | ~10.8 | 约第 9 帧到达顶点 |
| 完整跳跃时间 | ~18 帧 | 约 0.9 秒 |
| `INITIAL_SPEED` | 1.0 | 障碍物初始速度 |
| `MAX_SPEED` | 3.5 | 速度上限 |
| 速度公式 | `1.0 + score × 0.001` | 每 1000 分加速 1.0 |

## RuleAgent 跳跃时机推导

Agent 最核心的决策是「什么时候跳」。跳早了 → 落地时撞障碍物；跳晚了 → 来不及起跳。

```
反应距离 = 7 + speed × 4

其中:
  7 = 碰撞区起始距离
      (恐龙右边缘到障碍物左边缘刚好重叠时的 distance 值)
  speed × 4 = 提前量
      (跳跃从起跳到安全高度需要 ~3 帧，3帧 × speed ≈ 提前量)
```

例如 speed=1.5 时：
- `react_dist = 7 + 6 = 13`
- 障碍物 distance < 13 且恐龙在地面 → 立即跳
- 从跳到障碍物进入碰撞区约 3 帧，此时恐龙已升到安全高度

## 碰撞检测

使用 AABB (Axis-Aligned Bounding Box) 矩形碰撞：

```
恐龙碰撞箱 (比视觉小一圈，更公平):
  left   = DINO_COL + 2
  right  = DINO_COL + 7
  bottom = dino_y
  top    = dino_y + (3 if ducking else 5)

障碍物碰撞箱:
  left   = obs.x
  right  = obs.x + width - 1
  bottom = height
  top    = height + h - 1

碰撞条件 (有 ±1 容差):
  dino_right > obs_left + 1  AND
  dino_left  < obs_right - 1 AND
  dino_top   > obs_bottom + 1 AND
  dino_bottom < obs_top - 1
```

## 障碍物生成

| 分数区间 | 可能的障碍物 |
|---------|------------|
| 0 ~ 200 | 小仙人掌、大仙人掌 |
| 200 ~ 500 | + 仙人掌丛、鸟 |
| 500+ | 鸟出现频率翻倍 |

鸟有 3 种飞行高度：
- `height=0`（贴地）— 必须跳过
- `height=4`（中空）— 站着就能过（恐龙碰撞箱高度=5，鸟底部=4）
- `height=8`（高空）— 完全不用管

## 扩展思路

**想写自己的 Agent？** 只需实现 `decide(state) -> str` 方法：

```python
class MyAgent:
    def decide(self, state: dict) -> str:
        # 你的逻辑
        return "jump"  # or "duck" or "none"
```

一些可以尝试的方向：
- **强化学习**: 用 Q-learning 训练，state 作为输入，action 作为输出
- **神经网络**: 把连续几帧的状态堆叠作为输入
- **更聪明的规则**: 考虑连续障碍物的组合，动态调整跳跃力度
- **截屏 Agent**: 不用 `get_state()`，而是截取终端画面让视觉模型识别
