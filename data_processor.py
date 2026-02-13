"""数据处理模块 - 数据清洗和转换"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from logger import setup_logger

logger = setup_logger(__name__)


class DataProcessor:
    """数据处理器，负责数据清洗和格式转换"""
    
    # 审批状态映射
    STATUS_MAP = {
        "RUNNING": "审批中",
        "FINISHED": "已同意",
        "TERMINATED": "已拒绝",
        "REVOKED": "已撤销",
        "CANCELED": "已取消"
    }
    
    # 审批动作映射
    ACTION_MAP = {
        "EXECUTE_TASK_NORMAL": "同意",
        "EXECUTE_TASK_AGENT": "代同意",
        "APPEND_TASK_BEFORE": "前加签",
        "APPEND_TASK_AFTER": "后加签",
        "REDIRECT_TASK": "转交",
        "START_PROCESS_INSTANCE": "发起",
        "TERMINATE_PROCESS_INSTANCE": "终止",
        "REVOKE_PROCESS_INSTANCE": "撤销",
        "FINISH_PROCESS_INSTANCE": "完成",
        "ADD_REMARK": "评论",
        "DELETE": "删除"
    }
    
    @staticmethod
    def timestamp_to_datetime_str(ts: Optional[int]) -> Optional[str]:
        """
        将毫秒时间戳转换为日期时间字符串
        
        Args:
            ts: 毫秒时间戳
            
        Returns:
            日期时间字符串，格式：YYYY-MM-DD HH:MM:SS
        """
        if ts is None:
            return None
        try:
            dt = datetime.fromtimestamp(ts / 1000)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def extract_form_value(form_values: List[Dict], name: str) -> Optional[Any]:
        """
        从表单值列表中提取指定字段的值
        
        Args:
            form_values: 表单值列表
            name: 字段名或组件名
            
        Returns:
            字段值
        """
        for form_value in form_values:
            if form_value.get('name') == name or form_value.get('component_name') == name:
                value = form_value.get('value')
                # 处理不同类型的值
                if isinstance(value, str):
                    return value
                elif isinstance(value, (int, float)):
                    return value
                elif isinstance(value, list):
                    return ', '.join(str(v) for v in value) if value else None
                elif isinstance(value, dict):
                    # 复杂对象，尝试提取关键信息
                    return str(value.get('text', value))
                return str(value) if value is not None else None
        return None
    
    @classmethod
    def process_instance_main(cls, instance_detail: Dict) -> Dict[str, Any]:
        """
        处理审批实例主表数据
        
        Args:
            instance_detail: 钉钉审批实例详情数据
            
        Returns:
            主表字段字典
        """
        # 基本信息
        instance_id = instance_detail.get('process_instance_id', '')
        title = instance_detail.get('title', '')
        status = instance_detail.get('status', '')
        status_cn = cls.STATUS_MAP.get(status, status)
        
        # 发起人信息
        originator = instance_detail.get('originator_dept_name', '')
        originator_user_id = instance_detail.get('originator_userid', '')
        originator_name = instance_detail.get('originator_user_name', '')
        
        # 时间信息
        create_time = cls.timestamp_to_datetime_str(instance_detail.get('create_time'))
        finish_time = cls.timestamp_to_datetime_str(instance_detail.get('finish_time'))
        
        # 表单数据
        form_values = instance_detail.get('form_component_values', [])
        amount = cls.extract_form_value(form_values, '金额') or cls.extract_form_value(form_values, 'amount')
        if amount:
            try:
                # 尝试转换为数字
                amount = float(str(amount).replace(',', ''))
            except (ValueError, TypeError):
                amount = None
        
        # 审批流程信息
        process_code = instance_detail.get('process_code', '')
        current_approvers = instance_detail.get('current_approvers', [])
        
        # 获取当前节点名称
        current_node = None
        tasks = instance_detail.get('tasks', [])
        if tasks:
            # 获取正在处理的任务
            running_tasks = [t for t in tasks if t.get('status') == 'RUNNING']
            if running_tasks:
                current_node = running_tasks[0].get('task_name', '')
        
        # 最近动作
        last_action = None
        last_action_time = None
        if tasks:
            # 按时间排序，获取最近的任务
            sorted_tasks = sorted(tasks, key=lambda x: x.get('finish_time', 0), reverse=True)
            if sorted_tasks:
                last_task = sorted_tasks[0]
                if last_task.get('finish_time'):
                    last_action_time = cls.timestamp_to_datetime_str(last_task.get('finish_time'))
                    action_type = last_task.get('action_type', '')
                    last_action = cls.ACTION_MAP.get(action_type, action_type)
        
        # 构建审批链路
        approver_chain = None
        if tasks:
            approvers = []
            for task in sorted(tasks, key=lambda x: x.get('create_time', 0)):
                approver_name = task.get('user_name', '')
                if approver_name and approver_name not in approvers:
                    approvers.append(approver_name)
            if approvers:
                approver_chain = ' > '.join(approvers)
        
        # 返回主表字段
        return {
            "instance_id": instance_id,
            "template_code": process_code,
            "title": title,
            "status": status_cn,
            "applicant": originator_name or originator_user_id,
            "applicant_dept": originator or '',
            "amount": amount,
            "start_time": create_time,
            "end_time": finish_time,
            "current_node": current_node or '',
            "last_action": last_action or '',
            "last_action_time": last_action_time,
            "approver_chain": approver_chain or ''
        }
    
    @classmethod
    def process_instance_actions(cls, instance_detail: Dict) -> List[Dict[str, Any]]:
        """
        处理审批动作明细数据
        
        Args:
            instance_detail: 钉钉审批实例详情数据
            
        Returns:
            动作明细记录列表
        """
        instance_id = instance_detail.get('process_instance_id', '')
        tasks = instance_detail.get('tasks', [])
        
        action_records = []
        
        for task in tasks:
            node_name = task.get('task_name', '')
            user_name = task.get('user_name', '')
            action_type = task.get('action_type', '')
            action_cn = cls.ACTION_MAP.get(action_type, action_type)
            
            create_time = cls.timestamp_to_datetime_str(task.get('create_time'))
            finish_time = cls.timestamp_to_datetime_str(task.get('finish_time'))
            action_time = finish_time or create_time
            
            # 审批意见
            comment = task.get('comment', '') or task.get('task_comment', '')
            
            action_records.append({
                "instance_id": instance_id,
                "node_name": node_name,
                "approver": user_name,
                "action": action_cn,
                "action_time": action_time,
                "comment": comment or ''
            })
        
        return action_records
    
    @staticmethod
    def normalize_field_value(value: Any, field_type: str = "text") -> Any:
        """
        标准化字段值（根据飞书多维表格字段类型）
        
        Args:
            value: 原始值
            field_type: 字段类型（text, number, date, datetime等）
            
        Returns:
            标准化后的值
        """
        if value is None:
            return None
        
        if field_type == "number":
            try:
                return float(str(value).replace(',', ''))
            except (ValueError, TypeError):
                return None
        elif field_type in ["date", "datetime"]:
            if isinstance(value, str):
                return value
            return str(value)
        else:
            # 文本类型
            return str(value) if value else ""
