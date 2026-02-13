"""检查点管理模块 - 实现断点续传"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


class CheckpointManager:
    """检查点管理器，用于记录同步进度"""
    
    def __init__(self, checkpoint_file: str = "checkpoint.json"):
        """
        初始化检查点管理器
        
        Args:
            checkpoint_file: 检查点文件路径
        """
        self.checkpoint_file = checkpoint_file
        self.ensure_file_exists()
    
    def ensure_file_exists(self):
        """确保检查点文件存在"""
        checkpoint_path = Path(self.checkpoint_file)
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        if not checkpoint_path.exists():
            # 创建初始检查点（默认7天前）
            from datetime import timedelta
            default_time = datetime.now() - timedelta(days=7)
            self.save_checkpoint(default_time.strftime('%Y-%m-%d %H:%M:%S'))
    
    def load_checkpoint(self) -> Optional[str]:
        """
        加载上次同步的时间点
        
        Returns:
            上次同步时间字符串，格式：YYYY-MM-DD HH:MM:SS
        """
        if not os.path.exists(self.checkpoint_file):
            return None
        
        try:
            with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('last_sync_time')
        except (json.JSONDecodeError, KeyError, IOError) as e:
            print(f"加载检查点失败: {e}")
            return None
    
    def save_checkpoint(self, sync_time: str):
        """
        保存同步时间点
        
        Args:
            sync_time: 同步时间字符串，格式：YYYY-MM-DD HH:MM:SS
        """
        data = {
            'last_sync_time': sync_time,
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        try:
            with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"保存检查点失败: {e}")
    
    def reset(self):
        """重置检查点"""
        if os.path.exists(self.checkpoint_file):
            os.remove(self.checkpoint_file)
        self.ensure_file_exists()
