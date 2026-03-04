# 开发文档

## 开发环境搭建

### 后端开发

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp ../.env.example .env

# 以开发模式启动（自动重载）
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

访问 `http://localhost:8000/docs` 查看 Swagger UI。

### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 仅启动 Vite 开发服务器（不含 Electron）
npm run preview

# 同时启动 Electron + Vue
npm run dev
```

---

## 代码结构说明

### 后端

```
backend/
├── api/           # FastAPI 路由
│   ├── accounts.py    # 账号管理 API
│   ├── proxies.py     # 代理管理 API
│   ├── messages.py    # 群发消息 API
│   ├── direct.py      # 批量私信 API
│   ├── invites.py     # 批量拉人 API
│   ├── checker.py     # 账户检查 API
│   ├── profile.py     # 资料管理 API
│   ├── tasks.py       # 任务管理 API
│   ├── stats.py       # 数据统计 API
│   └── settings.py    # 系统设置 API
├── core/          # 核心功能模块
│   ├── telegram.py         # Telethon 封装
│   ├── account_manager.py  # 账号池管理
│   ├── message_sender.py   # 消息发送器
│   ├── proxy_manager.py    # 代理管理器
│   └── rate_limiter.py     # 风控限流
├── models/        # SQLAlchemy ORM 模型
├── schemas/       # Pydantic 数据模型
├── database/      # 数据库连接配置
├── config.py      # 应用配置
└── main.py        # FastAPI 应用入口
```

### 前端

```
frontend/src/renderer/
├── views/         # 页面组件
├── components/    # 公共组件
│   └── Layout/   # 布局组件
├── store/         # Pinia 状态管理
├── api/           # API 请求封装
├── router/        # Vue Router 配置
└── assets/styles/ # 全局样式
```

---

## 添加新 API 端点

1. 在 `backend/api/` 下找到对应文件
2. 添加新的路由函数，返回模拟数据
3. 在 `backend/schemas/` 中添加对应的 Pydantic 模型（可选）
4. 在前端 `frontend/src/renderer/api/index.js` 中添加调用方法

示例:
```python
@router.get("/new-endpoint")
async def new_endpoint():
    """新接口说明"""
    # TODO: 实现真实逻辑
    return {"data": "mock"}
```

---

## 添加新页面

1. 在 `frontend/src/renderer/views/` 下创建 `.vue` 文件
2. 在 `frontend/src/renderer/router/index.js` 中注册路由
3. 在 `frontend/src/renderer/components/Layout/Sidebar.vue` 中添加菜单项

---

## 代码规范

- Python: 遵循 PEP 8，使用 4 空格缩进
- JavaScript/Vue: 使用 2 空格缩进，`<script setup>` 语法
- API 命名: RESTful 风格，使用复数名词
- 注释: 所有 API 端点需有中文说明
