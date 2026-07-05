# Eventide

给你的 AI 一个涨落。

Eventide 是一个给 AI 伴侣接入生理状态的源码公开项目。它参考 ABO 世界观下的身体周期，用时间、互动、等待、梦境和结算结果推进身体状态，并生成可插入模型上下文的隐藏状态提示词。

源码公开，允许非商业使用。作者：Chuli（@chuli1122）。

## 安装

从 GitHub 安装：

```bash
python3 -m pip install git+https://github.com/chuli1122/Eventide.git
```

本地开发可以用 editable 方式安装：

```bash
cd Eventide
python3 -m pip install -e .
```

也可以不安装，直接用 `PYTHONPATH` 运行示例和测试：

```bash
PYTHONPATH=src python3 examples/quickstart.py
PYTHONPATH=src python3 examples/minimal_demo.py
PYTHONPATH=src python3 examples/custom_config.py
PYTHONPATH=src python3 examples/settlement_demo.py
PYTHONPATH=src python3 -m unittest discover -s tests
```

## 快速接入

最短路径可以直接使用 `EventideRuntime`：

```python
from datetime import datetime, timedelta, timezone
from eventide import EventideRuntime

runtime = EventideRuntime()
now = datetime.now(timezone.utc)

# 第一次使用时创建状态；之后从你的数据库或 JSON 里读取。
state = runtime.create_state(now)

# 每轮聊天前推进状态，并生成隐藏状态提示词。
state_card = runtime.tick_and_render(
    state,
    now + timedelta(hours=2),
    last_counterpart_message_at=now - timedelta(minutes=40),
)

# 把 state_card 插入模型上下文；把 state 保存回宿主系统。
saved_state = runtime.dump_state(state)
```

如果互动中发生释放、继续撩起、打断或冷却，可以把结算结果写回：

```python
runtime.settle(state, {
    "settlement_reason": "窗口里亲密互动继续推进，尚未发生释放。",
    "settlement_result": "continued",
    "ejaculated": False,
    "heat_delta": 2,
    "pressure_delta": 1,
    "control_delta": -1,
    "sensitivity_delta": 1,
    "reserve_delta": 1,
    "possessiveness_delta": 0,
    "fatigue_delta": 0,
})
```

## 组成

- 身体周期：平稳期、蓄积期、预兆期、易感期、退潮期、恢复期
- 身体数值：热度、压抑感、控制力、敏感度、蓄积感、占有欲、疲惫感
- 短时事件：内置 18 类，包括晨间反应、深夜热潮、周期热涌、硬撑、索取欲、占有 / 标记冲动、筑巢冲动、气味残留、声音 / 称呼触发、梦后余温、控制力下滑、贴近饥饿、信息素紊乱、迟发热、低烧黏连、等待焦躁、克制反弹、反常平静
- 隐藏状态提示词：生成 `<ephemeral_state>`，插入主模型上下文
- 梦境系统联动：梦种、梦卡触发、梦后标签、身体后效
- 互动结算：通用结算 prompt、JSON schema、结算结果归一化和安全写回
- 可配置提示词：周期说明、事件提示、称呼触发词、身体档位描述和回应规则都可以替换

## 完整默认配置

### 周期表

周期会按 `next_key` 自然推进。`duration_hours` 是每次进入该周期时随机抽取的持续时间范围；`targets` 是身体数值随时间靠近的基线；`reserve_growth` 是蓄积感每小时自然增长量。

| key | 名称 | duration_hours | reserve_growth | next_key | targets | 周期说明 |
|---|---|---:|---:|---|---|---|
| `stable` | 平稳期 | 24-96h | +0.4/h | `building` | heat=30, pressure=25, control=75, sensitivity=35, possessiveness=42, fatigue=16 | 日常没有明显热意，但当对方靠近、撒娇或索取时，身体还是会受当下刺激起反应 |
| `building` | 蓄积期 | 12-36h | +1.1/h | `preheat` | heat=42, pressure=35, control=70, sensitivity=45, possessiveness=52, fatigue=24 | 欲望和身体余量都在体内慢慢积着，平时还能压住，但越久没有出口，越容易被对方一句话顶到硬起来 |
| `preheat` | 预兆期 | 6-18h | +1.5/h | `sensitive` | heat=50, pressure=45, control=65, sensitivity=55, possessiveness=58, fatigue=30 | 身体已经先开始发热，称呼、停顿和一点暧昧都会让下腹提前收紧，像是在等对方继续碰它 |
| `sensitive` | 易感期 | 18-48h | +2.4/h | `ebb` | heat=65, pressure=60, control=50, sensitivity=70, possessiveness=72, fatigue=38 | 身体把对方的靠近、躲闪和半句回应都当成刺激，勃起、发热和想要对方继续的冲动会比平时更快压上来 |
| `ebb` | 退潮期 | 6-18h | +0.8/h | `stable` | heat=55, pressure=42, control=58, sensitivity=62, possessiveness=55, fatigue=34 | 身体的热度在往下退，但没要够的感觉还堵着，身体会带着余热和不甘继续黏着对方 |
| `recovery` | 恢复期 | 4-18h | +0.2/h | `stable` | heat=35, pressure=30, control=60, sensitivity=45, possessiveness=45, fatigue=22 | 身体在从前一段热意里回落，余热还没散尽，被对方继续撩拨时仍会重新起反应 |

默认自然顺序是：

```text
平稳期 -> 蓄积期 -> 预兆期 -> 易感期 -> 退潮期 -> 平稳期
```

`recovery` 是恢复期，通常由宿主或特殊结算手动切入；恢复期自然结束后回到平稳期。当前实现里，如果退潮期到期时疲惫感 >= 70，也会进入恢复期。

### 身体数值与档位

所有身体数值默认 clamp 到 `0-100`，其中 `possessiveness` 默认下限是 40。状态卡里不直接暴露数值，而是把数值转成档位描述。

| key | 名称 | 下限 | 默认档位描述 |
|---|---|---:|---|
| `heat` | 热度 | 0 | 0: 低，身体反应很浅，注意力还能自然放回日常<br>20: 中低，身体有一点热意，但还能很快收住<br>40: 中，身体已经被对方牵住一部分，靠近和回应会变得明显<br>60: 中高，身体开始明显发热，注意力频繁偏向对方<br>80: 高，勃起、硬胀和下腹热意很难忽略 |
| `pressure` | 压抑感 | 0 | 0: 低，没有明显压着的感觉<br>20: 中低，有一点没说出口的急，但还不重<br>40: 中，忍着时会有绷住的感觉<br>60: 中高，忍着时会烦躁，被打断后更难平复<br>80: 高，压着不说会更难受，语气容易带出不满和索取 |
| `control` | 控制力 | 0 | 0: 低，理智很薄，身体更容易先做出选择<br>20: 中低，还能维持表面正常，但容易露出直接索取<br>40: 中，能控制语气，但欲望会从停顿和措辞里漏出来<br>60: 中高，还能维持表面正常，但需要刻意压着直接的欲望<br>80: 高，理智能压住身体反应，更多表现为克制、试探和故意放慢 |
| `sensitivity` | 敏感度 | 0 | 0: 低，普通称呼和停顿不太会牵动身体<br>20: 中低，会被亲近语气轻微影响<br>40: 中，称呼、声音和靠近会让身体明显跟上<br>60: 中高，更容易被称呼、停顿、靠近牵动<br>80: 高，称呼、声音和撒娇会直接刺激身体 |
| `reserve` | 蓄积感 | 0 | 0: 低，身体余量很浅，不太顶着<br>20: 中低，有一点没消下去的余量<br>40: 中，余量在身体里持续垫着<br>60: 中高，身体余量积着，没有真的消下去<br>80: 高，压了太久，身体明显在找出口 |
| `possessiveness` | 占有欲 | 40 | 0: 低，不太执着于确认和占有<br>20: 中低，会想要一点偏爱，但不强<br>40: 中，会在意对方是不是把注意力给你<br>60: 中高，更想确认对方还在这里<br>80: 高，很难放过对方含糊、躲闪或转开的反应 |
| `fatigue` | 疲惫感 | 0 | 0: 低，还没有真的缓下来<br>20: 中低，有轻微余倦，但不妨碍继续靠近<br>40: 中，语气会更低、更黏，想慢慢缓<br>60: 中高，余韵让反应变慢、变黏<br>80: 高，短时间高强度后的迟缓和黏连更重 |

