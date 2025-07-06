# 安装指南

## 环境准备

### 系统要求

- **操作系统**: Ubuntu 20.04+ / CentOS 7+ / Windows 10+ (with WSL2)
- **内存**: 最少 8GB，推荐 16GB+
- **存储**: 最少 50GB 可用空间
- **GPU**: NVIDIA GPU (可选，用于MinerU加速)

### 软件依赖

1. **Python 3.8+**
   ```bash
   python --version
   pip --version
   ```

2. **Node.js 16+**
   ```bash
   node --version
   npm --version
   ```

3. **Docker & Docker Compose**
   ```bash
   docker --version
   docker-compose --version
   ```

4. **Git**
   ```bash
   git --version
   ```

## 项目初始化

### 1. 创建项目结构

```bash
# 进入工作目录
cd f:/04_AI/01_Workplace/ragflow-mineru-integration

# 创建基础目录结构
mkdir -p {\
  docs,\
  backend/{api,services,models,utils,tests},\
  frontend/{src,public},\
  docker/{ragflow,mineru,nginx},\
  scripts,\
  config,\
  tests/{unit,integration}\
}
```

### 2. 克隆依赖项目

```bash
# 克隆Ragflow源码（用于参考和修改）
git clone https://github.com/infiniflow/ragflow.git temp/ragflow

# 克隆MinerU源码（用于集成）
git clone https://github.com/opendatalab/MinerU.git temp/mineru

# 克隆KnowFlow源码（用于参考）
git clone https://github.com/knowflow/knowflow.git temp/knowflow
```

### 3. 环境配置

#### 创建Python虚拟环境

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 升级pip
pip install --upgrade pip
```

#### 安装Python依赖

```bash
# 安装基础依赖
pip install -r requirements.txt

# 安装开发依赖
pip install -r requirements-dev.txt
```

#### 安装前端依赖

```bash
cd frontend
npm install
cd ..
```

### 4. 数据库配置

#### 启动数据库服务

```bash
# 启动MySQL和Redis
docker-compose -f docker/docker-compose-db.yml up -d
```

#### 初始化数据库

```bash
# 创建数据库
mysql -h localhost -P 3306 -u root -p -e "CREATE DATABASE ragflow_mineru;"

# 运行数据库迁移
python backend/manage.py migrate

# 创建超级用户
python backend/manage.py create_superuser
```

### 5. 配置文件设置

#### 复制配置模板

```bash
# 复制环境配置
cp config/.env.example config/.env

# 复制应用配置
cp config/app.yml.example config/app.yml
```

#### 编辑配置文件

编辑 `config/.env` 文件：

```env
# 数据库配置
DATABASE_URL=mysql://root:password@localhost:3306/ragflow_mineru
REDIS_URL=redis://localhost:6379/0

# MinerU配置
MINERU_API_URL=http://localhost:8001
MINERU_MODEL_PATH=/app/models

# MinIO配置
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# 其他配置
SECRET_KEY=your-secret-key-here
DEBUG=true
```

### 6. MinerU服务配置

#### 下载模型文件

```bash
# 创建模型目录
mkdir -p models/{pipeline,vlm}

# 下载MinerU模型（需要较长时间）
python scripts/download_models.py
```

#### 构建MinerU Docker镜像

```bash
# 构建MinerU服务镜像
docker build -t ragflow-mineru:latest docker/mineru/
```

### 7. 启动服务

#### 启动后端服务

```bash
# 启动Flask应用
python backend/app.py
```

#### 启动前端服务

```bash
# 启动React开发服务器
cd frontend
npm start
```

#### 启动MinerU服务

```bash
# 启动MinerU API服务
docker-compose -f docker/docker-compose-mineru.yml up -d
```

### 8. 验证安装

#### 检查服务状态

```bash
# 检查后端API
curl http://localhost:5000/api/health

# 检查前端
curl http://localhost:3000

# 检查MinerU服务
curl http://localhost:8001/health
```

#### 运行测试

```bash
# 运行单元测试
python -m pytest tests/unit/

# 运行集成测试
python -m pytest tests/integration/
```

## 开发环境配置

### IDE配置

#### VSCode配置

创建 `.vscode/settings.json`：

```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "files.exclude": {
    "**/__pycache__": true,
    "**/node_modules": true,
    "**/.git": true
  }
}
```

#### 代码格式化配置

创建 `.pre-commit-config.yaml`：

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
        language_version: python3
  - repo: https://github.com/pycqa/isort
    rev: 5.10.1
    hooks:
      - id: isort
  - repo: https://github.com/pycqa/flake8
    rev: 4.0.1
    hooks:
      - id: flake8
```

### 调试配置

#### 后端调试

创建 `.vscode/launch.json`：

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Flask",
      "type": "python",
      "request": "launch",
      "program": "backend/app.py",
      "env": {
        "FLASK_ENV": "development",
        "FLASK_DEBUG": "1"
      },
      "console": "integratedTerminal"
    }
  ]
}
```

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查MySQL服务是否启动
   - 验证数据库配置信息
   - 确认防火墙设置

2. **MinerU模型下载失败**
   - 检查网络连接
   - 使用代理或镜像源
   - 手动下载模型文件

3. **前端编译错误**
   - 清除node_modules并重新安装
   - 检查Node.js版本兼容性
   - 更新npm到最新版本

4. **Docker服务启动失败**
   - 检查Docker守护进程状态
   - 验证docker-compose文件语法
   - 查看容器日志

### 日志查看

```bash
# 查看应用日志
tail -f logs/app.log

# 查看Docker容器日志
docker logs ragflow-mineru

# 查看数据库日志
docker logs ragflow-mysql
```

### 性能优化

1. **数据库优化**
   - 配置合适的连接池大小
   - 添加必要的索引
   - 定期清理日志

2. **缓存配置**
   - 配置Redis缓存策略
   - 启用应用级缓存
   - 使用CDN加速静态资源

3. **并发优化**
   - 配置合适的工作进程数
   - 使用负载均衡
   - 启用异步处理

## 下一步

安装完成后，请参考以下文档继续开发：

- [开发指南](development.md)
- [API文档](api.md)
- [部署指南](deployment.md)
- [贡献指南](contributing.md)