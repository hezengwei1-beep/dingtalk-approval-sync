# 部署指南

## 一、环境准备

### 1.1 Python环境

```bash
# 检查Python版本（需要Python 3.7+）
python3 --version

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 1.2 钉钉应用配置

#### 步骤1：创建钉钉应用

1. 访问 [钉钉开放平台](https://open.dingtalk.com/)
2. 登录企业管理员账号
3. 进入「应用开发」→「企业内部开发」→「H5微应用」或「移动应用」
4. 点击「创建应用」，填写应用信息
5. 记录应用的 **AppKey** 和 **AppSecret**

#### 步骤2：开通权限

在应用管理页面，开通以下权限：

- ✅ **工作台管理** (`workbench_management`)
- ✅ **审批流程管理（只读）** (`process_management_read`)
- ✅ **通讯录管理（只读）** (`contact_management_read`)

#### 步骤3：配置IP白名单（如需要）

在应用设置中添加服务器IP地址到白名单

### 1.3 飞书应用配置

#### 步骤1：创建飞书应用

1. 访问 [飞书开发者后台](https://open.feishu.cn/app)
2. 登录企业管理员账号
3. 点击「创建企业自建应用」
4. 填写应用名称和描述
5. 记录应用的 **App ID** 和 **App Secret**

#### 步骤2：开通权限

在应用管理页面，进入「权限管理」，开通以下权限：

- ✅ **查看、编辑和管理多维表格** (`bitable:app`)
- ✅ **查看多维表格** (`bitable:app:readonly`)
- ✅ **编辑和管理多维表格中的记录** (`bitable:table`)
- ✅ **查看多维表格中的记录** (`bitable:table:readonly`)

#### 步骤3：创建飞书多维表格

1. 在飞书中创建新的多维表格应用
2. 创建以下数据表：

**主表：审批实例表**

| 字段名 | 字段类型 | 必填 | 说明 |
|--------|---------|------|------|
| instance_id | 文本 | ✅ | 审批实例ID（主键） |
| template_code | 文本 | | 审批模板编码 |
| title | 文本 | ✅ | 审批标题 |
| status | 文本 | ✅ | 审批状态 |
| applicant | 文本 | ✅ | 发起人 |
| applicant_dept | 文本 | | 发起部门 |
| amount | 数字 | | 金额 |
| start_time | 日期时间 | ✅ | 发起时间 |
| end_time | 日期时间 | | 结束时间 |
| current_node | 文本 | | 当前节点 |
| last_action | 文本 | | 最近动作 |
| last_action_time | 日期时间 | | 最近动作时间 |
| approver_chain | 文本 | | 审批链路 |

**明细表：审批动作表**

| 字段名 | 字段类型 | 必填 | 说明 |
|--------|---------|------|------|
| instance_id | 文本 | ✅ | 审批实例ID（关联主表） |
| node_name | 文本 | ✅ | 节点名称 |
| approver | 文本 | ✅ | 审批人 |
| action | 文本 | ✅ | 动作 |
| action_time | 日期时间 | ✅ | 动作时间 |
| comment | 文本 | | 审批意见 |

3. 记录表格的 **app_token** 和 **table_id**（在表格URL中可以看到）

#### 步骤4：配置机器人（可选，用于告警）

1. 在飞书群中，点击「设置」→「群机器人」→「添加机器人」→「自定义机器人」
2. 填写机器人名称和描述
3. 复制 **Webhook地址**

### 1.4 配置文件设置

```bash
# 复制配置模板
cp config.yaml.example config.yaml

# 编辑配置文件
vim config.yaml  # 或使用其他编辑器
```

填写以下配置项：

```yaml
dingtalk:
  app_key: "你的钉钉AppKey"
  app_secret: "你的钉钉AppSecret"

feishu:
  app_id: "你的飞书AppID"
  app_secret: "你的飞书AppSecret"
  app_token: "你的多维表格app_token"
  tables:
    main: "主表table_id"
    action: "明细表table_id"

notification:
  enabled: true
  webhook_url: "你的飞书机器人webhook地址"
```

## 二、测试运行

### 2.1 首次测试

```bash
# 测试配置文件
python -c "import yaml; yaml.safe_load(open('config.yaml'))"

