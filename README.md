# PushMatrix

**PushMatrix** 是一个专为 Telegram 营销设计的多功能工具，提供账号管理、群发消息、批量私信、批量拉人等功能，带有漂亮的深色主题桌面应用界面。

---

## 📋 功能列表

| 功能模块 | 说明 |
|---------|------|
| 📊 数据面板 | 总览统计、趋势图、账号状态分布 |
| 👤 账号管理 | 多账号导入、分组管理、批量操作 |
| 🔑 代理管理 | 代理池管理、自动分配、连通性测试 |
| 📤 群发消息 | 向群组/频道批量发送消息 |
| 💬 批量私信 | 向用户批量发送个性化私信 |
| 👥 批量拉人 | 批量将用户添加到群组 |
| 🔍 账户检查 | 检测封禁、限制、健康度评分 |
| 🎯 资料管理 | 批量获取/修改账号资料、隐私设置 |
| 📈 数据统计 | 多维度数据分析与报表导出 |
| ⚙️ 系统设置 | API配置、风控设置、数据库管理 |

---

## 🏗️ 技术架构

- **后端**: Python 3.10+ / FastAPI / SQLAlchemy
- **前端**: Electron / Vue 3 / Element Plus / Pinia
- **数据库**: PostgreSQL (生产) / SQLite (开发)
- **任务队列**: Celery + Redis
- **Telegram**: Telethon

---

## 🚀 快速开始

### 后端启动

```bash
cd backend

# 安装依赖
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 配置环境变量
cp ../.env.example .env
# 编辑 .env 填入 Telegram API 信息

# 启动服务
python main.py
# 或
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

服务启动后访问 [http://localhost:8000/docs](http://localhost:8000/docs) 查看 API 文档。

### 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 开发模式（同时启动 Vite + Electron）
npm run dev

# 构建 Electron 应用
npm run build
```

---

## 📁 项目结构

```
PushMatrix/
├── backend/           # FastAPI 后端
│   ├── api/          # API 路由
│   ├── core/         # 核心功能模块
│   ├── models/       # 数据库模型
│   ├── schemas/      # Pydantic 数据模型
│   ├── database/     # 数据库配置
│   ├── config.py     # 配置文件
│   └── main.py       # 应用入口
├── frontend/          # Electron + Vue 3 前端
│   └── src/
│       ├── main/     # Electron 主进程
│       └── renderer/ # Vue 渲染进程
│           ├── views/      # 页面组件
│           ├── components/ # 公共组件
│           ├── store/      # Pinia 状态管理
│           ├── api/        # API 封装
│           └── router/     # 路由配置
├── deploy/            # 部署配置
├── docs/              # 文档
└── .env.example       # 环境变量示例
```

---

## 📦 部署

详见 [docs/DEPLOY.md](docs/DEPLOY.md)

---

## 🔒 注意事项

- **合规使用**: 请确保遵守 Telegram 服务条款，不得用于发送垃圾信息
- **账号安全**: 妥善保管 Session 文件，不要将其提交到代码仓库
- **风控合理**: 遵守平台规则，设置合理的发送间隔和日限额

---

## 📄 License

MIT
