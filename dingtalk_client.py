"""钉钉API客户端"""
import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from logger import setup_logger

logger = setup_logger(__name__)


class DingTalkClient:
    """钉钉API客户端"""
    
    def __init__(self, app_key: str, app_secret: str, base_url: str = "https://oapi.dingtalk.com"):
        """
        初始化钉钉客户端
        
        Args:
            app_key: 应用Key
            app_secret: 应用Secret
            base_url: API基础地址
        """
        self.app_key = app_key
        self.app_secret = app_secret
        self.base_url = base_url.rstrip('/')
        self._access_token = None
        self._token_expires_at = None
    
    def get_access_token(self) -> str:
        """
        获取访问令牌（带缓存和自动刷新）
        
        Returns:
            访问令牌
        """
        # 如果token有效，直接返回
        if self._access_token and self._token_expires_at:
            if time.time() < self._token_expires_at - 300:  # 提前5分钟刷新
                return self._access_token
        
        url = f"{self.base_url}/gettoken"
        params = {
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('errcode') != 0:
                raise Exception(f"获取token失败: {data.get('errmsg')}")
            
            self._access_token = data.get('access_token')
            # 默认token有效期为7200秒，这里设置为7100秒过期
            self._token_expires_at = time.time() + 7100
            
            logger.info("成功获取钉钉访问令牌")
            return self._access_token
            
        except Exception as e:
            logger.error(f"获取钉钉访问令牌失败: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_process_instances(self, start_time: str, end_time: str,
                            process_code: Optional[str] = None,
                            statuses: Optional[List[str]] = None,
                            cursor: int = 0, size: int = 20,
                            _retry_count: int = 0) -> Dict:
        """
        获取审批实例列表

        Args:
            start_time: 开始时间（毫秒时间戳）
            end_time: 结束时间（毫秒时间戳）
            process_code: 审批流程code（可选）
            statuses: 审批状态列表（RUNNING/FINISHED/TERMINATED/REVOKED）
            cursor: 分页游标
            size: 每页大小
            _retry_count: 内部重试计数器（用户不应手动设置）

        Returns:
            审批实例列表数据
        """
        url = f"{self.base_url}/topapi/processinstance/list"

        access_token = self.get_access_token()

        body = {
            "start_time": start_time,
            "end_time": end_time,
            "cursor": cursor,
            "size": size
        }

        if process_code:
            body["process_code"] = process_code

        if statuses:
            body["statuses"] = statuses

        params = {"access_token": access_token}

        try:
            response = requests.post(url, json=body, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if data.get('errcode') != 0:
                error_msg = data.get('errmsg', '未知错误')
                if data.get('errcode') == 40014:  # token过期，重新获取
                    if _retry_count >= 3:
                        raise Exception(f"Token刷新重试次数超限: {error_msg}")
                    self._access_token = None
                    logger.warning(f"Token过期，正在重试 (第{_retry_count + 1}次)")
                    return self.get_process_instances(start_time, end_time, process_code, statuses, cursor, size, _retry_count + 1)
                raise Exception(f"获取审批实例列表失败: {error_msg}")

            result = data.get('result', {})
            logger.debug(f"获取到 {len(result.get('list', []))} 条审批实例")
            return result

        except Exception as e:
            logger.error(f"获取审批实例列表失败: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_process_instance_detail(self, process_instance_id: str, _retry_count: int = 0) -> Dict:
        """
        获取审批实例详情

        Args:
            process_instance_id: 审批实例ID
            _retry_count: 内部重试计数器（用户不应手动设置）

        Returns:
            审批实例详情数据
        """
        url = f"{self.base_url}/topapi/processinstance/get"

        access_token = self.get_access_token()

        params = {
            "access_token": access_token,
            "process_instance_id": process_instance_id
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if data.get('errcode') != 0:
                error_msg = data.get('errmsg', '未知错误')
                if data.get('errcode') == 40014:  # token过期
                    if _retry_count >= 3:
                        raise Exception(f"Token刷新重试次数超限: {error_msg}")
                    self._access_token = None
                    logger.warning(f"Token过期，正在重试 (第{_retry_count + 1}次)")
                    return self.get_process_instance_detail(process_instance_id, _retry_count + 1)
                raise Exception(f"获取审批实例详情失败: {error_msg}")

            result = data.get('process_instance', {})
            return result

        except Exception as e:
            logger.error(f"获取审批实例详情失败: {e}")
            raise
    
    def get_user_info(self, userid: str) -> Optional[Dict]:
        """
        获取用户信息
        
        Args:
            userid: 用户ID
            
        Returns:
            用户信息
        """
        url = f"{self.base_url}/topapi/v2/user/get"
        
        access_token = self.get_access_token()
        
        params = {"access_token": access_token}
        body = {"userid": userid}
        
        try:
            response = requests.post(url, json=body, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('errcode') != 0:
                logger.warning(f"获取用户信息失败: {data.get('errmsg')}")
                return None
            
            return data.get('result', {})
            
        except Exception as e:
            logger.warning(f"获取用户信息失败: {e}")
            return None
    
    @staticmethod
    def datetime_to_timestamp(dt: datetime) -> int:
        """
        将datetime转换为毫秒时间戳
        
        Args:
            dt: datetime对象
            
        Returns:
            毫秒时间戳
        """
        return int(dt.timestamp() * 1000)
    
    @staticmethod
    def timestamp_to_datetime(ts: int) -> datetime:
        """
        将毫秒时间戳转换为datetime
        
        Args:
            ts: 毫秒时间戳
            
        Returns:
            datetime对象
        """
        return datetime.fromtimestamp(ts / 1000)
