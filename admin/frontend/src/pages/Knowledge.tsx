import {
  ExperimentOutlined,
  FolderAddOutlined,
  PlusOutlined,
  ReloadOutlined,
  SearchOutlined,
} from '@ant-design/icons'
import {
  Alert,
  App,
  Badge,
  Button,
  Card,
  Col,
  Divider,
  Drawer,
  Empty,
  Form,
  Input,
  Modal,
  Popconfirm,
  Row,
  Select,
  Space,
  Table,
  Tabs,
  Tag,
  Tooltip,
  Typography,
} from 'antd'
import { useCallback, useEffect, useState } from 'react'
import {
  createCategory,
  createItem,
  deleteCategory,
  deleteItem,
  listCategories,
  listItems,
  searchTest,
  updateCategory,
  updateItem,
} from '../api'
import type { KbCategory, KbItem, SearchTestResult } from '../types'

const STATUS_META: Record<string, { text: string; color: string }> = {
  published: { text: '已发布', color: 'green' },
  draft: { text: '草稿', color: 'gold' },
  disabled: { text: '已停用', color: 'default' },
}

export default function Knowledge() {
  const { message } = App.useApp()
  const [categories, setCategories] = useState<KbCategory[]>([])
  const [activeCat, setActiveCat] = useState<number | undefined>(undefined)
  const [items, setItems] = useState<KbItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [keyword, setKeyword] = useState('')
  const [status, setStatus] = useState<string>('')
  const [loading, setLoading] = useState(false)

  const [itemModal, setItemModal] = useState(false)
  const [editingItem, setEditingItem] = useState<KbItem | null>(null)
  const [itemForm] = Form.useForm()

  const [catModal, setCatModal] = useState(false)
  const [editingCat, setEditingCat] = useState<KbCategory | null>(null)
  const [catForm] = Form.useForm()

  const [testOpen, setTestOpen] = useState(false)
  const [testQuery, setTestQuery] = useState('')
  const [testResult, setTestResult] = useState<SearchTestResult | null>(null)
  const [testLoading, setTestLoading] = useState(false)

  const loadCategories = useCallback(async () => {
    setCategories(await listCategories())
  }, [])

  const loadItems = useCallback(async () => {
    setLoading(true)
    try {
      const res = await listItems({
        category_id: activeCat,
        keyword,
        status,
        page,
        page_size: 10,
      })
      setItems(res.items)
      setTotal(res.total)
    } catch (e: any) {
      message.error(e.message)
    } finally {
      setLoading(false)
    }
  }, [activeCat, keyword, status, page, message])

  useEffect(() => {
    loadCategories().catch((e) => message.error(e.message))
  }, [loadCategories, message])

  useEffect(() => {
    loadItems()
  }, [loadItems])

  const openItemModal = (item?: KbItem) => {
    setEditingItem(item ?? null)
    if (item) {
      itemForm.setFieldsValue(item)
    } else {
      itemForm.resetFields()
      itemForm.setFieldsValue({
        category_id: activeCat ?? categories[0]?.id,
        status: 'published',
      })
    }
    setItemModal(true)
  }

  const submitItem = async () => {
    const values = await itemForm.validateFields()
    try {
      if (editingItem) {
        await updateItem(editingItem.id, values)
        message.success('知识库条目已更新')
      } else {
        await createItem(values)
        message.success('知识库条目已创建')
      }
      setItemModal(false)
      loadItems()
      loadCategories()
    } catch (e: any) {
      message.error(e.message)
    }
  }

  const openCatModal = (cat?: KbCategory) => {
    setEditingCat(cat ?? null)
    if (cat) catForm.setFieldsValue(cat)
    else catForm.resetFields()
    setCatModal(true)
  }

  const submitCat = async () => {
    const values = await catForm.validateFields()
    try {
      if (editingCat) await updateCategory(editingCat.id, values)
      else await createCategory(values)
      message.success('分类已保存')
      setCatModal(false)
      loadCategories()
    } catch (e: any) {
      message.error(e.message)
    }
  }

  const runTest = async () => {
    if (!testQuery.trim()) return
    setTestLoading(true)
    try {
      setTestResult(await searchTest(testQuery))
    } catch (e: any) {
      message.error(e.message)
    } finally {
      setTestLoading(false)
    }
  }

  return (
    <Row gutter={16}>
      {/* 左：分类树 */}
      <Col xs={24} lg={6}>
        <Card
          bordered={false}
          title="知识分类"
          extra={
            <Tooltip title="新建分类">
              <Button type="text" icon={<FolderAddOutlined />} onClick={() => openCatModal()} />
            </Tooltip>
          }
          styles={{ body: { padding: 10 } }}
        >
          <div
            className={`kb-cat-item ${activeCat === undefined ? 'active' : ''}`}
            onClick={() => {
              setActiveCat(undefined)
              setPage(1)
            }}
          >
            <span>📚 全部条目</span>
            <Badge count={categories.reduce((s, c) => s + c.item_count, 0)} color="#4f46e5" />
          </div>
          {categories.map((c) => (
            <div
              key={c.id}
              className={`kb-cat-item ${activeCat === c.id ? 'active' : ''}`}
              onClick={() => {
                setActiveCat(c.id)
                setPage(1)
              }}
            >
              <span>
                {c.icon} {c.name}
              </span>
              <Space size={4}>
                <Badge count={c.item_count} color="#9095a8" />
                <Button
                  type="text"
                  size="small"
                  icon={<ReloadOutlined />}
                  onClick={(e) => {
                    e.stopPropagation()
                    openCatModal(c)
                  }}
                />
              </Space>
            </div>
          ))}
        </Card>
      </Col>

      {/* 右：条目表 */}
      <Col xs={24} lg={18}>
        <Card
          bordered={false}
          title="知识库条目"
          extra={
            <Space>
              <Button icon={<ExperimentOutlined />} onClick={() => setTestOpen(true)}>
                检索测试
              </Button>
              <Button type="primary" icon={<PlusOutlined />} onClick={() => openItemModal()}>
                新增条目
              </Button>
            </Space>
          }
        >
          <Space style={{ marginBottom: 14 }} wrap>
            <Input
              allowClear
              prefix={<SearchOutlined />}
              placeholder="搜索标题 / 内容 / 关键词"
              style={{ width: 280 }}
              value={keyword}
              onChange={(e) => {
                setKeyword(e.target.value)
                setPage(1)
              }}
            />
            <Select
              allowClear
              placeholder="状态"
              style={{ width: 130 }}
              value={status || undefined}
              onChange={(v) => {
                setStatus(v ?? '')
                setPage(1)
              }}
              options={[
                { value: 'published', label: '已发布' },
                { value: 'draft', label: '草稿' },
                { value: 'disabled', label: '已停用' },
              ]}
            />
            <Button icon={<ReloadOutlined />} onClick={loadItems}>
              刷新
            </Button>
          </Space>

          <Table<KbItem>
            rowKey="id"
            loading={loading}
            dataSource={items}
            size="middle"
            pagination={{
              current: page,
              pageSize: 10,
              total,
              onChange: setPage,
              showTotal: (t) => `共 ${t} 条`,
            }}
            columns={[
              {
                title: '标题',
                dataIndex: 'title_zh',
                render: (_, r) => (
                  <div>
                    <div style={{ fontWeight: 500, color: '#1e2030' }}>{r.title_zh}</div>
                    <div style={{ fontSize: 12, color: '#9095a8' }}>{r.title_en}</div>
                  </div>
                ),
              },
              {
                title: '分类',
                dataIndex: 'category_name',
                width: 130,
                render: (v) => <Tag style={{ borderRadius: 20 }}>{v}</Tag>,
              },
              {
                title: '关键词',
                dataIndex: 'keywords_zh',
                width: 200,
                render: (v: string) => (
                  <Space size={[4, 4]} wrap>
                    {(v || '').split(',').slice(0, 3).map((k) => (
                      <Tag key={k} style={{ fontSize: 11, borderRadius: 6 }}>
                        {k}
                      </Tag>
                    ))}
                    {(v || '').split(',').length > 3 && (
                      <Tag style={{ fontSize: 11 }}>+{v.split(',').length - 3}</Tag>
                    )}
                  </Space>
                ),
              },
              {
                title: '状态',
                dataIndex: 'status',
                width: 92,
                render: (v: string) => (
                  <Tag color={STATUS_META[v]?.color} style={{ borderRadius: 20 }}>
                    {STATUS_META[v]?.text ?? v}
                  </Tag>
                ),
              },
              {
                title: '命中',
                dataIndex: 'hit_count',
                width: 74,
                sorter: (a, b) => a.hit_count - b.hit_count,
                render: (v: number) => <span style={{ color: '#4f46e5', fontWeight: 600 }}>{v}</span>,
              },
              {
                title: '操作',
                width: 130,
                render: (_, r) => (
                  <Space>
                    <Button type="link" size="small" onClick={() => openItemModal(r)}>
                      编辑
                    </Button>
                    <Popconfirm
                      title="确认删除该条目？"
                      onConfirm={async () => {
                        await deleteItem(r.id)
                        message.success('已删除')
                        loadItems()
                        loadCategories()
                      }}
                    >
                      <Button type="link" size="small" danger>
                        删除
                      </Button>
                    </Popconfirm>
                  </Space>
                ),
              },
            ]}
          />
        </Card>
      </Col>

      {/* 条目编辑弹窗 */}
      <Modal
        open={itemModal}
        title={editingItem ? `编辑条目 · ${editingItem.title_zh}` : '新增知识库条目'}
        width={820}
        onCancel={() => setItemModal(false)}
        onOk={submitItem}
        okText="保存"
        destroyOnClose
      >
        <Form form={itemForm} layout="vertical" style={{ marginTop: 12 }}>
          <Row gutter={12}>
            <Col span={8}>
              <Form.Item name="category_id" label="所属分类" rules={[{ required: true }]}>
                <Select
                  options={categories.map((c) => ({ value: c.id, label: `${c.icon} ${c.name}` }))}
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="status" label="状态" rules={[{ required: true }]}>
                <Select
                  options={[
                    { value: 'published', label: '已发布（参与检索）' },
                    { value: 'draft', label: '草稿' },
                    { value: 'disabled', label: '已停用' },
                  ]}
                />
              </Form.Item>
            </Col>
          </Row>
          <Tabs
            items={[
              {
                key: 'zh',
                label: '🇨🇳 中文内容',
                children: (
                  <>
                    <Form.Item name="title_zh" label="标题" rules={[{ required: true, message: '请输入中文标题' }]}>
                      <Input placeholder="如：退换货基本政策" />
                    </Form.Item>
                    <Form.Item name="answer_zh" label="答案内容">
                      <Input.TextArea rows={6} placeholder="支持换行，可含 emoji 与项目符号" />
                    </Form.Item>
                    <Form.Item name="keywords_zh" label="触发关键词（逗号分隔）">
                      <Input placeholder="退,换,退款,退货" />
                    </Form.Item>
                  </>
                ),
              },
              {
                key: 'en',
                label: '🇺🇸 English Content',
                children: (
                  <>
                    <Form.Item name="title_en" label="Title">
                      <Input placeholder="e.g. Return & Refund Policy" />
                    </Form.Item>
                    <Form.Item name="answer_en" label="Answer">
                      <Input.TextArea rows={6} />
                    </Form.Item>
                    <Form.Item name="keywords_en" label="Keywords (comma separated)">
                      <Input placeholder="return,refund,exchange" />
                    </Form.Item>
                  </>
                ),
              },
            ]}
          />
        </Form>
      </Modal>

      {/* 分类编辑弹窗 */}
      <Modal
        open={catModal}
        title={editingCat ? `编辑分类 · ${editingCat.name}` : '新建分类'}
        onCancel={() => setCatModal(false)}
        onOk={submitCat}
        okText="保存"
        destroyOnClose
        footer={
          <Space>
            {editingCat && (
              <Popconfirm
                title="删除分类将同时删除其下所有条目，确认？"
                onConfirm={async () => {
                  await deleteCategory(editingCat.id)
                  message.success('分类已删除')
                  setCatModal(false)
                  setActiveCat(undefined)
                  loadCategories()
                  loadItems()
                }}
              >
                <Button danger>删除分类</Button>
              </Popconfirm>
            )}
            <Button onClick={() => setCatModal(false)}>取消</Button>
            <Button type="primary" onClick={submitCat}>
              保存
            </Button>
          </Space>
        }
      >
        <Form form={catForm} layout="vertical" style={{ marginTop: 12 }}>
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item name="name" label="分类名（中文）" rules={[{ required: true }]}>
                <Input />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="name_en" label="Category (EN)">
                <Input />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={12}>
            <Col span={8}>
              <Form.Item name="icon" label="图标 Emoji">
                <Input placeholder="📋" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="sort_order" label="排序">
                <Input type="number" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="description" label="分类说明">
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>

      {/* 检索测试 */}
      <Drawer
        open={testOpen}
        onClose={() => setTestOpen(false)}
        width={620}
        title="🔍 知识库检索测试"
        extra={<Tag color="processing">模拟 Agent 端检索</Tag>}
      >
        <Alert
          type="info"
          showIcon
          style={{ marginBottom: 14 }}
          message="输入一句用户问题，预览会命中哪些知识库条目、以及 Agent 会采用哪一条作答。"
        />
        <Space.Compact style={{ width: '100%', marginBottom: 16 }}>
          <Input
            value={testQuery}
            onChange={(e) => setTestQuery(e.target.value)}
            onPressEnter={runTest}
            placeholder="如：我想退货，尺码不合适"
          />
          <Button type="primary" loading={testLoading} onClick={runTest}>
            检索
          </Button>
        </Space.Compact>

        {testResult && (
          <>
            <Space style={{ marginBottom: 12 }}>
              <Tag color="blue">识别语言：{testResult.language === 'zh' ? '中文' : 'English'}</Tag>
              <Tag color={testResult.matched_count ? 'green' : 'red'}>
                命中 {testResult.matched_count} 条
              </Tag>
            </Space>
            {testResult.results.length === 0 ? (
              <Empty description="未命中任何条目 —— 建议在后台补充关键词" />
            ) : (
              testResult.results.map((r, i) => (
                <Card
                  key={r.item_id}
                  size="small"
                  style={{ marginBottom: 10, borderColor: i === 0 ? '#4f46e5' : undefined }}
                  title={
                    <Space>
                      {i === 0 && <Tag color="purple">最佳命中</Tag>}
                      <span>{r.title}</span>
                      <Tag>{r.category_name}</Tag>
                    </Space>
                  }
                  extra={<Tag color="blue">得分 {r.score}</Tag>}
                >
                  <Space size={[4, 4]} wrap style={{ marginBottom: 8 }}>
                    {r.hit_keywords.map((k) => (
                      <Tag key={k} color="cyan">
                        {k}
                      </Tag>
                    ))}
                  </Space>
                  <Divider style={{ margin: '8px 0' }} />
                  <Typography.Paragraph
                    style={{ whiteSpace: 'pre-wrap', marginBottom: 0, fontSize: 12.5, color: '#5b6079' }}
                    ellipsis={{ rows: 4, expandable: true, symbol: '展开' }}
                  >
                    {r.answer}
                  </Typography.Paragraph>
                </Card>
              ))
            )}
          </>
        )}
      </Drawer>
    </Row>
  )
}
