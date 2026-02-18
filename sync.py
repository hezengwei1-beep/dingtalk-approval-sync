"""钉钉审批记录同步到飞书主程序"""
import yaml
import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any
import requests

from dingtalk_client import DingTalkClient
from feishu_toolkit import TenantAuth, BitableClient
from data_processor import DataProcessor
from checkpoint import CheckpointManager
from logger import setup_logger

logger = setup_logger(__name__)


class SyncManager:
    """同步管理器"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        初始化同步管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self.load_config(config_path)
        
        # 初始化客户端
        dt_config = self.config['dingtalk']
        self.dingtalk_client = DingTalkClient(
            app_key=dt_config['app_key'],
            app_secret=dt_config['app_secret'],
            base_url=dt_config.get('base_url', 'https://oapi.dingtalk.com')
        )
        
        fs_config = self.config['feishu']
        feishu_auth = TenantAuth(
            app_id=fs_config['app_id'],
            app_secret=fs_config['app_secret'],
            base_url=fs_config.get('base_url', 'https://open.feishu.cn'),
        )
        self.bitable = BitableClient(feishu_auth)
        
        # 初始化处理器
        self.data_processor = DataProcessor()
        
        # 初始化检查点管理器
        sync_config = self.config.get('sync', {})
        self.checkpoint_manager = CheckpointManager(
            checkpoint_file=sync_config.get('checkpoint_file', 'checkpoint.json')
        )
        
        # 配置信息
        self.feishu_app_token = fs_config['app_token']
        self.main_table_id = fs_config['tables']['main']
        self.action_table_id = fs_config['tables'].get('action')
        self.batch_size = sync_config.get('batch_size', 20)
        self.max_retries = sync_config.get('max_retries', 3)
        
        # 通知配置
        self.notification_enabled = self.config.get('notification', {}).get('enabled', False)
        self.webhook_url = self.config.get('notification', {}).get('webhook_url', '')
    
    @staticmethod
    def load_config(config_path: str) -> Dict:
        """
        加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置字典
        """
        if not Path(config_path).exists():
            logger.error(f"配置文件不存在: {config_path}")
            logger.info("请复制 config.yaml.example 为 config.yaml 并填入配置信息")
            sys.exit(1)
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"成功加载配置文件: {config_path}")
            return config
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            sys.exit(1)
    
    def find_main_record(self, instance_id: str) -> Optional[Dict]:
        """
        查找主表记录
        
        Args:
            instance_id: 审批实例ID
            
        Returns:
            记录字典（包含record_id）或None
        """
        return self.bitable.find_record(
            self.feishu_app_token,
            self.main_table_id,
            "instance_id",
            instance_id
        )
    
    def upsert_main_record(self, main_data: Dict[str, Any]) -> Dict:
        """
        新增或更新主表记录
        
        Args:
            main_data: 主表数据
            
        Returns:
            操作结果
        """
        # 查找是否存在
        existing_record = self.find_main_record(main_data['instance_id'])
        record_id = existing_record.get('record_id') if existing_record else None
        
        # 转换为飞书字段格式（这里假设字段名与配置一致，实际需要根据飞书表格字段配置调整）
        fields = {}
        for key, value in main_data.items():
            if value is not None:
                fields[key] = value
        
        # 新增或更新
        result = self.bitable.upsert_record(
            self.feishu_app_token,
            self.main_table_id,
            record_id,
            fields
        )
        
        return result
    
    def upsert_action_records(self, action_records: List[Dict[str, Any]], 
                             instance_id: str) -> int:
        """
        新增或更新动作明细记录
        
        Args:
            action_records: 动作记录列表
            instance_id: 审批实例ID
            
        Returns:
            处理的记录数
        """
        if not self.action_table_id or not action_records:
            return 0
        
        # 批量处理
        batch_records = []
        for action in action_records:
            # 查找是否存在（根据instance_id和action_time判断唯一性）
            # 这里简化处理，实际可以根据业务需求调整去重逻辑
            fields = {}
            for key, value in action.items():
                if value is not None:
                    fields[key] = value
            
            batch_records.append({
                "fields": fields
            })
        
        # 批量写入（飞书支持批量接口，但需要去重处理）
        # 这里简化处理，逐条写入（生产环境可以优化为批量）
        success_count = 0
        for record in batch_records:
            try:
                self.bitable.upsert_record(
                    self.feishu_app_token,
                    self.action_table_id,
                    None,  # 明细表每次新增，不更新
                    record['fields']
                )
                success_count += 1
            except Exception as e:
                logger.warning(f"写入动作记录失败: {e}")
        
        return success_count
    
    def sync_instances(self, start_time: datetime, end_time: datetime, 
                      process_code: Optional[str] = None) -> Dict[str, int]:
        """
        同步审批实例
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            process_code: 审批流程代码（可选）
            
        Returns:
            同步统计信息
        """
        stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'main_updated': 0,
            'action_inserted': 0
        }
        
        # 转换时间戳
        start_ts = self.dingtalk_client.datetime_to_timestamp(start_time)
        end_ts = self.dingtalk_client.datetime_to_timestamp(end_time)
        
        logger.info(f"开始同步审批记录: {start_time.strftime('%Y-%m-%d %H:%M:%S')} ~ {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        cursor = 0
        size = self.batch_size
        
        while True:
            try:
                # 获取审批实例列表
                result = self.dingtalk_client.get_process_instances(
                    start_time=str(start_ts),
                    end_time=str(end_ts),
                    process_code=process_code,
                    cursor=cursor,
                    size=size
                )
                
                instances = result.get('list', [])
                if not instances:
                    break
                
                stats['total'] += len(instances)
                
                # 处理每条实例
                for instance in instances:
                    instance_id = instance.get('process_instance_id', '')
                    if not instance_id:
                        continue
                    
                    try:
                        # 获取详情
                        detail = self.dingtalk_client.get_process_instance_detail(instance_id)
                        
                        # 处理主表数据
                        main_data = self.data_processor.process_instance_main(detail)
                        self.upsert_main_record(main_data)
                        stats['main_updated'] += 1
                        
                        # 处理明细表数据
                        if self.action_table_id:
                            action_records = self.data_processor.process_instance_actions(detail)
                            action_count = self.upsert_action_records(action_records, instance_id)
                            stats['action_inserted'] += action_count
                        
                        stats['success'] += 1
                        logger.debug(f"成功同步审批实例: {instance_id}")
                        
                    except Exception as e:
                        stats['failed'] += 1
                        logger.error(f"同步审批实例失败 {instance_id}: {e}")
                
                # 检查是否有下一页
                if not result.get('has_more', False):
                    break
                
                cursor = result.get('next_cursor', 0)
                if cursor == 0:
                    break
                    
            except Exception as e:
                logger.error(f"获取审批实例列表失败: {e}")
                break
        
        logger.info(f"同步完成: 总计={stats['total']}, 成功={stats['success']}, 失败={stats['failed']}")
        return stats
    
    def send_notification(self, message: str):
        """
        发送通知（飞书机器人）
        
        Args:
            message: 通知消息
        """
        if not self.notification_enabled or not self.webhook_url:
            return
        
        try:
            payload = {
                "msg_type": "text",
                "content": {
                    "text": message
                }
            }
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("通知发送成功")
        except Exception as e:
            logger.warning(f"发送通知失败: {e}")
    
    def run(self, start_time: Optional[datetime] = None, 
            end_time: Optional[datetime] = None,
            init_mode: bool = False,
            full_check: bool = False):
        """
        运行同步任务
        
        Args:
            start_time: 开始时间（可选）
            end_time: 结束时间（可选）
            init_mode: 是否为初始化模式（全量同步）
            full_check: 是否为全量校验
        """
        try:
            # 确定时间范围
            if init_mode:
                # 初始化模式：同步最近7天
                end_time = datetime.now()
                start_time = end_time - timedelta(days=7)
                logger.info("初始化模式：同步最近7天数据")
            elif full_check:
                # 全量校验：同步最近30天
                end_time = datetime.now()
                start_time = end_time - timedelta(days=30)
                logger.info("全量校验模式：同步最近30天数据")
            elif not start_time or not end_time:
                # 增量同步：从上次检查点到当前
                last_sync_time = self.checkpoint_manager.load_checkpoint()
                if last_sync_time:
                    try:
                        start_time = datetime.strptime(last_sync_time, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        # 如果解析失败，默认同步最近24小时
                        default_hours = self.config.get('sync', {}).get('default_hours', 24)
                        start_time = datetime.now() - timedelta(hours=default_hours)
                else:
                    default_hours = self.config.get('sync', {}).get('default_hours', 24)
                    start_time = datetime.now() - timedelta(hours=default_hours)
                
                end_time = datetime.now()
            
            # 执行同步
            start = datetime.now()
            stats = self.sync_instances(start_time, end_time)
            elapsed = (datetime.now() - start).total_seconds()
            
            # 保存检查点
            self.checkpoint_manager.save_checkpoint(end_time.strftime('%Y-%m-%d %H:%M:%S'))
            
            # 发送通知
            message = f"""钉钉审批同步完成