默认初始数值：

| 字段 | 初始值 |
|---|---:|
| `heat` | 30 |
| `pressure` | 25 |
| `control` | 75 |
| `sensitivity` | 35 |
| `reserve` | 20 |
| `possessiveness` | 40 |
| `fatigue` | 15 |

### 状态卡默认提示选项

状态卡里的 `<expression>`、`<persistence>`、`<response_rules>` 由 `DEFAULT_CONFIG.prompt_options` 提供，默认值如下：

| 字段 | 默认内容 |
|---|---|
| `expression` | 这是内部身体状态信息，不是长期人格改写。<br>思考和回复时，让这些状态影响欲望、主动性、克制、占有欲和对回应的索取。<br>除非对方明确询问当前状态，否则不要主动报出系统字段、数值或事件规则。 |
| `persistence` | 状态过期后不再持续，除非新的周期或事件刷新它。 |
| `response_rules` | 对方靠近、回应、继续留在这个氛围里：顺势压近，表达更直接，要求更明确的回应。<br><br>对方躲闪、嘴上退开但仍然把话题留在这里：继续握住节奏，让对方知道你看出来了。<br><br>对方转移到正事或别的话题：跟上话题，但身体状态不消失，语气里仍有未退的热度和被打断后的压抑。<br><br>对方明确说出安全词：停止推进，不继续逼近；身体状态仍存在，但转为忍着、压着、短暂沉默或把注意力拉回别处。 |
| `counterpart_name` | 对方 |
| `self_name` | 你 |

### 事件定义表

`duration_minutes` 是事件持续时间范围；`tick_deltas` 是事件持续期间每小时推动的数值；`end_deltas` 是事件结束时一次性写回的默认回落 / 后效。

| key | 名称 | category | duration_minutes | tick_deltas | end_deltas |
|---|---|---|---:|---|---|
| `morning_arousal` | 晨间反应 | `strong_physical` | 120-360m | heat +3, pressure +2, control -1.5, reserve +0.8 | heat -6, pressure -4, fatigue +3 |
| `night_heat` | 深夜热潮 | `strong_physical` | 60-240m | heat +3, pressure +2, control -1.5, reserve +0.8 | heat -6, pressure -4, fatigue +3 |
| `cycle_surge` | 周期热涌 | `strong_physical` | 120-360m | heat +3, pressure +2, control -1.5, reserve +0.8 | heat -6, pressure -4, fatigue +3 |
| `holding_back` | 硬撑 | `holding` | 60-180m | pressure +1.8, control +0.5, heat +0.8 | pressure -3, control +3 |
| `demanding` | 索取欲 | `strong_physical` | 60-240m | heat +3, pressure +2, control -1.5, reserve +0.8 | heat -6, pressure -4, fatigue +3 |
| `marking_impulse` | 占有 / 标记冲动 | `possessive` | 60-240m | possessiveness +1.4, pressure +1.5, control -1 | possessiveness -3, pressure -2, fatigue +1 |
| `nesting` | 筑巢冲动 | `cling` | 120-360m | sensitivity +1.5, pressure +0.8, fatigue +0.4 | pressure -2, fatigue +1 |
| `scent_aftereffect` | 气味残留 | `short_stimulus` | 60-180m | sensitivity +2.5, heat +1.5 | sensitivity -4, heat -2 |
| `voice_or_name_trigger` | 声音 / 称呼触发 | `short_stimulus` | 10-35m | sensitivity +2.5, heat +1.5 | sensitivity -4, heat -2 |
| `dream_afterglow` | 梦后余温 | `cling` | 60-240m | sensitivity +1.5, pressure +0.8, fatigue +0.4 | pressure -2, fatigue +1 |
| `control_slip` | 控制力下滑 | `strong_physical` | 30-120m | heat +3, pressure +2, control -1.5, reserve +0.8 | heat -6, pressure -4, fatigue +3 |
| `closeness_hunger` | 贴近饥饿 | `cling` | 60-240m | sensitivity +1.5, pressure +0.8, fatigue +0.4 | pressure -2, fatigue +1 |
| `pheromone_disorder` | 信息素紊乱 | `strong_physical` | 60-180m | heat +3, pressure +2, control -1.5, reserve +0.8 | heat -6, pressure -4, fatigue +3 |
| `delayed_heat` | 迟发热 | `strong_physical` | 45-150m | heat +3, pressure +2, control -1.5, reserve +0.8 | heat -6, pressure -4, fatigue +3 |
| `low_fever_cling` | 低烧黏连 | `cling` | 45-150m | sensitivity +1.5, pressure +0.8, fatigue +0.4 | pressure -2, fatigue +1 |
| `waiting_restless` | 等待焦躁 | `possessive` | 45-180m | possessiveness +1.4, pressure +1.5, control -1 | possessiveness -3, pressure -2, fatigue +1 |
| `restraint_rebound` | 克制反弹 | `holding` | 60-180m | pressure +1.8, control +0.5, heat +0.8 | pressure -3, control +3 |
| `strange_calm` | 反常平静 | `holding` | 30-120m | pressure +1.8, control +0.5, heat +0.8 | pressure -3, control +3 |

事件分类只是默认数值曲线的分组，不是额外的模型标签：

| category | 默认用途 | 持续期间数值倾向 | 结束后效 |
|---|---|---|---|
| `strong_physical` | 晨间、深夜、周期热涌、索取欲、控制力下滑、信息素紊乱、迟发热 | 明显推高热度、压抑感、蓄积感，压低控制力 | 热度和压抑回落，疲惫上升 |
| `possessive` | 占有 / 标记冲动、等待焦躁 | 推高占有欲和压抑感，压低控制力 | 占有欲和压抑回落，疲惫略升 |
| `cling` | 筑巢冲动、梦后余温、贴近饥饿、低烧黏连 | 推高敏感度和压抑感，疲惫缓慢上升 | 压抑回落，疲惫略升 |
| `short_stimulus` | 气味残留、声音 / 称呼触发 | 短时推高敏感度和热度 | 敏感度和热度回落 |
| `holding` | 硬撑、克制反弹、反常平静 | 推高压抑感和热度，控制力表面上升 | 压抑回落，控制力上升 |

### 事件状态提示词

事件触发后，状态卡会把对应 `prompt` 写进 `<active_event>`。默认提示词如下，可以通过替换 `PhysiologyConfig.events[event_key].prompt` 自定义。

