# PushMatrix API 文档

## 基础信息

- **基础 URL**: `http://localhost:8000`
- **API 前缀**: `/api`
- **交互文档**: `http://localhost:8000/docs` (Swagger UI)
- **数据格式**: JSON

---

## 模块概览

| 模块 | 前缀 | 说明 |
|------|------|------|
| 账号管理 | `/api/accounts` | 账号 CRUD、分组、批量操作 |
| 代理管理 | `/api/proxies` | 代理 CRUD、测试、自动分配 |
| 群发消息 | `/api/messages` | 群发任务管理 |
| 批量私信 | `/api/direct` | 私信任务管理 |
| 批量拉人 | `/api/invites` | 拉人任务管理 |
| 账户检查 | `/api/checker` | 账号状态检测 |
| 资料管理 | `/api/profile` | 批量资料操作 |
| 任务管理 | `/api/tasks` | 统一任务管理 |
| 数据统计 | `/api/stats` | 统计数据接口 |
| 系统设置 | `/api/settings` | 系统配置管理 |

---

## 账号管理 `/api/accounts`

### GET /api/accounts/
获取账号列表。

**参数:**
- `skip` (int): 跳过条数，默认 0
- `limit` (int): 返回条数，默认 100
- `status` (str): 筛选状态 (online/offline/frozen/spam)

### POST /api/accounts/
添加新账号。

**请求体:**
```json
{
  "phone": "+1234567890",
  "session_string": "...",
  "api_id": 12345,
  "api_hash": "abcdef",
  "proxy_id": 1
}
```

### POST /api/accounts/bulk-action
批量操作账号。

**请求体:**
```json
{
  "action_type": "activate",
  "account_ids": [1, 2, 3],
  "params": {}
}
```

**支持的 action_type:**
- `activate` - 激活账号
- `check` - 检查状态
- `tag` - 修改标签
- `get-profile` - 获取资料
- `edit-profile` - 修改资料
- `privacy` - 设置隐私
- `logout-sessions` - 退出其他设备
- `export` - 导出数据

---

## 群发消息 `/api/messages`

### POST /api/messages/tasks
创建群发任务。

**请求体:**
```json
{
  "name": "任务名称",
  "account_ids": [1, 2],
  "target_groups": ["-1001234567890"],
  "message_content": "消息内容",
  "settings": {
    "interval": 30,
    "daily_limit": 100,
    "max_random_delay": 10
  }
}
```

---

## 错误码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 422 | 数据验证失败 |
| 500 | 服务器内部错误 |
