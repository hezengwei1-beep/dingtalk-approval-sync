"""飞书API客户端"""
import requests
import time
from typing import List, Dict, Optional, Any
from tenacity import retry, stop_after_attempt, wait_exponential
from logger import setup_logger

logger = setup_logger(__name__)


class FeishuClient:
    """飞书API客户端"""
    
    def __init__(self, app_id: str, app_secret: str, base_url: str = "https://open.feishu.cn"):
        """
        初始化飞书客户端
        
        Args:
            app_id: 应用ID
            app_secret: 应用Secret
            base_url: API基础地址
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_url = base_url.rstrip('/')
        self._tenant_access_token = None
        self._token_expires_at = None
    
    def get_tenant_access_token(self) -> str:
        """
        获取租户访问令牌（带缓存和自动刷新）
        
        Returns:
            租户访问令牌
        """
        # 如果token有效，直接返回
        if self._tenant_access_token and self._token_expires_at:
            if time.time() < self._token_expires_at - 300:  # 提前5分钟刷新
                return self._tenant_access_token
        
        url = f"{self.base_url}/open-apis/auth/v3/tenant_access_token/internal"
        
        body = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        try:
            response = requests.post(url, json=body, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('code') != 0:
                raise Exception(f"获取token失败: {data.get('msg')}")
            
            self._tenant_access_token = data.get('tenant_access_token')
            # token有效期为7200秒
            self._token_expires_at = time.time() + 7100
            
            logger.info("成功获取飞书访问令牌")
            return self._tenant_access_token
            
        except Exception as e:
            logger.error(f"获取飞书访问令牌失败: {e}")
            raise
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        token = self.get_tenant_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_bitable_records(self, app_token: str, table_id: str, 
                           filter: Optional[str] = None,
                           sort: Optional[List[str]] = None,
                           field_names: Optional[List[str]] = None,
                           page_size: int = 100, page_token: Optional[str] = None) -> Dict:
        """
        获取多维表格记录
        
        Args:
            app_token: 多维表格app_token
            table_id: 表格ID
            filter: 过滤条件（可选）
            sort: 排序（可选）
            field_names: 需要返回的字段名列表（可选）
            page_size: 每页大小
            page_token: 分页token（可选）
            
        Returns:
            记录列表数据
        """
        url = f"{self.base_url}/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
        
        params = {"page_size": page_size}
        if page_token:
            params["page_token"] = page_token
        
        body = {}
        if filter:
            body["filter"] = filter
        if sort:
            body["sort"] = sort
        if field_names:
            body["field_names"] = field_names
        
        try:
            response = requests.get(
                url, 
                params=params,
                json=body if body else None,
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('code') != 0:
                error_msg = data.get('msg', '未知错误')
                if data.get('code') == 99991663:  # token过期，重新获取
                    self._tenant_access_token = None
                    return self.get_bitable_records(app_token, table_id, filter, sort, field_names, page_size, page_token)
                raise Exception(f"获取多维表格记录失败: {error_msg}")
            
            result = data.get('data', {})
            logger.debug(f"获取到 {len(result.get('items', []))} 条记录")
            return result
            
        except Exception as e:
            logger.error(f"获取多维表格记录失败: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def upsert_bitable_record(self, app_token: str, table_id: str, 
                             record_id: Optional[str], fields: Dict[str, Any]) -> Dict:
        """
        新增或更新多维表格记录
        
        Args:
            app_token: 多维表格app_token
            table_id: 表格ID
            record_id: 记录ID（如果存在则更新，否则新增）
            fields: 字段数据字典
            
        Returns:
            操作结果
        """
        if record_id:
            # 更新记录
            url = f"{self.base_url}/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}"
            method = "PUT"
        else:
            # 新增记录
            url = f"{self.base_url}/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
            method = "POST"
        
        body = {"fields": fields}
        
        try:
            if method == "PUT":
                response = requests.put(url, json=body, headers=self._get_headers(), timeout=30)
            else:
                response = requests.post(url, json=body, headers=self._get_headers(), timeout=30)
            
            response.raise_for_status()
            data = response.json()
            
            if data.get('code') != 0:
                error_msg = data.get('msg', '未知错误')
                if data.get('code') == 99991663:  # token过期
                    self._tenant_access_token = None
                    return self.upsert_bitable_record(app_token, table_id, record_id, fields)
                raise Exception(f"{'更新' if record_id else '新增'}记录失败: {error_msg}")
            
            result = data.get('data', {})
            logger.debug(f"成功{'更新' if record_id else '新增'}记录: {result.get('record', {}).get('record_id')}")
            return result
            
        except Exception as e:
            logger.error(f"{'更新' if record_id else '新增'}记录失败: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def batch_upsert_bitable_records(self, app_token: str, table_id: str, 
                                     records: List[Dict[str, Any]]) -> Dict:
        """
        批量新增或更新多维表格记录
        
        Args:
            app_token: 多维表格app_token
            table_id: 表格ID
            records: 记录列表，每条记录格式: {"record_id": "...", "fields": {...}}
            
        Returns:
            操作结果
        """
        url = f"{self.base_url}/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create"
        
        # 分离新增和更新
        create_records = [r for r in records if not r.get('record_id')]
        update_records = [r for r in records if r.get('record_id')]
        
        results = {"created": [], "updated": []}
        
        # 批量新增
        if create_records:
            body = {"records": [{"fields": r["fields"]} for r in create_records]}
            try:
                response = requests.post(url, json=body, headers=self._get_headers(), timeout=60)
                response.raise_for_status()
                data = response.json()
                
                if data.get('code') != 0:
                    error_msg = data.get('msg', '未知错误')
                    if data.get('code') == 99991663:
                        self._tenant_access_token = None
                        return self.batch_upsert_bitable_records(app_token, table_id, records)
                    raise Exception(f"批量新增记录失败: {error_msg}")
                
                results["created"] = data.get('data', {}).get('records', [])
                logger.info(f"批量新增 {len(results['created'])} 条记录")
                
            except Exception as e:
                logger.error(f"批量新增记录失败: {e}")
                raise
        
        # 批量更新
        if update_records:
            update_url = f"{self.base_url}/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_update"
            body = {"records": [{"record_id": r["record_id"], "fields": r["fields"]} for r in update_records]}
            try:
                response = requests.post(update_url, json=body, headers=self._get_headers(), timeout=60)
                response.raise_for_status()
                data = response.json()
                
                if data.get('code') != 0:
                    error_msg = data.get('msg', '未知错误')
                    if data.get('code') == 99991663:
                        self._tenant_access_token = None
                        return self.batch_upsert_bitable_records(app_token, table_id, records)
                    raise Exception(f"批量更新记录失败: {error_msg}")
                
                results["updated"] = data.get('data', {}).get('records', [])
                logger.info(f"批量更新 {len(results['updated'])} 条记录")
                
            except Exception as e:
                logger.error(f"批量更新记录失败: {e}")
                raise
        
        return results
    
    def find_record_by_field(self, app_token: str, table_id: str, 
                            field_name: str, field_value: str) -> Optional[Dict]:
        """
        根据字段值查找记录
        
        Args:
            app_token: 多维表格app_token
            table_id: 表格ID
            field_name: 字段名
            field_value: 字段值
            
        Returns:
            找到的记录，如果不存在返回None
        """
        try:
            # 使用过滤条件查找
            filter_str = f'CurrentValue.[{field_name}] = "{field_value}"'
            result = self.get_bitable_records(app_token, table_id, filter=filter_str, page_size=1)
            
            items = result.get('items', [])
            if items:
                return items[0].get('record', {})
            
            return None
            
        except Exception as e:
            logger.warning(f"查找记录失败: {e}")
            return None
