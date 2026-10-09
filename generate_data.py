import requests
import random
import string
import json

# 目标接口地址（确保你的 Flask 服务已启动）
BASE_URL = "http://127.0.0.1:9999/register"


def batch_register(count=50):
    """批量注册用户，并将成功的数据保存为 JSON 供 pytestDemo 使用"""
    success_count = 0
    generated_users = []  # 用于收集成功的数据

    for i in range(1, count + 1):
        # 1. 构造用户数据（增加随机性，避免重复运行时报错）
        # 使用随机8位数字，确保手机号唯一
        telephone = f"138{random.randint(10000000, 99999999)}"
        # 生成随机用户名
        random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        username = f"test_user_{i}_{random_str}"

        payload = {
            "username": username,
            "password": "123456",
            "sex": random.choice(["0", "1"]),  # 随机性别
            "telephone": telephone,
            "address": f"测试地址_{i}号"
        }

        headers = {
            "Content-Type": "application/json"
        }

        # 2. 发送请求
        try:
            response = requests.post(BASE_URL, json=payload, headers=headers)
            res_data = response.json()

            if res_data.get("code") == 0:
                success_count += 1
                # 【核心修改】收集成功的账号信息
                generated_users.append({"username": username, "telephone": telephone})
                print(f"✅ [{i}/{count}] 成功: {username} | 手机号: {telephone}")
            else:
                print(f"❌ [{i}/{count}] 失败: {res_data.get('msg')}")

        except Exception as e:
            print(f"⚠️ [{i}/{count}] 请求异常，请检查 Flask 服务是否开启: {e}")

    # 3. 将生成的数据写入 JSON 文件，直接存到 pytestDemo 的 data 目录
    save_path = r"D:\PyCharm\pytestDemo-master\data\generated_users.json"
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(generated_users, f, ensure_ascii=False, indent=4)

    print(f"\n🎉 批量生成结束！共成功注册 {success_count} 个用户。")
    print(f"📁 账号数据已保存至 generated_users.json，请将其复制到 pytestDemo 的 data/ 目录下。")


if __name__ == '__main__':
    # 修改这里的数字，决定生成多少个用户
    batch_register(count=50)