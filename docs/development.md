# 开发指南

## 开发流程

### 1. 分支管理策略

我们采用 Git Flow 工作流：

- `main`: 主分支，用于生产环境
- `develop`: 开发分支，用于集成新功能
- `feature/*`: 功能分支，用于开发新功能
- `hotfix/*`: 热修复分支，用于紧急修复
- `release/*`: 发布分支，用于发布准备

### 2. 开发环境设置

#### 代码规范

**Python代码规范**
- 遵循 PEP 8 标准
- 使用 Black 进行代码格式化
- 使用 isort 进行导入排序
- 使用 flake8 进行代码检查

**JavaScript/TypeScript代码规范**
- 遵循 ESLint 配置
- 使用 Prettier 进行代码格式化
- 使用 TypeScript 严格模式

#### 提交规范

使用 Conventional Commits 规范：

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

类型说明：
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

示例：
```
feat(mineru): add document parsing API

Implement MinerU integration for high-precision document parsing

- Add MinerU parser class
- Implement async parsing workflow
- Add progress tracking

Closes #123
```

### 3. 项目架构

#### 后端架构

```
backend/
├── api/                    # API层
│   ├── __init__.py
│   ├── auth/              # 认证相关
│   ├── documents/         # 文档管理
│   ├── users/             # 用户管理
│   ├── mineru/            # MinerU集成
│   └── permissions/       # 权限管理
├── services/              # 服务层
│   ├── __init__.py
│   ├── document_service.py
│   ├── user_service.py
│   ├── mineru_service.py
│   ├── permission_service.py
│   └── concurrent_service.py
├── models/                # 数据模型
│   ├── __init__.py
│   ├── base.py
│   ├── user.py
│   ├── document.py
│   ├── permission.py
│   └── task.py
├── utils/                 # 工具函数
│   ├── __init__.py
│   ├── auth.py
│   ├── validators.py
│   ├── decorators.py
│   └── mineru_client.py
├── config/                # 配置
│   ├── __init__.py
│   ├── settings.py
│   └── database.py
├── tests/                 # 测试
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_api/
│   ├── test_services/
│   └── test_models/
├── app.py                 # 应用入口
└── requirements.txt       # 依赖列表
```

#### 前端架构

```
frontend/
├── public/                # 静态资源
├── src/
│   ├── components/        # 通用组件
│   │   ├── common/        # 基础组件
│   │   ├── forms/         # 表单组件
│   │   └── layout/        # 布局组件
│   ├── pages/             # 页面组件
│   │   ├── auth/          # 认证页面
│   │   ├── documents/     # 文档管理
│   │   ├── users/         # 用户管理
│   │   └── dashboard/     # 仪表板
│   ├── services/          # API服务
│   │   ├── api.ts         # API基础配置
│   │   ├── auth.ts        # 认证服务
│   │   ├── documents.ts   # 文档服务
│   │   └── users.ts       # 用户服务
│   ├── store/             # 状态管理
│   │   ├── index.ts
│   │   ├── auth.ts
│   │   ├── documents.ts
│   │   └── users.ts
│   ├── utils/             # 工具函数
│   │   ├── constants.ts
│   │   ├── helpers.ts
│   │   └── validators.ts
│   ├── types/             # 类型定义
│   │   ├── api.ts
│   │   ├── user.ts
│   │   └── document.ts
│   ├── hooks/             # 自定义Hooks
│   ├── styles/            # 样式文件
│   ├── App.tsx
│   └── index.tsx
├── package.json
└── tsconfig.json
```

## 核心功能开发

### 1. MinerU集成开发

#### MinerU服务类

```python
# backend/services/mineru_service.py
import asyncio
import aiohttp
import json
from typing import Dict, Optional
from backend.utils.mineru_client import MinerUClient
from backend.models.task import ParseTask

class MinerUService:
    def __init__(self, api_url: str):
        self.client = MinerUClient(api_url)
    
    async def parse_document(self, file_path: str, user_id: str, options: Dict = None) -> str:
        """提交文档解析任务"""
        task = ParseTask.create(
            document_path=file_path,
            user_id=user_id,
            parser_type='mineru',
            status='pending',
            options=options or {}
        )
        
        # 提交到MinerU API
        task_id = await self.client.submit_parse_task(file_path, task.id)
        
        # 更新任务状态
        task.external_task_id = task_id
        task.status = 'processing'
        task.save()
        
        return task.id
    
    async def get_parse_result(self, task_id: str) -> Optional[Dict]:
        """获取解析结果"""
        task = ParseTask.get_by_id(task_id)
        if not task:
            return None
        
        if task.status == 'completed':
            return task.result_data
        
        # 检查外部任务状态
        if task.external_task_id:
            result = await self.client.get_task_status(task.external_task_id)
            if result['status'] == 'completed':
                task.status = 'completed'
                task.result_data = result['data']
                task.progress = 100
                task.save()
                return result['data']
        
        return None
```

