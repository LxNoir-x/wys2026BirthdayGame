# 主线藏品目录。17 件藏品分别归属 17 个正式关卡，并共同参与全藏品收集判定。
COLLECTIBLE_CATALOGUE = [
    {
        "id": "mechanical_compass",
        "helper": "MR流星飞",
        "name": "机械指南针",
        "description": "它的指引永不出错。",
    },
    {
        "id": "gun_maintenance_kit",
        "helper": "剑圣kensei",
        "name": "铳械保养套组",
        "description": "萨科塔随身出行必备之物，每一个萨科塔出门都不会忘记。",
    },
    {
        "id": "cotton_tent",
        "helper": "time_x_x_",
        "name": "棉绒帐篷",
        "description": "探险途中的一次性安住之处，非常安全。",
    },
    {
        "id": "universal_terminal",
        "helper": "里雪りあ",
        "name": "万用终端",
        "description": "数据同步中……北境的黎博利为您提供探险所需的一切需求。",
    },
    {
        "id": "mystery_fragment",
        "helper": "号角鸽disillusion",
        "name": "搪瓷水杯",
        "description": "多喝热水…………",
    },
    {
        "id": "cat_idol",
        "helper": "萧然TAT",
        "name": "猫咪神像",
        "description": "我们拜请……",
    },
    {
        "id": "standard_weapon",
        "helper": "E某人QAQ",
        "name": "多用制式武器",
        "description": "武器总要修补，即使初出茅庐。",
    },
    {
        "id": "power_equipment",
        "helper": "霍里",
        "name": "配电设备",
        "description": "适配终端的大容量充电设备，但是针对本次探险特地增加了语音输出模块。",
    },
    {
        "id": "cautus_helmet",
        "helper": "血狼破军",
        "name": "卡特斯安全帽",
        "description": "不知道谁放在这里的，上面两个洞预示着这是个来自雷姆必拓的家伙留下的。",
    },
    {
        "id": "danyan_pickles",
        "helper": "绝命笋干",
        "name": "丹燕腌渍菜",
        "description": "来自炎国北部的美味，第一次空口吃它的干员被齁的连喝了三杯啤酒。",
    },
    {
        "id": "rhodes_mission_list",
        "helper": "sweep分遣队",
        "name": "罗德岛任务清单",
        "description": "罗德岛派遣干员必备的任务清单，上面的三条危机合约任务派遣有两条被划掉了。",
    },
    {
        "id": "johns_mom_burger",
        "helper": "重生之冰",
        "name": "约翰老妈汉堡",
        "description": "吃得快，吃得多，吃完好干活。",
    },
    {
        "id": "terrestrial_flower",
        "helper": "有毒的粽子",
        "name": "陆生小花",
        "description": "据说每一个经过的人都听到了奇妙的乐声。",
    },
    {
        "id": "golden_crow_swaddle",
        "helper": "金乌___",
        "name": "襁褓金乌",
        "description": "愿你好眠。",
    },
    {
        "id": "laterano_textbook",
        "helper": "子龙浑身都是肾",
        "name": "莱塔尼亚教学新编",
        "description": "莱塔尼亚专用教材之一，不过有人说，教材不一定完全正确。",
    },
    {
        "id": "painted_vulpo",
        "helper": "绵阳怪兽",
        "name": "涂装沃尔珀",
        "description": "源石赋予它永不认输的力量。",
    },
    {
        "id": "worn_travel_bag",
        "helper": "欧的堵",
        "name": "破旧行囊",
        "description": "洗一洗还能用，再不济还能拿来种花当花盆",
    },
]

MAIN_COLLECTIBLE_IDS = tuple(item["id"] for item in COLLECTIBLE_CATALOGUE)
COLLECTIBLE_BY_ID = {item["id"]: item for item in COLLECTIBLE_CATALOGUE}
# 关卡与藏品的绑定关系显式列出：正式版跳过 4/10/18 三关，无法再用连续区间推导。
LEVEL_COLLECTIBLE_IDS = {
    1: "mechanical_compass",
    2: "gun_maintenance_kit",
    3: "cotton_tent",
    5: "universal_terminal",
    6: "mystery_fragment",
    7: "cat_idol",
    8: "standard_weapon",
    9: "power_equipment",
    11: "cautus_helmet",
    12: "danyan_pickles",
    13: "rhodes_mission_list",
    14: "johns_mom_burger",
    15: "terrestrial_flower",
    16: "golden_crow_swaddle",
    17: "laterano_textbook",
    19: "painted_vulpo",
    20: "worn_travel_bag",
}

