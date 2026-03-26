import React from 'react';
import { Card, Form, Select, Input, Button, message, Divider, Typography, Space, Tag } from 'antd';

const { Title, Text, Paragraph } = Typography;

const Settings: React.FC = () => {
  const [form] = Form.useForm();

  const handleSave = () => {
    const values = form.getFieldsValue();
    localStorage.setItem('w4agent_settings', JSON.stringify(values));
    message.success('设置已保存');
  };

  const savedSettings = React.useMemo(() => {
    try {
      return JSON.parse(localStorage.getItem('w4agent_settings') || '{}');
    } catch {
      return {};
    }
  }, []);

  return (
    <div style={{ maxWidth: 700, margin: '0 auto' }}>
      <Card title="系统设置">
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            llm_provider: 'openai',
            openai_model: 'gpt-4o',
            ...savedSettings,
          }}
        >
          <Title level={5}>LLM 配置</Title>
          <Form.Item name="llm_provider" label="LLM提供商">
            <Select>
              <Select.Option value="openai">OpenAI (GPT-4o)</Select.Option>
              <Select.Option value="claude">Anthropic (Claude)</Select.Option>
              <Select.Option value="local">本地模型 (Ollama)</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item name="openai_api_key" label="OpenAI API Key">
            <Input.Password placeholder="sk-..." />
          </Form.Item>

          <Form.Item name="anthropic_api_key" label="Anthropic API Key">
            <Input.Password placeholder="sk-ant-..." />
          </Form.Item>

          <Divider />

          <Title level={5}>Jira 集成</Title>
          <Form.Item name="jira_base_url" label="Jira URL">
            <Input placeholder="https://your-org.atlassian.net" />
          </Form.Item>
          <Form.Item name="jira_api_token" label="Jira API Token">
            <Input.Password placeholder="API Token" />
          </Form.Item>
          <Form.Item name="jira_project_key" label="Jira 项目Key">
            <Input placeholder="例如: A11Y" />
          </Form.Item>

          <Divider />

          <Form.Item>
            <Button type="primary" onClick={handleSave}>
              保存设置
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Card title="关于系统" style={{ marginTop: 16 }}>
        <Paragraph>
          <Text strong>W4Agent</Text> - 基于智能体技术的Web无障碍检测系统
        </Paragraph>
        <Space>
          <Tag color="blue">WCAG 2.1</Tag>
          <Tag color="blue">GB/T 37668</Tag>
          <Tag color="green">AI驱动</Tag>
          <Tag color="purple">多Agent协作</Tag>
        </Space>
      </Card>
    </div>
  );
};

export default Settings;
