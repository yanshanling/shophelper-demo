import {
  ApiOutlined,
  CloudServerOutlined,
  PlusOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'
import {
  Alert,
  App,
  Button,
  Card,
  Col,
  Form,
  Input,
  InputNumber,
  Modal,
  Popconfirm,
  Row,
  Select,
  Slider,
  Space,
  Table,
  Tag,
  Tooltip,
} from 'antd'
import { useCallback, useEffect, useState } from 'react'
import { createModel, deleteModel, listModels, setDefaultModel, testModel, updateModel } from '../api'
import type { ModelConfig } from '../types'

const PROVIDERS = [
  { value: 'openai', label: 'OpenAI', base: 'https://api.openai.com/v1' },
  { value: 'deepseek', label: 'DeepSeek', base: 'https://api.deepseek.com/v1' },
  { value: 'qwen', label: '通义千问（兼容模式）', base: 'https://dashscope.aliyuncs.com/compatible-mode/v1' },
  { value: 'azure', label: 'Azure OpenAI', base: 'https://<resource>.openai.azure.com/' },
  { value: 'ollama', label: '本地 Ollama', base: 'http://localhost:11434/v1' },
  { value: 'custom', label: '自定义（OpenAI 兼容）', base: '' },
]

const ROUTE_META: Record<string, { text: string; color: string }> = {
  all: { text: '全语言兜底', color: 'geekblue' },
  zh: { text: '中文线路', color: 'volcano' },
  en: { text: '英文线路', color: 'blue' },
}

export default function Models() {
  const { message } = App.useApp()
  const [models, setModels] = useState<ModelConfig[]>([])
  const [loading, setLoading] = useState(false)
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState<ModelConfig | null>(null)
  const [testing, setTesting] = useState<number | null>(null)
  const [form] = Form.useForm()

  const load = useCallback(async () => {
    setLoading(true)
    try {
      setModels(await listModels())
    } catch (e: any) {
      message.error(e.message)
    } finally {
      setLoading(false)
    }
  }, [message])

  useEffect(() => {
    load()
  }, [load])

  const openModal = (m?: ModelConfig) => {
    setEditing(m ?? null)
    if (m) form.setFieldsValue(m)
    else
      form.setFieldsValue({
        provider: 'openai',
        base_url: PROVIDERS[0].base,
        model_name: 'gpt-4o-mini',
        temperature: 0.3,
        max_tokens: 1024,
        top_p: 1.0,
        route_lang: 'all',
        enabled: true,
      })
    setOpen(true)
  }

  const submit = async () => {
    const values = await form.validateFields()
    try {
      if (editing) await updateModel(editing.id, values)
      else await createModel(values)
      message.success('模型配置已保存')
      setOpen(false)
      load()
    } catch (e: any) {
      message.error(e.message)
    }
  }

  const doTest = async (m: ModelConfig) => {
    setTesting(m.id)
    try {
      const res = await testModel(m.id)
      if (res.success) message.success(res.message)
      else message.error(res.message)
      load()
    } catch (e: any) {
      message.error(e.message)
    } finally {
      setTesting(null)
    }
  }

  return (
    <>
      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
        message="统一走 OpenAI 兼容协议接入，切换模型只需改配置、不动代码；按语言线路路由，实现「英文线 + 中文线 + 兜底」策略。"
      />
      <Card
        bordered={false}
        title="模型接入配置"
        extra={
          <Space>
            <Button icon={<CloudServerOutlined />} onClick={load}>
              刷新
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => openModal()}>
              新增模型
            </Button>
          </Space>
        }
      >
        <Table<ModelConfig>
          rowKey="id"
          loading={loading}
          dataSource={models}
          pagination={false}
          columns={[
            {
              title: '配置名称',
              dataIndex: 'name',
              render: (v, r) => (
                <Space>
                  <ApiOutlined style={{ color: '#4f46e5' }} />
                  <div>
                    <div style={{ fontWeight: 500 }}>
                      {v}{' '}
                      {r.is_default && (
                        <Tag color="green" style={{ borderRadius: 20, fontSize: 11 }}>
                          默认
                        </Tag>
                      )}
                    </div>
                    <div style={{ fontSize: 12, color: '#9095a8' }}>{r.remark}</div>
                  </div>
                </Space>
              ),
            },
            {
              title: '供应商',
              dataIndex: 'provider',
              width: 130,
              render: (v) => <Tag style={{ borderRadius: 20 }}>{PROVIDERS.find((p) => p.value === v)?.label ?? v}</Tag>,
            },
            {
              title: '模型 / Endpoint',
              width: 280,
              render: (_, r) => (
                <div style={{ fontSize: 12.5 }}>
                  <div style={{ color: '#1e2030', fontWeight: 500 }}>{r.model_name}</div>
                  <div style={{ color: '#a0a4b8', fontSize: 11.5 }}>{r.base_url}</div>
                </div>
              ),
            },
            {
              title: '参数',
              width: 170,
              render: (_, r) => (
                <div style={{ fontSize: 12, color: '#5b6079' }}>
                  <div>temperature {r.temperature}</div>
                  <div>max_tokens {r.max_tokens}</div>
                </div>
              ),
            },
            {
              title: '语言路由',
              dataIndex: 'route_lang',
              width: 110,
              render: (v: string) => (
                <Tag color={ROUTE_META[v]?.color} style={{ borderRadius: 20 }}>
                  {ROUTE_META[v]?.text ?? v}
                </Tag>
              ),
            },
            {
              title: '状态',
              width: 110,
              render: (_, r) => (
                <Space direction="vertical" size={2}>
                  <Tag color={r.enabled ? 'green' : 'default'} style={{ borderRadius: 20 }}>
                    {r.enabled ? '已启用' : '已停用'}
                  </Tag>
                  {r.last_test_status && (
                    <span style={{ fontSize: 11.5, color: r.last_test_status === 'success' ? '#10b981' : '#ef4444' }}>
                      {r.last_test_status === 'success' ? '✅ 上次测试通过' : '❌ 上次测试失败'}
                    </span>
                  )}
                </Space>
              ),
            },
            {
              title: '操作',
              width: 220,
              render: (_, r) => (
                <Space>
                  <Button size="small" loading={testing === r.id} onClick={() => doTest(r)}>
                    连通性测试
                  </Button>
                  <Tooltip title="设为该语言线路的默认模型">
                    <Button
                      size="small"
                      icon={<ThunderboltOutlined />}
                      disabled={r.is_default}
                      onClick={async () => {
                        await setDefaultModel(r.id)
                        message.success('已设为默认')
                        load()
                      }}
                    />
                  </Tooltip>
                  <Button size="small" type="link" onClick={() => openModal(r)}>
                    编辑
                  </Button>
                  <Popconfirm
                    title="确认删除该模型配置？"
                    onConfirm={async () => {
                      await deleteModel(r.id)
                      message.success('已删除')
                      load()
                    }}
                  >
                    <Button size="small" type="link" danger>
                      删除
                    </Button>
                  </Popconfirm>
                </Space>
              ),
            },
          ]}
        />
      </Card>

      <Modal
        open={open}
        title={editing ? `编辑模型配置 · ${editing.name}` : '新增模型配置'}
        width={760}
        onCancel={() => setOpen(false)}
        onOk={submit}
        okText="保存"
        destroyOnClose
      >
        <Form form={form} layout="vertical" style={{ marginTop: 12 }}>
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item name="name" label="配置名称" rules={[{ required: true }]}>
                <Input placeholder="如：GPT-4o-mini · 海外英文线" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="provider" label="供应商" rules={[{ required: true }]}>
                <Select
                  options={PROVIDERS.map((p) => ({ value: p.value, label: p.label }))}
                  onChange={(v) => {
                    const p = PROVIDERS.find((x) => x.value === v)
                    if (p?.base) form.setFieldValue('base_url', p.base)
                  }}
                />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="base_url" label="Base URL（OpenAI 兼容）" rules={[{ required: true }]}>
            <Input placeholder="https://api.openai.com/v1" />
          </Form.Item>
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item name="api_key" label="API Key">
                <Input.Password placeholder="sk-..." />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="model_name" label="模型名" rules={[{ required: true }]}>
                <Input placeholder="gpt-4o-mini / deepseek-chat / qwen-max" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={12}>
            <Col span={8}>
              <Form.Item name="temperature" label="Temperature">
                <Slider min={0} max={1} step={0.1} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="top_p" label="Top P">
                <Slider min={0} max={1} step={0.05} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="max_tokens" label="Max Tokens">
                <InputNumber min={64} max={32000} step={64} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item name="route_lang" label="语言路由">
                <Select
                  options={[
                    { value: 'all', label: '全语言通用 / 兜底' },
                    { value: 'zh', label: '仅中文线路' },
                    { value: 'en', label: '仅英文线路' },
                  ]}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="enabled" label="启用状态">
                <Select
                  options={[
                    { value: true, label: '启用' },
                    { value: false, label: '停用' },
                  ]}
                />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="remark" label="备注">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Alert
            type="warning"
            showIcon
            message="演示环境说明：本后台负责保存模型接入配置；当前测试台仍走规则引擎，不发起真实计费调用。"
          />
        </Form>
      </Modal>
    </>
  )
}
