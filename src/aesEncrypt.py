from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import base64



def aes_encrypt(plaintext: str) -> str:
    """
    模拟前端JavaScript的AES加密
    参数:
        plaintext: 要加密的明文（手机号或密码）
    返回:
        Base64编码的加密结果
    """
    # 密钥和IV（与前端一致）
    key = "septnet0000000000000000000000000"  # 32字节，AES-256
    iv = "1234567890000000"  # 16字节

    # 将字符串转换为字节
    key_bytes = key.encode('utf-8')  # 32字节
    iv_bytes = iv.encode('utf-8')  # 16字节
    plaintext_bytes = plaintext.encode('utf-8')

    # 创建AES cipher对象 - ECB模式忽略IV
    # 注意：CryptoJS的ECB模式实际上使用了IV参数但忽略它
    cipher = AES.new(key_bytes, AES.MODE_ECB)

    # PKCS7填充
    padded_data = pad(plaintext_bytes, AES.block_size, style='pkcs7')

    # 加密
    encrypted_bytes = cipher.encrypt(padded_data)

    # Base64编码
    encrypted_b64 = base64.b64encode(encrypted_bytes).decode('utf-8')

    return encrypted_b64


# 测试
if __name__ == "__main__":
    test_cases = [
        "13997586074",  # 手机号
        "123456789",  # 密码
        "test",  # 短文本
        "hello world",  # 带空格
        "1234567890123456"  # 刚好16字节
    ]

    print("=== AES加密测试 ===")
    for text in test_cases:
        encrypted = aes_encrypt(text)
        print(f"明文: {text}")
        print(f"密文: {encrypted}")
        print(f"长度: {len(encrypted)}")
        print("-" * 40)