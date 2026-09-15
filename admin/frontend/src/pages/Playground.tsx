import { ClearOutlined, DatabaseOutlined, SendOutlined } from '@ant-design/icons'
import {
  Alert,
  App,
  Button,
  Card,
  Col,
  Divider,
  Empty,
  Input,
  Row,
  Space,
  Tag,
  Tooltip,
  Typography,
} from 'antd'
import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { chat, getScenarios } from '../api'
import type { ChatResult, TraceStep } from '../types'

interface Msg {
  role: 'user' | 'bot'
  text: string
  result?: ChatResult
}

const SAFETY_COLOR: Record<string, string> = {
  '🔴 极高风险': 'red',
  '🟠 高风险': 'orange',
  '🟡 中风险': 'gold',
  '🟢 低风险': 'green',
}

export default function Playground() {
  const { message } = App.useApp()
  const navigate = useNavigate()
  const [msgs, setMsgs] = useState<Msg[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [scenarios, setScenarios] = useState<{ label: string; text: string }[]>([])
  const [lastTrace, setLastTrace] = useState<TraceStep[]>([])
  const [lastResult, setLastResult] = useState<ChatResult | null>(null)
  const chatRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    getScenarios()
      .then(setScenarios)
      .catch(() => setScenarios([]))
  }, [])

  useEffect(() => {
    chatRef.current?.scrollTo({ top: chatRef.current.scrollHeight, behavior: 'smooth' })
  }, [msgs])

  const send = async (text?: string) => {
    const content = (text ?? input).trim()
    if (!content || loading) return
    setMsgs((m) => [...m, { role: 'user', text: content }])
    setInput('')
    setLoading(true)
    try {
      const res = await chat(content)
      setMsgs((m) => [...m, { role: 'bot', text: res.reply, result: res }])
      setLastTrace(res.trace)
      setLastResult(res)
    } catch (e: any) {
      message.error(e.message)
      setMsgs((m) => [...m, { role: 'bot', text: `⚠️ 调用失败：${e.message}` }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <Row gutter={16}>
      <Col xs={24} lg={14}>
        <Card
          bordered={false}
          title="💬 对话调试"
          extra={
            <Button
              size="small"
              icon={<ClearOutlined />}
              onClick={() => {
                setMsgs([])
                setLastTrace([])
                setLastResult(null)
              }}
            >
              清空
            </Button>
          }
          styles={{ body: { paddingTop: 12 } }}
        >
          <Alert
            type="success"
            showIcon
            style={{ marginBottom: 12 }}
            message="配置驱动验证"
            description={
              <span>
                Agent 运行时实时从配置库读取知识库与 Prompt。去「知识库管理」改一条答案，再回来问同样的问题，回复会立即变化。
                <Button type="link" size="small" onClick={() => navigate('/knowledge')} style={{ padding: 0 }}>
                  前往修改 →
                </Button>
              </span>
            }
          />
          <Space size={[6, 6]} wrap style={{ marginBottom: 12 }}>
            {scenarios.map((s) => (
              <Tag
                key={s.text}
                className="scene-chip"
                color="processing"
                style={{ borderRadius: 20, padding: '3px 11px', marginInlineEnd: 0 }}
                onClick={() => send(s.text)}
              >
                {s.label}
              </Tag>
            ))}
          </Space>

          <div className="chat-window" ref={chatRef}>
            {msgs.length === 0 && (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="点击上方场景标签，或在下方输入问题开始调试"
                style={{ marginTop: 64 }}
              />
            )}
            {msgs.map((m, i) => (
              <div key={i} style={{ marginBottom: 14 }}>
                {m.role === 'bot' && m.result && (
                  <Space size={4} wrap style={{ marginBottom: 6 }}>
                    <Tag color="purple" style={{ borderRadius: 20, fontSize: 11 }}>
                      {m.result.intent_name}
                    </Tag>
                    <Tag color="blue" style={{ borderRadius: 20, fontSize: 11 }}>
                      置信度 {(m.result.confidence * 100).toFixed(0)}%
                    </Tag>
                    <Tag
                      color={SAFETY_COLOR[m.result.safety.level] ?? 'default'}
                      style={{ borderRadius: 20, fontSize: 11 }}
                    >
                      {m.result.safety.level}
                    </Tag>
                    <Tag style={{ borderRadius: 20, fontSize: 11 }}>
                      {m.result.language === 'zh' ? '中文' : 'EN'}
                    </Tag>
                  </Space>
                )}
                <div className={`chat-bubble ${m.role}`}>{m.text}</div>
              </div>
            ))}
          </div>

          <Divider style={{ margin: '10px 0' }} />
          <Space.Compact style={{ width: '100%' }}>
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onPressEnter={() => send()}
              placeholder="输入用户问题，如：我想退货，尺码不合适"
              disabled={loading}
            />
            <Button type="primary" icon={<SendOutlined />} loading={loading} onClick={() => send()}>
              发送
            </Button>
          </Space.Compact>
        </Card>
      </Col>

      <Col xs={24} lg={10}>
        <Card
          bordered={false}
          title="🧠 推理 Trace"
          extra={lastResult && <Tag color="purple">{lastResult.intent_name}</Tag>}
          styles={{ body: { maxHeight: 300, overflow: 'auto', paddingTop: 14 } }}
        >
          {lastTrace.length === 0 ? (
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="发送一条消息后展示思考轨迹" />
          ) : (
            lastTrace.map((t, i) => (
              <div className="trace-item" key={i}>
                <span style={{ fontSize: 15 }}>{t.icon}</span>
                <div>
                  <div className="trace-step">{t.step}</div>
                  <div className="trace-detail">{t.detail}</div>
                </div>
              </div>
            ))
          )}
        </Card>

        <Card bordered={false} title="📎 配置溯源" style={{ marginTop: 16 }} styles={{ body: { paddingTop: 14 } }}>
          {!lastResult ? (
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无数据" />
          ) : (
            <>
              <div style={{ marginBottom: 10 }}>
                <span style={{ color: '#8a8fa3', fontSize: 12.5 }}>知识库命中：</span>
                {lastResult.matched_item_id ? (
                  <Tag
                    color="green"
                    icon={<DatabaseOutlined />}
                    style={{ borderRadius: 20, cursor: 'pointer' }}
                    onClick={() => navigate('/knowledge')}
                  >
                    条目 #{lastResult.matched_item_id}（点击查看）
                  </Tag>
                ) : (
                  <Tag style={{ borderRadius: 20 }}>未命中</Tag>
                )}
              </div>
              <div style={{ marginBottom: 10 }}>
                <span style={{ color: '#8a8fa3', fontSize: 12.5 }}>数据来源：</span>
                <Tag style={{ borderRadius: 20 }}>{lastResult.source}</Tag>
              </div>
              <div>
                <span style={{ color: '#8a8fa3', fontSize: 12.5 }}>安全策略：</span>
                <Tag color={SAFETY_COLOR[lastResult.safety.level] ?? 'default'} style={{ borderRadius: 20 }}>
                  {lastResult.safety.action}
                </Tag>
              </div>
            </>
          )}
        </Card>

        <Card bordered={false} title="📖 演示用 Mock 数据" style={{ marginTop: 16 }}>
          <Typography.Paragraph style={{ fontSize: 12.5, color: '#5b6079', marginBottom: 8 }}>
            <b>订单号：</b>
          </Typography.Paragraph>
          <Space size={[6, 6]} wrap>
            {['US2024-3821', 'US2024-4521', 'US2024-5100'].map((o) => (
              <Tooltip key={o} title="点击填入输入框">
                <Tag
                  className="scene-chip"
                  style={{ borderRadius: 20 }}
                  onClick={() => setInput(`What's the status of my order ${o}?`)}
                >
                  {o}
                </Tag>
              </Tooltip>
            ))}
          </Space>
          <Typography.Paragraph style={{ fontSize: 12.5, color: '#5b6079', margin: '12px 0 8px' }}>
            <b>物流单号：</b>
          </Typography.Paragraph>
          <Space size={[6, 6]} wrap>
            {['SF7890123456', 'DHL9876543210', '4PX1122334455'].map((t) => (
              <Tag
                key={t}
                className="scene-chip"
                style={{ borderRadius: 20 }}
                onClick={() => setInput(`Where is my package with tracking number ${t}?`)}
              >
                {t}
              </Tag>
            ))}
          </Space>
        </Card>
      </Col>
    </Row>
  )
}
