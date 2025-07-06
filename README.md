# Ragflow + MinerU 集成项目

## 项目概述

本项目旨在在Ragflow中集成MinerU文档解析功能、多用户管理和多并发支持，提升文档处理能力和系统可扩展性。

## 项目目标

1. **MinerU文档解析集成**: 集成高精度的MinerU文档解析引擎
2. **多用户权限管理**: 实现细粒度的用户权限控制系统
3. **多并发支持**: 优化系统架构以支持多用户并发访问

## 技术栈

- **后端**: Python, Flask, Peewee ORM
- **前端**: React, TypeScript, Ant Design
- **数据库**: MySQL/PostgreSQL, Redis
- **AI引擎**: MinerU, CUDA
- **容器化**: Docker, Docker Compose
- **存储**: MinIO
- **搜索**: Elasticsearch/OpenSearch

## 项目结构

```
ragflow-mineru-integration/
├── docs/                    # 项目文档
├── backend/                 # 后端代码
│   ├── api/                # API层
│   ├── services/           # 服务层
│   ├── models/             # 数据模型
│   └── utils/              # 工具函数
├── frontend/               # 前端代码
├── docker/                 # Docker配置
├── scripts/                # 部署脚本
├── tests/                  # 测试代码
└── config/                 # 配置文件
```

## 快速开始

### 环境要求

- Python 3.8+
- Node.js 16+
- Docker & Docker Compose
- NVIDIA GPU (可选，用于MinerU加速)

### 安装步骤

1. 克隆项目
2. 安装依赖
3. 配置环境变量
4. 启动服务

详细步骤请参考 `docs/installation.md`

## 开发指南

请参考 `docs/development.md` 了解开发规范和贡献指南。

## 许可证

MIT License
