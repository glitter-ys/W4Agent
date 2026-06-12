import React from 'react';
import { Card, Form, Select, Input, Button, message, Divider, Typography, Space, Tag } from 'antd';

const { Title, Text, Paragraph } = Typography;

const providerModelMap: Record<string, string> = {
  openai: 'gpt-4o',
  claude: 'claude-sonnet-4-20250514',
  local: 'llama3',
  custom: '',
};

const Settings: React.FC = () => {
  const [form] = Form.useForm();

  const handleSave = () => {
    const values = form.getFieldsValue();
    localStorage.setItem('w4agent_settings', JSON.stringify(values));
    message.success('设置已保存');
  };

  const savedSettings = React.useMemo(() => {
    try {
      const settings = JSON.parse(localStorage.getItem('w4agent_settings') || '{}');

      return {
        ...settings,
        model_name:
          settings.model_name ||
          settings.openai_model ||
          settings.anthropic_model ||
          settings.local_llm_model,
        api_key: settings.api_key || settings.openai_api_key || settings.anthropic_api_key,
      };
    } catch {
      return {};
    }
  }, []);

  const selectedProvider = Form.useWatch('llm_provider', form);

  const handleProviderChange = (provider: string) => {
    const currentModelName = form.getFieldValue('model_name');

    if (!currentModelName || Object.values(providerModelMap).includes(currentModelName)) {
      form.setFieldValue('model_name', providerModelMap[provider]);
    }
  };

  return (
    <div style={{ maxWidth: 700, margin: '0 auto' }}>
      <Card title="系统设置">
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            llm_provider: 'openai',
            model_name: 'gpt-4o',
            api_key: '',
            ...savedSettings,
          }}
        >
          <Title level={5}>模型配置</Title>
          <Form.Item name="llm_provider" label="模型提供商" rules={[{ required: true, message: '请选择模型提供商' }]}>
            <Select onChange={handleProviderChange}>
              <Select.Option value="openai">OpenAI</Select.Option>
              <Select.Option value="claude">Anthropic Claude</Select.Option>
              <Select.Option value="local">本地模型 / Ollama</Select.Option>
              <Select.Option value="custom">自定义 / OpenAI 兼容</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item name="model_name" label="模型名" rules={[{ required: true, message: '请输入模型名' }]}>
            <Input placeholder="例如：gpt-4o、claude-sonnet-4-20250514、qwen-plus" />
          </Form.Item>

          <Form.Item name="api_key" label="API Key" tooltip="仅保存在当前浏览器 localStorage 中">
            <Input.Password
              placeholder={selectedProvider === 'claude' ? 'sk-ant-...' : 'sk-...'}
              autoComplete="off"
            />
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