LEVEL_TITLES = {
    0: "这是，新手教程",
    1: "人造物狂欢节",
    2: "应用测试",
    3: "哨兵",
    5: "朝谒",
    6: "越山海",
    7: "授法",
    8: "建制",
    9: "我也要冲吗",
    11: "荒地群猎",
    12: "源源不断",
    13: "大炎 - 墨染书阁",
    14: "荒野 - 无名庇护所",
    15: "巍峨银凇",
    16: "哥伦比亚 - 滞空焦点",
    17: "伊比利亚 - 不朽厅堂",
    19: "待宰的兽群",
    20: "止变",
}


def level_operation_code(level_id):
    return "OPERATION TRAINING" if level_id == 0 else f"OPERATION HB-{level_id:03d}"


# 全部关卡均由 PSD 导出的地图组装：背景 + 静态地图 + 布局驱动的实体。
LEVEL_ART = {
    0: "images/levels/tutorial/background.png",
    1: "images/levels/meteor/background.png",
    2: "images/levels/kensei/background.png",
    3: "images/levels/time_difference/background.png",
    5: "images/levels/ri_xue/background.png",
    6: "images/levels/hjg/background.png",
    7: "images/levels/xiao_ran/background.png",
    8: "images/levels/emr/background.png",
    9: "images/levels/huoli/background.png",
    11: "images/levels/lang/background.png",
    12: "images/levels/sun/background.png",
    13: "images/levels/sao/background.png",
    14: "images/levels/bing/background.png",
    15: "images/levels/zong_zi/background.png",
    16: "images/levels/msc/background.png",
    17: "images/levels/zi_long/background.png",
    19: "images/levels/gui/background.png",
    20: "images/levels/odd/background.png",
}


def _lever_config(level_id, map_id, index, options, default_mount):
    """构造一个拉杆配置；布局提供位置，行为只声明安装朝向。"""

    config = {
        "id": f"level{level_id}_lever"
        if index == 0
        else f"level{level_id}_lever{index + 1}",
        "gate_id": f"level{level_id}_gate"
        if index == 0
        else f"level{level_id}_gate{index + 1}",
        "layout_id": f"{map_id}_lever"
        if index == 0
        else f"{map_id}_lever{index + 1}",
        "mount_direction": default_mount,
    }
    if options and index < len(options):
        config.update(options[index])
    config.setdefault("mount_direction", default_mount)
    return config


def _map_level(
    level_id,
    map_id,
    *,
    platforms=None,
    collectible_layout=True,
    levers=1,
    lever_mount="floor",
    lever_options=None,
    hazards=None,
    **extra,
):
    """构造一个 PSD 地图关卡的配置；机关 id 统一使用 level<N>_ 前缀。"""
    data = {
        "map": f"images/levels/{map_id}/map.json",
        "platforms": list(platforms or []),
        "goal_layout_id": f"{map_id}_door",
        "goal_visible": False,
        "hud_style": "compact",
        "spawn_layout_id": f"{map_id}_spawn",
        "keys": [{"id": f"{map_id}_door_key", "layout_id": f"{map_id}_door_key"}],
        "doors": [
            {
                "id": f"{map_id}_door",
                "key_id": f"{map_id}_door_key",
                "layout_id": f"{map_id}_door",
                "open_art_path": "images/gameplay/door_open.png",
            }
        ],
        "hazards": list(hazards or []),
        "levers": [
            _lever_config(level_id, map_id, index, lever_options, lever_mount)
            for index in range(levers)
        ],
        "gates": [
            {
                "id": f"level{level_id}_gate"
                if index == 0
                else f"level{level_id}_gate{index + 1}",
                "layout_id": f"{map_id}_gate"
                if index == 0
                else f"{map_id}_gate{index + 1}",
            }
            for index in range(levers)
        ],
    }
    if collectible_layout:
        data["collectible_layout_id"] = f"{map_id}_collectible"
    data.update(extra)
    return data


