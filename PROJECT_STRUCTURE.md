# 项目结构说明

## 目录结构

```
钉钉审批流程/
├── sync.py                      # 主同步程序（入口文件）
├── dingtalk_client.py          # 钉钉API客户端
├── feishu_client.py            # 飞书API客户端
├── data_processor.py           # 数据处理和转换逻辑
├── checkpoint.py               # 检查点管理（断点续传）
├── logger.py                   # 日志工具
│
├── config.yaml.example         # 配置文件模板
├── requirements.txt            # Python依赖包列表
├── .gitignore                 # Git忽略文件配置
│
├── README.md                   # 项目说明文档
├── QUICK_START.md             # 快速开始指南
├── DEPLOYMENT.md              # 部署指南
├── PROJECT_STRUCTURE.md       # 项目结构说明（本文件）
│
├── logs/                      # 日志目录
│   └── sync.log              # 同步日志文件
│
└── checkpoint.json            # 检查点文件（运行时生成）
```

## 核心模块说明

### 1. sync.py - 主同步程序

**功能**：
- 整合所有模块，实现完整的同步流程
- 命令行参数解析
- 同步任务调度和执行
- 统计和通知

**主要类**：
- `SyncManager`：同步管理器，负责协调各个模块

**使用方法**：
```bash
# 初始化同步（最近7天）
python sync.py --init

# 增量同步
python sync.py

# 指定时间范围
python sync.py --start-time "2025-01-10 00:00:00" --end-time "2025-01-11 23:59:59"
```

### 2. dingtalk_client.py - 钉钉API客户端

**功能**：
- 钉钉API调用封装
- 访问令牌获取和缓存
- 审批实例列表获取
- 审批实例详情获取
- 用户信息获取

**主要类**：
- `DingTalkClient`：钉钉API客户端

**主要方法**：
- `get_access_token()`：获取访问令牌
- `get_process_instances()`：获取审批实例列表
- `get_process_instance_detail()`：获取审批实例详情

### 3. feishu_client.py - 飞书API客户端

**功能**：
- 飞书API调用封装
- 租户访问令牌获取和缓存
- 多维表格记录读写
- 批量操作支持

**主要类**：
- `FeishuClient`：飞书API客户端

**主要方法**：
- `get_tenant_access_token()`：获取访问令牌
- `upsert_bitable_record()`：新增或更新记录
- `batch_upsert_bitable_records()`：批量新增或更新
- `find_record_by_field()`：根据字段查找记录

### 4. data_processor.py - 数据处理模块

**功能**：
- 数据清洗和转换
- 字段映射和标准化
- 审批状态和动作映射
- 时间格式转换

**主要类**：
- `DataProcessor`：数据处理器

**主要方法**：
- `process_instance_main()`：处理主表数据
- `process_instance_actions()`：处理明细表数据
- `extract_form_value()`：提取表单字段值

### 5. checkpoint.py - 检查点管理

**功能**：
- 记录同步进度（断点续传）
- 保存和加载检查点
- 重置检查点

**主要类**：
- `CheckpointManager`：检查点管理器

**主要方法**：
- `load_checkpoint()`：加载检查点
- `save_checkpoint()`：保存检查点
- `reset()`：重置检查点

### 6. logger.py - 日志工具

**功能**：
- 日志配置和初始化
- 文件日志轮转
- 控制台输出

**主要函数**：
- `setup_logger()`：配置日志记录器

## 数据流

```
钉钉审批API
    ↓
DingTalkClient (获取数据)
    ↓
DataProcessor (数据清洗和转换)
    ↓
FeishuClient (写入飞书多维表格)
    ↓
飞书多维表格
```

## 配置文件说明

### config.yaml

配置文件包含以下部分：

1. **dingtalk**：钉钉应用配置
   - `app_key`：应用Key
   - `app_secret`：应用Secret
   - `base_url`：API基础地址

2. **feishu**：飞书应用配置
   - `app_id`：应用ID
   - `app_secret`：应用Secret
   - `app_token`：多维表格app_token
   - `tables`：表格ID配置
     - `main`：主表ID
     - `action`：明细表ID

3. **sync**：同步配置
   - `batch_size`：每批处理数量
   - `max_retries`：最大重试次数
   - `checkpoint_file`：检查点文件路径
   - `default_hours`：默认同步时间范围（小时）

4. **notification**：通知配置
   - `enabled`：是否启用通知
   - `webhook_url`：飞书机器人webhook地址

5. **logging**：日志配置
   - `level`：日志级别
   - `file`：日志文件路径
   - `max_bytes`：单个日志文件最大字节数
   - `backup_count`：保留的备份文件数量

## 扩展建议

### 1. 添加新的数据源

- 在 `dingtalk_client.py` 中添加新的API调用方法
- 在 `data_processor.py` 中添加数据处理逻辑

### 2. 自定义字段映射

- 修改 `data_processor.py` 中的字段处理逻辑
- 调整飞书表格字段结构

### 3. 添加数据分析

- 创建新的数据分析脚本
- 使用飞书多维表格的视图和公式功能

### 4. 优化性能

- 实现批量处理
- 添加缓存机制
- 优化API调用频率

## 依赖包说明

- **requests**：HTTP请求库
- **pyyaml**：YAML配置文件解析
- **python-dateutil**：日期时间处理
- **tenacity**：重试机制

## 开发规范

1. **代码风格**：遵循PEP 8规范
2. **注释**：使用中文注释，关键函数添加文档字符串
3. **错误处理**：使用try-except捕获异常，记录日志
4. **日志记录**：关键操作记录日志，使用适当的日志级别

## 测试建议

1. **单元测试**：为每个模块编写单元测试
2. **集成测试**：测试完整同步流程
3. **数据验证**：验证数据准确性
4. **性能测试**：测试大量数据的处理性能

## 维护建议

1. **定期检查**：检查日志文件，发现问题及时处理
2. **更新依赖**：定期更新依赖包版本
3. **监控告警**：配置监控和告警机制
4. **备份数据**：定期备份检查点和配置文件
