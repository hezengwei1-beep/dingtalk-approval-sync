# 下一步操作指南

## 一、立即执行的步骤

### 步骤1：检查系统环境

```bash
# 运行配置检查脚本
python test_config.py
```

这个脚本会自动检查：
- ✅ 配置文件是否存在
- ✅ 依赖包是否安装
- ✅ 代码模块是否完整
- ✅ 目录结构是否正确

### 步骤2：创建配置文件

如果 `config.yaml` 不存在或未填写：

```bash
# 复制配置文件模板
cp config.yaml.example config.yaml

# 编辑配置文件（使用你喜欢的编辑器）
vim config.yaml
# 或
nano config.yaml
# 或使用VS Code
code config.yaml
```

### 步骤3：安装依赖包

如果依赖包未安装：

```bash
# 确保虚拟环境已激活
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 步骤4：配置应用信息

#### 4.1 钉钉应用配置

1. **访问钉钉开放平台**
   - 网址：https://open.dingtalk.com/
   - 使用企业管理员账号登录

2. **创建企业内部应用**
   - 进入「应用开发」→「企业内部开发」
   - 选择「H5微应用」或「移动应用」
   - 填写应用名称和描述
   - **记录 AppKey 和 AppSecret**

3. **开通权限**
   - 在应用管理页面，进入「权限管理」
   - 开通以下权限：
     - ✅ 工作台管理 (`workbench_management`)
     - ✅ 审批流程管理（只读）(`process_management_read`)
     - ✅ 通讯录管理（只读）(`contact_management_read`)

4. **填写到配置文件**
   ```yaml
   dingtalk:
     app_key: "你的AppKey"
     app_secret: "你的AppSecret"
   ```

#### 4.2 飞书应用配置

1. **访问飞书开发者后台**
   - 网址：https://open.feishu.cn/app
   - 使用企业管理员账号登录

2. **创建企业自建应用**
   - 点击「创建企业自建应用」
   - 填写应用名称和描述
   - **记录 App ID 和 App Secret**

3. **开通权限**
   - 进入「权限管理」
   - 开通以下权限：
     - ✅ 查看、编辑和管理多维表格 (`bitable:app`)
     - ✅ 查看多维表格 (`bitable:app:readonly`)
     - ✅ 编辑和管理多维表格中的记录 (`bitable:table`)
     - ✅ 查看多维表格中的记录 (`bitable:table:readonly`)

4. **创建飞书多维表格**

   a. 在飞书中创建新的多维表格应用
   
   b. 创建「审批实例表」（主表）
   
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
   
   c. 创建「审批动作表」（明细表，可选）
   
   | 字段名 | 字段类型 | 必填 |
   |--------|---------|------|
   | instance_id | 文本 | ✅ |
   | node_name | 文本 | ✅ |
   | approver | 文本 | ✅ |
   | action | 文本 | ✅ |
   | action_time | 日期时间 | ✅ |
   | comment | 文本 | |
   
   d. **记录 app_token 和 table_id**
   - `app_token`：在表格URL中可以看到（类似 `bascnXXXXXXXXXX`）
   - `table_id`：在表格URL中可以看到（类似 `tblXXXXXXXXXX`）

5. **填写到配置文件**
   ```yaml
   feishu:
     app_id: "你的AppID"
     app_secret: "你的AppSecret"
     app_token: "你的app_token"
     tables:
       main: "主表table_id"
       action: "明细表table_id"  # 可选，如果不想同步明细表可以省略
   ```

#### 4.3 配置飞书机器人（可选，用于告警）

1. 在飞书群中，点击「设置」→「群机器人」→「添加机器人」→「自定义机器人」
2. 填写机器人名称和描述
3. 复制 **Webhook地址**
4. 填写到配置文件：
   ```yaml
   notification:
     enabled: true
     webhook_url: "你的webhook地址"
   ```

## 二、测试验证

### 步骤5：验证配置

```bash
# 再次运行配置检查脚本
python test_config.py
```

确保所有检查都通过。

### 步骤6：首次测试运行

```bash
# 初始化同步（同步最近7天数据，用于测试）
python sync.py --init
```

**预期结果：**
- ✅ 程序正常运行
- ✅ 日志文件 `logs/sync.log` 中有输出
- ✅ 飞书多维表格中有数据写入

**如果出现错误：**
- 查看 `logs/sync.log` 中的错误信息
- 检查配置文件是否正确
- 确认应用权限是否开通
- 参考 `DEPLOYMENT.md` 中的故障排查章节

### 步骤7：验证数据

1. 登录飞书，打开多维表格
2. 检查「审批实例表」是否有数据
3. 抽查几条记录，验证字段是否正确：
   - `instance_id` 不为空
   - `title` 不为空
   - `status` 为中文状态（已同意/已拒绝/审批中等）
   - `start_time` 格式正确
   - 其他字段是否符合预期

## 三、生产部署

### 步骤8：配置定时任务

#### Linux/Mac (推荐使用crontab)

```bash
# 编辑crontab
crontab -e