时间范围: {start_time.strftime('%Y-%m-%d %H:%M:%S')} ~ {end_time.strftime('%Y-%m-%d %H:%M:%S')}
总计: {stats['total']} 条
成功: {stats['success']} 条
失败: {stats['failed']} 条
主表更新: {stats['main_updated']} 条
明细表新增: {stats['action_inserted']} 条
耗时: {elapsed:.2f} 秒
"""
            self.send_notification(message)
            
            logger.info("同步任务完成")
            
        except Exception as e:
            error_msg = f"同步任务失败: {e}"
            logger.error(error_msg)
            self.send_notification(error_msg)
            sys.exit(1)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='钉钉审批记录同步到飞书')
    parser.add_argument('--config', '-c', default='config.yaml', help='配置文件路径')
    parser.add_argument('--init', action='store_true', help='初始化模式（全量同步最近7天）')
    parser.add_argument('--full-check', action='store_true', help='全量校验模式（同步最近30天）')
    parser.add_argument('--start-time', help='开始时间（格式：YYYY-MM-DD HH:MM:SS）')
    parser.add_argument('--end-time', help='结束时间（格式：YYYY-MM-DD HH:MM:SS）')
    
    args = parser.parse_args()
    
    # 解析时间参数
    start_time = None
    end_time = None
    
    if args.start_time:
        try:
            start_time = datetime.strptime(args.start_time, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            logger.error("开始时间格式错误，应为：YYYY-MM-DD HH:MM:SS")
            sys.exit(1)
    
    if args.end_time:
        try:
            end_time = datetime.strptime(args.end_time, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            logger.error("结束时间格式错误，应为：YYYY-MM-DD HH:MM:SS")
            sys.exit(1)
    
    # 创建同步管理器并运行
    sync_manager = SyncManager(config_path=args.config)
    sync_manager.run(
        start_time=start_time,
        end_time=end_time,
        init_mode=args.init,
        full_check=args.full_check
    )


if __name__ == '__main__':
    main()
