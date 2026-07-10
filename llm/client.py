"""
DeepSeek API 调用模块

作用：连接 DeepSeek 大模型，发送提示词并获取回复。

使用前请先注册 DeepSeek 账号获取 API Key：
https://platform.deepseek.com/
"""
import requests
import json
import os

# ========== 配置（按优先级：.env文件 > 环境变量 > 代码回退） ==========
# ⚠️ .env 文件已在 .gitignore 中，不会提交到仓库
# 使用方式：cp .env.example .env，然后填入你的 Key
def _load_api_key():
    """从 .env 文件或环境变量读取 API Key"""
    # 1) 尝试从 .env 文件读取
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith('DEEPSEEK_API_KEY='):
                    key = line.split('=', 1)[1].strip().strip('"').strip("'")
                    if key and key != 'sk-your-key-here':
                        return key

    # 2) 回退到环境变量
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    if key:
        return key

    # 3) 最后回退（无 Key 时提示用户配置）
    return ""

DEEPSEEK_API_KEY = _load_api_key()

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"


def call_deepseek(messages: list) -> str:
    """
    调用 DeepSeek API，返回 AI 回复的文本内容。

    参数：
        messages: 消息列表
            [{"role": "system", "content": "..."},
             {"role": "user", "content": "..."}]

    返回：
        AI 回复的文本（JSON 字符串）

    如果调用失败，返回 None。
    """
    # 检查 API Key 是否已配置
    if not DEEPSEEK_API_KEY:
        print("❌ 请先配置 DeepSeek API Key！")
        print("   方法：设置环境变量 export DEEPSEEK_API_KEY='sk-xxx'")
        print("   或在运行前：DEEPSEEK_API_KEY='sk-xxx' streamlit run app.py")
        return None

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "deepseek-chat",          # 使用的模型名称
        "messages": messages,              # 你组装的提示词
        "temperature": 0.8,                # 创意程度 0~1（0.8 适合取名）
        "max_tokens": 2048,                # 最大输出长度
        "stream": False                    # 关闭流式输出（简单模式）
    }

    try:
        # 发送 POST 请求到 DeepSeek API
        print("📤 发送请求到 DeepSeek API...")
        response = requests.post(
            DEEPSEEK_API_URL,
            headers=headers,
            json=data,
            timeout=30  # 30秒超时，防止卡死
        )

        # 检查 HTTP 状态码
        if response.status_code == 200:
            result = response.json()
            # 从返回结果中提取 AI 的回复文本
            ai_response = result["choices"][0]["message"]["content"]
            print("📥 收到回复！")
            return ai_response
        else:
            print(f"❌ API请求失败（状态码：{response.status_code}）")
            print(f"   错误信息：{response.text}")
            return None

    except requests.exceptions.Timeout:
        print("❌ 请求超时（超过30秒），请检查网络或稍后重试")
        return None
    except requests.exceptions.ConnectionError:
        print("❌ 网络连接失败，请检查网络是否正常")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求出错：{e}")
        return None
    except Exception as e:
        print(f"❌ 未知错误：{e}")
        return None


# ========== 单独测试 ==========
if __name__ == "__main__":
    print("🧪 测试 DeepSeek API 连接...")

    test_messages = [
        {"role": "system", "content": "你是一个测试助手"},
        {"role": "user", "content": "你好，请回复'连接成功'四个字"}
    ]

    result = call_deepseek(test_messages)

    if result:
        print(f"✅ API连接成功！")
        print(f"   回复：{result}")
    else:
        print("❌ API连接失败")
        print("   请检查：")
        print("   1. API Key 是否已配置")
        print("   2. 网络是否正常")
        print("   3. DeepSeek 服务是否正常")
