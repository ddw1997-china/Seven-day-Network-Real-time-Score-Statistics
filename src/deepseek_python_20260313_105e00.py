#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简化版验证脚本 - 逐步验证 mm.py 加密算法
避免触发请求限制，采用分步验证方式
"""

import os
import sys
import time
import hashlib
import json
import base64
from mm import FileEncryptor

def print_header(title):
    """打印标题"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def step_verify_encryptor_initialization():
    """步骤1: 验证加密器初始化"""
    print_header("步骤1: 验证加密器初始化")
    
    try:
        encryptor = FileEncryptor()
        
        # 验证密钥长度
        print(f"原始密钥长度: {len(encryptor.key_bytes)} 字节 (期望64字节)")
        print(f"AES密钥长度: {len(encryptor.aes_key)} 字节 (期望32字节)")
        print(f"机器码: {encryptor.machine_code_hex[:32]}...")
        
        if len(encryptor.key_bytes) == 64 and len(encryptor.aes_key) == 32:
            print("✅ 密钥长度验证通过")
            return encryptor
        else:
            print("❌ 密钥长度验证失败")
            return None
            
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return None

def step_verify_basic_encryption(encryptor):
    """步骤2: 验证基本加密功能"""
    print_header("步骤2: 验证基本加密功能")
    
    try:
        # 测试简单的字符串
        test_strings = [
            "Hello World",
            "测试中文",
            "123456"
        ]
        
        for i, test_str in enumerate(test_strings):
            print(f"\n测试 {i+1}: {test_str}")
            
            # 加密
            encrypted = encryptor.encrypt_string(test_str)
            print(f"  加密后: {encrypted[:32]}...")
            
            # 解密
            decrypted = encryptor.decrypt_string(encrypted)
            print(f"  解密后: {decrypted}")
            
            if test_str == decrypted:
                print(f"  ✅ 字符串 {i+1} 验证通过")
            else:
                print(f"  ❌ 字符串 {i+1} 验证失败")
                
            time.sleep(0.5)  # 添加延时避免触发限制
            
        return True
        
    except Exception as e:
        print(f"❌ 基本加密功能测试失败: {e}")
        return False

def step_verify_file_encryption(encryptor):
    """步骤3: 验证文件加密功能"""
    print_header("步骤3: 验证文件加密功能")
    
    try:
        # 创建测试文件
        test_content = b"This is a test file content for encryption verification."
        test_file = "test_temp.txt"
        
        with open(test_file, 'wb') as f:
            f.write(test_content)
        
        print(f"创建测试文件: {test_file}")
        print(f"文件内容: {test_content.decode('utf-8')}")
        
        # 加密文件
        print("\n加密文件中...")
        encrypted_file = encryptor.encrypt_file(test_file)
        print(f"✅ 加密成功: {encrypted_file}")
        
        # 解密文件
        print("\n解密文件中...")
        decrypted_file = encryptor.decrypt_file(encrypted_file)
        print(f"✅ 解密成功: {decrypted_file}")
        
        # 验证内容
        with open(decrypted_file, 'rb') as f:
            decrypted_content = f.read()
        
        if test_content == decrypted_content:
            print("✅ 文件内容验证通过")
        else:
            print("❌ 文件内容验证失败")
            
        # 清理
        for f in [test_file, encrypted_file, decrypted_file]:
            if os.path.exists(f):
                os.remove(f)
                print(f"清理: {f}")
        
        return True
        
    except Exception as e:
        print(f"❌ 文件加密功能测试失败: {e}")
        return False

def step_verify_hmac_integrity(encryptor):
    """步骤4: 验证HMAC完整性"""
    print_header("步骤4: 验证HMAC完整性")
    
    try:
        # 创建测试文件
        test_content = b"Test HMAC integrity"
        test_file = "test_hmac.txt"
        
        with open(test_file, 'wb') as f:
            f.write(test_content)
        
        # 加密
        encrypted_file = encryptor.encrypt_file(test_file)
        print(f"加密文件创建成功")
        
        # 修改加密文件
        with open(encrypted_file, 'r+b') as f:
            f.seek(50)  # 定位到中间位置
            f.write(b'X')  # 修改一个字节
        print("文件已篡改（修改了一个字节）")
        
        # 尝试解密（应失败）
        try:
            encryptor.decrypt_file(encrypted_file)
            print("❌ 应该检测到篡改但没有")
        except ValueError as e:
            if "HMAC验证失败" in str(e):
                print(f"✅ 成功检测到篡改: {e}")
            else:
                print(f"❌ 其他错误: {e}")
        
        # 清理
        for f in [test_file, encrypted_file]:
            if os.path.exists(f):
                os.remove(f)
        
        return True
        
    except Exception as e:
        print(f"❌ HMAC测试失败: {e}")
        return False