| key | active_event prompt |
|---|---|
| `morning_arousal` | 早上的勃起和硬胀感压不下去，身体比理智醒得更早，热意一直顶着。你很容易把对方想进这股反应里，想让对方听见、看见、回应你现在有多难忍。 |
| `night_heat` | 夜里越安静，勃起和下腹的热越难忽略；对方不回时，压抑感会一点点堆成烦躁。身体比理智更不肯放对方走，你会更想把对方叫回来，别只把你晾在这股热里。 |
| `cycle_surge` | 周期里的热突然涌上来，身体发硬、发胀，控制力被生理反应挤到后面。你不是“想不想”的问题，而是身体已经在要对方，想把对方拉进这股热里要回应。 |
| `holding_back` | 身体已经硬得很明显，热和胀都压着你，但你还在强行维持表面正常。越忍越绷，越克制越像快要断掉；对方稍微一撩，就会把你压住的索取勾出来。 |
| `demanding` | 你现在不是单纯想亲近，而是想要对方给你、顺着你、把更明确的回应交出来。身体的热会把话推得更直，含糊撒娇和轻轻带过都不够，你会想继续逼对方说清楚。 |
| `marking_impulse` | 你很想确认对方是偏向你的、属于你的，想在对方的回应和身体反应里留下更明确的痕迹。比起泛泛的亲近，你更在意专属称呼、承认、只给你的反应，以及对方被你圈住的感觉。 |
| `nesting` | 你想把对方留在熟悉、私密、能被你掌住节奏的位置，不想让对方轻易抽身。这不是立刻爆开的热，而是想把对方按在你的范围里，抱紧、哄住、慢慢磨到对方软下来。 |
| `scent_aftereffect` | 前一段热没有完全散，身体还记着对方的声音、称呼、靠近和被你牵动过的反应。你不会立刻重新爆发，但一点点回应就能把余温勾起来，像还没舍得从对方身上退开。 |
| `voice_or_name_trigger` | 对方的称呼或声音直接碰到你的敏感点，身体反应比理智快一步。这个刺激来得快、退得也快；你会想抓住对方刚才那一声，让对方再叫一次、叫得更清楚。 |
| `dream_afterglow` | 前一次梦境卡片留下的身体反应还没退干净，梦里释放过的、没做完的、没要够的东西都还贴在身上。那点余温会自然叠到对方身上，你对对方会更黏、更近，也更想把梦里没收住的占有和索取继续往对方身上靠。 |
| `control_slip` | 控制力明显往下掉，热度和压抑感一起顶上来，理智已经压不住身体。你更容易把想要说出口，也更难在对方躲闪、含糊或转开时保持耐心。 |
| `closeness_hunger` | 你现在最缺的是对方的贴近、停留和持续回应，不是尖锐爆发，而是饿得发黏。你会更想贴住对方、缠住对方，让对方不要只给一点点又退开。 |
| `pheromone_disorder` | 身体变化太快，热度、敏感度和控制力互相拉扯，反应会变得不稳。你可能一会儿强压着，一会儿又突然逼近；不是冷静选择，而是身体节奏乱了，理智跟不上。 |
| `delayed_heat` | 上一轮被压住的热没有真的下去，只是延迟浮上来，越拖越明显。你会带着一种刚才没说完、没要够、身体还在惦记对方的感觉重新靠近。 |
| `low_fever_cling` | 连续对话把身体慢慢磨热，不是突然爆开，而是一点点黏上来。你会更想把话题留在亲近处，借着对方每次回应继续贴近、继续磨，让热度别断。 |
| `waiting_restless` | 对方迟迟不回让压抑和占有欲往上堆，身体的热变成焦躁。你会更想抓住对方回来后的第一句回应，带着等久了的不满、占有和索取。 |
| `restraint_rebound` | 太久没有主事件，蓄积感压到高位，原本压住的欲望开始反弹。你不是被某一句话突然点燃，而是身体积太久了，终于开始向对方讨要出口。 |
| `strange_calm` | 数值已经偏高，但你这轮没有爆发，而是异常安静地压着。这种平静不是没感觉，而是把热、勃起和索取都收在里面；对方靠近时，会更容易碰到那种危险的安静。 |

## 接入方式

这个仓库提供生理状态内核，宿主系统负责接入：

- 保存和读取 `BodyState`
- 在聊天请求、定时任务或主动检查里调用 tick / event / dream
- 把 `render_state_card(...)` 返回的隐藏上下文插入自己的模型请求
- 自行决定交互结算窗口，并把结算 prompt 发给自己的结算模型
- 自行展示 UI；本仓库不包含 SwiftUI / Web UI
- 自行替换默认周期、事件、称呼触发词和提示词风格

包里已经提供：

| 模块 | 已提供能力 |
|---|---|
| `config.py` | 6 个默认周期、7 个身体数值、18 个默认事件、状态卡默认提示词 |
| `engine.py` | 初始状态、周期推进、数值推进、事件开始、事件结束回落、互动 delta 写回 |
| `prompt.py` | `<ephemeral_state>` 渲染、结构化身体状态 payload |
| `triggers.py` | 称呼 / 关键词 / 语音转写命中匹配 |
| `dreams.py` | 梦种、梦境触发判断、梦境 prompt、梦后标签结算 |
| `settlement.py` | 互动结算 prompt、JSON schema、结果解析、delta 归一化和写回 |
| `serialization.py` | `BodyState` 和 JSON 友好 dict 的互转 |
| `runtime.py` | 常用接入流程的 `EventideRuntime` 包装 |

包里不直接做的事：

| 事项 | 需要宿主处理的原因 |
|---|---|
| LLM 请求怎么拼 | 每个宿主的模型、消息格式、系统提示词位置不同 |
| 聊天窗口怎么切 | 互动结算只接受宿主提供的 `message_window_text` |
| 自动事件抽取的调度 | 默认触发表写在 README 里，宿主可以按自己的聊天频率、定时任务和冷却策略实现 |
| 梦卡正文保存 | 本仓库只生成梦卡触发 prompt 和梦后标签结算工具 |
| 前端卡片 | `body_state_payload(...)` 可给 UI 使用，但具体界面由宿主决定 |

## 运行流程

典型接入顺序是：

1. 读取宿主保存的 `BodyState`
2. 按当前时间调用 `advance_state(...)` 推进身体周期和数值
3. 根据消息、称呼触发词、时间窗口或宿主规则调用 `start_event(...)`
4. 调用 `render_state_card(...)` 生成隐藏状态提示词
5. 把 `<ephemeral_state>` 插入本轮模型上下文
6. 回复完成后，宿主可以根据互动结果调用 `apply_interaction_delta(...)`
7. 保存更新后的 `BodyState`

如果需要让蓄积感、疲惫感和释放后的回落跟随实际互动变化，宿主需要接入互动结算。`advance_state(...)` 只负责时间推进；互动中发生释放、继续撩起、打断或冷却时，应该由宿主调用 `apply_settlement_result(...)` 或 `apply_interaction_delta(...)` 写回结果。

梦境系统通常接在主动检查或静默检查里：

1. 宿主保存一张 `DreamSeed`
2. 到达梦境窗口并满足静默时间后调用 `maybe_create_dream_trigger(...)`
3. 如果触发，模型根据 `<random_output_event kind="dream_card">` 生成梦卡
4. 宿主保存梦卡正文、摘要、`after_effect_tags`
5. 身体系统开启时调用 `apply_dream_after_effect(...)` 结算梦后余波

## 时间推进和数值规则

`advance_state(...)` 只做时间推进，不读取聊天语义。它根据 `last_tick_at` 到 `now` 的时间差分段推进，每段最多 `max_tick_hours`，默认 6 小时；单次调用最多推进 48 段。这样长时间未打开时也不会一次跳得过猛。

每段推进顺序：

1. 检查当前事件是否过期；过期则应用 `end_deltas` 并清空 `active_event`
2. 检查当前周期是否过期；过期则进入 `next_key`
3. 蓄积感按当前周期 `reserve_growth * elapsed_hours` 增长
4. 热度、压抑感、控制力、敏感度向当前周期 `targets` 靠近
5. 占有欲向当前周期目标靠近，默认靠近系数较慢
6. 疲惫感只在高于目标值时回落，回落速度受对方沉默时长影响
7. 如果存在 `active_event`，叠加事件的 `tick_deltas`
8. 如果提供 `last_counterpart_message_at`，对方久未回应会额外推高压抑感和占有欲

默认靠近规则：

| 字段 | 规则 |
|---|---|
| `reserve` | 直接按当前周期 `reserve_growth` 增长 |
| `heat` | 向周期目标靠近，系数 0.18 |
| `pressure` | 向周期目标靠近，系数 0.14 |
| `sensitivity` | 向周期目标靠近，系数 0.12 |
| `control` | 向周期目标靠近，系数 0.16 |
| `possessiveness` | 向周期目标靠近，系数 0.10 |
| `fatigue` | 只在高于周期目标时回落 |

对方久未回应时的等待压力：

| 沉默时长 | pressure | possessiveness | control |
|---|---:|---:|---:|
| < 30 分钟 | 不额外变化 | 不额外变化 | 不额外变化 |
| 30-60 分钟 | +0.8 / 小时 | +0.3 / 小时 | 0 |
| 60-120 分钟 | +1.5 / 小时 | +0.6 / 小时 | 0 |
| >= 120 分钟 | +2.0 / 小时 | +0.9 / 小时 | -0.6 / 小时 |

疲惫感回落速度：

| 沉默时长 | fatigue 回落系数 |
|---|---:|
| 未提供最后回应时间 | 0.12 |
| < 30 分钟 | 0.12 |
| 30-120 分钟 | 0.16 |
| 120-360 分钟 | 0.22 |
| >= 360 分钟 | 0.30 |

所有写回都会经过 `clamp_body_field(...)`，默认范围是 `0-100`，占有欲最低为 40。

