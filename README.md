# T-Rex Run | 暴龙快跑

Chrome 断网小恐龙的终端版。可以手动玩，也可以让规则 Agent 或 Claude LLM Agent 自动玩。

## 安装

在项目目录中安装到本地虚拟环境 `.venv`：

```bash
make install
```

这会创建 `.venv`，并把命令安装到：

```text
.venv/bin/trex
```

## 启动

```bash
# 人类手动玩
make run

# 规则 Agent 自动玩
make agent

# Claude LLM Agent 自动玩
export ANTHROPIC_API_KEY=sk-ant-...
make llm
```

也可以直接使用底层命令：

```bash
.venv/bin/trex
.venv/bin/trex --agent
.venv/bin/trex --llm
python3 dino_game.py
python3 dino_game.py --agent
python3 dino_game.py --llm
```

## 模式

| 命令 | 说明 | 依赖 |
|------|------|------|
| `trex` | 手动操作恐龙 | 无 |
| `trex --agent` | 使用本地规则 Agent 自动决策 | 无 |
| `trex --llm` | 使用 Claude API 决策 | `ANTHROPIC_API_KEY` |

如果 `trex --llm` 没有检测到 `ANTHROPIC_API_KEY`，游戏会降级为规则 Agent。

## 操控

| 按键 | 作用 |
|------|------|
| `SPACE` / `↑` | 跳跃 |
| `↓` | 蹲下（地面）/ 快速下落（空中） |
| `A` | 切换 人类 ↔ 规则 Agent |
| `R` | Game Over 后重新开始 |
| `Q` | 退出 |

## 运行要求

- Python 3.11+
- 支持 `curses` 的终端环境
- 游戏本身无第三方运行时依赖

开发、测试、架构和扩展 Agent 的说明见 [CONTRIBUTING.md](CONTRIBUTING.md)。
