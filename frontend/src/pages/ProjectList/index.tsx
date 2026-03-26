import React, { useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  message,
  Popconfirm,
} from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import { useProjectStore } from '../../stores/useProjectStore';
import type { Project } from '../../types/project';
import dayjs from 'dayjs';

const ProjectList: React.FC = () => {
  const { projects, total, loading, fetchProjects, addProject, removeProject } = useProjectStore();
  const [form] = Form.useForm();
  const [modalOpen, setModalOpen] = React.useState(false);
  const [creating, setCreating] = React.useState(false);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      setCreating(true);
      await addProject(values);
      message.success('项目创建成功');
      setModalOpen(false);
      form.resetFields();
    } catch (err: unknown) {
      // Ant Design validation errors have `errorFields`, skip showing message for those
      if (err && typeof err === 'object' && 'errorFields' in err) return;
      message.error('项目创建失败，请检查后端服务是否正常运行');
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await removeProject(id);
      message.success('项目已删除');
    } catch {
      message.error('删除失败');
    }
  };

  const columns = [
    {
      title: '项目名称',
      dataIndex: 'name',
      key: 'name',
      width: 200,
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (text: string | null) => text || '-',
    },
    {
      title: '基础URL',
      dataIndex: 'base_url',
      key: 'base_url',
      ellipsis: true,
      width: 300,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      render: (_: unknown, record: Project) => (
        <Space>
          <Popconfirm title="确定删除该项目？" onConfirm={() => handleDelete(record.id)}>
            <Button type="link" danger size="small" icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Card
        title="项目列表"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
            新建项目
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={projects}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10, total }}
        />
      </Card>

      <Modal
        title="新建项目"
        open={modalOpen}
        onOk={handleCreate}
        confirmLoading={creating}
        onCancel={() => {
          setModalOpen(false);
          form.resetFields();
        }}
        okText="创建"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="项目名称" rules={[{ required: true, message: '请输入项目名称' }]}>
            <Input placeholder="例如：公司官网无障碍检测" />
          </Form.Item>
          <Form.Item name="description" label="项目描述">
            <Input.TextArea placeholder="项目描述（可选）" rows={3} />
          </Form.Item>
          <Form.Item
            name="base_url"
            label="基础URL"
            rules={[
              { required: true, message: '请输入网站URL' },
              { type: 'url', message: '请输入有效的URL' },
            ]}
          >
            <Input placeholder="https://example.com" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ProjectList;
