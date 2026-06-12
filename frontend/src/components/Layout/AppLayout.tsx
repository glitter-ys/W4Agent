import React from 'react';
import { Layout, Menu, Typography } from 'antd';
import {
  DashboardOutlined,
  ProjectOutlined,
  ScanOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';

const { Sider, Header: AntHeader, Content } = Layout;
const { Title } = Typography;

const menuItems = [
  { key: '/', icon: <DashboardOutlined />, label: '仪表盘' },
  { key: '/projects', icon: <ProjectOutlined />, label: '项目管理' },
  { key: '/tasks/create', icon: <ScanOutlined />, label: '新建检测' },
  { key: '/settings', icon: <SettingOutlined />, label: '系统设置' },
];

interface AppLayoutProps {
  children: React.ReactNode;
}

const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        theme="dark"
        width={220}
        style={{ position: 'fixed', left: 0, top: 0, bottom: 0, zIndex: 100 }}
      >
        <div style={{ padding: '20px 24px', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
          <Title level={4} style={{ color: '#fff', margin: 0 }}>
            W4Agent
          </Title>
          <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: 12, marginTop: 4 }}>
            Web无障碍检测系统
          </div>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ marginTop: 8 }}
        />
      </Sider>
      <Layout style={{ marginLeft: 220 }}>
        <AntHeader
          style={{
            background: '#fff',
            padding: '0 24px',
            borderBottom: '1px solid #f0f0f0',
            display: 'flex',
            alignItems: 'center',
            position: 'sticky',
            top: 0,
            zIndex: 99,
          }}
        >
          <Title level={5} style={{ margin: 0 }}>
            {menuItems.find((item) => item.key === location.pathname)?.label || 'W4Agent'}
          </Title>
        </AntHeader>
        <Content style={{ padding: 24, background: '#f5f5f5', minHeight: 'calc(100vh - 64px)' }}>
          {children}
        </Content>
      </Layout>
    </Layout>
  );
};

export default AppLayout;
