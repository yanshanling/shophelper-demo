import {
  ApiOutlined,
  DatabaseOutlined,
  FileTextOutlined,
  RobotOutlined,
  AppstoreOutlined,
} from '@ant-design/icons'
import { Avatar, Layout, Menu, Tag } from 'antd'
import { Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Knowledge from './pages/Knowledge'
import Models from './pages/Models'
import Playground from './pages/Playground'
import Prompts from './pages/Prompts'

const { Sider, Header, Content } = Layout

const PAGE_META: Record<string, { title: string; sub: string }> = {
  '/dashboard': { title: '概览', sub: '配置资产与运营数据总览' },
  '/knowledge': { title: '知识库管理', sub: '分类与双语 FAQ 条目的增删改查、检索测试' },
  '/prompts': { title: 'Prompt 管理', sub: '人设与场景话术的编辑、版本回滚与生效控制' },
  '/models': { title: '大模型接入', sub: 'OpenAI 兼容协议的模型配置与多语言路由' },
  '/playground': { title: 'Agent 测试台', sub: '实时验证配置改动对 Agent 行为的影响' },
}

const MENU = [
  { key: '/dashboard', icon: <AppstoreOutlined />, label: '概览' },
  { key: '/knowledge', icon: <DatabaseOutlined />, label: '知识库管理' },
  { key: '/prompts', icon: <FileTextOutlined />, label: 'Prompt 管理' },
  { key: '/models', icon: <ApiOutlined />, label: '大模型接入' },
  { key: '/playground', icon: <RobotOutlined />, label: 'Agent 测试台' },
]

export default function App() {
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const meta = PAGE_META[pathname] ?? PAGE_META['/dashboard']

  return (
    <Layout style={{ height: '100vh' }}>
      <Sider width={232} className="admin-sider" theme="light">
        <div className="admin-logo">
          <div className="logo-mark">🌐</div>
          <div className="logo-text">
            <b>ShopHelper</b>
            <span>客服 Agent 运营后台</span>
          </div>
        </div>
        <Menu
          mode="inline"
          selectedKeys={[pathname]}
          items={MENU}
          onClick={(e) => navigate(e.key)}
          style={{ borderInlineEnd: 'none' }}
        />
      </Sider>
      <Layout>
        <Header className="admin-header">
          <div>
            <div className="page-title">{meta.title}</div>
            <div className="page-sub">{meta.sub}</div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <Tag color="processing" style={{ borderRadius: 20, padding: '2px 10px' }}>
              演示环境
            </Tag>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Avatar size={30} style={{ background: '#4f46e5' }}>
                运
              </Avatar>
              <span style={{ fontSize: 13, color: '#3d4157' }}>运营 · Amy</span>
            </div>
          </div>
        </Header>
        <Content className="admin-content">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/knowledge" element={<Knowledge />} />
            <Route path="/prompts" element={<Prompts />} />
            <Route path="/models" element={<Models />} />
            <Route path="/playground" element={<Playground />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  )
}
