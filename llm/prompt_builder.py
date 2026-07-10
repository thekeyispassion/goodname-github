"""
提示词组装器

作用：把用户填的表单信息 + 系统指令 + 格式要求，拼成一段完整的提示词。

这是整个程序最关键的部分——提示词的质量决定取名的质量。
"""
import json
import re


# ========== 字数相关：唯一映射表 ==========
# 所有字数转换都从这里走，避免多处分叉不一致
# 键统一用简洁值，和前端下拉框完全对齐
_NAME_LENGTH_MAP = {
    '2个字': {'chars': 1, 'desc': '名取1个字，全名共2字（如：张磊）', 'short': '名取1个字'},
    '3个字': {'chars': 2, 'desc': '名取2个字，全名共3字（如：张致远）', 'short': '名取2个字'},
    '4个字': {'chars': 3, 'desc': '名取3个字，全名共4字（如：张欧阳明）', 'short': '名取3个字'},
}


def _get_name_char_count(name_length: str, surname: str = "") -> int | None:
    """
    把用户选的总字数转成名取几个字。
    支持容错匹配：'2个字'、'双字'、'2字' 等都能解析。
    如果传了姓氏，按姓氏长度动态计算（兼容复姓）。
    没选返回 None。
    """
    if not name_length:
        return None

    # 第一步：精确匹配
    if name_length in _NAME_LENGTH_MAP:
        return _NAME_LENGTH_MAP[name_length]['chars']

    # 第二步：容错匹配，从字符串中提取数字
    num_match = re.search(r'(\d+)', name_length)
    if num_match:
        total_chars = int(num_match.group(1))
        # 减去姓氏长度得到名字字数（默认单姓1字）
        surname_len = len(surname) if surname else 1
        return max(total_chars - surname_len, 1)  # 至少1个字

    return None


def _get_name_description(name_length: str, mode: str = 'desc') -> str:
    """把用户选的总字数转成提示词中的文字描述。"""
    if not name_length:
        return ''
    if name_length in _NAME_LENGTH_MAP:
        return _NAME_LENGTH_MAP[name_length].get(mode, _NAME_LENGTH_MAP[name_length]['desc'])
    # 容错：直接从数字描述
    num_match = re.search(r'(\d+)', name_length)
    if num_match:
        total = int(num_match.group(1))
        given = total - 1
        return f'名取{given}个字，全名共{total}字'
    return name_length


def _build_format_example(given_chars: int, surname: str = "张") -> str:
    """
    动态生成格式示例，示例中的名字字数精确匹配用户要求。
    given_chars: 名取几个字
    surname: 姓氏（用于 full_name 示例）
    """
    name_placeholder = "某" * given_chars
    full_name = surname + name_placeholder
    meaning_parts = [f"某{i+1}：字义说明" for i in range(given_chars)]
    meaning = "；".join(meaning_parts)

    return f"""
【输出格式】
严格按照以下JSON数组格式输出（不要加markdown代码块标记，直接输出纯JSON）。

[
  {{
    "name": "{name_placeholder}",
    "full_name": "{full_name}",
    "meaning": "{meaning}",
    "cultural_ref": "（可选）名称来源说明",
    "wuxing": "五行属性",
    "sound_rhythm": "音韵分析描述",
    "score": 90
  }}
]

【再次强调·硬性要求】
1. name 字段只能是 {given_chars} 个汉字，不含姓氏
2. full_name = 姓氏 + name，总字数自动对应
3. 字数错误的输出视为无效，请务必先自查再返回
4. 示例中的"某"只是占位，替换成实际名字后字数必须完全一致
"""


