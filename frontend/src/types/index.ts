// 用户相关类型
export interface User {
  id: string;
  username: string;
  email: string;
  avatar?: string;
  role: UserRole;
  status: UserStatus;
  createdAt: string;
  updatedAt: string;
  lastLoginAt?: string;
  permissions: Permission[];
}

export enum UserRole {
  SUPER_ADMIN = 'super_admin',
  ADMIN = 'admin',
  USER = 'user',
  GUEST = 'guest'
}

export enum UserStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  SUSPENDED = 'suspended'
}

// 权限相关类型
export interface Permission {
  id: string;
  name: string;
  resource: string;
  action: string;
  description?: string;
}

// 文档相关类型
export interface Document {
  id: string;
  name: string;
  originalName: string;
  size: number;
  type: string;
  path: string;
  status: DocumentStatus;
  uploadedBy: string;
  uploadedAt: string;
  processedAt?: string;
  knowledgeBaseId: string;
  metadata?: DocumentMetadata;
  parseResult?: ParseResult;
}

export enum DocumentStatus {
  UPLOADED = 'uploaded',
  PROCESSING = 'processing',
  PROCESSED = 'processed',
  FAILED = 'failed'
}

export interface DocumentMetadata {
  pages?: number;
  language?: string;
  encoding?: string;
  author?: string;
  title?: string;
  subject?: string;
  creator?: string;
  producer?: string;
  creationDate?: string;
  modificationDate?: string;
}

// 解析结果类型
export interface ParseResult {
  id: string;
  documentId: string;
  content: string;
  markdown?: string;
  html?: string;
  chunks: TextChunk[];
  images?: ExtractedImage[];
  tables?: ExtractedTable[];
  metadata: ParseMetadata;
  createdAt: string;
}

export interface TextChunk {
  id: string;
  content: string;
  page?: number;
  position?: ChunkPosition;
  type: ChunkType;
  confidence?: number;
}

export interface ChunkPosition {
  x: number;
  y: number;
  width: number;
  height: number;
}

export enum ChunkType {
  TEXT = 'text',
  TITLE = 'title',
  HEADER = 'header',
  FOOTER = 'footer',
  TABLE = 'table',
  IMAGE = 'image',
  LIST = 'list'
}

export interface ExtractedImage {
  id: string;
  path: string;
  page: number;
  position: ChunkPosition;
  description?: string;
}

export interface ExtractedTable {
  id: string;
  content: string;
  html: string;
  page: number;
  position: ChunkPosition;
  rows: number;
  columns: number;
}

export interface ParseMetadata {
  parser: string;
  version: string;
  processingTime: number;
  confidence: number;
  options: Record<string, any>;
}

// 任务相关类型
export interface Task {
  id: string;
  type: TaskType;
  status: TaskStatus;
  progress: number;
  message?: string;
  data?: Record<string, any>;
  createdBy: string;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
  error?: TaskError;
}

export enum TaskType {
  DOCUMENT_PARSE = 'document_parse',
  BATCH_PARSE = 'batch_parse',
  KNOWLEDGE_BASE_BUILD = 'knowledge_base_build',
  DATA_EXPORT = 'data_export',
  SYSTEM_MAINTENANCE = 'system_maintenance'
}

export enum TaskStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

export interface TaskError {
  code: string;
  message: string;
  details?: Record<string, any>;
}

// 知识库相关类型
export interface KnowledgeBase {
  id: string;
  name: string;
  description?: string;
  ownerId: string;
  status: KnowledgeBaseStatus;
  documentsCount: number;
  size: number;
  createdAt: string;
  updatedAt: string;
  settings: KnowledgeBaseSettings;
  permissions: KnowledgeBasePermission[];
}

export enum KnowledgeBaseStatus {
  ACTIVE = 'active',
  BUILDING = 'building',
  INACTIVE = 'inactive'
}