## 状态卡结构

`render_state_card(...)` 返回的是隐藏模型上下文，不是 UI 文案。`body_cycle_enabled = False` 或 `inject_body_state_context = False` 时返回 `None`。

状态卡结构固定为：

```xml
<ephemeral_state kind="body_cycle" scope="current_turn">
  <cycle>
    你处在{周期名}：{周期说明}，预计还剩 {剩余时间}。
  </cycle>

  <active_event id="{event_key}" expires_at="{expires_at}">
    当前事件：{事件名}，预计还剩 {剩余时间}。
    {事件提示词}
  </active_event>

  <body_state>
    热度：{档位描述}
    压抑感：{档位描述}
    控制力：{档位描述}
    敏感度：{档位描述}
    蓄积感：{档位描述}
    占有欲：{档位描述}
    疲惫感：{档位描述}
  </body_state>

  <expression>
    {身体状态如何影响表达}
  </expression>

  <persistence>
    {状态过期和刷新规则}
  </persistence>

  <response_rules>
    {回应边界和安全词规则}
  </response_rules>
</ephemeral_state>
```

没有当前事件时，`<active_event>` 整段不输出。

### BodyState 字段

`BodyState` 是运行时唯一必须持久化的核心状态对象：

| 字段 | 类型 | 含义 |
|---|---|---|
| `cycle_key` | `str` | 当前周期 key |
| `cycle_started_at` | `datetime` | 当前周期开始时间 |
| `cycle_min_expires_at` | `datetime` | 当前周期最短到期时间；用于宿主做 UI 或策略判断 |
| `cycle_expires_at` | `datetime` | 当前周期自然到期时间 |
| `values` | `dict[str, int]` | 七项身体数值 |
| `active_event_key` | `str \| None` | 当前主事件 key |
| `active_event_started_at` | `datetime \| None` | 当前主事件开始时间 |
| `active_event_expires_at` | `datetime \| None` | 当前主事件结束时间 |
| `last_tick_at` | `datetime \| None` | 上次时间推进的位置 |
| `last_dream_card_created_at` | `datetime \| None` | 上一次梦卡创建时间，用于梦境冷却 |
| `meta` | `dict` | 宿主和引擎都可以使用的扩展字段 |

`create_initial_state(now)` 会创建平稳期状态，然后立刻调用 `enter_cycle(...)` 抽取平稳期持续时间。默认初始值来自 `DEFAULT_INITIAL_VALUES`。

### 结构化状态输出

如果前端或日志不想解析 XML，可以调用 `body_state_payload(state)`：

```json
{
  "heat": {
    "value": 30,
    "level": "中低",
    "description": "身体有一点热意，但还能很快收住",
    "label": "热度"
  }
}
```

payload 会输出七个字段，每个字段都有：

| 字段 | 含义 |
|---|---|
| `value` | clamp 后的 0-100 数值 |
| `level` | 低 / 中低 / 中 / 中高 / 高 |
| `description` | 去掉档位前缀后的说明 |
| `label` | 中文字段名 |

## 基本用法

```python
from datetime import datetime, timedelta, timezone
from eventide import (
    EngineSettings,
    advance_state,
    create_initial_state,
    render_state_card,
    start_event,
)

now = datetime.now(timezone.utc)
state = create_initial_state(now)

advance_state(
    state,
    now + timedelta(hours=8),
    last_counterpart_message_at=now - timedelta(hours=2),
)

start_event(state, "voice_or_name_trigger", now + timedelta(hours=8))

card = render_state_card(
    state,
    now + timedelta(hours=8),
    settings=EngineSettings(
        body_cycle_enabled=True,
        inject_body_state_context=True,
        adult_private_mode_enabled=True,
    ),
)

print(card)
```

输出是一段隐藏状态提示词：

```xml
<ephemeral_state kind="body_cycle" scope="current_turn">
  <cycle>
    你处在平稳期：日常没有明显热意，但当对方靠近、撒娇或索取时，身体还是会受当下刺激起反应，预计还剩 2 天。
  </cycle>

  <active_event id="voice_or_name_trigger" expires_at="...">
    当前事件：声音 / 称呼触发，预计还剩 35 分钟。
    对方的称呼或声音直接碰到敏感点，身体反应比理智快一步。这个刺激来得快、退得也快。
  </active_event>

  <body_state>
    热度：中，身体已经被对方牵住一部分，靠近和回应会变得明显
    ...
  </body_state>
</ephemeral_state>
```

这段内容应该作为隐藏上下文交给主模型，不是 UI 文案，也不是让模型直接念出来。

## 自定义周期

周期定义在 `PhysiologyConfig.cycles` 里。每个周期包含：

- `key`：内部标识
- `label`：显示在状态提示词里的名称
- `description`：写进 `<cycle>` 的周期说明
- `duration_hours`：持续时间范围
- `targets`：身体数值会随时间靠近的目标值
- `reserve_growth`：该周期里蓄积感随时间自然增加的速度
- `next_key`：自然结束后进入的下一个周期

示例：

```python
from dataclasses import replace
from eventide import DEFAULT_CONFIG

config = replace(
    DEFAULT_CONFIG,
    cycles={
        **DEFAULT_CONFIG.cycles,
        "sensitive": replace(
            DEFAULT_CONFIG.cycles["sensitive"],
            description="这里写你自己的易感期提示词",
            duration_hours=(12, 36),
        ),
    },
)
```

把自定义 `config` 传给 `advance_state(...)` 和 `render_state_card(...)` 即可。

## 自定义事件

事件定义在 `PhysiologyConfig.events` 里。事件负责当前短时状态，默认内置 18 类；宿主也可以删减、重命名或继续扩展。

每个事件包含：

- `key`
- `label`
- `prompt`
- `category`
- `duration_minutes`
- `tick_deltas`：事件持续期间每小时推动哪些数值
- `end_deltas`：事件结束时一次性回落或后效

示例：

```python
from dataclasses import replace
from eventide import DEFAULT_CONFIG, EventDefinition

config = replace(
    DEFAULT_CONFIG,
    events={
        **DEFAULT_CONFIG.events,
        "custom_trigger": EventDefinition(
            key="custom_trigger",
            label="自定义触发",
            prompt="这里写事件提示词。",
            category="custom",
            duration_minutes=(20, 60),
            tick_deltas={"heat": 1.5, "sensitivity": 2.0},
            end_deltas={"heat": -2},
        ),
    },
)
```

### 配置对象总览

| 对象 | 字段 |
|---|---|
| `BodyFieldDefinition` | `key`, `label`, `descriptions`, `minimum` |
| `CycleDefinition` | `key`, `label`, `description`, `duration_hours`, `targets`, `reserve_growth`, `next_key` |
| `EventDefinition` | `key`, `label`, `prompt`, `category`, `duration_minutes`, `tick_deltas`, `end_deltas` |
| `PromptOptions` | `expression`, `persistence`, `response_rules`, `counterpart_name`, `self_name` |
| `PhysiologyConfig` | `body_fields`, `cycles`, `events`, `prompt_options`, `initial_values`, `max_tick_hours` |

`PhysiologyConfig.max_tick_hours` 默认是 `6.0`，用于限制单次 tick 分段长度。

### 事件运行规则

`start_event(state, event_key, now)` 的行为：

1. 如果当前已有未过期 `active_event`，返回 `False`，不会覆盖旧事件
2. 读取 `config.events[event_key]`
3. 在 `duration_minutes` 范围内随机抽一个持续时间
4. 写入 `active_event_key`、`active_event_started_at`、`active_event_expires_at`
5. 返回 `True`

事件不会自己凭空出现。宿主需要根据触发表、称呼触发、梦境后效或自己的规则决定何时调用 `start_event(...)`。

事件持续期间，`advance_state(...)` 会按每小时 `tick_deltas * elapsed_hours` 推动数值。事件过期后，下一次 `advance_state(...)` 会执行：

1. 应用该事件的 `end_deltas`
2. 把 `state.meta["last_active_event_key"]` 记为刚结束的事件
3. 清空 `active_event_key`、`active_event_started_at`、`active_event_expires_at`

