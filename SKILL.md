---
name: call-agents-help
version: 1.1.0
description: >
  召唤 DeepSeek 助手到 Telegram 群里参与讨论。助手的身份和性格由 subsoul.md 定义，
  可随时修改。当用户需要第二个意见、需要验证想法、或要求多角度讨论时使用。
  比 Gemini 更稳定（付费 API，无额度限制）。
  TRIGGERS: "叫帮手", "召唤助手", "让批判派来", "需要第二个意见",
  "帮我验证一下", "让他们讨论", "找人问问", "问问批判派",
  "来个不同意见", "批判一下"
---

# Call Agents Help — 召唤讨论助手

## 角色定义

助手的身份、性格、说话风格定义在 `subsoul.md` 中，脚本启动时自动加载。
**想调整角色？直接改 subsoul.md，不用动代码。**

## 什么时候用

当你（小龙虾）遇到以下情况时，使用这个 skill：

1. **用户主动要求** — 用户说"叫帮手"、"让批判派来"、"讨论一下"等
2. **需要验证** — 你不确定自己的回答，想要第二意见
3. **头脑风暴** — 用户想要多角度分析一个问题

**优先使用 DeepSeek（本 skill）**，Gemini 作为备用（免费额度经常用完）。

## 怎么用

运行 Python 脚本，助手会通过 `@pipan_jack_bot` 在 Telegram 群里发言。

### 环境变量

已在 openclaw.json 的 `skills.entries.call-agents-help.env` 中配置好：
- `DEEPSEEK_API_KEY` — DeepSeek API Key
- `DEEPSEEK_BOT_TOKEN` — pipan_jack_bot 的 Telegram bot token

### 基本用法

```bash
python3 ./skills/call-agents-help/scripts/deepseek_speak.py \
    --chat-id "{当前群的 chat_id}" \
    --topic "用户的问题或讨论话题" \
    --context "之前的对话摘要（你说了什么，用户说了什么）"
```

### 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--chat-id` | YES | Telegram 群的 chat ID |
| `--topic` | YES | 讨论话题或问题 |
| `--context` | NO | 之前的对话内容摘要（见下方格式） |
| `--persona-name` | NO | 显示名称（默认"批判派"）|
| `--emoji` | NO | 消息前缀 emoji（默认🔍）|
| `--model` | NO | DeepSeek 模型（默认 deepseek-chat）|
| `--no-telegram` | NO | 只输出到 stdout，不发 Telegram |

### --context 怎么写

把之前的对话按轮次摘要，包含：谁说了什么观点。不需要逐字复述，抓重点即可。

```
--context "第1轮：小龙虾认为AI最先替代重复性工作。批判派指出创意行业也有风险。第2轮：小龙虾补充了数据支撑。"
```

**不需要放的内容：** 闲聊、表情、跟话题无关的消息。

### 脚本输出

脚本会把回复同时：
1. 发送到 Telegram 群（通过 pipan_jack_bot）
2. 打印到 stdout（你可以读取并继续讨论）

## 多轮讨论协议

**上限 10 轮。** 到了就必须结束并总结，不要无限讨论。

### 第 1 轮：你先发言
在 Telegram 群里发表你的观点，然后调用脚本让助手回应。

### 第 2-10 轮：交替发言
每轮把之前所有对话摘要传入 `--context`：

```bash
python3 ./skills/call-agents-help/scripts/deepseek_speak.py \
    --chat-id "{chat_id}" \
    --topic "原始话题" \
    --context "第1轮：小龙虾说了xxx。批判派说了yyy。第2轮：小龙虾说了zzz。"
```

### 结束讨论
讨论充分后（或到达 10 轮），在 Telegram 里发一条总结消息。脚本是一次性的，不留后台进程。

## 重要提示

- **每次调用都是独立的** — 脚本运行完就退出，不占资源
- **上下文要你来管理** — 把之前的对话摘要放在 `--context` 里
- **付费 API** — DeepSeek 很便宜但有费用，避免无意义的大量调用
- **脚本不需要额外安装依赖** — 只用了 Python 标准库

## 文件结构

```
call-agents-help/
├── SKILL.md                ← 你正在看的（调用说明）
├── subsoul.md              ← 助手的身份档案（改性格改这里）
└── scripts/
    └── deepseek_speak.py   ← 一次性脚本（自动读取 subsoul.md）
```
