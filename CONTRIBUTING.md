# 贡献指南

感谢您对 RAGFlow + MinerU 集成项目的关注！我们欢迎所有形式的贡献，包括但不限于代码、文档、测试、反馈和建议。

## 如何贡献

### 报告问题

如果您发现了 bug 或有功能建议，请通过以下方式报告：

1. 在 [GitHub Issues](https://github.com/your-org/ragflow-mineru-integration/issues) 中搜索是否已有相关问题
2. 如果没有找到，请创建新的 issue
3. 使用清晰的标题和详细的描述
4. 提供复现步骤（对于 bug）
5. 包含相关的环境信息

### 提交代码

#### 开发环境设置

1. **Fork 项目**
   ```bash
   git clone https://github.com/your-username/ragflow-mineru-integration.git
   cd ragflow-mineru-integration
   ```

2. **设置开发环境**
   ```bash
   # 后端环境
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements-dev.txt
   
   # 前端环境
   cd ../frontend
   npm install
   ```

3. **配置环境变量**
   ```bash
   cp config/.env.example config/.env
   # 编辑 .env 文件，配置必要的环境变量
   ```

4. **启动开发服务**
   ```bash
   # 启动后端
   cd backend
   python app.py
   
   # 启动前端
   cd frontend
   npm run dev
   ```

#### 代码规范

**Python 代码规范**
- 遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 规范
- 使用 `black` 进行代码格式化
- 使用 `flake8` 进行代码检查
- 使用 `mypy` 进行类型检查

```bash
# 格式化代码
black .

# 检查代码
flake8 .
mypy .
```

**TypeScript/React 代码规范**
- 遵循 ESLint 和 Prettier 配置
- 使用 TypeScript 严格模式
- 组件使用函数式组件和 Hooks
- 遵循 React 最佳实践

```bash
# 格式化代码
npm run format

# 检查代码
npm run lint
npm run type-check
```

#### Git 提交规范

我们使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**类型说明：**
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式调整（不影响功能）
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

**示例：**
```
feat(auth): add two-factor authentication

fix(api): resolve document upload timeout issue

docs: update installation guide
```

#### Pull Request 流程

1. **创建功能分支**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **开发和测试**
   - 编写代码
   - 添加或更新测试
   - 确保所有测试通过
   - 更新相关文档

3. **提交代码**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   git push origin feature/your-feature-name
   ```

4. **创建 Pull Request**
   - 在 GitHub 上创建 PR
   - 填写 PR 模板
   - 等待代码审查
   - 根据反馈进行修改

### 测试

#### 后端测试

```bash
cd backend

# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_auth.py

# 生成覆盖率报告
pytest --cov=app tests/
```

#### 前端测试

```bash
cd frontend

# 运行单元测试
npm run test

# 运行测试并生成覆盖率
npm run test:coverage

# 运行 E2E 测试
npm run test:e2e
```

### 文档

#### 文档类型

- **API 文档**: 使用 OpenAPI/Swagger 规范
- **用户文档**: Markdown 格式，存放在 `docs/` 目录
- **代码文档**: 使用 docstring 和注释

#### 文档更新

- 新功能必须包含相应文档
- API 变更需要更新 API 文档
- 重要配置变更需要更新安装指南

## 开发指南

### 项目架构

```
ragflow-mineru-integration/
├── backend/           # Python 后端服务
│   ├── api/          # API 路由
│   ├── services/     # 业务逻辑
│   ├── models/       # 数据模型
│   └── utils/        # 工具函数
├── frontend/         # React 前端应用
│   ├── src/
│   │   ├── components/  # React 组件
│   │   ├── pages/      # 页面组件
│   │   ├── services/   # API 服务
│   │   └── store/      # 状态管理
├── docs/             # 项目文档
└── docker/           # Docker 配置
```

### 技术栈

**后端**
- Python 3.8+
- Flask/FastAPI
- SQLAlchemy/Peewee
- Redis
- Celery
- Elasticsearch

**前端**
- React 18
- TypeScript
- Ant Design
- Redux Toolkit
- Vite

**基础设施**
- Docker
- MySQL/PostgreSQL
- MinIO
- Nginx

### 常见开发任务

#### 添加新的 API 端点

1. 在 `backend/api/` 中创建路由
2. 在 `backend/services/` 中实现业务逻辑
3. 添加相应的测试
4. 更新 API 文档

#### 添加新的前端页面

1. 在 `frontend/src/pages/` 中创建页面组件
2. 在路由配置中添加路由
3. 创建相应的 API 服务
4. 添加状态管理（如需要）
5. 编写测试

#### 添加新的数据模型

1. 在 `backend/models/` 中定义模型
2. 创建数据库迁移
3. 更新相关的 API 和服务
4. 添加测试数据和测试用例

## 发布流程

### 版本号规范

我们使用 [语义化版本](https://semver.org/) 规范：

- `MAJOR.MINOR.PATCH`
- `MAJOR`: 不兼容的 API 修改
- `MINOR`: 向下兼容的功能性新增
- `PATCH`: 向下兼容的问题修正

### 发布步骤

1. 更新版本号
2. 更新 CHANGELOG.md
3. 创建 release 分支
4. 进行最终测试
5. 合并到 main 分支
6. 创建 Git tag
7. 发布到生产环境

## 社区

### 沟通渠道

- **GitHub Issues**: 问题报告和功能请求
- **GitHub Discussions**: 一般讨论和问答
- **邮件**: technical-support@ragflow.com

### 行为准则

我们致力于为所有人提供友好、安全和欢迎的环境。请遵循以下原则：

- 使用友好和包容的语言
- 尊重不同的观点和经验
- 优雅地接受建设性批评
- 关注对社区最有利的事情
- 对其他社区成员表示同理心

## 许可证

通过贡献代码，您同意您的贡献将在 [MIT License](LICENSE) 下授权。

## 感谢

感谢所有为这个项目做出贡献的开发者！您的努力让这个项目变得更好。

---

如果您有任何问题，请随时通过 GitHub Issues 或邮件联系我们。我们很乐意帮助您开始贡献！