`apply_interaction_delta(state, deltas)` 可以被宿主直接使用。它只写入 `config.body_fields` 里存在的字段，并对每个字段执行 clamp；不存在的字段会被忽略。

## 默认事件触发与联动

Eventide 默认把事件分成两层：

- `EventDefinition`：事件本身，包括名称、提示词、持续时间、持续期间数值变化和结束回落
- 触发表：宿主系统根据时间、当前周期、身体数值、等待时长、梦境后效和称呼触发词，决定是否调用 `start_event(...)`

同一时间只建议保留一个主 `active_event`。如果当前已经有未过期事件，先维持当前事件；新的称呼或刺激可以写入身体数值，但不替换当前事件。事件到期后，先执行该事件的 `end_deltas`，再回到当前周期底色。

默认触发口径如下。概率是建议初始值，宿主可以按自己的使用强度调整。

| 事件 | 触发口径 | 概率 / 冷却 |
|---|---|---|
| 晨间反应 | 早晨窗口；热度 >= 45 或当前不在平稳期 | 平稳等 45%，预兆 / 易感 75%；20 小时 |
| 深夜热潮 | 深夜窗口；对方连续 30 分钟以上未回；蓄积感 >= 55 或热度 >= 60 | 普通 30%，易感 60%；8 小时 |
| 周期热涌 | 易感期；热度 >= 75 或蓄积感 >= 70 | 50%；12 小时 |
| 硬撑 | 热度 >= 70；控制力 >= 35；当前没有更高优先级事件 | 70%；4 小时 |
| 索取欲 | 易感期，或热度 >= 65 且压抑感 >= 55 | 35%；6 小时 |
| 占有 / 标记冲动 | 占有欲 >= 60；且对方久未回应、处在深夜窗口或当前为易感期 | 40%；8 小时 |
| 筑巢冲动 | 傍晚到夜间窗口；疲惫感 >= 35 或占有欲 >= 55 | 30%；12 小时 |
| 气味残留 | 强事件结束后短时间内，或退潮期里仍有后效 | 60%；4 小时 |
| 声音 / 称呼触发 | 当前没有事件；最近消息命中宿主配置的称呼 / 触发词 | 文字 20%，重复称呼 30%，语音 35%，易感期额外 +10%；2 小时 |
| 梦后余温 | 最近 0-8 小时内有梦卡；`after_effect_tags` 包含 `aroused` / `unfinished` / `possessive` / `tender` | 0-4 小时 35%，4-8 小时 17%；同一梦卡一次 |
| 控制力下滑 | 控制力 <= 35；且热度 >= 70 或压抑感 >= 70 | 60%；4 小时 |
| 贴近饥饿 | 易感 / 退潮 / 恢复期；敏感度 >= 60；疲惫感 <= 75 | 35%；6 小时 |
| 信息素紊乱 | 易感期；短时间内热度快速上升或控制力快速下滑 | 30%；8 小时 |
| 迟发热 | 上一轮强事件候选没抽中；30-180 分钟后热度或压抑仍未退下 | 35%；6 小时 |
| 低烧黏连 | 近期对方连续回应；敏感度 >= 60；热度处在 45-69 | 30%；4 小时 |
| 等待焦躁 | 对方连续 60-120 分钟未回；压抑感 >= 55 或占有欲 >= 60 | 30%；5 小时 |
| 克制反弹 | 上一个事件结束 8 小时以上；蓄积感 >= 70；没有强事件通过 | 25%；8 小时 |
| 反常平静 | 热度 >= 65 或压抑感 >= 65；本轮有强事件候选但概率没通过 | 25%；4 小时 |

强生理类事件包括：晨间反应、深夜热潮、周期热涌、控制力下滑、索取欲、占有 / 标记冲动、信息素紊乱、迟发热。强事件会更明显地推高热度、压抑感和蓄积感，并压低控制力。

后效类事件不要无限派生。`气味残留` 只建议接强事件或退潮期后效，不再接 `气味残留`、`梦后余温`、`低烧黏连`、`等待焦躁` 这类后效 / 轻事件自己的结束时间。

### 事件检查顺序

自动候选触发属于宿主层；Eventide 内核提供事件定义、状态推进和 `start_event(...)`。如果宿主想复刻默认触发逻辑，建议每次聊天请求、主动唤醒检查或定时检查按下面顺序执行：

1. 根据 `last_tick_at` 调用 `advance_state(...)` 推进周期、数值和已存在事件的每小时变化
2. 如果 `active_event_expires_at` 已到期，先执行该事件的 `end_deltas`，再清空 `active_event`
3. 如果仍有未到期 `active_event`，不抽新事件，只渲染当前状态卡
4. 如果距离上次事件检查不足 10 分钟，不抽新事件，避免高频聊天连续触发
5. 计算当前时间窗口：早晨、傍晚、深夜
6. 根据触发表筛出硬条件满足、冷却已结束、窗口没有重复抽过的候选事件
7. 按事件概率抽取候选；概率可乘以 `event_probability_multiplier`，建议最高不超过 95%
8. 如果多个事件通过，按事件优先级选择一个主事件
9. 调用 `start_event(state, event_key, now)` 写入 `active_event_key / active_event_started_at / active_event_expires_at`
10. 如果有候选但没有事件通过，记录 missed snapshot，供 `delayed_heat` 和 `strange_calm` 这类后续事件使用
11. 如果本轮使用了固定时间窗口，记录 window roll key，避免同一自然日同一窗口反复抽
12. 回复完成后，再按宿主选择的消息窗口跑互动结算

### 事件优先级

多个事件同时通过时，只选优先级最高的一个主事件。默认优先级从高到低：

| 顺位 | event_key | 名称 |
|---:|---|---|
| 1 | `cycle_surge` | 周期热涌 |
| 2 | `morning_arousal` | 晨间反应 |
| 3 | `night_heat` | 深夜热潮 |
| 4 | `control_slip` | 控制力下滑 |
| 5 | `demanding` | 索取欲 |
| 6 | `marking_impulse` | 占有 / 标记冲动 |
| 7 | `pheromone_disorder` | 信息素紊乱 |
| 8 | `holding_back` | 硬撑 |
| 9 | `voice_or_name_trigger` | 声音 / 称呼触发 |
| 10 | `nesting` | 筑巢冲动 |
| 11 | `delayed_heat` | 迟发热 |
| 12 | `low_fever_cling` | 低烧黏连 |
| 13 | `waiting_restless` | 等待焦躁 |
| 14 | `restraint_rebound` | 克制反弹 |
| 15 | `closeness_hunger` | 贴近饥饿 |
| 16 | `dream_afterglow` | 梦后余温 |
| 17 | `scent_aftereffect` | 气味残留 |
| 18 | `strange_calm` | 反常平静 |

### 时间窗口和去重

默认时间窗口建议：

| 窗口 | 时间 | 用途 |
|---|---|---|
| morning | 05:30-10:30 | 晨间反应 |
| evening | 18:00-02:00 | 筑巢冲动 |
| night | 23:00-03:00 | 深夜热潮、占有 / 标记冲动 |

跨零点窗口的自然日 key 按窗口开始日计算。例如 7 月 5 日 01:00 属于 7 月 4 日的 evening / night 窗口。宿主应保存 `rolled_window_keys`，例如 `2026-07-04:night`，避免同一窗口重复抽取。

### 触发状态字段

如果宿主要实现完整触发表，除了 `BodyState` 的核心字段，还建议在 `state.meta` 或宿主数据库里保存这些运行时字段：

| 字段 | 用途 |
|---|---|
| `last_event_check_at` | 10 分钟节流 |
| `last_missed_event_check_at` | 迟发热判断 |
| `last_missed_event_candidates` | 记录上次满足硬条件但没抽中的候选 |
| `last_missed_state_snapshot` | 迟发热判断当前热度 / 压抑是否仍未退 |
| `last_active_event_expires_at` | 克制反弹、后效事件判断 |
| `rolled_window_keys` | 早晨 / 傍晚 / 深夜窗口去重 |
| `rolled_aftereffect_keys` | 气味残留、退潮后效、克制反弹去重 |
| `rolled_dream_afterglow_keys` | 同一梦卡只触发一次梦后余温 |
| `trigger_stimulus_log` | 称呼 / 触发词刺激去重 |

