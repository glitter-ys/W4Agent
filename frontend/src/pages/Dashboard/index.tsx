import React, { useEffect } from 'react';
import { Card, Row, Col, Statistic, Table, Tag, Button, Space } from 'antd';
import {
  ScanOutlined,
  BugOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  PlusOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useTaskStore } from '../../stores/useTaskStore';
import { useProjectStore } from '../../stores/useProjectStore';
import type { Task } from '../../types/task';
import dayjs from 'dayjs';

const statusColors: Record<string, string> = {
  pending: 'default',
  running: 'processing',
  completed: 'success',
  failed: 'error',
  cancelled: 'warning',
};

const statusLabels: Record<string, string> = {
  pending: '待执行',
  running: '检测中',
  completed: '已完成',
  failed: '失败',
  cancelled: '已取消',
};

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { tasks, total, fetchTasks, loading } = useTaskStore();
  const { fetchProjects } = useProjectStore();

  useEffect(() => {
    fetchTasks();
    fetchProjects();
  }, [fetchTasks, fetchProjects]);

  const completedTasks = tasks.filter((t) => t.status === 'completed');
  const totalIssues = tasks.reduce((sum, t) => sum + t.issues_found, 0);
  const totalPages = tasks.reduce((sum, t) => sum + t.pages_tested, 0);

  const columns = [
    {
      title: '任务名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: Task) => (
        <a onClick={() => navigate(`/tasks/${record.id}`)}>{name}</a>
      ),
    },
    {
      title: '目标URL',
      dataIndex: 'target_url',
      key: 'target_url',
      ellipsis: true,
      width: 250,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={statusColors[status]}>{statusLabels[status] || status}</Tag>
      ),
    },
    {
      title: '页面',
      dataIndex: 'pages_tested',
      key: 'pages_tested',
    },
    {
      title: '问题',
      dataIndex: 'issues_found',
      key: 'issues_found',
      render: (count: number) => (
        <span style={{ color: count > 0 ? '#f5222d' : '#52c41a', fontWeight: 'bold' }}>
          {count}
        </span>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: unknown, record: Task) => (
        <Space>
          <Button type="link" size="small" onClick={() => navigate(`/tasks/${record.id}`)}>
            查看
          </Button>
          {record.status === 'completed' && (
            <Button type="link" size="small" onClick={() => navigate(`/reports/${record.id}`)}>
              报告
            </Button>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总检测任务"
              value={total}
              prefix={<ScanOutlined />}
              valueStyle={{ color: '#1677ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="已完成任务"
              value={completedTasks.length}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="发现问题"
              value={totalIssues}
              prefix={<BugOutlined />}
              valueStyle={{ color: '#f5222d' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="检测页面"
              value={totalPages}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      <Card
        title="最近检测任务"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/tasks/create')}>
            新建检测
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={tasks}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10, total }}
        />
      </Card>
    </div>
  );
};

export default Dashboard;
