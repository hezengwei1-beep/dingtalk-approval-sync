# 快速开始指南

## 一、5分钟快速部署

### 步骤1：安装依赖

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖包
pip install -r requirements.txt
```

### 步骤2：配置应用信息

```bash
# 复制配置文件模板
cp config.yaml.example config.yaml

# 编辑配置文件，填入以下信息：
# 1. 钉钉应用的 AppKey 和 AppSecret
# 2. 飞书应用的 App ID 和 App Secret
# 3. 飞书多维表格的 app_token 和 table_id
# 4. 飞书机器人 webhook（可选，用于告警）
vim config.yaml
```

### 步骤3：测试运行

```bash
# 首次运行（同步最近7天数据）
python sync.py --init

# 查看日志
tail -f logs/sync.log
```

### 步骤4：配置定时任务

```bash
# Linux/Mac - 添加crontab任务
crontab -e

# 添加以下内容（每天8:00, 12:00, 18:00执行）
0 8,12,18 * * * cd /path/to/project && /path/to/venv/bin/python sync.py >> logs/sync.log 2>&1
```

## 二、必需的应用配置

### 钉钉应用配置清单

- [ ] 在 [钉钉开放平台](https://open.dingtalk.com/) 创建企业内部应用
- [ ] 开通「工作台管理」权限
- [ ] 开通「审批流程管理（只读）」权限
- [ ] 记录 **AppKey** 和 **AppSecret**

### 飞书应用配置清单

- [ ] 在 [飞书开发者后台](https://open.feishu.cn/app) 创建企业自建应用
- [ ] 开通「查看、编辑和管理多维表格」权限
- [ ] 开通「编辑和管理多维表格中的记录」权限
- [ ] 创建飞书多维表格，创建「审批实例表」和「审批动作表」
- [ ] 记录 **App ID**、**App Secret**、**app_token** 和 **table_id**

### 飞书表格字段配置

#### 主表：审批实例表

必须创建的字段（字段名需要完全一致）：

| 字段名 | 字段类型 | 必填 |
|--------|---------|------|
| instance_id | 文本 | ✅ |
| template_code | 文本 | |
| title | 文本 | ✅ |
| status | 文本 | ✅ |
| applicant | 文本 | ✅ |
| applicant_dept | 文本 | |
| amount | 数字 | |
| start_time | 日期时间 | ✅ |
| end_time | 日期时间 | |
| current_node | 文本 | |
| last_action | 文本 | |
| last_action_time | 日期时间 | |
| approver_chain | 文本 | |

#### 明细表：审批动作表（可选）

| 字段名 | 字段类型 | 必填 |
|--------|---------|------|
| instance_id | 文本 | ✅ |
| node_name | 文本 | ✅ |
| approver | 文本 | ✅ |
| action | 文本 | ✅ |
| action_time | 日期时间 | ✅ |
| comment | 文本 | |

## 三、常见问题快速解决

### Q1: 配置文件找不到？

```bash
# 确保 config.yaml 文件存在
ls -la config.yaml

# 如果不存在，从模板复制
cp config.yaml.example config.yaml
```

### Q2: 获取token失败？

- 检查配置文件中的 AppKey/AppSecret 是否正确
- 确认应用权限已开通
- 检查网络连接

### Q3: 写入飞书失败？

- 确认飞书表格字段名与代码中的字段名一致
- 检查字段类型是否匹配（文本、数字、日期时间）
- 确认飞书应用权限已开通

### Q4: 数据为空？

- 确认时间范围内有审批记录
- 检查日志中的错误信息
- 尝试使用 `--init` 参数同步更多数据

## 四、验证清单

运行前检查：

- [ ] Python 3.7+ 已安装
- [ ] 虚拟环境已创建并激活
- [ ] 依赖包已安装（`pip list` 查看）
- [ ] config.yaml 配置文件已填写
- [ ] 钉钉应用权限已开通
- [ ] 飞书应用权限已开通
- [ ] 飞书表格字段已创建
- [ ] logs 目录存在

运行后验证：

- [ ] 检查 `logs/sync.log` 是否有错误
- [ ] 登录飞书查看表格是否有数据
- [ ] 抽查几条记录，验证字段是否正确

## 五、下一步

- 📖 查看 [README.md](README.md) 了解详细功能
- 📖 查看 [DEPLOYMENT.md](DEPLOYMENT.md) 了解部署细节
- 🔧 自定义字段映射，修改 `data_processor.py`
- 📊 配置数据分析视图，使用飞书多维表格的视图功能

## 六、获取帮助

如遇问题：

1. 查看 `logs/sync.log` 日志文件
2. 检查配置文件是否正确
3. 参考 [DEPLOYMENT.md](DEPLOYMENT.md) 的故障排查章节
4. 提交 Issue 或联系技术支持
