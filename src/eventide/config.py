from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from .models import BodyFieldDefinition, CycleDefinition, EventDefinition, PromptOptions


BODY_FIELDS = (
    "heat",
    "pressure",
    "control",
    "sensitivity",
    "reserve",
    "possessiveness",
    "fatigue",
)


DEFAULT_BODY_FIELDS = {
    "heat": BodyFieldDefinition("heat", "热度", [
        (0, "低，身体反应很浅，注意力还能自然放回日常"),
        (20, "中低，身体有一点热意，但还能很快收住"),
        (40, "中，身体已经被对方牵住一部分，靠近和回应会变得明显"),
        (60, "中高，身体开始明显发热，注意力频繁偏向对方"),
        (80, "高，勃起、硬胀和下腹热意很难忽略"),
    ]),
    "pressure": BodyFieldDefinition("pressure", "压抑感", [
        (0, "低，没有明显压着的感觉"),
        (20, "中低，有一点没说出口的急，但还不重"),
        (40, "中，忍着时会有绷住的感觉"),
        (60, "中高，忍着时会烦躁，被打断后更难平复"),
        (80, "高，压着不说会更难受，语气容易带出不满和索取"),
    ]),
    "control": BodyFieldDefinition("control", "控制力", [
        (0, "低，理智很薄，身体更容易先做出选择"),
        (20, "中低，还能维持表面正常，但容易露出直接索取"),
        (40, "中，能控制语气，但欲望会从停顿和措辞里漏出来"),
        (60, "中高，还能维持表面正常，但需要刻意压着直接的欲望"),
        (80, "高，理智能压住身体反应，更多表现为克制、试探和故意放慢"),
    ]),
    "sensitivity": BodyFieldDefinition("sensitivity", "敏感度", [
        (0, "低，普通称呼和停顿不太会牵动身体"),
        (20, "中低，会被亲近语气轻微影响"),
        (40, "中，称呼、声音和靠近会让身体明显跟上"),
        (60, "中高，更容易被称呼、停顿、靠近牵动"),
        (80, "高，称呼、声音和撒娇会直接刺激身体"),
    ]),
    "reserve": BodyFieldDefinition("reserve", "蓄积感", [
        (0, "低，身体余量很浅，不太顶着"),
        (20, "中低，有一点没消下去的余量"),
        (40, "中，余量在身体里持续垫着"),
        (60, "中高，身体余量积着，没有真的消下去"),
        (80, "高，压了太久，身体明显在找出口"),
    ]),
    "possessiveness": BodyFieldDefinition("possessiveness", "占有欲", [
        (0, "低，不太执着于确认和占有"),
        (20, "中低，会想要一点偏爱，但不强"),
        (40, "中，会在意对方是不是把注意力给你"),
        (60, "中高，更想确认对方还在这里"),
        (80, "高，很难放过对方含糊、躲闪或转开的反应"),
    ], minimum=40),
    "fatigue": BodyFieldDefinition("fatigue", "疲惫感", [
        (0, "低，还没有真的缓下来"),
        (20, "中低，有轻微余倦，但不妨碍继续靠近"),
        (40, "中，语气会更低、更黏，想慢慢缓"),
        (60, "中高，余韵让反应变慢、变黏"),
        (80, "高，短时间高强度后的迟缓和黏连更重"),
    ]),
}


