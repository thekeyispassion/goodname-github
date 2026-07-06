"""
结果解析器

作用：把 AI 返回的 JSON 字符串解析成 Python 能操作的列表。

为啥需要这个模块？
- AI 返回的是文本（字符串），不是 Python 对象
- 我们需要把 '[{"name": "致远", ...}]' 转成 [{"name": "致远", ...}]
- AI 有时会加 ```json 标记或格式不标准，这个模块自动处理各种情况
"""
import json
import re


def parse_ai_response(response_text: str) -> list:
    """
    解析 AI 返回的 JSON 字符串，返回名字列表。

    参数：
        response_text: AI 返回的原始文本

    返回：
        名字列表，每个元素是字典。解析失败时返回空列表 []。

    处理流程（从严格到宽松）：
        1. 直接当JSON解析
        2. 如果套了```json```代码块，提取里面的内容
        3. 正则模糊提取（至少能拿到名字和全名）
        4. 实在不行就返回空
    """

    if not response_text:
        print("⚠️ AI 返回为空")
        return []

    # ========== 方法1：直接解析 ==========
    # AI 严格按照要求返回纯 JSON 的情况
    try:
        names = json.loads(response_text)
        if isinstance(names, list):
            print(f"✅ 成功解析 {len(names)} 个名字")
            return names
    except json.JSONDecodeError:
        pass  # 不行就试下一种

    # ========== 方法2：提取代码块内容 ==========
    # AI 有时会返回：
    # ```json
    # [{"name": "致远", ...}]
    # ```
    json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', response_text, re.DOTALL)
    if json_match:
        try:
            names = json.loads(json_match.group(1))
            if isinstance(names, list):
                print(f"✅ 从代码块中解析出 {len(names)} 个名字")
                return names
        except json.JSONDecodeError:
            pass

    # ========== 方法3：模糊提取 ==========
    # 如果完全不是JSON格式，用正则捞出基本字段
    print("⚠️ 标准解析失败，尝试模糊提取...")

    name_pattern = re.findall(r'"name"\s*:\s*"([^"]+)"', response_text)
    full_name_pattern = re.findall(r'"full_name"\s*:\s*"([^"]+)"', response_text)

    if name_pattern and full_name_pattern:
        result = []
        for i in range(min(len(name_pattern), len(full_name_pattern))):
            result.append({
                "name": name_pattern[i],
                "full_name": full_name_pattern[i],
                "meaning": "",
                "cultural_ref": "",
                "wuxing": "",
                "sound_rhythm": "",
                "score": 0,
            })
        print(f"✅ 模糊提取出 {len(result)} 个名字（部分信息缺失）")
        return result

    # ========== 方法4：真不行了 ==========
    print("❌ 解析失败，AI 返回的内容格式不对")
    # 只打印前200字符，避免刷屏
    preview = response_text[:200].replace('\n', ' ')
    print(f"   原始内容预览：{preview}...")
    return []


# ========== 单独测试 ==========
if __name__ == "__main__":
    # 测试1：标准 JSON
    print("=== 测试1：标准JSON ===")
    test1 = '[{"name": "致远", "full_name": "张致远", "score": 95}]'
    result1 = parse_ai_response(test1)
    print(f"结果：{result1}")

    # 测试2：带代码块标记
    print("\n=== 测试2：带```json标记 ===")
    test2 = '```json\n[{"name": "明哲", "full_name": "李明哲", "score": 92}]\n```'
    result2 = parse_ai_response(test2)
    print(f"结果：{result2}")

    # 测试3：空值
    print("\n=== 测试3：空值 ===")
    result3 = parse_ai_response("")
    print(f"结果：{result3}")

    # 测试4：非 JSON 文本
    print("\n=== 测试4：非JSON（纯文本） ===")
    result4 = parse_ai_response("你好，这是取名字的结果...")
    print(f"结果：{result4}")
