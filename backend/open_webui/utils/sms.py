"""
阿里云短信服务工具类
"""
import random
import logging
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ClientException, ServerException
from aliyunsdkdysmsapi.request.v20170525.SendSmsRequest import SendSmsRequest
from aliyunsdkcore.auth.credentials import AccessKeyCredential
from open_webui.env import SRC_LOG_LEVELS, REDIS_URL, REDIS_SENTINEL_HOSTS, REDIS_SENTINEL_PORT
from open_webui.utils.redis import get_redis_connection, get_sentinels_from_env

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MAIN"])


test_accounts = [
    # 附加审核策略
    "18900000021",
    "18900000022",
    "18900000023",
    "18900000024",
    "18900000025",
    "18900000026",
    "18900000027",
    "18900000028",

    "18900000001",
    "18900000002",
    "18900000003",
    "18900000004",
    "18900000005",
    "18900000006",
    "18900000007",
    "18900000008",
    "18900000009",
    "18900000010",

    "18617007050",

    # 不附加审核策略（通过openwenui的权限组区分）
    "18900000011",
    "18900000012",
    "18900000013",
    "18900000014",
    "18900000015",
    "18900000016",
    "18900000017",
    "18900000018",
    "18900000019",
    "18900000020",
]

class SmsVerificationCodeStore:
    """
    短信验证码存储类，使用Redis实现
    """
    def __init__(self):
        """初始化Redis连接"""
        sentinel_hosts = get_sentinels_from_env(REDIS_SENTINEL_HOSTS, REDIS_SENTINEL_PORT)
        self.redis = get_redis_connection(REDIS_URL, sentinel_hosts)
        # 如果Redis连接失败，会直接抛出异常
    
    def _get_code_key(self, phone_number: str) -> str:
        """
        获取验证码的Redis键名
        
        Args:
            phone_number: 手机号
            
        Returns:
            Redis键名
        """
        return f"sms:code:{phone_number}"
    
    def _get_count_key(self, phone_number: str) -> str:
        """
        获取每日发送计数的Redis键名
        
        Args:
            phone_number: 手机号
            
        Returns:
            Redis键名
        """
        today = datetime.now().strftime("%Y%m%d")
        return f"sms:count:{phone_number}:{today}"
    
    def _get_interval_key(self, phone_number: str) -> str:
        """
        获取发送间隔的Redis键名
        
        Args:
            phone_number: 手机号
            
        Returns:
            Redis键名
        """
        return f"sms:interval:{phone_number}"
    
    def save_code(self, phone_number: str, code: str, expire_seconds: int) -> bool:
        """
        保存验证码到Redis
        
        Args:
            phone_number: 手机号
            code: 验证码
            expire_seconds: 过期时间（秒）
            
        Returns:
            是否保存成功
        """
        try:
            # 保存验证码
            code_key = self._get_code_key(phone_number)
            self.redis.set(code_key, code, ex=expire_seconds)
            
            # 更新发送间隔
            interval_key = self._get_interval_key(phone_number)
            self.redis.set(interval_key, '1', ex=60)  # 默认60秒发送间隔
            
            # 更新每日发送计数
            count_key = self._get_count_key(phone_number)
            count = self.redis.incr(count_key)
            
            # 如果是第一次设置计数，设置过期时间（今天结束）
            if count == 1:
                # 计算到今天结束的秒数
                now = datetime.now()
                tomorrow = datetime(now.year, now.month, now.day) + timedelta(days=1)
                seconds_until_tomorrow = int((tomorrow - now).total_seconds())
                self.redis.expire(count_key, seconds_until_tomorrow)
            
            return True
        except Exception as e:
            log.error(f"Error saving code to Redis: {str(e)}")
            raise e
    
    def verify_code(self, phone_number: str, code: str) -> bool:
        """
        验证验证码是否正确
        
        Args:
            phone_number: 手机号
            code: 验证码
            
        Returns:
            验证码是否正确
        """

        if phone_number in test_accounts and code == "888888":
            return True
        
        try:
            code_key = self._get_code_key(phone_number)
            stored_code = self.redis.get(code_key)
            
            if stored_code and stored_code == code:
                # 验证成功后删除验证码，防止重复使用
                self.redis.delete(code_key)
                return True
            return False
        except Exception as e:
            log.error(f"Error verifying code: {str(e)}")
            raise e
    
    def can_send_sms(self, phone_number: str, daily_limit: int) -> Tuple[bool, str]:
        """
        检查是否可以发送短信（基于发送间隔和每日限额）
        
        Args:
            phone_number: 手机号
            daily_limit: 每日发送限制
            
        Returns:
            Tuple[bool, str]: (是否可以发送, 原因)
        """
        try:
            interval_key = self._get_interval_key(phone_number)
            count_key = self._get_count_key(phone_number)
            
            # 检查发送间隔
            if self.redis.exists(interval_key):
                return False, "短信发送过于频繁，请稍后再试"
            
            # 检查每日发送限额
            count = self.redis.get(count_key)
            
            if count and int(count) >= daily_limit:
                return False, f"已达到每日短信发送限制({daily_limit}条)"
            
            return True, "可以发送短信"
        except Exception as e:
            log.error(f"Error checking SMS send limit: {str(e)}")
            raise e