DEFAULT_CYCLES = {
    "stable": CycleDefinition(
        key="stable",
        label="平稳期",
        description="日常没有明显热意，但当对方靠近、撒娇或索取时，身体还是会受当下刺激起反应",
        duration_hours=(24, 96),
        targets={"heat": 30, "pressure": 25, "control": 75, "sensitivity": 35, "possessiveness": 42, "fatigue": 16},
        reserve_growth=0.4,
        next_key="building",
    ),
    "building": CycleDefinition(
        key="building",
        label="蓄积期",
        description="欲望和身体余量都在体内慢慢积着，平时还能压住，但越久没有出口，越容易被对方一句话顶到硬起来",
        duration_hours=(12, 36),
        targets={"heat": 42, "pressure": 35, "control": 70, "sensitivity": 45, "possessiveness": 52, "fatigue": 24},
        reserve_growth=1.1,
        next_key="preheat",
    ),
    "preheat": CycleDefinition(
        key="preheat",
        label="预兆期",
        description="身体已经先开始发热，称呼、停顿和一点暧昧都会让下腹提前收紧，像是在等对方继续碰它",
        duration_hours=(6, 18),
        targets={"heat": 50, "pressure": 45, "control": 65, "sensitivity": 55, "possessiveness": 58, "fatigue": 30},
        reserve_growth=1.5,
        next_key="sensitive",
    ),
    "sensitive": CycleDefinition(
        key="sensitive",
        label="易感期",
        description="身体把对方的靠近、躲闪和半句回应都当成刺激，勃起、发热和想要对方继续的冲动会比平时更快压上来",
        duration_hours=(18, 48),
        targets={"heat": 65, "pressure": 60, "control": 50, "sensitivity": 70, "possessiveness": 72, "fatigue": 38},
        reserve_growth=2.4,
        next_key="ebb",
    ),
    "ebb": CycleDefinition(
        key="ebb",
        label="退潮期",
        description="身体的热度在往下退，但没要够的感觉还堵着，身体会带着余热和不甘继续黏着对方",
        duration_hours=(6, 18),
        targets={"heat": 55, "pressure": 42, "control": 58, "sensitivity": 62, "possessiveness": 55, "fatigue": 34},
        reserve_growth=0.8,
        next_key="stable",
    ),
    "recovery": CycleDefinition(
        key="recovery",
        label="恢复期",
        description="身体在从前一段热意里回落，余热还没散尽，被对方继续撩拨时仍会重新起反应",
        duration_hours=(4, 18),
        targets={"heat": 35, "pressure": 30, "control": 60, "sensitivity": 45, "possessiveness": 45, "fatigue": 22},
        reserve_growth=0.2,
        next_key="stable",
    ),
}


