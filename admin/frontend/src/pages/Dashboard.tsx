import {
  ApiOutlined,
  DatabaseOutlined,
  FileTextOutlined,
  MessageOutlined,
} from '@ant-design/icons'
import { App, Card, Col, Empty, Progress, Row, Spin, Tag, Timeline, Tooltip } from 'antd'
import { useEffect, useState } from 'react'
import { getDashboard } from '../api'
import type { DashboardStats } from '../types'

const INTENT_LABEL: Record<string, string> = {
  FAQ: '知识库查询',
  ORDER: '订单查询',
  SHIPPING: '物流追踪',
  REFUND: '退款请求',
  COMPLAINT: '投诉处理',
  CHITCHAT: '日常闲聊',
}

const ACTION_LABEL: Record<string, { text: string; color: string }> = {
  create: { text: '新增', color: 'green' },
  update: { text: '更新', color: 'blue' },
  delete: { text: '删除', color: 'red' },
  rollback: { text: '回滚', color: 'orange' },
  activate: { text: '设为生效', color: 'purple' },
  set_default: { text: '设为默认', color: 'geekblue' },
}

const ENTITY_LABEL: Record<string, string> = {
  kb_item: '知识库条目',
  kb_category: '知识库分类',
  prompt: 'Prompt',
  model: '大模型配置',
}

export default function Dashboard() {
  const { message } = App.useApp()
  const [data, setData] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getDashboard()
      .then(setData)
      .catch((e) => message.error(e.message))
      .finally(() => setLoading(false))
  }, [message])

  if (loading || !data) {
    return (
      <div style={{ textAlign: 'center', padding: 80 }}>
        <Spin size="large" />
      </div>
    )
  }

  const stats = [
    {
      label: '知识库条目',
      value: data.kb.total,
      icon: <DatabaseOutlined />,
      bg: 'linear-gradient(135deg,#6366f1,#4f46e5)',
      extra: `已发布 ${data.kb.published} · 草稿 ${data.kb.draft}`,
    },
    {
      label: 'Prompt 模板',
      value: data.prompts.total,
      icon: <FileTextOutlined />,
      bg: 'linear-gradient(135deg,#0ea5e9,#2563eb)',
      extra: `生效中 ${data.prompts.enabled} 个`,
    },
    {
      label: '大模型配置',
      value: data.models.total,
      icon: <ApiOutlined />,
      bg: 'linear-gradient(135deg,#10b981,#059669)',
      extra: `启用 ${data.models.enabled} 个`,
    },
    {
      label: '累计对话',
      value: data.chats.total,
      icon: <MessageOutlined />,
      bg: 'linear-gradient(135deg,#f59e0b,#ea580c)',
      extra: `待人工复核 ${data.chats.pending_review} 条`,
    },
  ]

  const maxIntent = Math.max(1, ...data.intent_distribution.map((i) => i.value))
  const maxCat = Math.max(1, ...data.category_distribution.map((i) => i.value))
  const maxHit = Math.max(1, ...data.top_items.map((i) => i.hit_count))

  return (
    <Row gutter={[16, 16]}>
      {stats.map((s) => (
        <Col xs={24} sm={12} xl={6} key={s.label}>
          <Card bordered={false} styles={{ body: { padding: '18px 20px' } }}>
            <div className="stat-card">
              <div className="stat-icon" style={{ background: s.bg }}>
                {s.icon}
              </div>
              <div>
                <div className="stat-value">{s.value}</div>
                <div className="stat-label">{s.label}</div>
              </div>
            </div>
            <div style={{ marginTop: 12, fontSize: 12, color: '#9095a8' }}>{s.extra}</div>
          </Card>
        </Col>
      ))}

      <Col xs={24} lg={12}>
        <Card bordered={false} title="用户意图分布" styles={{ body: { paddingTop: 8 } }}>
          {data.intent_distribution.length === 0 ? (
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} />
          ) : (
            data.intent_distribution.map((i) => (
              <div key={i.name} style={{ marginBottom: 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4 }}>
                  <span style={{ color: '#3d4157' }}>{INTENT_LABEL[i.name] ?? i.name}</span>
                  <span style={{ color: '#8a8fa3' }}>{i.value} 次</span>
                </div>
                <Progress
                  percent={Math.round((i.value / maxIntent) * 100)}
                  showInfo={false}
                  strokeColor={{ from: '#818cf8', to: '#4f46e5' }}
                />
              </div>
            ))
          )}
        </Card>
      </Col>

      <Col xs={24} lg={12}>
        <Card bordered={false} title="知识库分类分布" styles={{ body: { paddingTop: 8 } }}>
          {data.category_distribution.map((i) => (
            <div key={i.name} style={{ marginBottom: 10 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4 }}>
                <span style={{ color: '#3d4157' }}>{i.name}</span>
                <span style={{ color: '#8a8fa3' }}>{i.value} 条</span>
              </div>
              <Progress
                percent={Math.round((i.value / maxCat) * 100)}
                showInfo={false}
                strokeColor={{ from: '#67e8f9', to: '#0ea5e9' }}
              />
            </div>
          ))}
        </Card>
      </Col>

      <Col xs={24} lg={14}>
        <Card bordered={false} title="知识库命中排行 TOP 8" styles={{ body: { paddingTop: 14 } }}>
          {data.top_items.map((item, idx) => (
            <div className="rank-row" key={item.id}>
              <div
                className="rank-badge"
                style={idx < 3 ? { background: 'linear-gradient(135deg,#6366f1,#4f46e5)', color: '#fff' } : {}}
              >
                {idx + 1}
              </div>
              <Tooltip title={item.title}>
                <div className="rank-name">{item.title}</div>
              </Tooltip>
              <Tag style={{ borderRadius: 20, fontSize: 11 }}>{item.category}</Tag>
              <div style={{ flex: 1, minWidth: 60 }}>
                <Progress
                  percent={Math.round((item.hit_count / maxHit) * 100)}
                  showInfo={false}
                  strokeColor={{ from: '#a78bfa', to: '#7c3aed' }}
                  size="small"
                />
              </div>
              <span style={{ fontSize: 12, color: '#8a8fa3', width: 52, textAlign: 'right' }}>
                {item.hit_count} 次
              </span>
            </div>
          ))}
        </Card>
      </Col>

      <Col xs={24} lg={10}>
        <Card bordered={false} title="最近配置变更" styles={{ body: { paddingTop: 18, maxHeight: 380, overflow: 'auto' } }}>
          <Timeline
            items={data.recent_changes.map((c) => {
              const act = ACTION_LABEL[c.action] ?? { text: c.action, color: 'gray' }
              return {
                color: act.color,
                children: (
                  <div style={{ fontSize: 13 }}>
                    <Tag color={act.color} style={{ borderRadius: 6, marginInlineEnd: 6 }}>
                      {act.text}
                    </Tag>
                    <span style={{ color: '#5b6079' }}>{ENTITY_LABEL[c.entity_type] ?? c.entity_type}</span>
                    <div style={{ color: '#1e2030', fontWeight: 500, margin: '3px 0' }}>{c.entity_name}</div>
                    <div style={{ color: '#a0a4b8', fontSize: 11.5 }}>
                      {c.operator} · {c.created_at ? new Date(c.created_at).toLocaleString('zh-CN') : ''}
                    </div>
                  </div>
                ),
              }
            })}
          />
        </Card>
      </Col>
    </Row>
  )
}
