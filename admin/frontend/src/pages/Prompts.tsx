import {
  CheckCircleOutlined,
  HistoryOutlined,
  PlusOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'
import {
  App,
  Button,
  Card,
  Col,
  Collapse,
  Empty,
  Form,
  Input,
  Modal,
  Popconfirm,
  Row,
  Space,
  Tag,
  Timeline,
  Tooltip,
} from 'antd'
import { useCallback, useEffect, useState } from 'react'
import {
  createPrompt,
  deletePrompt,
  listPromptVersions,
  listPrompts,
  renderPrompt,
  rollbackPrompt,
  setDefaultPrompt,
  updatePrompt,
} from '../api'
import type { PromptTemplate, PromptVersion } from '../types'

const SCENE_META: Record<string, { text: string; color: string }> = {
  system: { text: '人设主 Prompt', color: 'purple' },
  faq: { text: 'FAQ 话术', color: 'blue' },
  refund: { text: '退款话术', color: 'orange' },
  complaint: { text: '投诉话术', color: 'red' },
  order: { text: '订单话术', color: 'cyan' },
}

export default function Prompts() {
  const { message } = App.useApp()
  const [prompts, setPrompts] = useState<PromptTemplate[]>([])
  const [active, setActive] = useState<PromptTemplate | null>(null)
  const [content, setContent] = useState('')
  const [versions, setVersions] = useState<PromptVersion[]>([])
  const [saving, setSaving] = useState(false)
  const [createOpen, setCreateOpen] = useState(false)
  const [form] = Form.useForm()
  const [previewVars, setPreviewVars] = useState<Record<string, string>>({})
  const [preview, setPreview] = useState('')

  const load = useCallback(async () => {
    const list = await listPrompts()
    setPrompts(list)
    return list
  }, [])

  useEffect(() => {
    load()
      .then((list) => {
        if (list.length && !active) {
          setActive(list[0])
          setContent(list[0].content)
        }
      })
      .catch((e) => message.error(e.message))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (!active) return
    listPromptVersions(active.id)
      .then(setVersions)
      .catch(() => setVersions([]))
    setPreview('')
    setPreviewVars({})
  }, [active])

  const selectPrompt = (p: PromptTemplate) => {
    setActive(p)
    setContent(p.content)
  }

  const save = async () => {
    if (!active) return
    setSaving(true)
    try {
      const updated = await updatePrompt(active.id, { content })
      message.success(`已保存，版本升级至 v${updated.version}`)
      setActive(updated)
      const list = await load()
      const fresh = list.find((p) => p.id === updated.id)
      if (fresh) setContent(fresh.content)
      setVersions(await listPromptVersions(updated.id))
    } catch (e: any) {
      message.error(e.message)
    } finally {
      setSaving(false)
    }
  }

  const activate = async (p: PromptTemplate) => {
    await setDefaultPrompt(p.id)
    message.success(`「${p.name}」已设为该场景生效版本`)
    const list = await load()
    const fresh = list.find((x) => x.id === p.id)
    if (fresh && active?.id === p.id) setActive(fresh)
  }

  const doRollback = async (v: PromptVersion) => {
    if (!active) return
    const updated = await rollbackPrompt(active.id, v.id)
    message.success(`已回滚到 v${v.version} 的内容（新版本 v${updated.version}）`)
    setActive(updated)
    setContent(updated.content)
    await load()
    setVersions(await listPromptVersions(updated.id))
  }

  const doPreview = async () => {
    if (!active) return
    const res = await renderPrompt(active.id, previewVars)
    setPreview(res.rendered)
    setPreview('')
    setTimeout(() => setPreview(res.rendered), 0)
  }

  const submitCreate = async () => {
    const values = await form.validateFields()
    try {
      await createPrompt(values)
      message.success('Prompt 已创建')
      setCreateOpen(false)
      form.resetFields()
      const list = await load()
      if (list.length) selectPrompt(list[list.length - 1])
    } catch (e: any) {
      message.error(e.message)
    }
  }

  const varList = (active?.variables || '')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)

  return (
    <Row gutter={16}>
      <Col xs={24} lg={8}>
        <Card
          bordered={false}
          title="Prompt 模板"
          extra={
            <Button type="primary" size="small" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
              新建
            </Button>
          }
          styles={{ body: { padding: 12 } }}
        >
          {prompts.map((p) => (
            <div
              key={p.id}
              className={`kb-cat-item ${active?.id === p.id ? 'active' : ''}`}
              style={{ display: 'block' }}
              onClick={() => selectPrompt(p)}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: 13.5 }}>{p.name}</span>
                {p.is_default && <CheckCircleOutlined style={{ color: '#10b981' }} />}
              </div>
              <Space size={4} style={{ marginTop: 6 }} wrap>
                <Tag color={SCENE_META[p.scene]?.color ?? 'default'} style={{ borderRadius: 20, fontSize: 11 }}>
                  {SCENE_META[p.scene]?.text ?? p.scene}
                </Tag>
                <Tag style={{ borderRadius: 20, fontSize: 11 }}>v{p.version}</Tag>
                {!p.enabled && (
                  <Tag color="default" style={{ borderRadius: 20, fontSize: 11 }}>
                    未生效
                  </Tag>
                )}
              </Space>
            </div>
          ))}
        </Card>
      </Col>

      <Col xs={24} lg={16}>
        {!active ? (
          <Card bordered={false}>
            <Empty description="请选择左侧 Prompt 模板" />
          </Card>
        ) : (
          <Card
            bordered={false}
            title={
              <Space>
                <span>{active.name}</span>
                <Tag color={SCENE_META[active.scene]?.color ?? 'default'}>
                  {SCENE_META[active.scene]?.text ?? active.scene}
                </Tag>
                <Tag>v{active.version}</Tag>
              </Space>
            }
            extra={
              <Space>
                <Tooltip title="设为该场景的生效版本，Agent 运行时将读取它">
                  <Button icon={<ThunderboltOutlined />} onClick={() => activate(active)} disabled={active.is_default}>
                    {active.is_default ? '生效中' : '设为生效'}
                  </Button>
                </Tooltip>
                <Popconfirm
                  title="确认删除该 Prompt？"
                  onConfirm={async () => {
                    await deletePrompt(active.id)
                    message.success('已删除')
                    setActive(null)
                    const list = await load()
                    if (list.length) selectPrompt(list[0])
                  }}
                >
                  <Button danger>删除</Button>
                </Popconfirm>
                <Button type="primary" loading={saving} onClick={save}>
                  保存
                </Button>
              </Space>
            }
          >
            <Form layout="vertical">
              <Form.Item
                label="Prompt 内容"
                extra={
                  varList.length > 0 && (
                    <span style={{ fontSize: 12 }}>
                      可用变量：{varList.map((v) => <Tag key={v} color="geekblue">{`{${v}}`}</Tag>)}
                    </span>
                  )
                }
              >
                <Input.TextArea
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  rows={16}
                  style={{ fontFamily: 'Consolas, Monaco, monospace', fontSize: 12.5, lineHeight: 1.75 }}
                />
              </Form.Item>
            </Form>
            <Collapse
              ghost
              items={[
                {
                  key: 'preview',
                  label: (
                    <Space>
                      <ThunderboltOutlined />
                      <span>渲染预览（填变量，看运营改动后的最终效果）</span>
                    </Space>
                  ),
                  children: (
                    <>
                      <Space wrap style={{ marginBottom: 10 }}>
                        {varList.map((v) => (
                          <Input
                            key={v}
                            addonBefore={v}
                            size="small"
                            style={{ width: 220 }}
                            value={previewVars[v] || ''}
                            onChange={(e) => setPreviewVars({ ...previewVars, [v]: e.target.value })}
                          />
                        ))}
                        <Button size="small" type="primary" onClick={doPreview} disabled={!varList.length}>
                          渲染
                        </Button>
                      </Space>
                      {preview && <div className="code-block">{preview}</div>}
                    </>
                  ),
                },
                {
                  key: 'versions',
                  label: (
                    <Space>
                      <HistoryOutlined />
                      <span>版本历史（{versions.length}）</span>
                    </Space>
                  ),
                  children: (
                    <Timeline
                      items={versions.map((v) => ({
                        color: v.version === active.version ? 'blue' : 'gray',
                        children: (
                          <div style={{ fontSize: 13 }}>
                            <Space>
                              <b>v{v.version}</b>
                              <span style={{ color: '#9095a8' }}>{v.note}</span>
                              {v.version === active.version && <Tag color="blue">当前</Tag>}
                              {v.version !== active.version && (
                                <Popconfirm
                                  title={`回滚到 v${v.version} 的内容？`}
                                  onConfirm={() => doRollback(v)}
                                >
                                  <Button type="link" size="small">
                                    回滚
                                  </Button>
                                </Popconfirm>
                              )}
                            </Space>
                            <div style={{ color: '#a0a4b8', fontSize: 11.5, marginTop: 2 }}>
                              {v.operator} · {v.created_at ? new Date(v.created_at).toLocaleString('zh-CN') : ''}
                            </div>
                          </div>
                        ),
                      }))}
                    />
                  ),
                },
              ]}
            />
          </Card>
        )}
      </Col>

      <Modal
        open={createOpen}
        title="新建 Prompt 模板"
        onCancel={() => setCreateOpen(false)}
        onOk={submitCreate}
        okText="创建"
        destroyOnClose
      >
        <Form form={form} layout="vertical" style={{ marginTop: 12 }}>
          <Form.Item name="name" label="名称" rules={[{ required: true }]}>
            <Input placeholder="如：订单查询话术" />
          </Form.Item>
          <Form.Item name="scene" label="场景" rules={[{ required: true }]}>
            <Input placeholder="system / faq / refund / complaint / order" />
          </Form.Item>
          <Form.Item name="variables" label="变量（逗号分隔）">
            <Input placeholder="category,kb_content" />
          </Form.Item>
          <Form.Item name="content" label="内容">
            <Input.TextArea rows={8} placeholder="支持 {variable} 占位符" />
          </Form.Item>
          <Form.Item name="note" label="备注">
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </Row>
  )
}