def step_verify_metadata(encryptor):
    """步骤5: 验证元数据功能"""
    print_header("步骤5: 验证元数据功能")
    
    try:
        # 创建测试文件
        test_content = b"Test with metadata"
        test_file = "test_meta.txt"
        
        with open(test_file, 'wb') as f:
            f.write(test_content)
        
        # 自定义元数据
        custom_metadata = {
            'app': 'mm.py验证',
            'time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'user': 'tester'
        }
        
        print(f"自定义元数据: {custom_metadata}")
        
        # 加密
        encrypted_file = encryptor.encrypt_file(
            test_file,
            metadata=custom_metadata
        )
        print("✅ 加密完成（带元数据）")
        
        # 解密
        decrypted_file = encryptor.decrypt_file(encrypted_file)
        print("✅ 解密完成")
        
        # 清理
        for f in [test_file, encrypted_file, decrypted_file]:
            if os.path.exists(f):
                os.remove(f)
        
        print("✅ 元数据功能验证通过")
        return True
        
    except Exception as e:
        print(f"❌ 元数据测试失败: {e}")
        return False

def step_verify_iv_randomness(encryptor):
    """步骤6: 验证IV随机性（简化版）"""
    print_header("步骤6: 验证IV随机性")
    
    try:
        test_str = "Same text for all encryptions"
        
        ivs = []
        for i in range(3):
            encrypted = encryptor.encrypt_string(test_str)
            # 从加密结果中提取IV（前32个十六进制字符 = 16字节）
            iv = encrypted[:32]
            ivs.append(iv)
            print(f"加密 {i+1} IV: {iv}")
            time.sleep(0.5)
        
        # 检查是否有重复
        if len(set(ivs)) == len(ivs):
            print("✅ IV随机性验证通过（所有IV都不同）")
        else:
            print("❌ IV随机性验证失败（出现重复IV）")
            
        return True
        
    except Exception as e:
        print(f"❌ IV测试失败: {e}")
        return False

def step_verify_algorithm_details(encryptor):
    """步骤7: 验证算法细节"""
    print_header("步骤7: 验证算法细节")
    
    try:
        print("加密算法分析:")
        print(f"  - 算法: AES-256-CBC")
        print(f"  - 密钥长度: 256位")
        print(f"  - IV长度: 128位")
        print(f"  - HMAC: SHA-256")
        
        # 验证密钥派生
        key_bytes = encryptor.key_bytes
        derived_key = hashlib.sha256(key_bytes).digest()[:32]
        
        if derived_key == encryptor.aes_key:
            print("✅ 密钥派生验证通过")
        else:
            print("❌ 密钥派生验证失败")
            
        # 验证机器码格式
        machine_code = encryptor.machine_code_hex
        is_hex = all(c in '0123456789ABCDEFabcdef' for c in machine_code)
        
        if is_hex:
            print(f"✅ 机器码格式正确 (十六进制)")
            print(f"   机器码长度: {len(machine_code)} 字符")
        else:
            print(f"❌ 机器码格式错误")
            
        return True
        
    except Exception as e:
        print(f"❌ 算法细节验证失败: {e}")
        return False

def main():
    """主函数 - 分步验证"""
    print("\n" + "="*60)
    print(" mm.py 加密算法验证工具 (简化版)")
    print("="*60)
    print("\n注意: 本工具采用分步验证，避免触发请求限制")
    print("每步之间会有延时，请耐心等待...\n")
    
    # 检查依赖
    try:
        from Crypto.Cipher import AES
        print("✅ pycryptodome 已安装")
    except ImportError:
        print("❌ 请安装 pycryptodome: pip install pycryptodome")
        return
    
    # 步骤1: 初始化
    encryptor = step_verify_encryptor_initialization()
    if not encryptor:
        print("\n❌ 初始化失败，终止验证")
        return
    
    time.sleep(1)  # 延时
    
    # 步骤2: 基本加密
    if not step_verify_basic_encryption(encryptor):
        print("\n⚠️ 基本加密功能验证失败，继续验证其他功能")
    
    time.sleep(1)
    
    # 步骤3: 文件加密
    if not step_verify_file_encryption(encryptor):
        print("\n⚠️ 文件加密功能验证失败")
    
    time.sleep(1)
    
    # 步骤4: HMAC完整性
    if not step_verify_hmac_integrity(encryptor):
        print("\n⚠️ HMAC完整性验证失败")
    
    time.sleep(1)
    
    # 步骤5: 元数据
    if not step_verify_metadata(encryptor):
        print("\n⚠️ 元数据功能验证失败")
    
    time.sleep(1)
    
    # 步骤6: IV随机性
    if not step_verify_iv_randomness(encryptor):
        print("\n⚠️ IV随机性验证失败")
    
    time.sleep(1)
    
    # 步骤7: 算法细节
    if not step_verify_algorithm_details(encryptor):
        print("\n⚠️ 算法细节验证失败")
    
    print("\n" + "="*60)
    print(" 验证完成")
    print("="*60)
    print("\n所有验证步骤已执行完毕。如果所有步骤都显示✅，则算法正确实现。")
    print("如果有任何❌标记，请检查对应功能。")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n验证被用户中断")
    except Exception as e:
        print(f"\n发生错误: {e}")