# 添加以下任务（根据实际情况修改路径）
# 每天8:00, 12:00, 18:00执行增量同步
0 8,12,18 * * * cd /Users/mac/Projects/钉钉审批流程 && /Users/mac/Projects/钉钉审批流程/venv/bin/python sync.py >> /Users/mac/Projects/钉钉审批流程/logs/sync.log 2>&1

# 每天23:30执行全量校验
30 23 * * * cd /Users/mac/Projects/钉钉审批流程 && /Users/mac/Projects/钉钉审批流程/venv/bin/python sync.py --full-check >> /Users/mac/Projects/钉钉审批流程/logs/full_check.log 2>&1
```

#### Windows (使用任务计划程序)

1. 打开「任务计划程序」
2. 创建基本任务
3. 设置触发器（每天8:00, 12:00, 18:00）
4. 操作：启动程序
   - 程序：`C:\path\to\venv\Scripts\python.exe`
   - 参数：`sync.py`
   - 起始于：`C:\path\to\项目目录`

### 步骤9：监控和维护

#### 查看日志

```bash
# 实时查看日志
tail -f logs/sync.log

# 查看最近的错误
grep ERROR logs/sync.log | tail -20
```

#### 检查同步状态

```bash
# 查看检查点文件
cat checkpoint.json

# 手动触发同步测试
python sync.py
```

## 四、常见问题快速解决

### Q1: 配置文件找不到？

```bash
# 确保文件存在
ls -la config.yaml

# 如果不存在，从模板复制
cp config.yaml.example config.yaml
```

### Q2: 模块导入失败？

```bash
# 确保依赖已安装
pip install -r requirements.txt

# 确保虚拟环境已激活
source venv/bin/activate  # Linux/Mac
```

### Q3: 获取token失败？

- 检查配置文件中的 AppKey/AppSecret 是否正确
- 确认应用权限已开通
- 检查网络连接
- 查看日志中的具体错误信息

### Q4: 写入飞书失败？

- 确认飞书表格字段名与代码中的字段名完全一致
- 检查字段类型是否匹配（文本/数字/日期时间）
- 确认飞书应用权限已开通
- 检查 app_token 和 table_id 是否正确

### Q5: 数据为空？

- 确认时间范围内有审批记录
- 尝试使用 `--init` 参数同步更多数据
- 检查日志中的错误信息
- 确认审批流程是否有权限访问

## 五、验收清单

完成以下检查项后，系统即可投入生产使用：

- [ ] 配置文件已填写完整
- [ ] 配置检查脚本全部通过
- [ ] 首次测试运行成功
- [ ] 飞书表格中有数据写入
- [ ] 数据字段验证正确
- [ ] 定时任务已配置
- [ ] 日志正常记录
- [ ] 通知功能正常（如已配置）

## 六、获取帮助

如遇问题：

1. **查看日志**：`logs/sync.log`
2. **运行检查脚本**：`python test_config.py`
3. **参考文档**：
   - `README.md` - 项目说明
   - `QUICK_START.md` - 快速开始
   - `DEPLOYMENT.md` - 部署指南
   - `PROJECT_STRUCTURE.md` - 项目结构
   - `dingtalk_to_feishu_plan.md` - 方案文档
4. **提交Issue**或联系技术支持

---

**祝使用顺利！** 🚀
