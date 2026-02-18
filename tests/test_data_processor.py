"""data_processor.py 单元测试"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from data_processor import DataProcessor


class TestTimestampConversion:
    def test_valid_timestamp(self):
        # 2024-01-15 10:30:00 UTC+8 = 1705285800000 ms
        result = DataProcessor.timestamp_to_datetime_str(1705285800000)
        assert result is not None
        assert result.startswith("2024-01-15")

    def test_none(self):
        assert DataProcessor.timestamp_to_datetime_str(None) is None

    def test_invalid(self):
        assert DataProcessor.timestamp_to_datetime_str("abc") is None


class TestStatusMap:
    def test_known_statuses(self):
        assert DataProcessor.STATUS_MAP["RUNNING"] == "审批中"
        assert DataProcessor.STATUS_MAP["FINISHED"] == "已同意"
        assert DataProcessor.STATUS_MAP["TERMINATED"] == "已拒绝"
        assert DataProcessor.STATUS_MAP["REVOKED"] == "已撤销"


class TestExtractFormValue:
    def test_by_name(self):
        forms = [
            {"name": "金额", "value": "5000"},
            {"name": "备注", "value": "测试"},
        ]
        assert DataProcessor.extract_form_value(forms, "金额") == "5000"
        assert DataProcessor.extract_form_value(forms, "备注") == "测试"

    def test_by_component_name(self):
        forms = [{"component_name": "amount", "value": 1234}]
        assert DataProcessor.extract_form_value(forms, "amount") == 1234

    def test_not_found(self):
        forms = [{"name": "金额", "value": "5000"}]
        assert DataProcessor.extract_form_value(forms, "不存在") is None

    def test_list_value(self):
        forms = [{"name": "tags", "value": ["A", "B", "C"]}]
        assert DataProcessor.extract_form_value(forms, "tags") == "A, B, C"

    def test_empty_list(self):
        forms = [{"name": "tags", "value": []}]
        assert DataProcessor.extract_form_value(forms, "tags") is None


class TestNormalizeFieldValue:
    def test_number(self):
        assert DataProcessor.normalize_field_value("1,234.56", "number") == 1234.56
        assert DataProcessor.normalize_field_value(None, "number") is None
        assert DataProcessor.normalize_field_value("abc", "number") is None

    def test_text(self):
        assert DataProcessor.normalize_field_value("hello", "text") == "hello"
        assert DataProcessor.normalize_field_value(None, "text") is None
        assert DataProcessor.normalize_field_value("", "text") == ""

    def test_date(self):
        assert DataProcessor.normalize_field_value("2024-01-15", "date") == "2024-01-15"


class TestProcessInstanceMain:
    def test_basic_instance(self):
        instance = {
            "process_instance_id": "test-001",
            "title": "出差审批",
            "status": "FINISHED",
            "originator_user_name": "张三",
            "originator_dept_name": "技术部",
            "create_time": 1705285800000,
            "finish_time": 1705372200000,
            "process_code": "PROC-001",
            "form_component_values": [
                {"name": "金额", "value": "5000"},
            ],
            "tasks": [],
        }
        result = DataProcessor.process_instance_main(instance)
        assert result["instance_id"] == "test-001"
        assert result["title"] == "出差审批"
        assert result["status"] == "已同意"
        assert result["applicant"] == "张三"
        assert result["applicant_dept"] == "技术部"
        assert result["amount"] == 5000.0

    def test_minimal_instance(self):
        result = DataProcessor.process_instance_main({})
        assert result["instance_id"] == ""
        assert result["status"] == ""
        assert result["amount"] is None


class TestProcessInstanceActions:
    def test_with_tasks(self):
        instance = {
            "process_instance_id": "test-001",
            "tasks": [
                {
                    "task_name": "部门审批",
                    "user_name": "李四",
                    "action_type": "EXECUTE_TASK_NORMAL",
                    "create_time": 1705285800000,
                    "finish_time": 1705286400000,
                    "comment": "同意",
                },
            ],
        }
        actions = DataProcessor.process_instance_actions(instance)
        assert len(actions) == 1
        assert actions[0]["instance_id"] == "test-001"
        assert actions[0]["node_name"] == "部门审批"
        assert actions[0]["approver"] == "李四"
        assert actions[0]["action"] == "同意"
        assert actions[0]["comment"] == "同意"

    def test_empty_tasks(self):
        actions = DataProcessor.process_instance_actions({"process_instance_id": "x", "tasks": []})
        assert actions == []
