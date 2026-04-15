import React, { useEffect, useCallback, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Row,
  Col,
  Tag,
  Button,
  Space,
  Descriptions,
  Progress,
  Tabs,
  Table,
  Typography,
  Timeline,
  Spin,
  Statistic,
  Empty,
  message,
  Popconfirm,
} from 'antd';
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  FileTextOutlined,
  BugOutlined,
  PictureOutlined,
  DownloadOutlined,
  DeleteOutlined,
} from '@ant-design/icons';
import { useTaskStore } from '../../stores/useTaskStore';
import { TaskWebSocket } from '../../api/ws';
import { getTaskPages } from '../../api/tasks';
import { downloadTaskScreenshots } from '../../api/screenshots';
import type { WSMessage } from '../../types/ws';
import type { PageInfo } from '../../types/a11y';
import AnnotatedScreenshot from '../../components/AnnotatedScreenshot';
import dayjs from 'dayjs';

const { Title, Text } = Typography;

const severityColors: Record<string, string> = {
  critical: '#f5222d',
  major: '#fa8c16',
  minor: '#faad14',
  info: '#1677ff',
};

const severityLabels: Record<string, string> = {
  critical: '严重',
  major: '重要',
  minor: '一般',
  info: '提示',
};

const ISSUES_PAGE_SIZE = 20;