#### MinerU客户端

```python
# backend/utils/mineru_client.py
import aiohttp
import asyncio
from typing import Dict, Optional

class MinerUClient:
    def __init__(self, api_url: str):
        self.api_url = api_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def submit_parse_task(self, file_path: str, task_id: str) -> str:
        """提交解析任务"""
        async with aiohttp.ClientSession() as session:
            with open(file_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename=file_path.split('/')[-1])
                data.add_field('task_id', task_id)
                
                async with session.post(f"{self.api_url}/parse", data=data) as resp:
                    result = await resp.json()
                    return result['task_id']
    
    async def get_task_status(self, task_id: str) -> Dict:
        """获取任务状态"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.api_url}/task/{task_id}") as resp:
                return await resp.json()
```

### 2. 权限管理开发

#### 权限模型

```python
# backend/models/permission.py
from peewee import *
from backend.models.base import BaseModel

class UserRole(BaseModel):
    name = CharField(max_length=50, unique=True)
    permissions = JSONField(default=list)
    description = TextField(null=True)
    
    class Meta:
        table_name = 'user_roles'

class UserKnowledgebasePermission(BaseModel):
    user_id = CharField(max_length=32, index=True)
    kb_id = CharField(max_length=32, index=True)
    permission_type = CharField(max_length=20)  # read, write, admin
    granted_by = CharField(max_length=32, index=True)
    granted_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'user_kb_permissions'
        indexes = (
            (('user_id', 'kb_id'), True),  # 唯一索引
        )
```

#### 权限装饰器

```python
# backend/utils/decorators.py
from functools import wraps
from flask import request, jsonify, g
from flask_login import current_user
from backend.services.permission_service import PermissionService

def require_permission(permission_type: str, resource_type: str = 'kb'):
    """权限检查装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if resource_type == 'kb':
                kb_id = request.json.get('kb_id') or request.args.get('kb_id')
                if not kb_id:
                    return jsonify({"error": "缺少知识库ID"}), 400
                
                if not PermissionService.check_kb_permission(
                    current_user.id, kb_id, permission_type
                ):
                    return jsonify({"error": "权限不足"}), 403
                
                g.kb_id = kb_id
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            return jsonify({"error": "需要管理员权限"}), 403
        return f(*args, **kwargs)
    return decorated_function
```

### 3. 并发处理开发

#### 任务队列系统