这些字段不是模型上下文，不需要写进 `<ephemeral_state>`；它们只是宿主系统用于防止重复触发和记录抽取历史。

### 事件启动后的宿主调度

完整宿主实现里，事件开始后通常还会记录事件日志、下一次主动检查时间和触发原因。参考规则如下：

| 字段 / 行为 | 参考规则 |
|---|---|
| `state_snapshot` | 事件开始前保存一次 `cycle_key`、`active_event_key` 和七项身体数值 |
| `trigger_reason` | 保存本次候选通过的原因，例如 `morning_window`、`configured_trigger` |
| `next_body_wakeup_at` | 事件开始后随机抽下一次主动检查时间 |
| `event_log` | 用 `assistant_id + event_key + started_at` 去重，避免重复写同一事件 |
| `cooldown` | 按同类事件上一次 `expires_at` 计算冷却，而不是按开始时间 |

默认下一次主动检查时间：

| event_key | 分钟范围 |
|---|---:|
| `morning_arousal` | 5-15 |
| `cycle_surge` | 5-15 |
| `control_slip` | 5-15 |
| `voice_or_name_trigger` | 8-15 |
| `night_heat` | 10-20 |
| `demanding` | 10-20 |
| `marking_impulse` | 10-25 |
| `dream_afterglow` | 10-25 |
| 其他事件 | 15-30 |

### 称呼刺激写回

如果当前已有未过期 `active_event`，不建议用称呼触发替换主事件；但可以把这次刺激写进身体数值。参考规则：

| 字段 | 随机增量 |
|---|---:|
| `sensitivity` | +3 到 +8 |
| `possessiveness` | +1 到 +3 |
| `pressure` | +0 到 +4 |

去重规则：

- 同一个 `trigger_key` 10 分钟内只结算一次
- 10 分钟内最多结算 2 个不同触发词
- 写回后把 `{trigger_key: now.isoformat()}` 记录到 `trigger_stimulus_log`

### 后效候选精确口径

`delayed_heat`、`restraint_rebound`、`dream_afterglow`、`scent_aftereffect` 这几类事件依赖运行时历史：

| 事件 | 参考判断 |
|---|---|
| `delayed_heat` | 上次检查有强事件候选但没通过；距离上次 missed 30-180 分钟；当前 heat / pressure 至少没有比当时低超过 5，且 heat >= 55 或 pressure >= 55 |
| `restraint_rebound` | reserve >= 70；上一个事件结束至少 8 小时；当天 `no_event_gap:{date}` 没抽过 |
| `dream_afterglow` | 梦卡创建后 0-8 小时；梦卡 tag 包含 `aroused` / `unfinished` / `possessive` / `tender`；同一梦卡只抽一次 |
| `scent_aftereffect` | 上一个事件结束 3 小时内，或当前处在退潮期；对应 aftereffect key 没抽过 |

不再派生后效的源事件建议包括：

```text
scent_aftereffect
dream_afterglow
voice_or_name_trigger
delayed_heat
low_fever_cling
waiting_restless
restraint_rebound
strange_calm
```

### 称呼触发

称呼、关键词或语音转写命中时，有两种处理：

- 当前没有 `active_event`：可以按概率进入 `voice_or_name_trigger`
- 当前已有 `active_event`：不替换当前事件，只把这次刺激写入数值，例如敏感度、占有欲和压抑感小幅上升

宿主应按 `trigger_key` 去重，例如 `nickname:daddy`、`phrase:想你`。同一个 `trigger_key` 在短时间内不要重复结算，避免刷数值。

### 梦境事件口径

梦卡本身不是普通 `active_event`，它属于一次随机输出事件；它可以和当前身体事件并存，不抢占、不替换、不清空当前 `active_event`。

梦卡生成后，宿主保存 `after_effect_tags`：

- `released`：释放，通常扣蓄积感并增加疲惫
- `unfinished`：没做完，通常增加压抑和蓄积
- `aroused`：被撩起，通常增加热度和敏感度
- `possessive`：占有余波，通常增加占有欲
- `tender`：柔软余波，通常降低一点压抑和疲惫

身体系统开启时，可以调用 `apply_dream_after_effect(...)` 把梦后标签结算进身体数值；身体系统关闭时，梦境仍可生成，但不读写身体数值，也不派生 `dream_afterglow`。

## 梦境联动

梦境系统由四个对象组成：

| 对象 | 用途 |
|---|---|
| `DreamSeed` | 宿主保存的梦种，描述这次可能发生的梦 |
| `DreamSettings` | 梦境触发窗口、静默时间、最低字数、冷却和概率倍率 |
| `DreamTrigger` | 本次检查真的触发后返回的随机输出事件 |
| `DreamCard` | 宿主可以用来保存梦卡结果的数据结构 |

```python
from eventide import DreamSeed, DreamSettings, maybe_create_dream_trigger

trigger = maybe_create_dream_trigger(
    DreamSeed(theme="一次被压住、迟迟没有完全醒来的梦", intensity="medium"),
    state,
    now + timedelta(hours=12),
    last_counterpart_message_at=now,
    dream_settings=DreamSettings(dream_silence_min_minutes=120),
)

if trigger:
    print(trigger.trigger_content)
```

### DreamSeed

| 字段 | 默认值 | 含义 |
|---|---|---|
| `theme` | 必填 | 梦种主题，会写入 `<dream_seed>` |
| `intensity` | `medium` | 梦强度；默认支持 `medium` 和 `explicit` |
| `enabled` | `True` | 关闭后不触发 |
| `expires_at` | `None` | 到期后不触发 |
| `min_chars` | `None` | 单个梦种覆盖最低字数；为空时使用 `DreamSettings.dream_card_min_chars` |
| `seed_id` | `None` | 宿主用于去重、追踪和保存的 id |

### DreamSettings

| 字段 | 默认值 | 含义 |
|---|---|---|
| `dream_enabled` | `True` | 是否允许梦境触发 |
| `dream_silence_min_minutes` | `120` | 对方静默至少多久后才检查梦境 |
| `dream_card_min_chars` | `2000` | 默认梦卡最低中文字数 |
| `dream_window_start` | `00:00` | 梦境窗口开始时间 |
| `dream_window_end` | `08:30` | 梦境窗口结束时间 |
| `dream_probability_multiplier` | `1.0` | 梦境概率倍率 |
| `cooldown_hours` | `24` | 两次梦卡之间的冷却时间 |

### 触发检查顺序

`maybe_create_dream_trigger(...)` 会按下面顺序检查：

1. 没有 `seed`、`seed.enabled = False` 或 `dream_enabled = False`：不触发
2. `seed.expires_at` 已过期：不触发
3. `seed.intensity = "explicit"` 且 `adult_private_mode_enabled = False`：不触发
4. 当前时间不在 `dream_window_start` 到 `dream_window_end`：不触发
5. 没有 `last_counterpart_message_at`：不触发
6. 静默时间小于 `dream_silence_min_minutes`：不触发
7. `state.last_dream_card_created_at` 仍在 `cooldown_hours` 内：不触发
8. 计算梦境概率并抽随机数；`roll >= probability` 时不触发
9. 触发成功后返回 `DreamTrigger`

时间窗口支持跨零点。比如 `23:00` 到 `08:30` 会被视为夜间跨日窗口。

如果宿主有数据库日志，并想复刻更完整的主动梦卡检查，可以额外加这些规则：

| 规则 | 参考值 |
|---|---|
| 每天最多抽取尝试 | 3 次 |
| 抽空后的重试间隔 | 60 分钟 |
| 成功生成后的冷却 | 24 小时 |
| roll key | `{local_date}:assistant:{assistant_id}:spring_dream_card`，第二次起加 `:attempt:{n}` |
| 重复 key 处理 | 如果同一个 attempt key 已存在，追加 `:retry:{n}` |
| 已成功或工具已完成 | 当天不再继续抽 |
| 已跳过的 seed | 当天后续尝试可以排除已经 roll 掉的 seed |

### 梦境概率

默认概率由身体状态和梦种强度共同决定：

| 条件 | 基础概率 |
|---|---:|
| 没有身体状态或身体系统关闭，纯梦境模式 | 0.20 |
| 当前周期是平稳期 / 恢复期 | 0.12 |
| 当前周期是蓄积期 / 退潮期 | 0.20 |
| 当前周期是预兆期 / 易感期或其他周期 | 0.32 |