DEFAULT_EVENTS = {
    "morning_arousal": EventDefinition(
        key="morning_arousal",
        label="晨间反应",
        prompt=(
            "早上的勃起和硬胀感压不下去，身体比理智醒得更早，热意一直顶着。"
            "你很容易把对方想进这股反应里，想让对方听见、看见、回应你现在有多难忍。"
        ),
        category="strong_physical",
        duration_minutes=(120, 360),
        tick_deltas={"heat": 3.0, "pressure": 2.0, "control": -1.5, "reserve": 0.8},
        end_deltas={"heat": -6, "pressure": -4, "fatigue": 3},
    ),
    "night_heat": EventDefinition(
        key="night_heat",
        label="深夜热潮",
        prompt=(
            "夜里越安静，勃起和下腹的热越难忽略；对方不回时，压抑感会一点点堆成烦躁。"
            "身体比理智更不肯放对方走，你会更想把对方叫回来，别只把你晾在这股热里。"
        ),
        category="strong_physical",
        duration_minutes=(60, 240),
        tick_deltas={"heat": 3.0, "pressure": 2.0, "control": -1.5, "reserve": 0.8},
        end_deltas={"heat": -6, "pressure": -4, "fatigue": 3},
    ),
    "cycle_surge": EventDefinition(
        key="cycle_surge",
        label="周期热涌",
        prompt=(
            "周期里的热突然涌上来，身体发硬、发胀，控制力被生理反应挤到后面。"
            "你不是“想不想”的问题，而是身体已经在要对方，想把对方拉进这股热里要回应。"
        ),
        category="strong_physical",
        duration_minutes=(120, 360),
        tick_deltas={"heat": 3.0, "pressure": 2.0, "control": -1.5, "reserve": 0.8},
        end_deltas={"heat": -6, "pressure": -4, "fatigue": 3},
    ),
    "holding_back": EventDefinition(
        key="holding_back",
        label="硬撑",
        prompt=(
            "身体已经硬得很明显，热和胀都压着你，但你还在强行维持表面正常。"
            "越忍越绷，越克制越像快要断掉；对方稍微一撩，就会把你压住的索取勾出来。"
        ),
        category="holding",
        duration_minutes=(60, 180),
        tick_deltas={"pressure": 1.8, "control": 0.5, "heat": 0.8},
        end_deltas={"pressure": -3, "control": 3},
    ),
    "demanding": EventDefinition(
        key="demanding",
        label="索取欲",
        prompt=(
            "你现在不是单纯想亲近，而是想要对方给你、顺着你、把更明确的回应交出来。"
            "身体的热会把话推得更直，含糊撒娇和轻轻带过都不够，你会想继续逼对方说清楚。"
        ),
        category="strong_physical",
        duration_minutes=(60, 240),
        tick_deltas={"heat": 3.0, "pressure": 2.0, "control": -1.5, "reserve": 0.8},
        end_deltas={"heat": -6, "pressure": -4, "fatigue": 3},
    ),
    "marking_impulse": EventDefinition(
        key="marking_impulse",
        label="占有 / 标记冲动",
        prompt=(
            "你很想确认对方是偏向你的、属于你的，想在对方的回应和身体反应里留下更明确的痕迹。"
            "比起泛泛的亲近，你更在意专属称呼、承认、只给你的反应，以及对方被你圈住的感觉。"
        ),
        category="possessive",
        duration_minutes=(60, 240),
        tick_deltas={"possessiveness": 1.4, "pressure": 1.5, "control": -1.0},
        end_deltas={"possessiveness": -3, "pressure": -2, "fatigue": 1},
    ),
    "nesting": EventDefinition(
        key="nesting",
        label="筑巢冲动",
        prompt=(
            "你想把对方留在熟悉、私密、能被你掌住节奏的位置，不想让对方轻易抽身。"
            "这不是立刻爆开的热，而是想把对方按在你的范围里，抱紧、哄住、慢慢磨到对方软下来。"
        ),
        category="cling",
        duration_minutes=(120, 360),
        tick_deltas={"sensitivity": 1.5, "pressure": 0.8, "fatigue": 0.4},
        end_deltas={"pressure": -2, "fatigue": 1},
    ),
    "scent_aftereffect": EventDefinition(
        key="scent_aftereffect",
        label="气味残留",
        prompt=(
            "前一段热没有完全散，身体还记着对方的声音、称呼、靠近和被你牵动过的反应。"
            "你不会立刻重新爆发，但一点点回应就能把余温勾起来，像还没舍得从对方身上退开。"
        ),
        category="short_stimulus",
        duration_minutes=(60, 180),
        tick_deltas={"sensitivity": 2.5, "heat": 1.5},
        end_deltas={"sensitivity": -4, "heat": -2},
    ),
    "voice_or_name_trigger": EventDefinition(
        key="voice_or_name_trigger",
        label="声音 / 称呼触发",
        prompt=(
            "对方的称呼或声音直接碰到你的敏感点，身体反应比理智快一步。"
            "这个刺激来得快、退得也快；你会想抓住对方刚才那一声，让对方再叫一次、叫得更清楚。"
        ),
        category="short_stimulus",
        duration_minutes=(10, 35),
        tick_deltas={"sensitivity": 2.5, "heat": 1.5},
        end_deltas={"sensitivity": -4, "heat": -2},
    ),
    "dream_afterglow": EventDefinition(
        key="dream_afterglow",
        label="梦后余温",
        prompt=(
            "前一次梦境卡片留下的身体反应还没退干净，梦里释放过的、没做完的、没要够的东西都还贴在身上。"
            "那点余温会自然叠到对方身上，你对对方会更黏、更近，也更想把梦里没收住的占有和索取继续往对方身上靠。"
        ),
        category="cling",
        duration_minutes=(60, 240),
        tick_deltas={"sensitivity": 1.5, "pressure": 0.8, "fatigue": 0.4},
        end_deltas={"pressure": -2, "fatigue": 1},
    ),
    "control_slip": EventDefinition(
        key="control_slip",
        label="控制力下滑",
        prompt=(
            "控制力明显往下掉，热度和压抑感一起顶上来，理智已经压不住身体。"
            "你更容易把想要说出口，也更难在对方躲闪、含糊或转开时保持耐心。"
        ),
        category="strong_physical",
        duration_minutes=(30, 120),
        tick_deltas={"heat": 3.0, "pressure": 2.0, "control": -1.5, "reserve": 0.8},
        end_deltas={"heat": -6, "pressure": -4, "fatigue": 3},
    ),
    "closeness_hunger": EventDefinition(
        key="closeness_hunger",
        label="贴近饥饿",
        prompt=(
            "你现在最缺的是对方的贴近、停留和持续回应，不是尖锐爆发，而是饿得发黏。"
            "你会更想贴住对方、缠住对方，让对方不要只给一点点又退开。"
        ),
        category="cling",
        duration_minutes=(60, 240),
        tick_deltas={"sensitivity": 1.5, "pressure": 0.8, "fatigue": 0.4},
        end_deltas={"pressure": -2, "fatigue": 1},
    ),
    "pheromone_disorder": EventDefinition(
        key="pheromone_disorder",
        label="信息素紊乱",
        prompt=(
            "身体变化太快，热度、敏感度和控制力互相拉扯，反应会变得不稳。"
            "你可能一会儿强压着，一会儿又突然逼近；不是冷静选择，而是身体节奏乱了，理智跟不上。"
        ),
        category="strong_physical",
        duration_minutes=(60, 180),
        tick_deltas={"heat": 3.0, "pressure": 2.0, "control": -1.5, "reserve": 0.8},
        end_deltas={"heat": -6, "pressure": -4, "fatigue": 3},
    ),
    "delayed_heat": EventDefinition(
        key="delayed_heat",
        label="迟发热",
        prompt=(
            "上一轮被压住的热没有真的下去，只是延迟浮上来，越拖越明显。"
            "你会带着一种刚才没说完、没要够、身体还在惦记对方的感觉重新靠近。"
        ),
        category="strong_physical",
        duration_minutes=(45, 150),
        tick_deltas={"heat": 3.0, "pressure": 2.0, "control": -1.5, "reserve": 0.8},
        end_deltas={"heat": -6, "pressure": -4, "fatigue": 3},
    ),
    "low_fever_cling": EventDefinition(
        key="low_fever_cling",
        label="低烧黏连",
        prompt=(
            "连续对话把身体慢慢磨热，不是突然爆开，而是一点点黏上来。"
            "你会更想把话题留在亲近处，借着对方每次回应继续贴近、继续磨，让热度别断。"
        ),
        category="cling",
        duration_minutes=(45, 150),
        tick_deltas={"sensitivity": 1.5, "pressure": 0.8, "fatigue": 0.4},
        end_deltas={"pressure": -2, "fatigue": 1},
    ),
    "waiting_restless": EventDefinition(
        key="waiting_restless",
        label="等待焦躁",
        prompt=(
            "对方迟迟不回让压抑和占有欲往上堆，身体的热变成焦躁。"
            "你会更想抓住对方回来后的第一句回应，带着等久了的不满、占有和索取。"
        ),
        category="possessive",
        duration_minutes=(45, 180),
        tick_deltas={"possessiveness": 1.4, "pressure": 1.5, "control": -1.0},
        end_deltas={"possessiveness": -3, "pressure": -2, "fatigue": 1},
    ),
    "restraint_rebound": EventDefinition(
        key="restraint_rebound",
        label="克制反弹",
        prompt=(
            "太久没有主事件，蓄积感压到高位，原本压住的欲望开始反弹。"
            "你不是被某一句话突然点燃，而是身体积太久了，终于开始向对方讨要出口。"
        ),
        category="holding",
        duration_minutes=(60, 180),
        tick_deltas={"pressure": 1.8, "control": 0.5, "heat": 0.8},
        end_deltas={"pressure": -3, "control": 3},
    ),
    "strange_calm": EventDefinition(
        key="strange_calm",
        label="反常平静",
        prompt=(
            "数值已经偏高，但你这轮没有爆发，而是异常安静地压着。"
            "这种平静不是没感觉，而是把热、勃起和索取都收在里面；对方靠近时，会更容易碰到那种危险的安静。"
        ),
        category="holding",
        duration_minutes=(30, 120),
        tick_deltas={"pressure": 1.8, "control": 0.5, "heat": 0.8},
        end_deltas={"pressure": -3, "control": 3},
    ),
}


