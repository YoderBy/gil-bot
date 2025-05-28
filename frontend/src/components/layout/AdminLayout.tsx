import React, { useState } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { Layout, Menu } from 'antd';
import {
    DashboardOutlined,
    FileTextOutlined,
    MessageOutlined,
    SettingOutlined,
    ExperimentOutlined,
} from '@ant-design/icons';

const { Header, Content, Footer, Sider } = Layout;

const menuItems = [
    { key: '/admin', icon: <DashboardOutlined />, label: <Link to="/admin">Dashboard</Link> },
    { key: '/admin/syllabus', icon: <FileTextOutlined />, label: <Link to="/admin/syllabus">Syllabus</Link> },
    { key: '/admin/llm-test', icon: <ExperimentOutlined />, label: <Link to="/admin/llm-test">Test LLM</Link> },
    { key: '/admin/logs', icon: <MessageOutlined />, label: <Link to="/admin/logs">Logs</Link> },
    { key: '/admin/settings', icon: <SettingOutlined />, label: <Link to="/admin/settings">Settings</Link> },
];

const AdminLayout: React.FC = () => {
    const [collapsed, setCollapsed] = useState(false);
    const location = useLocation();

    // Determine the selected key based on the current path
    const selectedKeys = [location.pathname];

    return (
        <Layout style={{ minHeight: '100vh' }}>
            <Sider collapsible collapsed={collapsed} onCollapse={(value) => setCollapsed(value)}>
                <div style={{ height: 32, margin: 16, background: 'rgba(255, 255, 255, 0.2)' }} /> {/* Placeholder for logo */}
                <Menu theme="dark" selectedKeys={selectedKeys} mode="inline" items={menuItems} />
            </Sider>
            <Layout className="site-layout">
                <Header style={{ padding: 0, background: '#fff' }}> {/* Customize Header if needed */}
                    {/* Add Header content here if needed, like user profile, logout */}
                </Header>
                <Content style={{ margin: '16px' }}>
                    <div style={{ padding: 24, minHeight: 360, background: '#fff' }}>
                        <Outlet /> {/* Nested routes will render here */}
                    </div>
                </Content>
                <Footer style={{ textAlign: 'center' }}>Syllabus Bot Admin ©{new Date().getFullYear()}</Footer>
            </Layout>
        </Layout>
    );
};

export default AdminLayout; 