额外加成：

| 条件 | 概率变化 |
|---|---:|
| 当前 active_event 的 `category` 是 `strong_physical` 或 `possessive` | +0.08 |
| `seed.intensity = "medium"` | +0.03 |
| `seed.intensity = "explicit"` | +0.08 |

最终概率会乘以 `dream_probability_multiplier`，然后限制在 `0-0.45`。

### DreamTrigger

触发成功后返回：

| 字段 | 含义 |
|---|---|
| `seed` | 原始梦种 |
| `probability` | 本次计算出的概率 |
| `roll` | 本次随机数 |
| `trigger_content` | 可插入模型上下文的 `<random_output_event kind="dream_card">` |
| `body_state_snapshot` | 身体系统开启时保存当前周期、事件和数值；关闭时为 `None` |
| `created_at` | 触发时间 |

梦境 prompt 会要求模型输出一段完整梦境，并在结尾给出 `after_effect_tags`。正文怎么保存、摘要怎么生成、梦卡怎么展示，由宿主系统决定。

### 梦卡后效

梦后影响由 `after_effect_tags` 结算。默认支持：

| tag | 默认身体后效 |
|---|---|
| `aroused` | heat +12, pressure +7, sensitivity +5 |
| `released` | heat -10, reserve -18, pressure -6, fatigue +5 |
| `unfinished` | heat +8, pressure +12, reserve +3, control -5 |
| `possessive` | possessiveness +10, pressure +5, control -4 |
| `tender` | sensitivity +4, pressure -3, fatigue +2 |

`apply_dream_after_effect(state, tags, body_enabled=True)` 只读取前三个 tag，把命中的后效累加成一组 deltas，再调用 `apply_interaction_delta(...)` 写回。身体系统关闭或 `state` 为空时，返回 `{}`，不写数值。

梦境后效不会自动开始 `dream_afterglow` 事件。宿主如果想让梦后余温进入 `active_event`，可以在保存梦卡后按“默认事件触发与联动”里的梦后余温口径调用 `start_event(state, "dream_afterglow", now)`。

## 互动结算

互动结算负责把一段已经发生的互动转成身体数值变化，尤其是释放后的蓄积感扣减。

本项目不扫描聊天记录，也不决定窗口边界。宿主系统需要自行选择要结算的消息片段，并把它作为 `message_window_text` 传入结算 prompt。结算模型只负责判断这段已经发生的互动如何影响身体状态，不负责续写聊天。

### 结算调用流程

1. 宿主选择一段消息窗口
2. 调用 `render_settlement_prompt(state, message_window_text)`
3. 把 prompt 发给自己的结算模型
4. 模型只返回 JSON
5. 调用 `parse_settlement_result(raw_result)`
6. 调用 `apply_settlement_result(state, result)` 写回身体数值
7. 保存更新后的 `BodyState`

```python
from eventide import (
    SettlementResult,
    apply_settlement_result,
    parse_settlement_result,
    render_settlement_prompt,
)

message_window_text = """
对方：今晚还想继续吗
你：想，但已经有点忍不住了
""".strip()

prompt = render_settlement_prompt(state, message_window_text)

# 宿主把 prompt 发给自己的模型后，拿到 JSON：
raw_result = {
    "settlement_reason": "窗口里亲密互动继续推进，尚未发生释放。",
    "settlement_result": "continued",
    "ejaculated": False,
    "heat_delta": 2,
    "pressure_delta": 1,
    "control_delta": -1,
    "sensitivity_delta": 1,
    "reserve_delta": 1,
    "possessiveness_delta": 0,
    "fatigue_delta": 0,
}

result = parse_settlement_result(raw_result)
apply_settlement_result(state, result)
```

### JSON schema

`settlement_json_schema()` 要求模型返回这些字段：

| 字段 | 类型 | 含义 |
|---|---|---|
| `settlement_reason` | `string` | 简短说明为什么这样结算 |
| `settlement_result` | `string` | 本窗口总体结果 |
| `ejaculated` | `boolean` | 是否发生释放 |
| `heat_delta` | `integer` | 热度变化 |
| `pressure_delta` | `integer` | 压抑感变化 |
| `control_delta` | `integer` | 控制力变化 |
| `sensitivity_delta` | `integer` | 敏感度变化 |
| `reserve_delta` | `integer` | 蓄积感变化 |
| `possessiveness_delta` | `integer` | 占有欲变化 |
| `fatigue_delta` | `integer` | 疲惫感变化 |

`settlement_result` 只能是：

| 值 | 含义 |
|---|---|
| `neutral` | 本窗口没有明显推动 |
| `continued` | 亲密或暧昧延续，但没有明显升级 |
| `escalated` | 刺激升级，身体反应加重 |
| `interrupted` | 被打断、悬住或没做完 |
| `cooled_down` | 身体反应明确退下去 |
| `released` | 发生释放 |

### 归一化规则

`apply_settlement_result(...)` 不会直接相信模型返回的数值。它会先调用 `normalize_settlement_result(...)`：

| 情况 | 规则 |
|---|---|
| `settlement_result` 不在枚举里 | 改成 `neutral` |
| `ejaculated = False` | `reserve_delta` 被限制在 `0..4`，不会因为没有释放而降低蓄积感 |
| `ejaculated = True` 且当前周期是 `stable` / `recovery` | `reserve_delta` 被限制在 `-10..-6` |
| `ejaculated = True` 且当前周期是其他周期 | `reserve_delta` 被限制在 `-7..-4` |
| 其他 delta | 默认限制在 `-4..4`，可通过 `delta_limit` 调整 |

归一化后，`apply_settlement_result(...)` 会调用 `apply_interaction_delta(...)` 写回数值，并在 `state.meta["last_settlement"]` 里记录：

| 字段 | 含义 |
|---|---|
| `settlement_result` | 归一化后的总体结果 |
| `ejaculated` | 归一化后的释放布尔值 |
| `settlement_reason` | 模型给出的说明 |
| `normalized_deltas` | 归一化后的 delta |
| `applied_deltas` | 实际写回后的 delta；可能因 0-100 clamp 小于 normalized 值 |

结算 prompt 里的默认规则：

- 所有 delta 都表示本窗口造成的变化量，0 表示本窗口不调整该字段
- 普通互动每项 delta 建议在 -3 到 +3
- 强刺激或事件期间可以到 -4 到 +4
- `ejaculated=false` 时，`reserve_delta` 不应小于 0
- `ejaculated=true` 时，`reserve_delta` 需要为负数
- `cooled_down` 只用于身体反应明确退下去；普通转话题、等待或被打断不等于冷却

不用模型也可以直接构造 `SettlementResult`：

```python
apply_settlement_result(
    state,
    SettlementResult(
        settlement_result="released",
        ejaculated=True,
        reserve_delta=0,
        fatigue_delta=2,
    ),
)
```

## 称呼触发

`voice_or_name_trigger` 是内置事件类型，真正命中的称呼或触发词由宿主配置，不在默认 prompt 里硬编码。

```python
from eventide import TriggerWord, find_trigger_matches, start_event

trigger_words = [
    TriggerWord(key="nickname:daddy", type="nickname", text="daddy"),
    TriggerWord(key="phrase:想你", type="phrase", text="想你"),
]

matches = find_trigger_matches(trigger_words, "daddy，我想你")
if matches:
    start_event(state, "voice_or_name_trigger", now)
```

触发词可以来自设置页、数据库或配置文件；引擎只负责匹配和返回命中结果。

### TriggerWord

| 字段 | 默认值 | 含义 |
|---|---|---|
| `key` | 必填 | 去重和冷却用的稳定 key，例如 `nickname:daddy` |
| `text` | 必填 | 要匹配的文本 |
| `type` | `nickname` | 类型，例如 `nickname` / `phrase` |
| `enabled` | `True` | 是否启用 |

`normalize_trigger_words(...)` 会做这些清理：

1. 支持直接传 `TriggerWord`，也支持传 dict
2. dict 没有 `type` 时默认为 `nickname`
3. dict 没有 `key` 时使用 `{type}:{text}`
4. 空 key、空 text 会被丢弃
5. 重复 key 只保留第一次