const TaskDetail: React.FC = () => {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();
  const [pages, setPages] = useState<PageInfo[]>([]);
  const [issuesPage, setIssuesPage] = useState(1);
  const {
    currentTask,
    taskProgress,
    issues,
    issuesTotal,
    agentLogs,
    fetchTask,
    startTask,
    stopTask,
    removeTask,
    fetchIssues,
    updateProgress,
    addAgentLog,
    clearLogs,
    loading,
  } = useTaskStore();

  const wsRef = React.useRef<TaskWebSocket | null>(null);

  const handleWSMessage = useCallback(
    (msg: WSMessage) => {
      switch (msg.type) {
        case 'task_progress':
          updateProgress({
            task_id: msg.task_id,
            status: 'running',
            pages_discovered: (msg.data.pages_discovered as number) || 0,
            pages_tested: (msg.data.pages_tested as number) || 0,
            issues_found: (msg.data.issues_found as number) || 0,
            current_url: msg.data.current_url as string,
          });
          break;
        case 'agent_reasoning':
          addAgentLog({
            agent: msg.data.agent as string,
            reasoning: msg.data.reasoning as string,
            timestamp: msg.timestamp || new Date().toISOString(),
          });
          break;
        case 'task_completed':
        case 'task_failed':
          fetchTask(taskId!);
          setIssuesPage(1);
          fetchIssues(taskId!, { skip: 0, limit: ISSUES_PAGE_SIZE });
          // Reload pages so screenshot tab picks up newly saved screenshots
          getTaskPages(taskId!, { limit: 200 }).then((data) => {
            setPages(data.items);
          }).catch(() => {});
          break;
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [taskId]
  );

  useEffect(() => {
    if (taskId) {
      fetchTask(taskId);
      fetchIssues(taskId, { skip: 0, limit: ISSUES_PAGE_SIZE });
      clearLogs();

      // Load pages for screenshot tab
      getTaskPages(taskId, { limit: 200 }).then((data) => {
        setPages(data.items);
      }).catch(() => {});

      // Connect WebSocket
      wsRef.current = new TaskWebSocket(taskId, handleWSMessage);
      wsRef.current.connect();
    }

    return () => {
      wsRef.current?.disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [taskId]);

  if (!currentTask) {
    return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  }

  const task = currentTask;
  const progress = taskProgress;

  const isRunning = task.status === 'running';
  const pagesDiscovered = progress?.pages_discovered ?? task.pages_discovered;
  const pagesTested = progress?.pages_tested ?? task.pages_tested;
  const issuesFound = progress?.issues_found ?? task.issues_found;

  const handleStart = async () => {
    try {
      await startTask(task.id);
      message.success('检测已启动');
    } catch {
      message.error('启动失败');
    }
  };

  const handleStop = async () => {
    try {
      await stopTask(task.id);
      message.success('检测已停止');
    } catch {
      message.error('停止失败');
    }
  };

  const handleDelete = async () => {
    try {
      await removeTask(task.id);
      message.success('任务已删除');
      navigate('/');
    } catch {
      message.error('删除失败');
    }
  };

  const issueColumns = [
    {
      title: '严重程度',
      dataIndex: 'severity',
      key: 'severity',
      width: 100,
      render: (sev: string) => (
        <Tag color={severityColors[sev]}>{severityLabels[sev] || sev}</Tag>
      ),
    },
    {
      title: 'WCAG准则',
      dataIndex: 'wcag_criterion',
      key: 'wcag_criterion',
      width: 100,
    },
    {
      title: '问题标题',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      width: 300,
    },
    {
      title: '检测来源',
      dataIndex: 'detected_by',
      key: 'detected_by',
      width: 100,
      render: (v: string) => (
        <Tag color={v === 'vision_ai' ? 'geekblue' : v === 'ai' ? 'purple' : 'blue'}>
          {v === 'vision_ai' ? '视觉AI' : v === 'ai' ? 'AI检测' : '规则检测'}
        </Tag>
      ),
    },
  ];

  return (
    <div>
      {/* Task header */}
      <Card style={{ marginBottom: 16 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Space>
              <Title level={4} style={{ margin: 0 }}>
                {task.name}
              </Title>
              <Tag
                color={
                  task.status === 'completed'
                    ? 'success'
                    : task.status === 'running'
                    ? 'processing'
                    : task.status === 'failed'
                    ? 'error'
                    : 'default'
                }
              >
                {task.status === 'running' ? '检测中' : task.status === 'completed' ? '已完成' : task.status === 'failed' ? '失败' : task.status}
              </Tag>
            </Space>
            <div style={{ marginTop: 8 }}>
              <Text type="secondary">{task.target_url}</Text>
            </div>
          </Col>
          <Col>
            <Space>
              {task.status === 'pending' && (
                <Button type="primary" icon={<PlayCircleOutlined />} onClick={handleStart}>
                  开始检测
                </Button>
              )}
              {isRunning && (
                <Button danger icon={<PauseCircleOutlined />} onClick={handleStop}>
                  停止检测
                </Button>
              )}
              {task.status === 'completed' && (
                <Button
                  type="primary"
                  icon={<FileTextOutlined />}
                  onClick={() => navigate(`/reports/${task.id}`)}
                >
                  查看报告
                </Button>
              )}
              {!isRunning && (
                <Popconfirm
                  title="确定要删除此任务吗？"
                  description="删除后将无法恢复，相关的检测数据和报告也会一并删除。"
                  onConfirm={handleDelete}
                  okText="删除"
                  cancelText="取消"
                  okButtonProps={{ danger: true }}
                >
                  <Button danger icon={<DeleteOutlined />}>
                    删除任务
                  </Button>
                </Popconfirm>
              )}
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Progress */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={8}>
          <Card>
            <Statistic title="发现页面" value={pagesDiscovered} />
            {isRunning && <Progress percent={Math.min(100, (pagesDiscovered / (task.config?.max_pages || 50)) * 100)} showInfo={false} status="active" />}
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic title="已检测页面" value={pagesTested} />
            {pagesDiscovered > 0 && (
              <Progress percent={Math.round((pagesTested / pagesDiscovered) * 100)} showInfo={false} />
            )}
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic title="发现问题" value={issuesFound} valueStyle={{ color: issuesFound > 0 ? '#f5222d' : '#52c41a' }} prefix={<BugOutlined />} />
          </Card>
        </Col>
      </Row>

      {/* Tabs: Issues / Agent Logs */}
      <Card>
        <Tabs
          items={[
            {
              key: 'issues',
              label: `无障碍问题 (${issuesTotal})`,
              children: (
                <Table
                  columns={issueColumns}
                  dataSource={issues}
                  rowKey="id"
                  pagination={{
                    current: issuesPage,
                    pageSize: ISSUES_PAGE_SIZE,
                    total: issuesTotal,
                    showTotal: (total) => `共 ${total} 条`,
                    showSizeChanger: false,
                    onChange: (page) => {
                      setIssuesPage(page);
                      fetchIssues(taskId!, {
                        skip: (page - 1) * ISSUES_PAGE_SIZE,
                        limit: ISSUES_PAGE_SIZE,
                      });
                    },
                  }}
                  size="small"
                />
              ),
            },
            {
              key: 'logs',
              label: `Agent推理日志 (${agentLogs.length})`,
              children: (
                <div style={{ maxHeight: 500, overflow: 'auto', padding: '0 16px' }}>
                  <Timeline
                    items={agentLogs.map((log) => ({
                      color: 'blue',
                      children: (
                        <div>
                          <Tag>{log.agent}</Tag>
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            {dayjs(log.timestamp).format('HH:mm:ss')}
                          </Text>
                          <div style={{ marginTop: 4 }}>{log.reasoning}</div>
                        </div>
                      ),
                    }))}
                  />
                  {agentLogs.length === 0 && (
                    <Text type="secondary">暂无日志，启动检测后将实时显示Agent推理过程</Text>
                  )}
                </div>
              ),
            },
            {
              key: 'screenshots',
              label: (
                <span>
                  <PictureOutlined style={{ marginRight: 4 }} />
                  页面截图
                </span>
              ),
              children: (() => {
                const screenshotPages = pages.filter(p => p.screenshot_path);
                const handleDownloadAll = async () => {
                  try {
                    await downloadTaskScreenshots(taskId!);
                    message.success('截图打包下载成功');
                  } catch {
                    message.error('截图下载失败');
                  }
                };
                return (
                  <div>
                    {screenshotPages.length > 0 ? (
                      <>
                        <div style={{ marginBottom: 16 }}>
                          <Button icon={<DownloadOutlined />} onClick={handleDownloadAll}>
                            下载全部截图
                          </Button>
                        </div>
                        <Space direction="vertical" size="large" style={{ width: '100%' }}>
                          {screenshotPages.map(page => (
                            <Card key={page.id} type="inner" size="small">
                              <AnnotatedScreenshot
                                page={page}
                                issues={issues}
                              />
                            </Card>
                          ))}
                        </Space>
                      </>
                    ) : (
                      <Empty description="暂无页面截图" />
                    )}
                  </div>
                );
              })(),
            },
            {
              key: 'config',
              label: '任务配置',
              children: (
                <Descriptions bordered column={2}>
                  <Descriptions.Item label="WCAG级别">{task.config?.wcag_level || 'AA'}</Descriptions.Item>
                  <Descriptions.Item label="最大深度">{task.config?.max_depth || 5}</Descriptions.Item>
                  <Descriptions.Item label="最大页面">{task.config?.max_pages || 50}</Descriptions.Item>
                  <Descriptions.Item label="AI检测">{task.config?.enable_ai_detection ? '启用' : '禁用'}</Descriptions.Item>
                  <Descriptions.Item label="视觉检测">{task.config?.enable_vision_detection ? '启用' : '禁用'}</Descriptions.Item>
                  <Descriptions.Item label="视口">{task.config?.viewport_width || 1280} x {task.config?.viewport_height || 720}</Descriptions.Item>
                  <Descriptions.Item label="截图">{task.config?.enable_screenshots ? '启用' : '禁用'}</Descriptions.Item>
                </Descriptions>
              ),
            },
          ]}
        />
      </Card>
    </div>
  );
};

export default TaskDetail;