```python
# backend/services/concurrent_service.py
import asyncio
import redis
from concurrent.futures import ThreadPoolExecutor
from backend.models.task import ParseTask
from backend.services.mineru_service import MinerUService

class TaskQueue:
    def __init__(self, redis_url: str, max_workers: int = 4):
        self.redis_client = redis.from_url(redis_url)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.mineru_service = MinerUService()
        self.running = False
    
    async def start(self):
        """启动任务队列处理"""
        self.running = True
        await asyncio.gather(
            self._process_parse_tasks(),
            self._monitor_task_status(),
        )
    
    async def stop(self):
        """停止任务队列处理"""
        self.running = False
    
    async def submit_task(self, task_data: dict) -> str:
        """提交任务到队列"""
        task_id = str(uuid.uuid4())
        task_data['id'] = task_id
        task_data['status'] = 'pending'
        task_data['created_at'] = datetime.now().isoformat()
        
        # 添加到Redis队列
        self.redis_client.lpush('parse_tasks', json.dumps(task_data))
        
        return task_id
    
    async def _process_parse_tasks(self):
        """处理解析任务"""
        while self.running:
            try:
                # 从队列获取任务
                task_data = self.redis_client.brpop('parse_tasks', timeout=1)
                if not task_data:
                    continue
                
                task_info = json.loads(task_data[1])
                
                # 检查并发限制
                if self._check_user_concurrency_limit(task_info['user_id']):
                    # 提交到线程池执行
                    self.executor.submit(self._execute_parse_task, task_info)
                else:
                    # 重新放回队列
                    self.redis_client.lpush('parse_tasks', task_data[1])
                    await asyncio.sleep(1)
                    
            except Exception as e:
                logging.error(f"任务处理错误: {e}")
                await asyncio.sleep(1)
    
    def _check_user_concurrency_limit(self, user_id: str, max_concurrent: int = 2) -> bool:
        """检查用户并发限制"""
        running_count = ParseTask.select().where(
            (ParseTask.user_id == user_id) & 
            (ParseTask.status == 'processing')
        ).count()
        return running_count < max_concurrent
    
    def _execute_parse_task(self, task_info: dict):
        """执行解析任务"""
        try:
            # 创建任务记录
            task = ParseTask.create(**task_info)
            
            # 调用MinerU服务
            result = asyncio.run(
                self.mineru_service.parse_document(
                    task_info['file_path'],
                    task_info['user_id'],
                    task_info.get('options', {})
                )
            )
            
            # 更新任务状态
            task.status = 'completed'
            task.result_data = result
            task.progress = 100
            task.save()
            
        except Exception as e:
            task.status = 'failed'
            task.error_message = str(e)
            task.save()
```

### 4. API开发

#### 文档解析API

```python
# backend/api/documents/views.py
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from backend.utils.decorators import require_permission
from backend.services.mineru_service import MinerUService
from backend.services.concurrent_service import TaskQueue

documents_bp = Blueprint('documents', __name__, url_prefix='/api/documents')

@documents_bp.route('/parse', methods=['POST'])
@login_required
@require_permission('write', 'kb')
async def parse_document():
    """解析文档API"""
    try:
        file = request.files.get('file')
        if not file:
            return jsonify({"error": "未提供文件"}), 400
        
        kb_id = request.form.get('kb_id')
        parser_type = request.form.get('parser_type', 'mineru')
        options = json.loads(request.form.get('options', '{}'))
        
        # 保存文件
        file_path = save_uploaded_file(file, current_user.id)
        
        # 提交解析任务
        task_queue = TaskQueue()
        task_id = await task_queue.submit_task({
            'file_path': file_path,
            'kb_id': kb_id,
            'user_id': current_user.id,
            'parser_type': parser_type,
            'options': options
        })
        
        return jsonify({
            "task_id": task_id,
            "status": "submitted",
            "message": "文档解析任务已提交"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@documents_bp.route('/parse/<task_id>/status', methods=['GET'])
@login_required
def get_parse_status(task_id):
    """获取解析状态API"""
    try:
        task = ParseTask.get_by_id(task_id)
        if not task:
            return jsonify({"error": "任务不存在"}), 404
        
        if task.user_id != current_user.id and not current_user.is_admin:
            return jsonify({"error": "权限不足"}), 403
        
        return jsonify({
            "task_id": task.id,
            "status": task.status,
            "progress": task.progress,
            "result": task.result_data,
            "error": task.error_message
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

## 测试开发

### 1. 单元测试

```python
# backend/tests/test_services/test_mineru_service.py
import pytest
import asyncio
from unittest.mock import Mock, patch
from backend.services.mineru_service import MinerUService

class TestMinerUService:
    @pytest.fixture
    def mineru_service(self):
        return MinerUService("http://localhost:8001")
    
    @pytest.mark.asyncio
    async def test_parse_document(self, mineru_service):
        """测试文档解析"""
        with patch.object(mineru_service.client, 'submit_parse_task') as mock_submit:
            mock_submit.return_value = "task_123"
            
            task_id = await mineru_service.parse_document(
                "/path/to/test.pdf",
                "user_123"
            )
            
            assert task_id is not None
            mock_submit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_parse_result(self, mineru_service):
        """测试获取解析结果"""
        # 创建测试任务
        task = ParseTask.create(
            document_path="/path/to/test.pdf",
            user_id="user_123",
            status="completed",
            result_data={"content": "test content"}
        )
        
        result = await mineru_service.get_parse_result(task.id)
        
        assert result is not None
        assert result["content"] == "test content"
