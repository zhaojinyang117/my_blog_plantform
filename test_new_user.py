#!/usr/bin/env python3
"""
测试新用户注册功能
"""
import requests
import json
import time

def test_new_user_register():
    """测试新用户注册功能"""
    
    # 生成唯一的测试用户数据
    timestamp = int(time.time())
    test_data = {
        "username": f"newuser{timestamp}",
        "email": f"newuser{timestamp}@example.com",
        "password": "newpassword123",
        "password2": "newpassword123"
    }
    
    print(f"测试注册新用户: {test_data['username']}")
    print(f"测试邮箱: {test_data['email']}")
    
    # 测试前端API代理
    try:
        response = requests.post(
            "http://localhost:3000/api/users/register/",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\n前端代理响应状态码: {response.status_code}")
        
        if response.status_code == 201:
            response_data = response.json()
            print(f"✅ 前端代理注册成功!")
            print(f"响应数据: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
            
            # 检查响应格式是否正确
            if 'message' in response_data and 'user_id' in response_data and 'email' in response_data:
                print("✅ 响应格式正确，包含所需字段")
            else:
                print("❌ 响应格式不正确")
                
        else:
            print(f"❌ 前端代理注册失败!")
            try:
                error_data = response.json()
                print(f"错误数据: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"响应文本: {response.text}")
                
    except Exception as e:
        print(f"❌ 请求异常: {e}")

if __name__ == "__main__":
    test_new_user_register()