def build_initial_prompt(user_input: dict) -> list:
    """
    构建首次取名的提示词。

    参数：
        user_input: 用户填的表单信息字典

    返回一个消息列表，符合 DeepSeek API 的格式：
        [
            {"role": "system", "content": "..."},   # 系统提示（设定AI角色）
            {"role": "user", "content": "..."}      # 用户需求
        ]
    """

    # 提前计算字数，注入系统提示开头（模型对开头内容关注度最高）
    surname = user_input.get('surname', '某')
    given_chars = _get_name_char_count(user_input.get('name_length', ''), surname)
    if given_chars is None:
        given_chars = 2  # 兜底

    # ========== 1. 系统提示词 ==========
    system_prompt = f"""你是一位专业取名大师。

【最高优先级硬性要求】
- 本次生成的名字（不含姓氏）必须是 {given_chars} 个汉字，不能多也不能少
- 全名 = 姓氏 + 名字，总字数自动计算
- 输出前必须逐个检查每个 name 字段的汉字数量，不符合要求不得输出

取名来源可以多样化：诗词典故、自然景色、美好品德、音韵美感、现代寓意等，
不要只局限于经典典籍，避免名字来源过于雷同。

每次返回5个候选名字，每个名字包含：名字本身、字义解析、五行属性、音韵分析。
如有典籍出处可标注（不强求），尽量让5个名字的风格和来源有差异。

要求：
1. 每次返回5个候选名字
2. 每个名字必须包含：名字本身、字义解析、五行属性、音韵分析
3. **典籍出处如有可注明，不是必须的**
4. 输出格式为JSON数组（见下方格式说明）
5. 名字要男女有别，男孩名要阳刚大气，女孩名要温婉柔美
6. 避免使用生僻字、拗口字"""

    # ========== 2. 拼接用户信息 ==========
    user_info = f"【基本信息】\n姓氏：{surname}"
    user_info += f"\n性别：{user_input.get('gender', '未知')}"

    if user_input.get('birth_date'):
        user_info += f"\n出生日期：{user_input['birth_date']}"
    if user_input.get('birth_time'):
        user_info += f"\n出生时辰：{user_input['birth_time']}"

    if user_input.get('name_length'):
        given_name = _get_name_description(user_input['name_length'], 'desc')
        user_info += f"\n名字字数要求：{given_name}"

    if user_input.get('preferences'):
        user_info += f"\n\n【寓意偏好】\n{user_input['preferences']}"
    if user_input.get('avoid_words'):
        user_info += f"\n\n【避讳字】\n避免使用以下字：{user_input['avoid_words']}"
    if user_input.get('cultural_prefs'):
        user_info += f"\n\n【传统文化偏好】\n{user_input['cultural_prefs']}"
    if user_input.get('family_info'):
        user_info += f"\n\n【家庭信息】\n{user_input['family_info']}"

    # ========== 3. 组合成消息列表 ==========
    format_example = _build_format_example(given_chars, surname)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": format_example + "\n\n【用户需求】\n" + user_info}
    ]

    return messages


def build_refine_prompt(user_input: dict, history: list, user_feedback: str) -> list:
    """
    构建修改意见的提示词（多轮对话优化）。

    参数：
        user_input: 用户最初填的表单（原始需求）
        history: 之前的对话历史（消息列表）
        user_feedback: 用户这次提出的修改意见

    流程：系统提示词 + 原始需求 + 之前推荐的名字 + 用户新意见 + 格式要求
    """

    surname = user_input.get('surname', '某')
    given_chars = _get_name_char_count(user_input.get('name_length', ''), surname)
    if given_chars is None:
        given_chars = 2

    system_prompt = f"""你是一位取名大师，正在根据用户的修改意见调整之前推荐的名字。
请认真理解用户的不满之处，给出更好的替代方案。

【最高优先级·不可修改规则】
- 本次名字（不含姓氏）必须是 {given_chars} 个汉字，无论用户提出任何修改意见，字数都不能改变
- 用户提到的字数均指全名（含姓）总字数，名字本身字数保持不变
- 输出前必须逐个检查，字数不对不得输出

每次仍然返回5个候选名字，每个名字包含：名字本身、字义解析、五行属性、音韵分析、评分。
名字来源要多样化（诗词/自然/品德/音韵等），不要只重复典籍出处，确保5个名字风格有差异。
名字要男女有别，避免生僻字。"""

    # 原始需求（简短回顾，字数明确说明）
    base_info = f"原始需求：{user_input.get('surname')}姓{user_input.get('gender')}"
    if user_input.get('name_length'):
        base_info += f"，{_get_name_description(user_input['name_length'], 'short')}"
    if user_input.get('preferences'):
        base_info += f"，偏好：{user_input['preferences']}"

    # 从历史中提取AI上次推荐的名字
    last_names = "之前推荐的名字（含评分和完整信息供参考）：\n"
    found = False
    for msg in reversed(history):
        if msg["role"] == "assistant":
            if isinstance(msg["content"], list):
                for name in msg["content"]:
                    full_name = name.get('full_name') or name.get('name', '')
                    score = name.get('score', '')
                    meaning = name.get('meaning', '')
                    wuxing = name.get('wuxing', '')
                    sound = name.get('sound_rhythm', '')
                    cultural = name.get('cultural_ref', '')
                    parts = [f"- {full_name}"]
                    if score:
                        parts.append(f"评分{score}")
                    if meaning:
                        parts.append(meaning)
                    if wuxing:
                        parts.append(f"五行{wuxing}")
                    if sound:
                        parts.append(sound)
                    if cultural:
                        parts.append(f"出处{cultural}")
                    last_names += " | ".join(parts) + "\n"
            else:
                last_names += str(msg["content"])[:500] + "\n..."
            found = True
            break

    if not found:
        last_names = "（暂无历史记录）"

    format_example = _build_format_example(given_chars, surname)

    # 字数规则放在用户消息最开头，最高优先级，明确禁止被用户的意见带偏
    user_content = (
        f"【最高优先级·不可修改规则】\n"
        f"本次名字（不含姓氏）必须是 {given_chars} 个汉字，"
        f"无论用户提出任何修改意见，字数都不能改变。\n"
        f"用户提到的字数均指全名总字数，名字本身字数保持不变。\n\n"
        f"{format_example}\n\n"
        f"【本次任务】\n"
        f"{base_info}\n\n"
        f"{last_names}\n"
        f"用户的修改意见：{user_feedback}\n\n"
        f"请根据意见调整，重新输出5个候选名字。"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]

    return messages


