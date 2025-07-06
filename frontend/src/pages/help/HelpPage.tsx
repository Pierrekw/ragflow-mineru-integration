import React, { useState, useEffect } from 'react';
import {
  Card,
  Typography,
  Input,
  Tabs,
  Collapse,
  Space,
  Button,
  Tag,
  Divider,
  Row,
  Col,
  Steps,
  Alert,
  List,
  Avatar,
  Badge,
  Anchor,
  BackTop,
  Tooltip,
  message,
} from 'antd';
import {
  SearchOutlined,
  BookOutlined,
  ApiOutlined,
  QuestionCircleOutlined,
  RocketOutlined,
  ToolOutlined,
  BulbOutlined,
  FileTextOutlined,
  VideoCameraOutlined,
  DownloadOutlined,
  LinkOutlined,
  HeartOutlined,
  StarOutlined,
  GithubOutlined,
  MailOutlined,
  PhoneOutlined,
  GlobalOutlined,
} from '@ant-design/icons';
import { useAppDispatch } from '@/store';
import { setPageTitle, setBreadcrumb } from '@/store/slices/uiSlice';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;
const { Panel } = Collapse;
const { Step } = Steps;
const { Link } = Anchor;

interface FAQ {
  id: string;
  question: string;
  answer: string;
  category: string;
  tags: string[];
  helpful: number;
}

interface Tutorial {
  id: string;
  title: string;
  description: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  duration: string;
  steps: Array<{
    title: string;
    content: string;
    code?: string;
  }>;
  category: string;
}

const HelpPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const [activeTab, setActiveTab] = useState('guide');
  const [searchQuery, setSearchQuery] = useState('');
  const [faqs, setFaqs] = useState<FAQ[]>([]);
  const [tutorials, setTutorials] = useState<Tutorial[]>([]);
  const [filteredFaqs, setFilteredFaqs] = useState<FAQ[]>([]);

  useEffect(() => {
    dispatch(setPageTitle('帮助中心'));
    dispatch(setBreadcrumb([
      { title: '首页', path: '/' },
      { title: '帮助中心' },
    ]));

    loadHelpData();
  }, [dispatch]);

  useEffect(() => {
    // 搜索过滤
    if (searchQuery) {
      const filtered = faqs.filter(faq => 
        faq.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
        faq.answer.toLowerCase().includes(searchQuery.toLowerCase()) ||
        faq.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
      );
      setFilteredFaqs(filtered);
    } else {
      setFilteredFaqs(faqs);
    }
  }, [searchQuery, faqs]);

  const loadHelpData = () => {
    // 模拟FAQ数据
    const mockFaqs: FAQ[] = [
      {
        id: '1',
        question: '如何上传文档？',
        answer: '您可以通过以下方式上传文档：\n1. 点击"文档管理"页面的"上传文档"按钮\n2. 拖拽文件到上传区域\n3. 选择文件并点击确认\n\n支持的文件格式包括：PDF、Word、Excel、PowerPoint、TXT等。',
        category: '文档管理',
        tags: ['上传', '文档', '格式'],
        helpful: 25,
      },
      {
        id: '2',
        question: '如何创建知识库？',
        answer: '创建知识库的步骤：\n1. 进入"知识库管理"页面\n2. 点击"创建知识库"按钮\n3. 填写知识库名称和描述\n4. 选择知识库类型和配置\n5. 添加文档到知识库\n6. 等待索引构建完成',
        category: '知识库',
        tags: ['知识库', '创建', '索引'],
        helpful: 32,
      },
      {
        id: '3',
        question: 'API调用频率限制是多少？',
        answer: 'API调用频率限制根据您的订阅计划而定：\n- 免费版：100次/小时\n- 基础版：1000次/小时\n- 专业版：10000次/小时\n- 企业版：无限制\n\n如需提高限制，请联系客服或升级订阅计划。',
        category: 'API',
        tags: ['API', '限制', '频率'],
        helpful: 18,
      },
      {
        id: '4',
        question: '如何使用AI对话功能？',
        answer: 'AI对话功能使用方法：\n1. 进入"智能对话"页面\n2. 选择合适的知识库（可选）\n3. 在输入框中输入您的问题\n4. 点击发送或按Enter键\n5. AI会基于知识库内容回答您的问题\n\n您还可以调整对话参数来获得更好的回答效果。',
        category: 'AI对话',
        tags: ['AI', '对话', '聊天'],
        helpful: 41,
      },
      {
        id: '5',
        question: '忘记密码怎么办？',
        answer: '如果忘记密码，请按以下步骤重置：\n1. 在登录页面点击"忘记密码"\n2. 输入您的邮箱地址\n3. 查收重置密码邮件\n4. 点击邮件中的重置链接\n5. 设置新密码\n\n如果没有收到邮件，请检查垃圾邮件文件夹或联系客服。',
        category: '账户',
        tags: ['密码', '重置', '登录'],
        helpful: 15,
      },
    ];

    // 模拟教程数据
    const mockTutorials: Tutorial[] = [
      {
        id: '1',
        title: '快速开始指南',
        description: '了解如何快速开始使用RAGFlow平台',
        difficulty: 'beginner',
        duration: '10分钟',
        category: '入门',
        steps: [
          {
            title: '注册账户',
            content: '首先需要注册一个RAGFlow账户。点击注册按钮，填写必要信息完成注册。',
          },
          {
            title: '上传第一个文档',
            content: '登录后，进入文档管理页面，上传您的第一个文档。支持PDF、Word等多种格式。',
          },
          {
            title: '创建知识库',
            content: '将上传的文档添加到知识库中，系统会自动进行索引和向量化处理。',
          },
          {
            title: '开始对话',
            content: '进入AI对话页面，选择刚创建的知识库，开始与AI进行基于文档内容的对话。',
          },
        ],
      },
      {
        id: '2',
        title: 'API集成指南',
        description: '学习如何将RAGFlow API集成到您的应用中',
        difficulty: 'intermediate',
        duration: '30分钟',
        category: 'API',
        steps: [
          {
            title: '获取API密钥',
            content: '在API管理页面创建新的API密钥，设置适当的权限和限制。',
          },
          {
            title: '认证请求',
            content: '在请求头中添加API密钥进行认证。',
            code: `curl -X GET "https://api.ragflow.com/v1/documents" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json"`,
          },
          {
            title: '上传文档',
            content: '使用API上传文档到系统中。',
            code: `curl -X POST "https://api.ragflow.com/v1/documents" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -F "file=@document.pdf" \\
  -F "name=My Document"`,
          },
          {
            title: '查询对话',
            content: '调用对话API与AI进行交互。',
            code: `curl -X POST "https://api.ragflow.com/v1/chat/completions" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{\n    "message": "What is this document about?",\n    "knowledge_base": "kb_123"\n  }'`,
          },
        ],
      },
    ];

    setFaqs(mockFaqs);
    setTutorials(mockTutorials);
    setFilteredFaqs(mockFaqs);
  };

  const markHelpful = (faqId: string) => {
    setFaqs(prev => prev.map(faq => 
      faq.id === faqId 
        ? { ...faq, helpful: faq.helpful + 1 }
        : faq
    ));
    message.success('感谢您的反馈！');
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner': return 'green';
      case 'intermediate': return 'orange';
      case 'advanced': return 'red';
      default: return 'default';
    }
  };

  const getDifficultyText = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner': return '初级';
      case 'intermediate': return '中级';
      case 'advanced': return '高级';
      default: return difficulty;
    }
  };

  return (
    <div className="max-w-6xl mx-auto">
      {/* 搜索栏 */}
      <Card className="mb-6">
        <div className="text-center">
          <Title level={2}>帮助中心</Title>
          <Paragraph type="secondary" className="mb-4">
            欢迎来到RAGFlow帮助中心，这里有您需要的所有信息
          </Paragraph>
          <Input.Search
            placeholder="搜索帮助内容..."
            size="large"
            style={{ maxWidth: 500 }}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            prefix={<SearchOutlined />}
          />
        </div>
      </Card>

      {/* 主要内容 */}
      <Tabs activeKey={activeTab} onChange={setActiveTab} size="large">
        {/* 用户指南 */}
        <TabPane tab={<span><BookOutlined />用户指南</span>} key="guide">
          <Row gutter={[16, 16]}>
            <Col span={16}>
              <Card title="快速开始">
                <Anchor affix={false}>
                  <Link href="#overview" title="平台概述" />
                  <Link href="#getting-started" title="快速开始" />
                  <Link href="#features" title="主要功能" />
                  <Link href="#best-practices" title="最佳实践" />
                </Anchor>

                <div id="overview" className="mt-6">
                  <Title level={3}>平台概述</Title>
                  <Paragraph>
                    RAGFlow是一个基于检索增强生成(RAG)技术的智能文档处理平台。
                    它能够帮助您将文档转化为可查询的知识库，并通过AI对话的方式获取文档中的信息。
                  </Paragraph>
                  
                  <Alert
                    message="核心优势"
                    description={
                      <ul className="mt-2">
                        <li>支持多种文档格式的智能解析</li>
                        <li>基于向量数据库的高效检索</li>
                        <li>自然语言对话式查询</li>
                        <li>企业级安全和权限控制</li>
                        <li>丰富的API接口支持</li>
                      </ul>
                    }
                    type="info"
                    showIcon
                    className="mb-4"
                  />
                </div>

                <div id="getting-started" className="mt-6">
                  <Title level={3}>快速开始</Title>
                  <Steps direction="vertical" size="small">
                    <Step
                      title="注册账户"
                      description="创建您的RAGFlow账户，选择合适的订阅计划"
                      icon={<RocketOutlined />}
                    />
                    <Step
                      title="上传文档"
                      description="将您的文档上传到平台，支持PDF、Word、Excel等格式"
                      icon={<FileTextOutlined />}
                    />
                    <Step
                      title="创建知识库"
                      description="将文档组织到知识库中，系统会自动进行索引处理"
                      icon={<BookOutlined />}
                    />
                    <Step
                      title="开始对话"
                      description="通过AI对话功能，基于文档内容进行智能问答"
                      icon={<BulbOutlined />}
                    />
                  </Steps>
                </div>

                <div id="features" className="mt-6">
                  <Title level={3}>主要功能</Title>
                  <Row gutter={[16, 16]}>
                    <Col span={12}>
                      <Card size="small" title="文档管理">
                        <ul>
                          <li>多格式文档上传</li>
                          <li>文档预览和编辑</li>
                          <li>批量操作支持</li>
                          <li>版本控制</li>
                        </ul>
                      </Card>
                    </Col>
                    <Col span={12}>
                      <Card size="small" title="知识库">
                        <ul>
                          <li>智能索引构建</li>
                          <li>向量化存储</li>
                          <li>语义搜索</li>
                          <li>知识图谱</li>
                        </ul>
                      </Card>
                    </Col>
                    <Col span={12}>
                      <Card size="small" title="AI对话">
                        <ul>
                          <li>自然语言查询</li>
                          <li>上下文理解</li>
                          <li>多轮对话</li>
                          <li>引用溯源</li>
                        </ul>
                      </Card>
                    </Col>
                    <Col span={12}>
                      <Card size="small" title="API集成">
                        <ul>
                          <li>RESTful API</li>
                          <li>SDK支持</li>
                          <li>Webhook通知</li>
                          <li>批量处理</li>
                        </ul>
                      </Card>
                    </Col>
                  </Row>
                </div>

                <div id="best-practices" className="mt-6">
                  <Title level={3}>最佳实践</Title>
                  <Alert
                    message="文档准备建议"
                    description={
                      <ul className="mt-2">
                        <li>确保文档内容清晰、结构化</li>
                        <li>使用有意义的文件名和描述</li>
                        <li>定期更新和维护文档</li>
                        <li>合理组织知识库分类</li>
                      </ul>
                    }
                    type="success"
                    showIcon
                    className="mb-4"
                  />
                  
                  <Alert
                    message="对话优化技巧"
                    description={
                      <ul className="mt-2">
                        <li>使用具体、明确的问题</li>
                        <li>提供足够的上下文信息</li>
                        <li>善用关键词和专业术语</li>
                        <li>根据回答调整问题策略</li>
                      </ul>
                    }
                    type="warning"
                    showIcon
                  />
                </div>
              </Card>
            </Col>
            
            <Col span={8}>
              <Card title="教程视频" className="mb-4">
                <List
                  size="small"
                  dataSource={[
                    { title: '平台介绍', duration: '5:30' },
                    { title: '快速上手', duration: '8:45' },
                    { title: 'API使用', duration: '12:20' },
                    { title: '高级功能', duration: '15:10' },
                  ]}
                  renderItem={(item) => (
                    <List.Item>
                      <div className="flex justify-between items-center w-full">
                        <span className="flex items-center">
                          <VideoCameraOutlined className="mr-2" />
                          {item.title}
                        </span>
                        <Text type="secondary">{item.duration}</Text>
                      </div>
                    </List.Item>
                  )}
                />
              </Card>

              <Card title="下载资源">
                <List
                  size="small"
                  dataSource={[
                    { name: 'API文档', format: 'PDF' },
                    { name: '用户手册', format: 'PDF' },
                    { name: 'SDK包', format: 'ZIP' },
                    { name: '示例代码', format: 'ZIP' },
                  ]}
                  renderItem={(item) => (
                    <List.Item>
                      <div className="flex justify-between items-center w-full">
                        <span className="flex items-center">
                          <DownloadOutlined className="mr-2" />
                          {item.name}
                        </span>
                        <Tag>{item.format}</Tag>
                      </div>
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
          </Row>
        </TabPane>

        {/* API文档 */}
        <TabPane tab={<span><ApiOutlined />API文档</span>} key="api">
          <Card>
            <Title level={3}>API文档</Title>
            <Paragraph>
              RAGFlow提供完整的RESTful API，支持所有核心功能的编程访问。
            </Paragraph>

            <Divider />

            <Row gutter={[16, 16]}>
              <Col span={12}>
                <Card title="认证" size="small">
                  <Paragraph>
                    所有API请求都需要在请求头中包含API密钥：
                  </Paragraph>
                  <SyntaxHighlighter language="bash" style={tomorrow}>
                    {`Authorization: Bearer YOUR_API_KEY`}
                  </SyntaxHighlighter>
                </Card>
              </Col>
              <Col span={12}>
                <Card title="基础URL" size="small">
                  <Paragraph>
                    API的基础URL为：
                  </Paragraph>
                  <SyntaxHighlighter language="text" style={tomorrow}>
                    {`https://api.ragflow.com/v1`}
                  </SyntaxHighlighter>
                </Card>
              </Col>
            </Row>

            <Divider />

            <Title level={4}>主要接口</Title>
            
            <Collapse>
              <Panel header="文档管理" key="documents">
                <div className="space-y-4">
                  <div>
                    <Tag color="blue">GET</Tag>
                    <code className="ml-2">/documents</code>
                    <Paragraph className="mt-2">获取文档列表</Paragraph>
                  </div>
                  <div>
                    <Tag color="green">POST</Tag>
                    <code className="ml-2">/documents</code>
                    <Paragraph className="mt-2">上传新文档</Paragraph>
                  </div>
                  <div>
                    <Tag color="orange">PUT</Tag>
                    <code className="ml-2">/documents/{id}</code>
                    <Paragraph className="mt-2">更新文档信息</Paragraph>
                  </div>
                  <div>
                    <Tag color="red">DELETE</Tag>
                    <code className="ml-2">/documents/{id}</code>
                    <Paragraph className="mt-2">删除文档</Paragraph>
                  </div>
                </div>
              </Panel>
              
              <Panel header="知识库管理" key="knowledge-bases">
                <div className="space-y-4">
                  <div>
                    <Tag color="blue">GET</Tag>
                    <code className="ml-2">/knowledge-bases</code>
                    <Paragraph className="mt-2">获取知识库列表</Paragraph>
                  </div>
                  <div>
                    <Tag color="green">POST</Tag>
                    <code className="ml-2">/knowledge-bases</code>
                    <Paragraph className="mt-2">创建新知识库</Paragraph>
                  </div>
                  <div>
                    <Tag color="blue">GET</Tag>
                    <code className="ml-2">/knowledge-bases/{id}/search</code>
                    <Paragraph className="mt-2">在知识库中搜索</Paragraph>
                  </div>
                </div>
              </Panel>
              
              <Panel header="AI对话" key="chat">
                <div className="space-y-4">
                  <div>
                    <Tag color="green">POST</Tag>
                    <code className="ml-2">/chat/completions</code>
                    <Paragraph className="mt-2">发送对话消息</Paragraph>
                    <SyntaxHighlighter language="json" style={tomorrow}>
{`{
  "message": "What is this document about?",
  "knowledge_base": "kb_123",
  "model": "gpt-3.5-turbo",
  "temperature": 0.7
}`}
                    </SyntaxHighlighter>
                  </div>
                </div>
              </Panel>
            </Collapse>

            <Divider />

            <Alert
              message="SDK支持"
              description={
                <div>
                  <Paragraph>我们提供多种编程语言的SDK：</Paragraph>
                  <Space wrap>
                    <Tag>Python</Tag>
                    <Tag>JavaScript</Tag>
                    <Tag>Java</Tag>
                    <Tag>Go</Tag>
                    <Tag>PHP</Tag>
                  </Space>
                </div>
              }
              type="info"
              showIcon
            />
          </Card>
        </TabPane>

        {/* 常见问题 */}
        <TabPane tab={<span><QuestionCircleOutlined />常见问题</span>} key="faq">
          <Card>
            <div className="mb-4">
              <Title level={3}>常见问题</Title>
              <Text type="secondary">
                找到 {filteredFaqs.length} 个相关问题
              </Text>
            </div>

            <Collapse>
              {filteredFaqs.map(faq => (
                <Panel
                  key={faq.id}
                  header={
                    <div className="flex justify-between items-center">
                      <span>{faq.question}</span>
                      <div className="flex items-center space-x-2">
                        <Tag>{faq.category}</Tag>
                        <Badge count={faq.helpful} showZero color="#52c41a" />
                      </div>
                    </div>
                  }
                >
                  <div className="space-y-4">
                    <ReactMarkdown>{faq.answer}</ReactMarkdown>
                    
                    <div className="flex justify-between items-center pt-4 border-t">
                      <div>
                        {faq.tags.map(tag => (
                          <Tag key={tag} size="small">{tag}</Tag>
                        ))}
                      </div>
                      <div className="flex items-center space-x-2">
                        <Text type="secondary">这个回答有帮助吗？</Text>
                        <Button
                          type="text"
                          size="small"
                          icon={<HeartOutlined />}
                          onClick={() => markHelpful(faq.id)}
                        >
                          有帮助 ({faq.helpful})
                        </Button>
                      </div>
                    </div>
                  </div>
                </Panel>
              ))}
            </Collapse>
          </Card>
        </TabPane>

        {/* 教程 */}
        <TabPane tab={<span><ToolOutlined />教程</span>} key="tutorials">
          <Row gutter={[16, 16]}>
            {tutorials.map(tutorial => (
              <Col span={12} key={tutorial.id}>
                <Card
                  title={
                    <div className="flex justify-between items-center">
                      <span>{tutorial.title}</span>
                      <div className="flex items-center space-x-2">
                        <Tag color={getDifficultyColor(tutorial.difficulty)}>
                          {getDifficultyText(tutorial.difficulty)}
                        </Tag>
                        <Text type="secondary">{tutorial.duration}</Text>
                      </div>
                    </div>
                  }
                  extra={<Button type="link">开始学习</Button>}
                >
                  <Paragraph>{tutorial.description}</Paragraph>
                  
                  <Steps size="small" direction="vertical">
                    {tutorial.steps.map((step, index) => (
                      <Step
                        key={index}
                        title={step.title}
                        description={
                          <div>
                            <Paragraph className="mb-2">{step.content}</Paragraph>
                            {step.code && (
                              <SyntaxHighlighter language="bash" style={tomorrow}>
                                {step.code}
                              </SyntaxHighlighter>
                            )}
                          </div>
                        }
                      />
                    ))}
                  </Steps>
                </Card>
              </Col>
            ))}
          </Row>
        </TabPane>

        {/* 联系支持 */}
        <TabPane tab={<span><MailOutlined />联系支持</span>} key="contact">
          <Row gutter={[16, 16]}>
            <Col span={12}>
              <Card title="联系方式">
                <div className="space-y-4">
                  <div className="flex items-center space-x-3">
                    <MailOutlined className="text-blue-500" />
                    <div>
                      <div className="font-medium">邮箱支持</div>
                      <Text type="secondary">support@ragflow.com</Text>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-3">
                    <PhoneOutlined className="text-green-500" />
                    <div>
                      <div className="font-medium">电话支持</div>
                      <Text type="secondary">400-123-4567</Text>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-3">
                    <GlobalOutlined className="text-purple-500" />
                    <div>
                      <div className="font-medium">在线客服</div>
                      <Text type="secondary">工作日 9:00-18:00</Text>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-3">
                    <GithubOutlined className="text-gray-700" />
                    <div>
                      <div className="font-medium">GitHub</div>
                      <Text type="secondary">github.com/ragflow/ragflow</Text>
                    </div>
                  </div>
                </div>
              </Card>
            </Col>
            
            <Col span={12}>
              <Card title="社区资源">
                <List
                  dataSource={[
                    {
                      title: '用户社区',
                      description: '与其他用户交流经验',
                      icon: <GlobalOutlined />,
                      link: '#',
                    },
                    {
                      title: '开发者论坛',
                      description: '技术讨论和问题解答',
                      icon: <GithubOutlined />,
                      link: '#',
                    },
                    {
                      title: '知识库',
                      description: '详细的技术文档',
                      icon: <BookOutlined />,
                      link: '#',
                    },
                    {
                      title: '视频教程',
                      description: '视频形式的使用指南',
                      icon: <VideoCameraOutlined />,
                      link: '#',
                    },
                  ]}
                  renderItem={(item) => (
                    <List.Item>
                      <List.Item.Meta
                        avatar={<Avatar icon={item.icon} />}
                        title={<a href={item.link}>{item.title}</a>}
                        description={item.description}
                      />
                      <Button type="link" icon={<LinkOutlined />}>
                        访问
                      </Button>
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
          </Row>
        </TabPane>
      </Tabs>

      <BackTop />
    </div>
  );
};

export default HelpPage;