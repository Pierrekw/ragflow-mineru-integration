# RAGFlow + MinerU 集成项目

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![React](https://img.shields.io/badge/React-18.x-blue.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-blue.svg)](https://www.typescriptlang.org/)
[![Ant Design](https://img.shields.io/badge/Ant%20Design-5.x-blue.svg)](https://ant.design/)

## 项目概述

本项目是一个企业级的RAG（检索增强生成）平台，集成了MinerU高精度文档解析引擎，提供完整的文档处理、知识库管理、多用户权限控制和智能问答功能。系统采用现代化的微服务架构，支持高并发访问和水平扩展。

## 核心功能

### 🚀 文档处理
- **MinerU集成**: 高精度PDF、Word、Excel等文档解析
- **多格式支持**: 支持20+种文档格式
- **智能分块**: 基于语义的文档分块策略
- **OCR识别**: 图片和扫描文档的文字识别

### 📚 知识库管理
- **多知识库**: 支持创建和管理多个独立知识库
- **版本控制**: 文档版本管理和回滚功能
- **标签系统**: 灵活的文档分类和标签管理
- **搜索优化**: 基于向量和关键词的混合搜索

### 👥 用户管理
- **多租户架构**: 完整的多租户隔离
- **角色权限**: 细粒度的RBAC权限控制
- **SSO集成**: 支持LDAP、OAuth2等单点登录
- **审计日志**: 完整的用户操作审计

### 💬 智能问答
- **多模型支持**: 集成多种大语言模型
- **上下文管理**: 智能的对话上下文维护
- **引用溯源**: 答案来源的精确定位
- **API接口**: 完整的RESTful API

### 📊 监控运维
- **实时监控**: 系统性能和资源使用监控
- **日志管理**: 结构化日志收集和分析
- **告警通知**: 多渠道的异常告警
- **健康检查**: 服务健康状态检测

## 技术架构

### 后端技术栈
- **框架**: Python 3.8+, Flask/FastAPI
- **ORM**: Peewee/SQLAlchemy
- **缓存**: Redis 6.0+
- **消息队列**: Celery + Redis
- **搜索引擎**: Elasticsearch 8.x
- **向量数据库**: Milvus/Qdrant

### 前端技术栈
- **框架**: React 18.x + TypeScript 5.x
- **UI库**: Ant Design 5.x
- **状态管理**: Redux Toolkit
- **路由**: React Router 6.x
- **构建工具**: Vite 4.x
- **图表**: ECharts + echarts-for-react

### 基础设施
- **容器化**: Docker + Docker Compose
- **数据库**: MySQL 8.0+ / PostgreSQL 14+
- **对象存储**: MinIO / AWS S3
- **负载均衡**: Nginx
- **监控**: Prometheus + Grafana

## 项目结构

```
ragflow-mineru-integration/
├── docs/                    # 项目文档
│   ├── api/                # API文档
│   ├── deployment/         # 部署文档
│   └── development/        # 开发文档
├── backend/                 # 后端服务
│   ├── api/                # API路由和控制器
│   ├── services/           # 业务逻辑服务
│   ├── models/             # 数据模型
│   ├── utils/              # 工具函数
│   ├── middleware/         # 中间件
│   └── config/             # 配置文件
├── frontend/               # 前端应用
│   ├── src/
│   │   ├── components/     # React组件
│   │   ├── pages/          # 页面组件
│   │   ├── services/       # API服务
│   │   ├── store/          # Redux状态管理
│   │   ├── types/          # TypeScript类型定义
│   │   └── styles/         # 样式文件
│   ├── public/             # 静态资源
│   └── package.json        # 前端依赖
├── docker/                 # Docker配置
│   ├── backend/            # 后端Docker文件
│   ├── frontend/           # 前端Docker文件
│   └── docker-compose.yml  # 容器编排
├── scripts/                # 部署和工具脚本
├── tests/                  # 测试代码
├── config/                 # 环境配置
└── README.md               # 项目说明
```

## 快速开始

### 环境要求

- **操作系统**: Linux/macOS/Windows
- **Python**: 3.8+ (推荐3.10+)
- **Node.js**: 16+ (推荐18+)
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **内存**: 最小8GB，推荐16GB+
- **存储**: 最小50GB可用空间
- **GPU**: NVIDIA GPU (可选，用于MinerU加速)

### 快速部署

#### 1. 克隆项目

```bash
git clone https://github.com/your-org/ragflow-mineru-integration.git
cd ragflow-mineru-integration
```

#### 2. 环境配置

```bash
# 复制环境配置文件
cp config/.env.example config/.env

# 编辑配置文件
vim config/.env
```

#### 3. Docker部署（推荐）

```bash
# 构建和启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

#### 4. 本地开发部署

**后端服务**:
```bash
cd backend
pip install -r requirements.txt
python app.py
```

**前端服务**:
```bash
cd frontend
npm install
npm run dev
```

### 访问应用

- **前端界面**: http://localhost:3000
- **API文档**: http://localhost:8000/docs
- **管理后台**: http://localhost:3000/admin

### 默认账户

- **管理员**: admin@example.com / admin123
- **普通用户**: user@example.com / user123

## 功能模块

### 前端页面

| 页面 | 路径 | 功能描述 |
|------|------|----------|
| 仪表板 | `/dashboard` | 系统概览、统计数据、快速操作 |
| 文档管理 | `/documents` | 文档上传、解析、管理、预览 |
| 知识库 | `/knowledge-base` | 知识库创建、配置、向量化管理 |
| 智能问答 | `/chat` | 多轮对话、知识检索、答案生成 |
| 用户管理 | `/users` | 用户CRUD、角色分配、权限管理 |
| API管理 | `/api` | API密钥、调用统计、接口文档 |
| 系统设置 | `/settings` | 系统配置、模型管理、参数调优 |
| 监控中心 | `/monitoring` | 性能监控、日志查看、告警管理 |
| 个人中心 | `/profile` | 个人信息、偏好设置、安全配置 |
| 帮助中心 | `/help` | 使用指南、API文档、常见问题 |

### API接口

| 模块 | 端点 | 功能 |
|------|------|------|
| 认证 | `/api/auth/*` | 登录、注册、权限验证 |
| 文档 | `/api/documents/*` | 文档CRUD、解析、搜索 |
| 知识库 | `/api/knowledge-base/*` | 知识库管理、向量操作 |
| 问答 | `/api/chat/*` | 对话管理、问答接口 |
| 用户 | `/api/users/*` | 用户管理、角色权限 |
| 系统 | `/api/system/*` | 系统配置、监控数据 |

## 开发指南

### 代码规范

- **Python**: 遵循PEP 8规范，使用black格式化
- **TypeScript**: 遵循ESLint + Prettier规范
- **Git**: 使用Conventional Commits规范
- **API**: 遵循RESTful设计原则

### 测试

```bash
# 后端测试
cd backend
pytest tests/

# 前端测试
cd frontend
npm run test

# E2E测试
npm run test:e2e
```

### 贡献指南

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

## 部署指南

### 生产环境部署

详细的生产环境部署指南请参考 [部署文档](docs/deployment/production.md)

### 性能优化

- **数据库优化**: 索引优化、查询优化、连接池配置
- **缓存策略**: Redis缓存、CDN加速、静态资源优化
- **负载均衡**: Nginx配置、服务器集群、容器编排
- **监控告警**: Prometheus监控、Grafana可视化、告警规则

## 常见问题

### Q: 如何配置MinerU？
A: 请参考 [MinerU配置指南](docs/mineru-setup.md)

### Q: 如何添加新的文档格式支持？
A: 请参考 [文档解析扩展指南](docs/document-parser-extension.md)

### Q: 如何集成自定义大语言模型？
A: 请参考 [模型集成指南](docs/model-integration.md)

## 技术支持

- **文档**: [在线文档](https://docs.example.com)
- **Issues**: [GitHub Issues](https://github.com/your-org/ragflow-mineru-integration/issues)
- **讨论**: [GitHub Discussions](https://github.com/your-org/ragflow-mineru-integration/discussions)
- **邮件**: support@example.com

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 致谢

- [RAGFlow](https://github.com/infiniflow/ragflow) - 原始RAG框架
- [MinerU](https://github.com/opendatalab/MinerU) - 文档解析引擎
- [Ant Design](https://ant.design/) - UI组件库
- 所有贡献者和社区成员