export interface KnowledgeBaseSettings {
  parser: string;
  chunkSize: number;
  chunkOverlap: number;
  enableOCR: boolean;
  enableTableExtraction: boolean;
  enableImageExtraction: boolean;
  language: string;
}

export interface KnowledgeBasePermission {
  userId: string;
  permission: 'read' | 'write' | 'admin';
  grantedBy: string;
  grantedAt: string;
}

// API 响应类型
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: ApiError;
  timestamp: string;
  requestId: string;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, any>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

// 系统统计类型
export interface SystemStats {
  users: {
    total: number;
    active: number;
    newToday: number;
  };
  documents: {
    total: number;
    processed: number;
    processing: number;
    failed: number;
  };
  knowledgeBases: {
    total: number;
    active: number;
  };
  tasks: {
    pending: number;
    running: number;
    completed: number;
    failed: number;
  };
  storage: {
    used: number;
    total: number;
    percentage: number;
  };
  performance: {
    cpu: number;
    memory: number;
    disk: number;
  };
}

// WebSocket 消息类型
export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

export interface TaskProgressMessage {
  taskId: string;
  progress: number;
  status: TaskStatus;
  message?: string;
}

export interface SystemNotification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
}

// 系统相关类型
export interface SystemInfo {
  version: string;
  buildTime: string;
  environment: string;
  uptime: number;
  nodeVersion: string;
  platform: string;
  architecture: string;
  memory: {
    total: number;
    used: number;
    free: number;
  };
  cpu: {
    model: string;
    cores: number;
    usage: number;
  };
  disk: {
    total: number;
    used: number;
    free: number;
  };
}

export interface SystemSettings {
  siteName: string;
  siteDescription: string;
  allowRegistration: boolean;
  defaultUserRole: UserRole;
  maxFileSize: number;
  allowedFileTypes: string[];
  enableOCR: boolean;
  enableTableExtraction: boolean;
  enableImageExtraction: boolean;
  defaultParser: string;
  emailSettings: {
    enabled: boolean;
    host: string;
    port: number;
    secure: boolean;
    username: string;
    from: string;
  };
  storageSettings: {
    provider: 'local' | 's3' | 'oss';
    config: Record<string, any>;
  };
  securitySettings: {
    sessionTimeout: number;
    maxLoginAttempts: number;
    lockoutDuration: number;
    passwordMinLength: number;
    requireSpecialChars: boolean;
  };
}

export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  isRead: boolean;
  createdAt: string;
  userId?: string;
  data?: Record<string, any>;
}

// 登录凭据类型（用于API调用）
export interface LoginCredentials {
  username: string;
  password: string;
  remember?: boolean;
}

// 注册数据类型（用于API调用）
export interface RegisterData {
  username: string;
  email: string;
  password: string;
  confirmPassword?: string;
}



export interface DocumentUploadForm {
  files: File[];
  knowledgeBaseId: string;
  parser?: string;
  options?: Record<string, any>;
}

export interface CreateKnowledgeBaseForm {
  name: string;
  description?: string;
  settings: KnowledgeBaseSettings;
}

export interface UpdateKnowledgeBaseForm {
  name?: string;
  description?: string;
  settings?: Partial<KnowledgeBaseSettings>;
}

export interface CreateTaskForm {
  type: TaskType;
  data: Record<string, any>;
  priority?: 'low' | 'normal' | 'high';
}

export interface UpdateTaskForm {
  status?: TaskStatus;
  progress?: number;
  message?: string;
  data?: Record<string, any>;
}

export interface CreateUserForm {
  username: string;
  email: string;
  password: string;
  role: UserRole;
  permissions?: string[];
}

export interface UpdateUserForm {
  username?: string;
  email?: string;
  role?: UserRole;
  status?: UserStatus;
  permissions?: string[];
}

// 路由类型
export interface RouteConfig {
  path: string;
  component: React.ComponentType;
  exact?: boolean;
  roles?: UserRole[];
  permissions?: string[];
}