# 初始化同步（同步最近7天数据）
python sync.py --init
```

### 2.2 验证数据

1. 登录飞书，查看多维表格
2. 检查是否有数据写入
3. 验证字段是否正确

### 2.3 增量同步测试

```bash
# 增量同步（默认同步最近24小时）
python sync.py
```

## 三、定时任务配置

### 3.1 Linux/Mac (crontab)

```bash
# 编辑crontab
crontab -e

# 添加以下任务
# 每天8:00, 12:00, 18:00执行增量同步
0 8,12,18 * * * cd /path/to/project && /path/to/venv/bin/python sync.py >> logs/sync.log 2>&1

# 每天23:30执行全量校验
30 23 * * * cd /path/to/project && /path/to/venv/bin/python sync.py --full-check >> logs/full_check.log 2>&1
```

### 3.2 Windows (任务计划程序)

1. 打开「任务计划程序」
2. 创建基本任务
3. 设置触发器（每天8:00, 12:00, 18:00）
4. 操作：启动程序
   - 程序：`C:\path\to\venv\Scripts\python.exe`
   - 参数：`sync.py`
   - 起始于：`C:\path\to\project`

### 3.3 使用systemd (Linux)

创建服务文件 `/etc/systemd/system/dingtalk-sync.service`:

```ini
[Unit]
Description=DingTalk Approval Sync Service
After=network.target

[Service]
Type=oneshot
User=your_user
WorkingDirectory=/path/to/project
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python sync.py
StandardOutput=append:/path/to/project/logs/sync.log
StandardError=append:/path/to/project/logs/sync_error.log

[Install]
WantedBy=multi-user.target
```

创建定时器 `/etc/systemd/system/dingtalk-sync.timer`:

```ini
[Unit]
Description=Run DingTalk Sync Daily
Requires=dingtalk-sync.service

[Timer]
OnCalendar=*-*-* 08,12,18:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

启用定时器：

```bash
sudo systemctl enable dingtalk-sync.timer
sudo systemctl start dingtalk-sync.timer
```

### 3.4 使用Docker（可选）

创建 `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "sync.py"]
```

创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  sync:
    build: .
    volumes:
      - ./config.yaml:/app/config.yaml
      - ./logs:/app/logs
      - ./checkpoint.json:/app/checkpoint.json
    environment:
      - TZ=Asia/Shanghai
```

运行：

```bash
docker-compose up -d
```

## 四、监控与维护

### 4.1 日志查看

```bash
# 查看同步日志
tail -f logs/sync.log

# 查看错误日志
grep ERROR logs/sync.log
```

### 4.2 检查点管理

```bash
# 查看检查点文件
cat checkpoint.json

# 重置检查点（从新开始同步）
rm checkpoint.json
```

### 4.3 故障排查

#### 问题1：获取token失败

- 检查应用凭据是否正确
- 确认应用权限已开通
- 检查网络连接

#### 问题2：同步数据为空

- 确认时间范围是否正确
- 检查审批流程是否有数据
- 查看日志中的错误信息

#### 问题3：写入飞书失败

- 确认飞书表格字段名与代码中一致
- 检查字段类型是否匹配
- 确认飞书应用权限已开通

### 4.4 性能优化

1. **批量处理**：调整 `batch_size` 参数
2. **并发控制**：根据API限流调整请求频率
3. **缓存优化**：token缓存减少API调用

## 五、安全建议

1. ✅ 配置文件不要提交到Git（已加入.gitignore）
2. ✅ 使用环境变量存储敏感信息（可选）
3. ✅ 定期轮换应用密钥
4. ✅ 限制服务器访问权限
5. ✅ 启用日志审计

## 六、常见问题

### Q1: 如何处理字段映射不一致？

A: 修改 `data_processor.py` 中的字段处理逻辑，或在飞书表格中添加字段别名。

### Q2: 如何同步特定审批流程？

A: 在配置文件中添加 `process_code` 配置，或在代码中过滤特定流程。

### Q3: 数据同步延迟怎么办？

A: 增加同步频率，或检查网络和API调用限制。

## 七、更新与升级

```bash
# 拉取最新代码
git pull

# 更新依赖
pip install -r requirements.txt --upgrade

# 测试新版本
python sync.py --init
```

## 八、联系支持

如有问题，请：
1. 查看日志文件
2. 检查配置文件
3. 提交Issue或联系技术支持