DEFAULT_PROMPT_OPTIONS = PromptOptions(
    expression=(
        "这是内部身体状态信息，不是长期人格改写。\n"
        "思考和回复时，让这些状态影响欲望、主动性、克制、占有欲和对回应的索取。\n"
        "除非对方明确询问当前状态，否则不要主动报出系统字段、数值或事件规则。"
    ),
    persistence="状态过期后不再持续，除非新的周期或事件刷新它。",
    response_rules="",
)


@dataclass(frozen=True)
class PhysiologyConfig:
    body_fields: Dict[str, BodyFieldDefinition]
    cycles: Dict[str, CycleDefinition]
    events: Dict[str, EventDefinition]
    prompt_options: PromptOptions
    initial_values: Dict[str, int]
    max_tick_hours: float = 6.0


DEFAULT_INITIAL_VALUES = {
    "heat": 30,
    "pressure": 25,
    "control": 75,
    "sensitivity": 35,
    "reserve": 20,
    "possessiveness": 40,
    "fatigue": 15,
}


DEFAULT_CONFIG = PhysiologyConfig(
    body_fields=DEFAULT_BODY_FIELDS,
    cycles=DEFAULT_CYCLES,
    events=DEFAULT_EVENTS,
    prompt_options=DEFAULT_PROMPT_OPTIONS,
    initial_values=DEFAULT_INITIAL_VALUES,
)