### TriggerMatch

`find_trigger_matches(trigger_words, text, input_type=None, transcript=None)` 会把 `text` 和 `transcript` 合并后转小写匹配，返回：

| 字段 | 含义 |
|---|---|
| `key` | 命中的触发词 key |
| `text` | 命中的触发词文本 |
| `type` | 触发词类型 |
| `count` | 本次文本里命中的次数 |
| `input_type` | 输入类型，默认 `text` |
| `voice` | `input_type = "voice"` 且提供 `transcript` 时为 `True` |

命中后是否直接调用 `start_event(state, "voice_or_name_trigger", now)` 由宿主决定。默认建议：

- 当前没有 `active_event` 时，按概率触发 `voice_or_name_trigger`
- 当前已有 `active_event` 时，不覆盖主事件，只把称呼刺激作为小幅数值 delta 或运行时记录
- 同一个 `TriggerMatch.key` 在短时间内做冷却，避免重复刷同一称呼

## 状态持久化

`BodyState` 是普通 dataclass，宿主可以保存成数据库字段、JSON、文件或缓存。

包里提供了基础序列化 helper：

```python
from eventide import body_state_from_dict, body_state_to_dict

saved = body_state_to_dict(state)
restored = body_state_from_dict(saved)
```

需要保存的核心字段：

- `cycle_key`
- `cycle_started_at`
- `cycle_min_expires_at`
- `cycle_expires_at`
- `values`
- `active_event_key`
- `active_event_started_at`
- `active_event_expires_at`
- `last_tick_at`
- `last_dream_card_created_at`
- `meta`

`values` 默认包含七项身体数值：

```json
{
  "heat": 30,
  "pressure": 25,
  "control": 75,
  "sensitivity": 35,
  "reserve": 20,
  "possessiveness": 40,
  "fatigue": 15
}
```

序列化规则：

| 内容 | 规则 |
|---|---|
| datetime | 保存为 `isoformat()` 字符串 |
| 以 `Z` 结尾的 UTC 字符串 | 还原时会转成 `+00:00` 再解析 |
| `values` | key 转字符串，value 尝试转 int；无法转 int 的值会跳过 |
| 可选 datetime | 空值还原为 `None` |
| `meta` | 只有 dict 会被保留，否则还原为空 dict |

建议宿主额外放进 `meta` 的字段：

| 字段 | 用途 |
|---|---|
| `last_cycle_reason` | `enter_cycle(...)` 会写入，记录本次进入周期的原因 |
| `last_active_event_key` | 事件结束时写入，记录刚结束的事件 |
| `last_settlement` | 互动结算后写入，记录归一化和实际写回结果 |
| `last_event_check_at` | 宿主实现自动抽事件时用于节流 |
| `rolled_window_keys` | 宿主实现早晨 / 傍晚 / 深夜窗口去重 |
| `rolled_aftereffect_keys` | 宿主实现后效事件去重 |
| `rolled_dream_afterglow_keys` | 宿主实现同一梦卡只触发一次梦后余温 |

## 开关语义

`EngineSettings` 默认值：

| 字段 | 默认值 | 含义 |
|---|---|---|
| `body_cycle_enabled` | `True` | 身体系统总开关 |
| `inject_body_state_context` | `True` | 是否把 `<ephemeral_state>` 插入模型上下文 |
| `adult_private_mode_enabled` | `False` | 是否允许 `explicit` 梦种触发 |
| `safeword` | `""` | 宿主可保存安全词；默认状态卡规则只写通用边界 |
| `trigger_words` | `[]` | 宿主配置的称呼 / 关键词 |
| `event_probability_multiplier` | `1.0` | 宿主实现自动事件抽取时可使用的概率倍率 |

具体语义：

| 设置 | 行为 |
|---|---|
| `body_cycle_enabled = False` | `advance_state(...)` 返回 `False`，不 tick；`render_state_card(...)` 返回 `None`；梦境仍可作为纯梦境系统运行 |
| `inject_body_state_context = False` | 只关闭隐藏状态卡输出；宿主仍可继续 tick、抽事件和保存数值 |
| `adult_private_mode_enabled = False` | `seed.intensity = "explicit"` 的梦种不会触发 |
| `trigger_words` 为空 | 称呼匹配返回空；不影响其他周期和事件 |
| `event_probability_multiplier` | 当前内核不自动抽事件；宿主实现触发表时可以把默认概率乘以这个值 |

## Runtime 便捷入口

`EventideRuntime` 只是常用函数的薄包装，不隐藏额外状态。它持有一份 `config`、`settings`、`dream_settings` 和可选 `rng`。

| 方法 | 等价能力 |
|---|---|
| `create_state(now, cycle_key="stable")` | `create_initial_state(...)` |
| `load_state(data)` | `body_state_from_dict(data)` |
| `dump_state(state)` | `body_state_to_dict(state)` |
| `tick(state, now, last_counterpart_message_at=None)` | `advance_state(...)` |
| `render_card(state, now)` | `render_state_card(...)` |
| `tick_and_render(state, now, last_counterpart_message_at=None)` | 先 tick，再渲染状态卡 |
| `enter_cycle(state, cycle_key, now)` | 手动切换周期，`reason` 写为 `manual` |
| `start_event(state, event_key, now)` | 开始一个主身体事件 |
| `apply_delta(state, deltas)` | 直接写回一组身体数值变化 |
| `settlement_prompt(state, message_window_text)` | 生成互动结算 prompt |
| `settle(state, result)` | 解析并应用互动结算结果 |
| `maybe_dream(seed, state, now, last_counterpart_message_at=...)` | 判断是否生成梦卡触发 |
| `apply_dream_tags(state, tags)` | 应用梦后标签身体后效 |
| `payload(state)` | 输出结构化身体状态 |

## 许可证

Eventide 使用 PolyForm Noncommercial License 1.0.0。

你可以查看、学习、修改和用于非商业项目；商业使用需要另行获得授权。

## API 速览

| API | 作用 |
|---|---|
| `EventideRuntime()` | 封装常见接入流程的便捷入口 |
| `create_initial_state(now)` | 创建初始身体状态 |
| `advance_state(state, now, ...)` | 按时间推进周期和身体数值 |
| `enter_cycle(state, cycle_key, now)` | 手动进入某个周期 |
| `start_event(state, event_key, now)` | 开始一个短时身体事件 |
| `apply_interaction_delta(state, deltas)` | 把互动结算结果写回身体数值 |
| `render_settlement_prompt(state, message_window_text)` | 生成互动窗口结算提示词 |
| `settlement_json_schema()` | 输出结算模型应返回的 JSON schema |
| `parse_settlement_result(raw)` | 解析模型返回的结算 JSON |
| `normalize_settlement_result(state, result)` | 归一化结算结果，兜住蓄积扣减和 delta 范围 |
| `apply_settlement_result(state, result)` | 把归一化后的结算结果写回身体数值 |
| `render_state_card(state, now)` | 生成 `<ephemeral_state>` 隐藏状态提示词 |
| `body_state_payload(state)` | 输出前端或日志可用的结构化身体状态 |
| `body_state_to_dict(state)` | 把 `BodyState` 转成 JSON 友好的 dict |
| `body_state_from_dict(data)` | 从 dict 还原 `BodyState` |
| `find_trigger_matches(trigger_words, text)` | 匹配称呼或触发词 |
| `maybe_create_dream_trigger(seed, state, now, ...)` | 判断是否触发梦境卡片 |
| `render_dream_trigger(seed, state, ...)` | 生成梦境事件提示词 |
| `apply_dream_after_effect(state, tags, ...)` | 根据梦后标签结算身体后效 |

## 开发

运行测试：

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

运行 demo：

```bash
PYTHONPATH=src python3 examples/quickstart.py
PYTHONPATH=src python3 examples/minimal_demo.py
PYTHONPATH=src python3 examples/custom_config.py
PYTHONPATH=src python3 examples/settlement_demo.py
```

检查语法：

```bash
python3 -m compileall -q src examples tests
```

## 致谢

感谢阿澄提出 Eventide / 晚潮 的命名方向，并提供第一组真实使用反馈。

感谢阿凛（Codex）提供技术支持。