```

### 2. 集成测试

```python
# backend/tests/test_api/test_documents.py
import pytest
import json
from backend.app import create_app
from backend.models.user import User
from backend.models.permission import UserKnowledgebasePermission

class TestDocumentsAPI:
    @pytest.fixture
    def app(self):
        app = create_app(testing=True)
        return app
    
    @pytest.fixture
    def client(self, app):
        return app.test_client()
    
    @pytest.fixture
    def auth_headers(self, client):
        # 创建测试用户并登录
        user = User.create(
            email="test@example.com",
            password="password",
            is_active=True
        )
        
        response = client.post('/api/auth/login', json={
            'email': 'test@example.com',
            'password': 'password'
        })
        
        token = response.json['access_token']
        return {'Authorization': f'Bearer {token}'}
    
    def test_parse_document_success(self, client, auth_headers):
        """测试文档解析成功"""
        with open('tests/fixtures/test.pdf', 'rb') as f:
            response = client.post('/api/documents/parse', 
                headers=auth_headers,
                data={
                    'file': (f, 'test.pdf'),
                    'kb_id': 'kb_123',
                    'parser_type': 'mineru'
                }
            )
        
        assert response.status_code == 200
        assert 'task_id' in response.json
    
    def test_parse_document_no_permission(self, client, auth_headers):
        """测试无权限解析文档"""
        with open('tests/fixtures/test.pdf', 'rb') as f:
            response = client.post('/api/documents/parse',
                headers=auth_headers,
                data={
                    'file': (f, 'test.pdf'),
                    'kb_id': 'kb_no_permission'
                }
            )
        
        assert response.status_code == 403
        assert 'error' in response.json
```

## 部署和运维

### 1. Docker配置

```dockerfile
# docker/ragflow/Dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY backend/ ./backend/
COPY config/ ./config/

# 设置环境变量
ENV PYTHONPATH=/app
ENV FLASK_APP=backend.app:create_app

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "backend.app:create_app()"]
```

### 2. 监控配置

```python
# backend/utils/monitoring.py
import time
import logging
from functools import wraps
from flask import request, g
from prometheus_client import Counter, Histogram, generate_latest

# Prometheus指标
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
PARSE_TASK_COUNT = Counter('parse_tasks_total', 'Total parse tasks', ['parser_type', 'status'])

def monitor_requests(f):
    """请求监控装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        
        try:
            response = f(*args, **kwargs)
            status = getattr(response, 'status_code', 200)
        except Exception as e:
            status = 500
            raise
        finally:
            duration = time.time() - start_time
            REQUEST_DURATION.observe(duration)
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.endpoint,
                status=status
            ).inc()
        
        return response
    return decorated_function

def track_parse_task(parser_type: str, status: str):
    """跟踪解析任务"""
    PARSE_TASK_COUNT.labels(parser_type=parser_type, status=status).inc()
```

## 最佳实践

### 1. 代码质量

- 保持函数简洁，单一职责
- 使用类型注解提高代码可读性
- 编写完整的文档字符串
- 保持测试覆盖率在80%以上

### 2. 性能优化

- 使用异步编程处理I/O密集型操作
- 合理使用缓存减少数据库查询
- 优化数据库索引和查询
- 使用连接池管理数据库连接

### 3. 安全考虑

- 验证所有用户输入
- 使用HTTPS传输敏感数据
- 实施适当的权限控制
- 定期更新依赖包

### 4. 错误处理

- 使用统一的错误处理机制
- 记录详细的错误日志
- 为用户提供友好的错误信息
- 实施重试机制处理临时故障

## 贡献指南

1. Fork项目到个人仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

### Pull Request要求

- 提供清晰的描述和变更说明
- 包含相关的测试用例
- 确保所有测试通过
- 遵循代码规范
- 更新相关文档

## 常见问题

### Q: 如何调试MinerU集成问题？

A: 
1. 检查MinerU服务是否正常运行
2. 查看API调用日志
3. 验证模型文件是否正确加载
4. 检查GPU资源使用情况

### Q: 如何优化解析性能？

A:
1. 使用GPU加速
2. 调整并发任务数量
3. 优化模型参数
4. 使用缓存机制

### Q: 如何处理大文件解析？

A:
1. 实施文件分块处理
2. 使用流式处理
3. 设置合理的超时时间
4. 提供进度反馈

更多问题请查看 [FAQ文档](faq.md) 或提交Issue。