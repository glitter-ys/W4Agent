import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  Card,
  Row,
  Col,
  Typography,
  Statistic,
  Progress,
  Tag,
  Table,
  Button,
  Space,
  Spin,
  Divider,
  message,
  Empty,
} from 'antd';
import {
  DownloadOutlined,
  FilePdfOutlined,
  FileExcelOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined,
  PictureOutlined,
} from '@ant-design/icons';
import { getReportByTask, exportReport } from '../../api/reports';
import { getTaskIssues, getTaskPages } from '../../api/tasks';
import { downloadTaskScreenshots } from '../../api/screenshots';
import type { Report } from '../../types/report';
import type { Issue, PageInfo } from '../../types/a11y';
import AnnotatedScreenshot from '../../components/AnnotatedScreenshot';

const { Title, Paragraph, Text } = Typography;

const REPORT_ISSUES_PAGE_SIZE = 20;

const ReportView: React.FC = () => {
  const { taskId } = useParams<{ taskId: string }>();
  const [report, setReport] = useState<Report | null>(null);
  const [issues, setIssues] = useState<Issue[]>([]);
  const [issuesTotal, setIssuesTotal] = useState(0);
  const [issuesPage, setIssuesPage] = useState(1);
  const [pages, setPages] = useState<PageInfo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (taskId) {
      loadData(taskId);
    }
  }, [taskId]);

  const loadData = async (id: string) => {
    try {
      setLoading(true);
      const [reportData, issueData, pageData] = await Promise.all([
        getReportByTask(id),
        getTaskIssues(id, { skip: 0, limit: REPORT_ISSUES_PAGE_SIZE }),
        getTaskPages(id, { limit: 200 }),
      ]);
      setReport(reportData);
      setIssues(issueData.items);
      setIssuesTotal(issueData.total);
      setPages(pageData.items);
    } catch {
      message.error('加载报告失败');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format: 'html' | 'pdf' | 'json') => {
    try {
      const blob = await exportReport(taskId!, format);
      const url = window.URL.createObjectURL(new Blob([blob]));
      const link = document.createElement('a');
      link.href = url;
      link.download = `report_${taskId}.${format}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      message.success(`报告已导出为 ${format.toUpperCase()} 格式`);
    } catch {
      message.error('导出失败');
    }
  };

  if (loading) {
    return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  }

  if (!report) {
    return <Card><Text type="secondary">报告暂未生成</Text></Card>;
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return '#52c41a';
    if (score >= 60) return '#faad14';
    return '#f5222d';
  };

  const getScoreStatus = (score: number) => {
    if (score >= 80) return 'success' as const;
    if (score >= 60) return 'normal' as const;
    return 'exception' as const;
  };

  return (
    <div>
      {/* Header */}
      <Card style={{ marginBottom: 16 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Title level={3} style={{ margin: 0 }}>
              无障碍检测报告
            </Title>
            <Text type="secondary">基于 WCAG 2.1 / GB/T 37668 标准</Text>
          </Col>
          <Col>
            <Space>
              <Button icon={<DownloadOutlined />} onClick={() => handleExport('html')}>
                导出HTML
              </Button>
              <Button icon={<FilePdfOutlined />} onClick={() => handleExport('pdf')}>
                导出PDF
              </Button>
              <Button icon={<FileExcelOutlined />} onClick={() => handleExport('json')}>
                导出JSON
              </Button>
              <Button icon={<PictureOutlined />} onClick={async () => {
                try {
                  await downloadTaskScreenshots(taskId!);
                  message.success('截图打包下载成功');
                } catch {
                  message.error('截图下载失败');
                }
              }}>
                下载截图
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Score Overview */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <Progress
                type="circle"
                percent={report.overall_score}
                format={(v) => `${v}分`}
                size={120}
                strokeColor={getScoreColor(report.overall_score)}
                status={getScoreStatus(report.overall_score)}
              />
              <div style={{ marginTop: 12 }}>
                <Text strong>综合评分</Text>
              </div>
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="检测页面" value={report.total_pages} />
            <Divider style={{ margin: '12px 0' }} />
            <Statistic title="总发现问题" value={report.total_issues} valueStyle={{ color: report.total_issues > 0 ? '#f5222d' : '#52c41a' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="严重问题"
              value={report.critical_issues}
              valueStyle={{ color: '#f5222d' }}
              prefix={<CloseCircleOutlined />}
            />
            <Divider style={{ margin: '12px 0' }} />
            <Statistic
              title="重要问题"
              value={report.major_issues}
              valueStyle={{ color: '#fa8c16' }}
              prefix={<ExclamationCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="WCAG A 合规" value={`${report.level_a_score}%`} />
            <Divider style={{ margin: '12px 0' }} />
            <Statistic title="WCAG AA 合规" value={`${report.level_aa_score}%`} />
          </Card>
        </Col>
      </Row>

      {/* Summary */}
      {report.summary && (
        <Card title="检测摘要" style={{ marginBottom: 16 }}>
          <Paragraph>{report.summary}</Paragraph>
        </Card>
      )}

      {/* Recommendations */}
      {report.recommendations && (
        <Card title="改进建议" style={{ marginBottom: 16 }}>
          <Paragraph>{report.recommendations}</Paragraph>
        </Card>
      )}

      {/* Page Screenshots & Annotations */}
      {pages.length > 0 && (
        <Card title="页面截图与标注" style={{ marginBottom: 16 }}>
          {pages.filter(p => p.screenshot_path).length > 0 ? (
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              {pages
                .filter(p => p.screenshot_path)
                .map(page => (
                  <Card key={page.id} type="inner" size="small">
                    <AnnotatedScreenshot
                      page={page}
                      issues={issues}
                    />
                  </Card>
                ))}
            </Space>
          ) : (
            <Empty description="暂无页面截图" />
          )}
        </Card>
      )}

      {/* Issues Table */}
      <Card title={`问题详情 (${issuesTotal})`}>
        <Table
          dataSource={issues}
          rowKey="id"
          scroll={{ x: 1400 }}
          pagination={{
            current: issuesPage,
            pageSize: REPORT_ISSUES_PAGE_SIZE,
            total: issuesTotal,
            showTotal: (total) => `共 ${total} 条`,
            showSizeChanger: false,
          }}
          onChange={async (pagination, filters) => {
            const page = pagination.current || 1;
            const severityFilter = filters.severity?.[0] as string | undefined;
            setIssuesPage(page);
            const data = await getTaskIssues(taskId!, {
              skip: (page - 1) * REPORT_ISSUES_PAGE_SIZE,
              limit: REPORT_ISSUES_PAGE_SIZE,
              ...(severityFilter ? { severity: severityFilter } : {}),
            });
            setIssues(data.items);
            setIssuesTotal(data.total);
          }}
          columns={[
            {
              title: '严重程度',
              dataIndex: 'severity',
              width: 100,
              filters: [
                { text: '严重', value: 'critical' },
                { text: '重要', value: 'major' },
                { text: '一般', value: 'minor' },
                { text: '提示', value: 'info' },
              ],
              render: (v: string) => {
                const colors: Record<string, string> = { critical: 'red', major: 'orange', minor: 'gold', info: 'blue' };
                const labels: Record<string, string> = { critical: '严重', major: '重要', minor: '一般', info: '提示' };
                return <Tag color={colors[v]}>{labels[v]}</Tag>;
              },
            },
            {
              title: 'WCAG准则',
              dataIndex: 'wcag_criterion',
              width: 100,
            },
            {
              title: '级别',
              dataIndex: 'wcag_level',
              width: 70,
            },
            {
              title: '问题',
              dataIndex: 'title',
              width: 200,
              ellipsis: true,
            },
            {
              title: '描述',
              dataIndex: 'description',
              ellipsis: true,
              width: 300,
            },
            {
              title: '页面网址',
              dataIndex: 'page_url',
              ellipsis: true,
              width: 200,
              render: (v: string | null) => v ? <a href={v} target="_blank" rel="noopener noreferrer">{v}</a> : '-',
            },
            {
              title: '建议',
              dataIndex: 'recommendation',
              ellipsis: true,
              width: 300,
              render: (v: string | null) => v || '-',
            },
            {
              title: '来源',
              dataIndex: 'detected_by',
              width: 100,
              render: (v: string) => (
                <Tag color={v === 'vision_ai' ? 'geekblue' : v === 'ai' ? 'purple' : 'blue'}>
                  {v === 'vision_ai' ? '视觉AI' : v === 'ai' ? 'AI' : '规则'}
                </Tag>
              ),
            },
          ]}
        />
      </Card>
    </div>
  );
};

export default ReportView;
