import React, { useEffect } from 'react';
import {
  Card,
  Form,
  Input,
  Select,
  InputNumber,
  Switch,
  Button,
  message,
  Row,
  Col,
  Divider,
  Typography,
} from 'antd';
import { useNavigate } from 'react-router-dom';
import { useTaskStore } from '../../stores/useTaskStore';
import { useProjectStore } from '../../stores/useProjectStore';

const { Title } = Typography;

const TaskCreate: React.FC = () => {
  const navigate = useNavigate();
  const { addTask, startTask } = useTaskStore();
  const { projects, fetchProjects } = useProjectStore();
  const [form] = Form.useForm();
  const [creating, setCreating] = React.useState(false);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setCreating(true);

      const config = {
        max_depth: values.max_depth,
        max_pages: values.max_pages,
        wcag_level: values.wcag_level,
        enable_ai_detection: values.enable_ai_detection,
        enable_screenshots: values.enable_screenshots,
        viewport_width: values.viewport_width,
        viewport_height: values.viewport_height,
      };

      const task = await addTask({
        project_id: values.project_id,
        name: values.name,
        target_url: values.target_url,
        config,
      });

      if (values.auto_start) {
        await startTask(task.id);
        message.success('检测任务已创建并开始执行');
      } else {
        message.success('检测任务已创建');
      }

      navigate(`/tasks/${task.id}`);
    } catch {
      message.error('创建任务失败');
    } finally {
      setCreating(false);
    }
  };

  return (
    <Card title="新建检测任务" style={{ maxWidth: 800, margin: '0 auto' }}>
      <Form
        form={form}
        layout="vertical"
        initialValues={{
          max_depth: 5,
          max_pages: 50,
          wcag_level: 'AA',
          enable_ai_detection: true,
          enable_screenshots: true,
          viewport_width: 1280,
          viewport_height: 720,
          auto_start: true,
        }}
      >
        <Title level={5}>基本信息</Title>
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="project_id"
              label="所属项目"
              rules={[{ required: true, message: '请选择项目' }]}
            >
              <Select placeholder="选择项目">
                {projects.map((p) => (
                  <Select.Option key={p.id} value={p.id}>
                    {p.name}
                  </Select.Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="name"
              label="任务名称"
              rules={[{ required: true, message: '请输入任务名称' }]}
            >
              <Input placeholder="例如：首页无障碍全量检测" />
            </Form.Item>
          </Col>
        </Row>

        <Form.Item
          name="target_url"
          label="检测目标URL"
          rules={[
            { required: true, message: '请输入目标URL' },
            { type: 'url', message: '请输入有效的URL' },
          ]}
        >
          <Input placeholder="https://example.com" size="large" />
        </Form.Item>

        <Divider />
        <Title level={5}>检测配置</Title>

        <Row gutter={16}>
          <Col span={8}>
            <Form.Item name="wcag_level" label="WCAG级别">
              <Select>
                <Select.Option value="A">WCAG A</Select.Option>
                <Select.Option value="AA">WCAG AA (推荐)</Select.Option>
                <Select.Option value="AAA">WCAG AAA</Select.Option>
              </Select>
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item name="max_depth" label="最大遍历深度">
              <InputNumber min={1} max={20} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item name="max_pages" label="最大页面数">
              <InputNumber min={1} max={500} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={8}>
            <Form.Item name="viewport_width" label="视口宽度">
              <InputNumber min={320} max={3840} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item name="viewport_height" label="视口高度">
              <InputNumber min={480} max={2160} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={8}>
            <Form.Item name="enable_ai_detection" label="AI智能检测" valuePropName="checked">
              <Switch />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item name="enable_screenshots" label="页面截图" valuePropName="checked">
              <Switch />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item name="auto_start" label="创建后立即执行" valuePropName="checked">
              <Switch />
            </Form.Item>
          </Col>
        </Row>

        <Divider />

        <Form.Item>
          <Button type="primary" size="large" onClick={handleSubmit} loading={creating} block>
            创建检测任务
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default TaskCreate;