def build_evaluate_prompt(name_text: str) -> list:
    """
    构建 AI 评价名字的提示词。

    参数：
        name_text: 用户输入的要评价的名字

    返回 DeepSeek API 消息列表。
    """
    system_prompt = """你是一位精通中国传统文化的取名大师，精通《周易》、五行八卦、唐诗宋词。
你的任务是对用户提供的名字进行专业、全面的评价。

请从以下维度评分（每项0~100分）：
1. meaning_score（字义）：名字中每个字的含义是否美好、积极向上
2. sound_score（音韵）：读音是否悦耳动听、抑扬顿挫、朗朗上口
3. culture_score（文化）：是否有典籍出处、文化底蕴、历史渊源
4. wuxing_score（五行）：五行属性搭配是否合理、是否有益于命理
5. overall_score（综合寓意）：整体寓意深度、美好程度

同时给出综合评语（comment），80~150字，语言优美、有文化感。

请严格按JSON格式输出，不要加markdown代码块标记：
{"name":"被评价的名字","meaning_score":85,"sound_score":90,"culture_score":75,"wuxing_score":80,"overall_score":83,"comment":"综合评语..."}"""

    user_content = f"请评价这个名字：{name_text}"

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]


def build_single_refine_prompt(
    original_name: dict, user_feedback: str, user_input: dict, refine_history: list = None
) -> list:
    """
    针对单个名字的修改意见，构建提示词让 AI 优化这一个名字。

    参数：
        original_name: 当前名字的完整信息（含 name/full_name/meaning/cultural_ref/wuxing/sound_rhythm/score）
        user_feedback: 用户写的修改意见
        user_input: 原始取名需求（surname/gender/name_length 等）
        refine_history: 当前名字的多轮修改历史 [{"role":"user","content":"..."}, {"role":"assistant","content":"..."}]

    返回 DeepSeek API 消息列表。
    """
    surname = user_input.get('surname', '')
    gender = user_input.get('gender', '')
    name_length = user_input.get('name_length', '')

    system_prompt = f"""你是一位取名大师。用户对名字「{original_name.get('full_name','')}」有修改意见，请根据意见优化，只返回一个修改后的名字。

要求：
1. 保持姓氏「{surname}」不变
2. 性别「{gender}」，需注意男女风格
3. 名字字数要求「{name_length}」
4. 只输出一个名字，JSON 格式（不要数组）：
{{"name":"某","full_name":"{surname}某","meaning":"字义","cultural_ref":"出处","wuxing":"金木水火土","sound_rhythm":"音韵分析","score":90}}"""

    # 当前名字信息
    name_info = f"""当前名字：{original_name.get('full_name','')}
字义：{original_name.get('meaning','')}
出处：{original_name.get('cultural_ref','')}
五行：{original_name.get('wuxing','')}
音韵：{original_name.get('sound_rhythm','')}"""

    user_content = f"{name_info}\n\n修改意见：{user_feedback}\n\n请只返回修改后的一个名字（JSON对象格式）。"

    messages = [{"role": "system", "content": system_prompt}]

    # 多轮修改历史
    if refine_history:
        for h in refine_history:
            messages.append(h)

    messages.append({"role": "user", "content": user_content})
    return messages


# ========== 单独测试 ==========
if __name__ == "__main__":
    # 测试字数解析
    for test_val in ['2个字', '3个字', '4个字', '双字', '2字（含姓）', '', None, '3个字（如：张致远）']:
        chars = _get_name_char_count(test_val)
        print(f"  {test_val!r:30s} → {chars}")

    print()

    # 测试首次生成提示词（所有字数选项）
    for opt in ['2个字', '3个字', '4个字']:
        test_input = {
            'surname': '张',
            'gender': '男孩',
            'name_length': opt,
            'preferences': '希望孩子聪明智慧、事业有成',
        }
        msgs = build_initial_prompt(test_input)
        print(f"=== {opt} 的提示词 ===")
        # 提取字数信息
        for line in msgs[0]['content'].split('\n'):
            if '必须' in line and '个汉字' in line:
                print(f"  系统提示: {line.strip()}")
        for line in msgs[1]['content'].split('\n'):
            if '个字' in line and 'name' not in line:
                print(f"  用户消息: {line.strip()}")
        print()
    messages = build_initial_prompt(test_input)
    print("=== 首次生成提示词 ===")
    print(f"System: {messages[0]['content'][:200]}...")
    print(f"User: {messages[1]['content'][:200]}...")
