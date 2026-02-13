# 钉钉审批记录同步到飞书文档

## 项目简介

本项目实现将钉钉审批记录自动同步到飞书多维表格，并提供数据分析和可视化功能。

## 功能特性

- ✅ 自动同步钉钉审批记录到飞书多维表格
- ✅ 支持增量同步和全量校验
- ✅ 数据清洗和字段标准化
- ✅ 断点续传机制
- ✅ 错误重试和日志记录
- ✅ 告警通知（飞书机器人）

## 快速开始

### 1. 环境准备

```bash
# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置应用

#### 2.1 创建钉钉应用

1. 访问 [钉钉开放平台](https://open.dingtalk.com/)
2. 创建企业内部应用
3. 开通以下权限：
   - `workbench_management` - 工作台管理
   - `process_management_read` - 审批流程读取权限
4. 记录 `AppKey` 和 `AppSecret`

#### 2.2 创建飞书应用

1. 访问 [飞书开发者后台](https://open.feishu.cn/app)
2. 创建企业自建应用
3. 开通以下权限：
   - `bitable:app:readonly` - 多维表格应用读取
   - `bitable:app` - 多维表格应用读写
   - `bitable:table:readonly` - 多维表格读取
   - `bitable:table` - 多维表格写入
4. 记录 `App ID` 和 `App Secret`

#### 2.3 创建飞书多维表格

1. 在飞书中创建新的多维表格
2. 按照方案文档创建以下数据表：
   - **主表（审批实例表）**：包含审批基本信息
   - **明细表（审批动作表）**：包含审批节点详情
3. 记录表格的 `app_token` 和 `table_id`

#### 2.4 配置机器人（可选）

如需告警功能，创建飞书机器人并记录 `webhook_url`

### 3. 配置文件

```bash
# 复制配置模板
cp config.yaml.example config.yaml

# 编辑配置文件，填入应用信息
vim config.yaml
```

配置文件示例：

```yaml
dingtalk:
  app_key: "your_dingtalk_app_key"
  app_secret: "your_dingtalk_app_secret"
  
feishu:
  app_id: "your_feishu_app_id"
  app_secret: "your_feishu_app_secret"
  app_token: "your_bitable_app_token"
  tables:
    main: "tbl_main_table_id"      # 审批实例表
    action: "tbl_action_table_id"  # 审批动作表
  
sync:
  batch_size: 20           # 每批处理数量
  max_retries: 3           # 最大重试次数
  checkpoint_file: "checkpoint.json"  # 检查点文件路径
  
notification:
  enabled: true
  webhook_url: "your_feishu_webhook_url"  # 可选
```

### 4. 运行同步

```bash
# 首次运行（全量同步最近7天数据）
python sync.py --init

# 增量同步（默认同步最近24小时）
python sync.py

# 指定时间范围
python sync.py --start-time "2025-01-10 00:00:00" --end-time "2025-01-11 23:59:59"
```

### 5. 定时任务配置

#### Linux/Mac (crontab)

```bash
# 编辑 crontab
crontab -e

# 添加以下任务（每天8:00, 12:00, 18:00增量同步，23:30全量校验）
0 8,12,18 * * * cd /path/to/project && /path/to/venv/bin/python sync.py >> logs/sync.log 2>&1
30 23 * * * cd /path/to/project && /path/to/venv/bin/python sync.py --full-check >> logs/full_check.log 2>&1
```

#### Docker (可选)

```bash
# 构建镜像
docker build -t dingtalk-feishu-sync .

# 运行容器
docker run -d --name sync-task \
  -v $(pwd)/config.yaml:/app/config.yaml \
  -v $(pwd)/logs:/app/logs \
  dingtalk-feishu-sync
```

## 项目结构

```
钉钉审批流程/
├── config.yaml.example          # 配置文件模板
├── requirements.txt              # Python依赖
├── README.md                    # 项目说明
├── sync.py                      # 主同步脚本
├── dingtalk_client.py           # 钉钉API客户端
├── feishu_client.py             # 飞书API客户端
├── data_processor.py            # 数据处理逻辑
├── checkpoint.py                # 检查点管理
├── logger.py                    # 日志工具
└── logs/                        # 日志目录
```

## 数据字段说明

### 主表（审批实例表）字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| instance_id | 文本 | 审批实例ID（主键） |
| template_code | 文本 | 审批模板编码 |
| title | 文本 | 审批标题 |
| status | 文本 | 审批状态 |
| applicant | 文本 | 发起人 |
| applicant_dept | 文本 | 发起部门 |
| amount | 数字 | 金额 |
| start_time | 日期时间 | 发起时间 |
| end_time | 日期时间 | 结束时间 |
| current_node | 文本 | 当前节点 |
| last_action | 文本 | 最近动作 |
| last_action_time | 日期时间 | 最近动作时间 |

### 明细表（审批动作表）字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| instance_id | 文本 | 审批实例ID（关联主表） |
| node_name | 文本 | 节点名称 |
| approver | 文本 | 审批人 |
| action | 文本 | 动作（同意/拒绝/转交） |
| action_time | 日期时间 | 动作时间 |
| comment | 文本 | 审批意见 |

## 常见问题

### Q: 同步失败怎么办？

A: 查看 `logs/sync.log` 日志文件，根据错误信息排查：
- 检查应用权限是否开通
- 确认配置文件中的凭据是否正确
- 检查网络连接和API调用频率限制

### Q: 如何重置同步进度？

A: 删除 `checkpoint.json` 文件，下次运行时会从指定时间开始同步

### Q: 如何查看同步统计？

A: 运行日志会输出同步统计信息，包括成功/失败数量、耗时等

## 开发计划

- [ ] 添加数据分析报表生成
- [ ] 实现审批效率分析指标
- [ ] 添加可视化看板
- [ ] 支持多租户配置
- [ ] 添加数据导出功能

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交 Issue 或联系项目维护者。
