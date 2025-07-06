import React, { useState, useRef, useEffect, useMemo } from 'react';
import {
  Input,
  Button,
  Card,
  Typography,
  Avatar,
  Space,
  Dropdown,
  Menu,
  Tooltip,
  Spin,
  message,
  Modal,
  Select,
  Slider,
  Switch,
  Divider,
  Empty,
  Tag,
} from 'antd';
import {
  SendOutlined,
  SettingOutlined,
  ClearOutlined,
  DownloadOutlined,
  CopyOutlined,
  DeleteOutlined,
  RobotOutlined,
  UserOutlined,
  PlusOutlined,
  BookOutlined,
  ThunderboltOutlined,
  BulbOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import { useAppDispatch, useAppSelector } from '@/store';
import { setPageTitle, setBreadcrumb } from '@/store/slices/uiSlice';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';

const { TextArea } = Input;
const { Title, Text } = Typography;
const { Option } = Select;

// 优化后的类型定义
interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: string; // 改为 string（ISO 格式）
  sources?: Array<{
    title: string;
    content: string;
    score: number;
    document: string;
  }>;
  tokens?: {
    input: number;
    output: number;
  };
}

interface ChatSession {
  id: string;
  title: string;
  messages: Message[];
  createdAt: string; // 改为 string
  updatedAt: string; // 改为 string
  knowledgeBase?: string;
  model?: string;
}

interface ChatSettings {
  model: string;
  temperature: number;
  maxTokens: number;
  topP: number;
  knowledgeBase: string;
  enableRAG: boolean;
  enableHistory: boolean;
  maxHistoryLength: number;
}

// 工具函数
const formatTimestamp = (isoString: string) => {
  return new Date(isoString).toLocaleTimeString();
};

const formatDate = (isoString: string) => {
  return new Date(isoString).toLocaleDateString();
};

