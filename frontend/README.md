# Ragflow-MinerU 集成平台 - 前端

基于 React 18 + TypeScript + Ant Design Pro 构建的现代化前端应用，为 Ragflow-MinerU 集成项目提供用户界面。

## 🚀 技术栈

- **框架**: React 18 + TypeScript
- **构建工具**: Vite 4
- **UI 库**: Ant Design 5
- **状态管理**: Redux Toolkit
- **路由**: React Router 6
- **样式**: Tailwind CSS + Less
- **HTTP 客户端**: Axios
- **实时通信**: Socket.IO Client
- **图表**: ECharts
- **代码规范**: ESLint + Prettier
- **测试**: Vitest + Testing Library

## 📦 项目结构

```
frontend/
├── public/                 # 静态资源
├── src/
│   ├── components/         # 组件
│   │   ├── common/        # 通用组件
│   │   ├── layouts/       # 布局组件
│   │   └── forms/         # 表单组件
│   ├── pages/             # 页面组件
│   │   ├── auth/          # 认证页面
│   │   ├── dashboard/     # 仪表板
│   │   ├── documents/     # 文档管理
│   │   ├── users/         # 用户管理
│   │   ├── profile/       # 个人资料
│   │   └── settings/      # 系统设置
│   ├── store/             # Redux 状态管理
│   │   └── slices/        # Redux slices
│   ├── services/          # API 服务
│   ├── hooks/             # 自定义 Hooks
│   ├── utils/             # 工具函数
│   ├── types/             # TypeScript 类型定义
│   ├── styles/            # 样式文件
│   ├── App.tsx            # 主应用组件
│   └── main.tsx           # 应用入口
├── package.json           # 依赖配置
├── vite.config.ts         # Vite 配置
├── tsconfig.json          # TypeScript 配置
├── tailwind.config.js     # Tailwind 配置
└── README.md              # 项目说明
```

## 🛠️ 开发环境设置

### 前置要求

- Node.js >= 16.0.0
- npm >= 8.0.0 或 yarn >= 1.22.0

### 安装依赖

```bash
# 使用 npm
npm install

# 或使用 yarn
yarn install
```

### 环境配置

1. 复制环境变量文件：
```bash
cp .env.example .env.development
```

2. 根据需要修改 `.env.development` 中的配置

### 启动开发服务器

```bash
# 使用 npm
npm run dev

# 或使用 yarn
yarn dev
```

应用将在 `http://localhost:3000` 启动

## 📝 可用脚本

```bash
# 开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览生产构建
npm run preview

# 代码检查
npm run lint

# 代码格式化
npm run format

# 类型检查
npm run type-check

# 运行测试
npm run test

# 运行测试并生成覆盖率报告
npm run test:coverage
```

## 🎨 主要功能

### 用户认证
- 用户登录/注册
- 密码重置
- 两步验证
- 会话管理

### 文档管理
- 文档上传（支持拖拽）
- 文档解析（集成 MinerU）
- 解析结果查看
- 文档搜索和过滤
- 批量操作

### 用户管理
- 用户列表和详情
- 角色权限管理
- 用户状态管理
- 批量操作

### 系统监控
- 实时数据仪表板
- 系统性能监控
- 任务状态跟踪
- 错误日志查看

### 个性化设置
- 主题切换（明/暗模式）
- 语言切换（中/英文）
- 个人资料管理
- 系统偏好设置

## 🔧 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `VITE_API_BASE_URL` | API 基础地址 | `http://localhost:5000/api` |
| `VITE_SOCKET_URL` | WebSocket 地址 | `http://localhost:5000` |
| `VITE_MAX_FILE_SIZE` | 最大文件大小(MB) | `100` |
| `VITE_ALLOWED_FILE_TYPES` | 允许的文件类型 | `pdf,doc,docx,txt,md,html,rtf,odt` |

### 主题配置

应用支持明暗两种主题，可以通过以下方式切换：
- 用户界面中的主题切换器
- 系统偏好设置
- 环境变量 `VITE_DEFAULT_THEME`

### 国际化

目前支持中文和英文两种语言：
- 中文 (zh-CN)
- 英文 (en-US)

## 🚀 部署

### 构建生产版本

```bash
npm run build
```

构建文件将生成在 `dist/` 目录中。

### Docker 部署

```bash
# 构建镜像
docker build -t ragflow-mineru-frontend .

# 运行容器
docker run -p 3000:80 ragflow-mineru-frontend
```

### Nginx 配置示例

```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /path/to/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://backend:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /socket.io {
        proxy_pass http://backend:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 🧪 测试

项目使用 Vitest 和 React Testing Library 进行测试：

```bash
# 运行所有测试
npm run test

# 监听模式运行测试
npm run test:watch

# 生成覆盖率报告
npm run test:coverage
```

## 📋 开发规范

### 代码风格
- 使用 ESLint 进行代码检查
- 使用 Prettier 进行代码格式化
- 遵循 TypeScript 严格模式

### 组件开发
- 使用函数式组件和 Hooks
- 组件名使用 PascalCase
- 文件名使用 PascalCase
- 导出使用 default export

### 状态管理
- 使用 Redux Toolkit 进行状态管理
- 按功能模块划分 slice
- 使用 RTK Query 处理异步请求

### 样式规范
- 优先使用 Tailwind CSS 工具类
- 复杂样式使用 CSS Modules 或 styled-components
- 遵循 BEM 命名规范

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](../LICENSE) 文件了解详情。

## 🆘 支持

如果您遇到问题或有疑问，请：

1. 查看 [FAQ](docs/FAQ.md)
2. 搜索现有的 [Issues](https://github.com/your-repo/issues)
3. 创建新的 Issue
4. 联系开发团队

## 🔄 更新日志

查看 [CHANGELOG.md](CHANGELOG.md) 了解版本更新历史。