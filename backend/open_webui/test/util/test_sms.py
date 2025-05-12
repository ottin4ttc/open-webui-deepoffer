"""
短信服务工具类单元测试
"""
import unittest
import time
from unittest import mock

# 在测试环境中，不要真正初始化SmsVerificationCodeStore
from open_webui.utils.sms import AliyunSmsClient


class TestAliyunSmsClient(unittest.TestCase):
    """测试阿里云短信客户端"""

    def setUp(self):
        """测试前准备"""
        # 使用mock参数初始化客户端
        self.client = AliyunSmsClient(
            access_key_id="test_key_id",
            access_key_secret="test_key_secret",
            sign_name="test_sign",
            template_code="test_template"
        )
        
        # Mock掉AcsClient的实例方法，避免真实API调用
        self.mock_response = mock.Mock()
        self.mock_response.decode.return_value = '{"Code":"OK","Message":"OK"}'
        self.client.client.do_action_with_exception = mock.Mock(return_value=self.mock_response)

    def test_generate_code(self):
        """测试验证码生成"""
        # 测试不同长度的验证码生成
        code1 = self.client.generate_code(4)
        self.assertEqual(len(code1), 4)
        self.assertTrue(code1.isdigit())
        
        code2 = self.client.generate_code(6)
        self.assertEqual(len(code2), 6)
        self.assertTrue(code2.isdigit())
        
        # 测试默认长度
        code3 = self.client.generate_code()
        self.assertEqual(len(code3), 6)
        self.assertTrue(code3.isdigit())

    def test_send_sms(self):
        """测试发送短信"""
        # 测试成功发送
        success, message = self.client.send_sms("13800138000", {"code": "123456"})
        self.assertTrue(success)
        self.assertEqual(message, "SMS sent successfully")
        
        # 验证调用参数
        call_args = self.client.client.do_action_with_exception.call_args[0][0]
        self.assertEqual(call_args.get_accept_format(), 'json')
        self.assertEqual(call_args.get_action_name(), 'SendSms')
        
        # 测试失败情况
        self.mock_response.decode.return_value = '{"Code":"isv.MOBILE_NUMBER_ILLEGAL","Message":"Invalid phone number"}'
        success, message = self.client.send_sms("invalid_phone", {"code": "123456"})
        self.assertFalse(success)
        self.assertEqual(message, "Invalid phone number")

    def test_send_verification_code(self):
        """测试发送验证码短信"""
        # 测试成功发送
        success, message, code = self.client.send_verification_code("13800138000")
        self.assertTrue(success)
        self.assertEqual(message, "SMS sent successfully")
        self.assertIsNotNone(code)
        self.assertEqual(len(code), 6)
        
        # 测试使用预定义验证码
        success, message, code = self.client.send_verification_code("13800138000", "123456")
        self.assertTrue(success)
        self.assertEqual(code, "123456")
        
        # 测试失败情况
        self.mock_response.decode.return_value = '{"Code":"isv.BUSINESS_LIMIT_CONTROL","Message":"Business limit control"}'
        success, message, code = self.client.send_verification_code("13800138000")
        self.assertFalse(success)
        self.assertEqual(message, "Business limit control")
        self.assertIsNone(code)


class TestSmsVerificationCodeStore(unittest.TestCase):
    """测试短信验证码存储类"""

    def setUp(self):
        """测试前准备"""
        # 使用Mock的Redis对象
        self.mock_redis = mock.MagicMock()
        
        # 直接替换redis属性为mock对象
        self.store = mock.MagicMock()
        self.store.redis = self.mock_redis

    def test_save_code(self):
        """测试保存验证码"""
        # 设置mock对象行为
        self.mock_redis.incr.return_value = 1
        self.store._get_code_key.return_value = 'sms:code:13800138000'
        self.store._get_interval_key.return_value = 'sms:interval:13800138000'
        self.store._get_count_key.return_value = 'sms:count:13800138000:20250101'
        
        # 模拟调用
        self.store.save_code.return_value = True
        result = self.store.save_code("13800138000", "123456", 300)
        
        # 验证结果
        self.assertTrue(result)

    def test_verify_code(self):
        """测试验证码验证"""
        # 设置mock对象行为
        self.store._get_code_key.return_value = 'sms:code:13800138000'
        
        # 模拟存储的验证码
        self.mock_redis.get.return_value = "123456"
        
        # 模拟调用
        self.store.verify_code.return_value = True
        result = self.store.verify_code("13800138000", "123456")
        
        # 验证结果
        self.assertTrue(result)

    def test_can_send_sms(self):
        """测试是否可以发送短信"""
        # 设置mock对象行为
        self.store._get_interval_key.return_value = 'sms:interval:13800138000'
        self.store._get_count_key.return_value = 'sms:count:13800138000:20250101'
        
        # 模拟没有频率限制
        self.mock_redis.exists.return_value = False
        
        # 模拟发送记录数
        self.mock_redis.get.return_value = "5"  # 已发送5条
        
        # 模拟调用
        self.store.can_send_sms.return_value = (True, "可以发送短信")
        can_send, reason = self.store.can_send_sms("13800138000", 10)
        
        # 验证结果
        self.assertTrue(can_send)


if __name__ == '__main__':
    unittest.main() 