class AliyunSmsClient:
    """
    阿里云短信服务客户端
    """
    def __init__(self, 
                 access_key_id: str, 
                 access_key_secret: str, 
                 sign_name: str, 
                 template_code: str,
                 region_id: str = "cn-hangzhou"):
        """
        初始化阿里云短信服务客户端
        
        Args:
            access_key_id: 阿里云AccessKey ID
            access_key_secret: 阿里云AccessKey Secret
            sign_name: 短信签名
            template_code: 短信模板CODE
            region_id: 区域ID，默认为cn-hangzhou
        """
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.sign_name = sign_name
        self.template_code = template_code
        self.region_id = region_id
        credentials = AccessKeyCredential(self.access_key_id, self.access_key_secret)
        self.client = AcsClient(region_id=self.region_id, credential=credentials)
    
    def generate_code(self, length: int = 6) -> str:
        """
        生成随机验证码
        
        Args:
            length: 验证码长度，默认为6位
            
        Returns:
            生成的验证码
        """
        # 生成指定长度的随机数字验证码
        code = ''.join(random.choice('0123456789') for _ in range(length))
        return code
    
    def send_sms(self, phone_number: str, template_param: Dict[str, Any]) -> Tuple[bool, str]:
        """
        发送短信
        
        Args:
            phone_number: 手机号
            template_param: 模板参数，如验证码等
            
        Returns:
            Tuple[bool, str]: (是否成功, 返回消息)
        """
        try:
            request = SendSmsRequest()
            request.set_accept_format('json')
            
            # 设置参数
            request.set_SignName(self.sign_name)
            request.set_TemplateCode(self.template_code)
            request.set_PhoneNumbers(phone_number)
            
            # 转换模板参数为JSON字符串
            template_param_json = json.dumps(template_param)
            request.set_TemplateParam(template_param_json)
            
            # 发送请求
            response = self.client.do_action_with_exception(request)
            response_str = response.decode('utf-8')
            response_json = json.loads(response_str)
            
            # 判断是否发送成功
            if response_json.get('Code') == 'OK':
                log.info(f"SMS sent successfully to {phone_number}")
                return True, "SMS sent successfully"
            else:
                log.error(f"Failed to send SMS to {phone_number}: {response_json}")
                return False, response_json.get('Message', 'Unknown error') 
                
        except (ClientException, ServerException) as e:
            log.error(f"Error sending SMS: {str(e)}")
            return False, str(e)
        except Exception as e:
            log.error(f"Unexpected error sending SMS: {str(e)}")
            return False, f"Unexpected error: {str(e)}"

    def send_verification_code(self, phone_number: str, code: Optional[str] = None, length: int = 6) -> Tuple[bool, str, Optional[str]]:
        """
        发送验证码短信
        
        Args:
            phone_number: 手机号
            code: 验证码，如果为None则自动生成
            length: 验证码长度，默认为6位（当code为None时使用）
            
        Returns:
            Tuple[bool, str, Optional[str]]: (是否成功, 返回消息, 验证码)
        """
        # 如果没有提供验证码，则生成一个
        if code is None:
            code = self.generate_code(length)
        
        # 发送短信验证码
        success, message = self.send_sms(phone_number, {'code': code})
        
        if success:
            return True, message, code
        else:
            return False, message, None 