"""
测试短信验证码登录功能
"""
import unittest
import json
from unittest import mock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from open_webui.routers import auths
from open_webui.models.users import Users
from open_webui.models.auths import Auths
from open_webui.utils.sms import SmsVerificationCodeStore

# 在导入前先模拟redis模块
mock_redis = mock.MagicMock()
mock_redis.from_url.return_value = mock.MagicMock()
mock.patch('open_webui.utils.redis.redis.Redis', mock_redis).start()

# 模拟SmsVerificationCodeStore
mock_verification_store = mock.MagicMock()
# 设置可以正确比较的返回值
mock_verification_store.redis = {}
# 设置验证码检查方法返回值
mock_verification_store.can_send_sms.return_value = (True, "可以发送短信")
mock_verification_store.verify_code.return_value = True
mock.patch('open_webui.utils.sms.SmsVerificationCodeStore', return_value=mock_verification_store).start()

class TestSmsAuth(unittest.TestCase):
    """测试短信验证码登录认证功能"""

    def setUp(self):
        """测试前准备"""
        # 创建FastAPI应用和测试客户端
        self.app = FastAPI()
        self.app.include_router(auths.router, prefix="/api/auth")
        self.client = TestClient(self.app)
        
        # 模拟应用状态
        self.app.state.config = mock.MagicMock()
        self.app.state.config.ENABLE_SMS.value = True
        self.app.state.config.ALIYUN_SMS_ACCESS_KEY_ID.value = "test_key_id"
        self.app.state.config.ALIYUN_SMS_ACCESS_KEY_SECRET.value = "test_key_secret"
        self.app.state.config.ALIYUN_SMS_SIGN_NAME.value = "测试签名"
        self.app.state.config.ALIYUN_SMS_TEMPLATE_CODE.value = "SMS_12345678"
        self.app.state.config.ALIYUN_SMS_REGION_ID.value = "cn-hangzhou"
        self.app.state.config.SMS_VERIFICATION_CODE_LENGTH.value = 6
        self.app.state.config.SMS_VERIFICATION_CODE_EXPIRE_SECONDS.value = 300
        self.app.state.config.SMS_VERIFICATION_CODE_DAILY_LIMIT.value = 10
        self.app.state.config.JWT_EXPIRES_IN.value = "7d"
        self.app.state.config.DEFAULT_USER_ROLE.value = "user"
        self.app.state.config.USER_PERMISSIONS.value = {}
        self.app.state.config.WEBHOOK_URL.value = None
        self.app.state.WEBUI_NAME = "Open WebUI"
        
        # Mock SmsVerificationCodeStore
        self.mock_code_store = mock_verification_store
        
        # Mock AliyunSmsClient
        self.mock_sms_client = mock.patch("open_webui.utils.sms.AliyunSmsClient").start()
        self.mock_sms_client_instance = mock.MagicMock()
        self.mock_sms_client.return_value = self.mock_sms_client_instance
        self.mock_sms_client_instance.generate_code.return_value = "123456"
        self.mock_sms_client_instance.send_sms.return_value = (True, "SMS sent successfully")
        
        # Mock Auths
        self.mock_auths = mock.patch("open_webui.routers.auths.Auths").start()
        
        # Mock Users
        self.mock_users = mock.patch("open_webui.routers.auths.Users").start()
        self.mock_users.get_num_users.return_value = 0
        
        # Mock validation functions
        self.mock_validate_phone_format = mock.patch("open_webui.routers.auths.validate_phone_format").start()
        self.mock_validate_phone_format.return_value = True

    def tearDown(self):
        """测试后清理"""
        mock.patch.stopall()

    def test_send_sms_code_success(self):
        """测试成功发送短信验证码"""
        # 设置mock返回值
        self.mock_code_store.can_send_sms.return_value = (True, "可以发送短信")
        
        # 发送请求
        response = self.client.post(
            "/api/auth/sms/send_code",
            json={"phone": "13800138000"}
        )
        
        # 验证结果
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"success": True, "message": "验证码已发送"})

    def test_send_sms_code_rate_limit(self):
        """测试短信发送频率限制"""
        # 设置mock返回值
        self.mock_code_store.can_send_sms.return_value = (False, "短信发送过于频繁，请稍后再试")
        
        # 发送请求
        response = self.client.post(
            "/api/auth/sms/send_code",
            json={"phone": "13800138000"}
        )
        
        # 验证结果
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json(), {"detail": "短信发送过于频繁，请稍后再试"})

    def test_sms_login_new_user(self):
        """测试新用户短信验证码登录"""
        # 设置mock返回值
        self.mock_code_store.verify_code.return_value = True
        self.mock_auths.authenticate_user_by_phone.return_value = None  # 用户不存在
        
        # 模拟创建新用户
        mock_user = mock.MagicMock()
        mock_user.id = "user123"
        mock_user.email = "13800138000@phone.sms.user"
        mock_user.name = "用户8000"
        mock_user.role = "admin"  # 首位用户为admin
        mock_user.profile_image_url = "/user.png"
        mock_user.model_dump_json.return_value = "{}"
        
        self.mock_auths.insert_new_user_by_phone.return_value = mock_user
        
        # 发送请求
        response = self.client.post(
            "/api/auth/sms/login",
            json={"phone": "13800138000", "code": "123456"}
        )
        
        # 验证结果
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["id"], "user123")
        self.assertEqual(result["email"], "13800138000@phone.sms.user")
        self.assertEqual(result["name"], "用户8000")
        self.assertEqual(result["role"], "admin")

    def test_sms_login_existing_user(self):
        """测试已存在用户短信验证码登录"""
        # 设置mock返回值
        self.mock_code_store.verify_code.return_value = True
        
        # 模拟已存在用户
        mock_user = mock.MagicMock()
        mock_user.id = "user123"
        mock_user.email = "13800138000@phone.sms.user"
        mock_user.name = "用户8000"
        mock_user.role = "user"
        mock_user.profile_image_url = "/user.png"
        mock_user.model_dump_json.return_value = "{}"
        
        self.mock_auths.authenticate_user_by_phone.return_value = mock_user
        
        # 发送请求
        response = self.client.post(
            "/api/auth/sms/login",
            json={"phone": "13800138000", "code": "123456"}
        )
        
        # 验证结果
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["id"], "user123")
        self.assertEqual(result["email"], "13800138000@phone.sms.user")

    def test_sms_login_invalid_code(self):
        """测试短信验证码错误"""
        # 设置mock返回值
        self.mock_code_store.verify_code.return_value = False
        
        # 发送请求
        response = self.client.post(
            "/api/auth/sms/login",
            json={"phone": "13800138000", "code": "123456"}
        )
        
        # 验证结果
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"detail": "验证码错误或已过期"})

if __name__ == "__main__":
    unittest.main() 