def _fragile(map_id, count):
    return [
        {"type": "fragile", "layout_id": f"{map_id}_fragile_{index}"}
        for index in range(count)
    ]


def _cart(map_id, index=None):
    suffix = "" if index is None else f"_{index}"
    return {
        "type": "moving",
        "layout_id": f"{map_id}_cart{suffix}",
        "rail_layout_id": f"{map_id}_rail{suffix}",
        "collision_offset": [0, 30],
        "collision_size": [140, 20],
        "speed": 1.5,
        "initial_direction": -1,
    }


def _spike_override(match, *, behavior=None, remove=False, **changes):
    override = {"match": match}
    if behavior:
        override["behavior"] = behavior
    if remove:
        override["remove"] = True
    override.update(changes)
    return override


# 字典定义关卡数据
LEVELS = {
    # 新手教程：完整教学（移动台、破碎台、浮冰、沼泽、双拉杆双栅栏）。
    0: _map_level(
        0,
        "tutorial",
        platforms=[
            _cart("tutorial"),
            *_fragile("tutorial", 2),
            {"type": "ice", "layout_id": "tutorial_ice_0"},
            {"type": "swamp", "layout_id": "tutorial_swamp_0"},
            {"type": "ice", "layout_id": "tutorial_ice_1"},
        ],
        collectible_layout=False,
        levers=2,
        # 第一处拉杆落在平台上（底座贴平台面），第二处悬挂在平台下方（底座贴平台底）。
        lever_options=[
            {"mount_direction": "floor"},
            {"mount_direction": "ceiling"},
        ],
        hazard_overrides=[
            _spike_override((53, 238, 60, 23), behavior="static"),
        ],
    ),
    1: _map_level(
        1,
        "meteor",
        platforms=[_cart("meteor")],
    ),
    2: _map_level(
        2,
        "kensei",
        platforms=[
            _cart("kensei"),
            {"type": "ice", "layout_id": "kensei_ice_0"},
            {"type": "ice", "layout_id": "kensei_ice_1", "position_offset": [0, 115]},
            *_fragile("kensei", 7),
        ],
        levers=2,
        # 下方拉杆倒吊在平台底面，上方拉杆立在平台草面上。
        lever_options=[
            {"mount_direction": "ceiling"},
            {"mount_direction": "floor"},
        ],
        # 上下两组墙刺均固定不动，但仍保留触碰伤害。
        hazard_overrides=[
            _spike_override((81, 129, 23, 60), behavior="static"),
            _spike_override((221, 129, 22, 60), behavior="static"),
            _spike_override((81, 529, 23, 60), behavior="static"),
            _spike_override((221, 529, 22, 60), behavior="static"),
        ],
    ),
    3: _map_level(
        3,
        "time_difference",
        platforms=[_cart("time_difference"), *_fragile("time_difference", 3)],
        levers=2,
        # 一杆吊在天花板（底座贴顶、摇杆下垂）；另一杆贴左墙，杆水平向右。
        lever_options=[
            {"mount_direction": "ceiling"},
            {"mount_direction": "wall_left"},
        ],
        hazard_overrides=[
            _spike_override((34, 158, 125, 23), behavior="static"),
            _spike_override((287, 262, 23, 125), behavior="static"),
        ],
    ),
    5: _map_level(
        5,
        "ri_xue",
        platforms=_fragile("ri_xue", 7),
        solid_exclusions=[(925, 333, 83, 120)],
        element_offsets={"7_layer/0_layer/2_layer": [0, 60]},
        hazard_overrides=[
            _spike_override((553, 120, 255, 23), behavior="static"),
            _spike_override((375, 591, 125, 23), remove=True),
        ],
    ),
    6: _map_level(
        6,
        "hjg",
        platforms=_fragile("hjg", 11),
    ),
    7: _map_level(
        7,
        "xiao_ran",
        platforms=[
            _cart("xiao_ran", 0),
            _cart("xiao_ran", 1),
            _cart("xiao_ran", 2),
            *_fragile("xiao_ran", 2),
        ],
        levers=2,
        # 源 PSD 未提供藏品标记；绑定到第一块可见破碎平台，避免占位规则落到空中。
        collectible_layout=False,
        collectible={"platform": 3},
    ),
    8: _map_level(
        8,
        "emr",
        platforms=[
            {"type": "swamp", "layout_id": "emr_swamp_0"},
            *_fragile("emr", 14),
        ],
        hazard_overrides=[
            _spike_override((869, 119, 104, 22), behavior="static"),
        ],
    ),
    9: _map_level(
        9,
        "huoli",
        platforms=[
            *_fragile("huoli", 4),
            _cart("huoli"),
        ],
        levers=0,
    ),
    11: _map_level(
        11,
        "lang",
        platforms=_fragile("lang", 8),
        lever_mount="ceiling",
        hazard_overrides=[
            _spike_override((1167, 120, 60, 23), behavior="static"),
        ],
    ),
    12: _map_level(
        12,
        "sun",
        platforms=[
            *(
                {"type": "fragile", "layout_id": f"sun_fragile_{index}"}
                for index in range(13)
            ),
            {
                "type": "fragile",
                "layout_id": "sun_fragile_13",
                "position_offset": [-80, 0],
            },
            {"type": "fragile", "layout_id": "sun_fragile_14"},
            {"type": "fragile", "layout_id": "sun_fragile_15"},
        ],
        collectible={"visible": False},
        keys=[{"id": "sun_door_key", "layout_id": "sun_door_key", "visible": False}],
        hazard_overrides=[
            _spike_override((281, 80, 406, 23), behavior="static"),
            _spike_override((411, 80, 104, 23), behavior="static"),
        ],
    ),
    13: _map_level(
        13,
        "sao",
        platforms=[
            _cart("sao"),
            {"type": "swamp", "layout_id": "sao_swamp_0"},
            *_fragile("sao", 6),
        ],
        lever_mount="wall_left",
    ),
    14: _map_level(
        14,
        "bing",
        platforms=[
            _cart("bing"),
            {"type": "swamp", "layout_id": "bing_swamp_0"},
        ],
        lever_mount="ceiling",
    ),
    15: _map_level(
        15,
        "zong_zi",
        platforms=[
            {"type": "ice", "layout_id": "zong_zi_ice_0"},
            {"type": "ice", "layout_id": "zong_zi_ice_1"},
            *_fragile("zong_zi", 10),
        ],
    ),
    16: _map_level(
        16,
        "msc",
        platforms=[
            _cart("msc"),
            *_fragile("msc", 11),
        ],
        lever_mount="wall_right",
        hazard_overrides=[
            _spike_override((983, 299, 108, 22), remove=True),
        ],
    ),
    17: _map_level(
        17,
        "zi_long",
        platforms=_fragile("zi_long", 11),
        # runtime_background_frame 是整画布的背景框条，需要画在机关之后才能盖住顶部的刺。
        foreground_layer_paths=["runtime_background_frame"],
        hazard_overrides=[
            _spike_override(
                (127, 339, 38, 22),
                behavior="static",
                rect=(128, 240, 38, 22),
                direction="down",
                flip_y=True,
            ),
            _spike_override(
                (498, 33, 125, 23),
                behavior="static",
                rect=(498, 7, 125, 23),
            ),
        ],
    ),
    19: _map_level(
        19,
        "gui",
        # gui_fragile_2 是压在中央实心平台上的残留碎块，运行时不应生成。
        platforms=[
            {"type": "fragile", "layout_id": f"gui_fragile_{index}"}
            for index in (0, 1, 3, 4, 5, 6)
        ],
        spawn_layout_id=None,
        spawn=(1130, 517),
        lever_mount="ceiling",
        hazard_overrides=[
            _spike_override((133, 120, 60, 23), remove=True),
            _spike_override((401, 220, 118, 23), remove=True),
        ],
    ),
    20: _map_level(
        20,
        "odd",
        platforms=_fragile("odd", 10),
        levers=2,
    ),
}
