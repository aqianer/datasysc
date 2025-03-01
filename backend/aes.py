import os
import base64

def generate_encryption_key():
    # 生成32字节的随机密钥
    key = os.urandom(32)
    # 转换为Base64字符串
    key_base64 = base64.b64encode(key).decode('utf-8')
    return key_base64

if __name__ == "__main__":
    key = generate_encryption_key()
    print("将以下密钥复制到 .env 文件中：")
    print(f"VITE_ENCRYPTION_KEY={key}")