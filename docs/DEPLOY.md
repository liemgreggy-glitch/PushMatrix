# 部署文档

## 宝塔面板部署（推荐）

### 环境要求

- Ubuntu 20.04 / 22.04
- Python 3.10+
- Node.js 18+
- Redis 6+
- PostgreSQL 13+（可选，默认使用 SQLite）

### 步骤

#### 1. 安装宝塔面板

```bash
wget -O install.sh https://download.bt.cn/install/install-ubuntu_6.0.sh
sudo bash install.sh
```

#### 2. 在宝塔面板安装组件

- Nginx
- Redis
- Python 管理器（安装 3.10+）
- PM2 或 Supervisor

#### 3. 部署后端

```bash
# 上传项目到服务器
cd /www/wwwroot/PushMatrix/backend

# 创建虚拟环境
python3.10 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp ../../.env.example .env
nano .env  # 填入配置

# 测试启动
uvicorn main:app --host 0.0.0.0 --port 8000
```

#### 4. 配置 Supervisor

```bash
# 复制配置文件
cp /www/wwwroot/PushMatrix/deploy/supervisor.conf /etc/supervisor/conf.d/pushmatrix.conf

# 重新加载配置
supervisorctl reread
supervisorctl update
supervisorctl start pushmatrix
```

#### 5. 配置 Nginx

```bash
# 在宝塔面板 -> 网站 -> 添加站点
# 域名: your-domain.com
# 配置反向代理到 127.0.0.1:8000

# 或直接使用配置文件
cp /www/wwwroot/PushMatrix/deploy/nginx.conf /etc/nginx/conf.d/pushmatrix.conf
nginx -t && nginx -s reload
```

---

## Docker 部署

```bash
cd /www/wwwroot/PushMatrix

# 启动所有服务
docker-compose -f deploy/docker-compose.yml up -d

# 查看日志
docker-compose -f deploy/docker-compose.yml logs -f

# 停止
docker-compose -f deploy/docker-compose.yml down
```

---

## 前端打包 (生成 Windows EXE)

```bash
cd frontend

# 安装依赖
npm install

# 先构建 Vue 静态文件
npm run build

# 打包 Electron（需要 Windows 环境或 Wine）
npm run build
```

生成的安装包在 `frontend/dist/electron/` 目录。

---

## 防火墙配置

```bash
# 开放端口
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8000/tcp  # 仅内网访问时
```