// 消息组件
// 在MessageItem组件中修复ReactMarkdown的code组件
const MessageItem = React.memo(({ message, onCopy }: { message: Message; onCopy: (content: string) => void }) => {
  return (
    <div className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
      <div className={`flex max-w-4xl ${message.type === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
        <Avatar
          icon={message.type === 'user' ? <UserOutlined /> : <RobotOutlined />}
          className={`${message.type === 'user' ? 'ml-3' : 'mr-3'} flex-shrink-0`}
        />
        <div className={`flex-1 ${message.type === 'user' ? 'text-right' : 'text-left'}`}>
          <div
            className={`inline-block p-4 rounded-lg ${
              message.type === 'user'
                ? 'bg-blue-500 text-white'
                : 'bg-white border border-gray-200'
            }`}
          >
            {message.type === 'user' ? (
              <div className="whitespace-pre-wrap">{message.content}</div>
            ) : (
              <ReactMarkdown
                components={{
                  code: ({ inline, className, children, ...props }: any) => {
                    const match = /language-(\w+)/.exec(className || '');
                    return !inline && match ? (
                      <SyntaxHighlighter
                        style={tomorrow}
                        language={match[1]}
                        PreTag="div"
                        customStyle={{}}
                      >
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                    ) : (
                      <code className={className} {...props}>
                        {children}
                      </code>
                    );
                  },
                } as any}
              >
                {message.content}
              </ReactMarkdown>
            )}
          </div>
          
          <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
            <span>{formatTimestamp(message.timestamp)}</span>
            <Space>
              <Tooltip title="复制">
                <Button
                  type="text"
                  size="small"
                  icon={<CopyOutlined />}
                  onClick={() => onCopy(message.content)}
                />
              </Tooltip>
              {message.tokens && (
                <span>
                  输入: {message.tokens.input} | 输出: {message.tokens.output}
                </span>
              )}
            </Space>
          </div>

          {/* 显示引用来源 */}
          {message.sources && message.sources.length > 0 && (
            <div className="mt-3 p-3 bg-gray-50 rounded-lg">
              <div className="text-sm font-medium mb-2">参考来源:</div>
              <div className="space-y-2">
                {message.sources.map((source, index) => (
                  <div key={index} className="text-sm">
                    <div className="font-medium">{source.title}</div>
                    <div className="text-gray-600 truncate">{source.content}</div>
                    <div className="text-xs text-gray-500">
                      来源: {source.document} | 相关度: {(source.score * 100).toFixed(1)}%
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
});

// 消息列表组件
const MessageList = React.memo(({ messages, isLoading, onCopy }: { 
  messages: Message[]; 
  isLoading: boolean; 
  onCopy: (content: string) => void;
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="space-y-4">
      {messages.map(message => (
        <MessageItem key={message.id} message={message} onCopy={onCopy} />
      ))}
      
      {isLoading && (
        <div className="flex justify-start">
          <div className="flex">
            <Avatar icon={<RobotOutlined />} className="mr-3" />
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <Spin size="small" />
              <span className="ml-2">AI正在思考中...</span>
            </div>
          </div>
        </div>
      )}
      
      <div ref={messagesEndRef} />
    </div>
  );
});

// 输入区域组件
const InputArea = React.memo(({ 
  inputValue, 
  setInputValue, 
  isLoading, 
  onSend 
}: {
  inputValue: string;
  setInputValue: (value: string) => void;
  isLoading: boolean;
  onSend: () => void;
}) => {
  const inputRef = useRef<any>(null);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  return (
    <div className="bg-white border-t border-gray-200 p-4">
      <div className="flex space-x-2">
        <TextArea
          ref={inputRef}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="输入您的问题... (Shift+Enter 换行，Enter 发送)"
          autoSize={{ minRows: 1, maxRows: 4 }}
          className="flex-1"
          disabled={isLoading}
        />
        <Button
          type="primary"
          icon={<SendOutlined />}
          onClick={onSend}
          loading={isLoading}
          disabled={!inputValue.trim()}
          className="self-end"
        >
          发送
        </Button>
      </div>
    </div>
  );
});

// 设置模态框组件
const SettingsModal = React.memo(({ 
  settings, 
  setSettings, 
  visible, 
  onClose 
}: {
  settings: ChatSettings;
  setSettings: React.Dispatch<React.SetStateAction<ChatSettings>>;
  visible: boolean;
  onClose: () => void;
}) => {
  return (
    <Modal
      title="对话设置"
      open={visible}
      onCancel={onClose}
      onOk={onClose}
      width={600}
    >
      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium mb-2">AI 模型</label>
          <Select
            value={settings.model}
            onChange={(value) => setSettings(prev => ({ ...prev, model: value }))}
            className="w-full"
          >
            <Option value="gpt-3.5-turbo">GPT-3.5 Turbo</Option>
            <Option value="gpt-4">GPT-4</Option>
            <Option value="claude-3">Claude-3</Option>
            <Option value="local-llm">本地模型</Option>
          </Select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">知识库</label>
          <Select
            value={settings.knowledgeBase}
            onChange={(value) => setSettings(prev => ({ ...prev, knowledgeBase: value }))}
            className="w-full"
            allowClear
            placeholder="选择知识库（可选）"
          >
            <Option value="general">通用知识库</Option>
            <Option value="ml-docs">机器学习文档</Option>
            <Option value="company-docs">公司文档</Option>
          </Select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">
            温度 (Temperature): {settings.temperature}
          </label>
          <Slider
            min={0}
            max={2}
            step={0.1}
            value={settings.temperature}
            onChange={(value) => setSettings(prev => ({ ...prev, temperature: value }))}
          />
          <div className="text-xs text-gray-500 mt-1">
            较低的值使输出更确定，较高的值使输出更随机
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">
            最大令牌数: {settings.maxTokens}
          </label>
          <Slider
            min={256}
            max={4096}
            step={256}
            value={settings.maxTokens}
            onChange={(value) => setSettings(prev => ({ ...prev, maxTokens: value }))}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">
            Top P: {settings.topP}
          </label>
          <Slider
            min={0}
            max={1}
            step={0.1}
            value={settings.topP}
            onChange={(value) => setSettings(prev => ({ ...prev, topP: value }))}
          />
        </div>

        <Divider />

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">启用 RAG 检索</span>
            <Switch
              checked={settings.enableRAG}
              onChange={(checked) => setSettings(prev => ({ ...prev, enableRAG: checked }))}
            />
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">启用对话历史</span>
            <Switch
              checked={settings.enableHistory}
              onChange={(checked) => setSettings(prev => ({ ...prev, enableHistory: checked }))}
            />
          </div>

          {settings.enableHistory && (
            <div>
              <label className="block text-sm font-medium mb-2">
                历史消息长度: {settings.maxHistoryLength}
              </label>
              <Slider
                min={1}
                max={50}
                value={settings.maxHistoryLength}
                onChange={(value) => setSettings(prev => ({ ...prev, maxHistoryLength: value }))}
              />
            </div>
          )}
        </div>
      </div>
    </Modal>
  );
});

const ChatPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [settingsVisible, setSettingsVisible] = useState(false);
  const [settings, setSettings] = useState<ChatSettings>({
    model: 'gpt-3.5-turbo',
    temperature: 0.7,
    maxTokens: 2048,
    topP: 0.9,
    knowledgeBase: '',
    enableRAG: true,
    enableHistory: true,
    maxHistoryLength: 10,
  });

  // 使用 useMemo 优化性能
  const memoizedSessions = useMemo(() => sessions, [sessions]);
  const memoizedMessages = useMemo(() => currentSession?.messages || [], [currentSession]);

  useEffect(() => {
    dispatch(setPageTitle('智能对话'));
    dispatch(setBreadcrumb([
      { title: '首页', path: '/' },
      { title: '智能对话' },
    ]));

    // 加载聊天历史
    loadChatSessions();
    
    // 创建新会话
    createNewSession();
  }, [dispatch]);

  // 会话持久化 - 保存到 localStorage
  useEffect(() => {
    if (sessions.length > 0) {
      localStorage.setItem('chatSessions', JSON.stringify(sessions));
    }
  }, [sessions]);

  // 初始化时加载会话
  useEffect(() => {
    const savedSessions = localStorage.getItem('chatSessions');
    if (savedSessions) {
      try {
        const parsedSessions = JSON.parse(savedSessions);
        setSessions(parsedSessions);
        if (parsedSessions.length > 0) {
          setCurrentSession(parsedSessions[0]);
        }
      } catch (error) {
        console.error('Failed to parse saved sessions:', error);
      }
    }
  }, []);

  const loadChatSessions = async () => {
    try {
      // TODO: 调用 API 加载聊天历史
      const mockSessions: ChatSession[] = [
        {
          id: '1',
          title: '关于机器学习的讨论',
          messages: [],
          createdAt: new Date(Date.now() - 86400000).toISOString(),
          updatedAt: new Date(Date.now() - 86400000).toISOString(),
          knowledgeBase: 'ml-docs',
          model: 'gpt-3.5-turbo',
        },
        {
          id: '2',
          title: '文档处理问题',
          messages: [],
          createdAt: new Date(Date.now() - 172800000).toISOString(),
          updatedAt: new Date(Date.now() - 172800000).toISOString(),
          knowledgeBase: 'general',
          model: 'gpt-4',
        },
      ];
      setSessions(mockSessions);
    } catch (error) {
      message.error('加载聊天历史失败');
    }
  };

  const createNewSession = () => {
    const newSession: ChatSession = {
      id: Date.now().toString(),
      title: '新对话',
      messages: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      knowledgeBase: settings.knowledgeBase,
      model: settings.model,
    };
    setCurrentSession(newSession);
    setSessions(prev => [newSession, ...prev]);
  };

  // 优化后的消息发送逻辑
  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading || !currentSession) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue.trim(),
      timestamp: new Date().toISOString(),
    };

    // 添加用户消息
    setCurrentSession(prev => ({
      ...prev!,
      messages: [...prev!.messages, userMessage],
      updatedAt: new Date().toISOString(),
    }));

    setInputValue('');
    setIsLoading(true);

    try {
      // 实际 API 调用（替换模拟代码）
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage.content,
          session_id: currentSession.id,
          settings,
          history: settings.enableHistory 
            ? currentSession.messages.slice(-settings.maxHistoryLength)
            : [],
        }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: data.response || `这是对"${userMessage.content}"的回复。这里会显示AI的回答内容，支持Markdown格式。\n\n## 示例代码\n\n\`\`\`python\ndef hello_world():\n    print("Hello, World!")\n\`\`\`\n\n根据您的问题，我建议您查看相关文档以获取更多信息。`,
        timestamp: new Date().toISOString(),
        sources: data.sources || [
          {
            title: '相关文档1',
            content: '这是相关文档的摘要内容...',
            score: 0.95,
            document: 'doc1.pdf',
          },
          {
            title: '相关文档2',
            content: '这是另一个相关文档的摘要...',
            score: 0.87,
            document: 'doc2.pdf',
          },
        ],
        tokens: data.tokens || {
          input: 50,
          output: 120,
        },
      };

      // 添加助手回复
      setCurrentSession(prev => ({
        ...prev!,
        messages: [...prev!.messages, assistantMessage],
        updatedAt: new Date().toISOString(),
      }));

      // 更新会话标题（如果为空）
      if (currentSession.messages.length === 0) {
        const title = userMessage.content.length > 20 
          ? userMessage.content.substring(0, 20) + '...'
          : userMessage.content;
        setCurrentSession(prev => ({ ...prev!, title }));
        setSessions(prev => prev.map(session => 
          session.id === currentSession.id 
            ? { ...session, title }
            : session
        ));
      }
    } catch (error) {
      console.error('Send message error:', error);
      message.error('发送消息失败，请检查网络连接或稍后重试');
      
      // 如果是网络错误，使用模拟回复
      if (error instanceof TypeError && error.message.includes('fetch')) {
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: `这是对"${userMessage.content}"的模拟回复。当前处于离线模式，实际部署时将连接到真实的AI服务。`,
          timestamp: new Date().toISOString(),
        };
        
        setCurrentSession(prev => ({
          ...prev!,
          messages: [...prev!.messages, assistantMessage],
          updatedAt: new Date().toISOString(),
        }));
      }
    } finally {
      setIsLoading(false);
    }
  };

  const clearCurrentSession = () => {
    Modal.confirm({
      title: '清空对话',
      content: '确定要清空当前对话吗？此操作不可撤销。',
      onOk: () => {
        if (currentSession) {
          setCurrentSession({
            ...currentSession,
            messages: [],
            updatedAt: new Date().toISOString(),
          });
        }
      },
    });
  };

  const deleteSession = (sessionId: string) => {
    Modal.confirm({
      title: '删除对话',
      content: '确定要删除这个对话吗？此操作不可撤销。',
      onOk: () => {
        setSessions(prev => prev.filter(session => session.id !== sessionId));
        if (currentSession?.id === sessionId) {
          createNewSession();
        }
      },
    });
  };

  const exportChat = () => {
    if (!currentSession || currentSession.messages.length === 0) {
      message.warning('当前对话为空，无法导出');
      return;
    }

    const content = currentSession.messages.map(msg => 
      `${msg.type === 'user' ? '用户' : 'AI助手'} (${formatTimestamp(msg.timestamp)}):\n${msg.content}\n\n`
    ).join('');

    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${currentSession.title}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const copyMessage = (content: string) => {
    navigator.clipboard.writeText(content).then(() => {
      message.success('已复制到剪贴板');
    }).catch(() => {
      message.error('复制失败');
    });
  };

  const settingsMenu = (
    <Menu>
      <Menu.Item key="settings" icon={<SettingOutlined />} onClick={() => setSettingsVisible(true)}>
        对话设置
      </Menu.Item>
      <Menu.Item key="clear" icon={<ClearOutlined />} onClick={clearCurrentSession}>
        清空对话
      </Menu.Item>
      <Menu.Item key="export" icon={<DownloadOutlined />} onClick={exportChat}>
        导出对话
      </Menu.Item>
    </Menu>
  );

  const quickPrompts = [
    { icon: <BulbOutlined />, text: '解释这个概念', prompt: '请详细解释' },
    { icon: <FileTextOutlined />, text: '总结文档', prompt: '请帮我总结这个文档的主要内容' },
    { icon: <ThunderboltOutlined />, text: '优化代码', prompt: '请帮我优化这段代码' },
    { icon: <BookOutlined />, text: '学习建议', prompt: '请给我一些学习建议' },
  ];

  return (
    <div className="h-full flex">
      {/* 侧边栏 - 聊天历史 */}
      <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <Button
            type="primary"
            icon={<PlusOutlined />}
            block
            onClick={createNewSession}
          >
            新建对话
          </Button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-2">
          {memoizedSessions.length === 0 ? (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description="暂无对话历史"
            />
          ) : (
            <div className="space-y-2">
              {memoizedSessions.map(session => (
                <div
                  key={session.id}
                  className={`p-3 rounded-lg cursor-pointer transition-colors ${
                    currentSession?.id === session.id
                      ? 'bg-blue-50 border border-blue-200'
                      : 'hover:bg-gray-50'
                  }`}
                  onClick={() => setCurrentSession(session)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-sm truncate">
                        {session.title}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {formatDate(session.updatedAt)}
                      </div>
                      {session.knowledgeBase && (
                        <Tag className="mt-1">
                          {session.knowledgeBase}
                        </Tag>
                      )}
                    </div>
                    <Button
                      type="text"
                      size="small"
                      icon={<DeleteOutlined />}
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteSession(session.id);
                      }}
                      className="opacity-0 group-hover:opacity-100"
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 主聊天区域 */}
      <div className="flex-1 flex flex-col">
        {/* 头部 */}
        <div className="bg-white border-b border-gray-200 p-4 flex items-center justify-between">
          <div>
            <Title level={4} className="mb-0">
              {currentSession?.title || '新对话'}
            </Title>
            {currentSession?.knowledgeBase && (
              <Text type="secondary" className="text-sm">
                知识库: {currentSession.knowledgeBase}
              </Text>
            )}
          </div>
          <Space>
            <Dropdown overlay={settingsMenu} trigger={['click']}>
              <Button icon={<SettingOutlined />}>设置</Button>
            </Dropdown>
          </Space>
        </div>

        {/* 消息区域 */}
        <div className="flex-1 overflow-y-auto p-4 bg-gray-50">
          {!currentSession || memoizedMessages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center">
              <div className="text-center mb-8">
                <RobotOutlined className="text-6xl text-gray-300 mb-4" />
                <Title level={3} type="secondary">开始新的对话</Title>
                <Text type="secondary">选择一个快速提示或直接输入您的问题</Text>
              </div>
              
              <div className="grid grid-cols-2 gap-4 max-w-md">
                {quickPrompts.map((prompt, index) => (
                  <Card
                    key={index}
                    hoverable
                    className="text-center cursor-pointer"
                    onClick={() => setInputValue(prompt.prompt)}
                  >
                    <div className="text-2xl mb-2">{prompt.icon}</div>
                    <div className="text-sm">{prompt.text}</div>
                  </Card>
                ))}
              </div>
            </div>
          ) : (
            <MessageList 
              messages={memoizedMessages} 
              isLoading={isLoading} 
              onCopy={copyMessage}
            />
          )}
        </div>

        {/* 输入区域 */}
        <InputArea 
          inputValue={inputValue}
          setInputValue={setInputValue}
          isLoading={isLoading}
          onSend={sendMessage}
        />
      </div>

      {/* 设置模态框 */}
      <SettingsModal 
        settings={settings}
        setSettings={setSettings}
        visible={settingsVisible}
        onClose={() => setSettingsVisible(false)}
      />
    </div>
  );
}

export default ChatPage;