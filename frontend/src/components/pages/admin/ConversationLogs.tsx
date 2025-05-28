import React from 'react';
import {
    Typography,
    Table,
    Tag,
    Space
} from 'antd';
import type { ColumnsType } from 'antd/es/table';

const { Title } = Typography;

// Mock data structure for Conversation Logs table
interface LogDataType {
    key: React.Key;
    timestamp: string;
    userId: string;
    platform: 'WhatsApp' | 'Telegram' | 'Web';
    query: string;
    responseSnippet: string;
}

const ConversationLogs: React.FC = () => {

    // Mock data - replace with actual data fetching later
    const data: LogDataType[] = [
        {
            key: '1',
            timestamp: '2024-12-12 10:30:00',
            userId: 'whatsapp:+1***',
            platform: 'WhatsApp',
            query: 'When is the final exam?',
            responseSnippet: 'The final exam is scheduled for...',
        },
        {
            key: '2',
            timestamp: '2024-12-12 10:35:15',
            userId: 'tg:123***',
            platform: 'Telegram',
            query: 'What is the policy on late homework?',
            responseSnippet: 'Late homework is penalized by 10%...',
        },
        {
            key: '3',
            timestamp: '2024-12-12 11:05:20',
            userId: 'web:user-abc',
            platform: 'Web',
            query: 'Office hours?',
            responseSnippet: 'Professor Smith holds office hours...',
        },
    ];

    const getPlatformTagColor = (platform: LogDataType['platform']) => {
        switch (platform) {
            case 'WhatsApp': return 'green';
            case 'Telegram': return 'blue';
            case 'Web': return 'purple';
            default: return 'default';
        }
    }

    const columns: ColumnsType<LogDataType> = [
        { title: 'Timestamp', dataIndex: 'timestamp', key: 'timestamp', width: 180 },
        { title: 'User ID', dataIndex: 'userId', key: 'userId', width: 150 },
        {
            title: 'Platform',
            dataIndex: 'platform',
            key: 'platform',
            width: 100,
            render: (platform: LogDataType['platform']) => (
                <Tag color={getPlatformTagColor(platform)}>{platform}</Tag>
            ),
        },
        { title: 'Query', dataIndex: 'query', key: 'query' },
        { title: 'Response Snippet', dataIndex: 'responseSnippet', key: 'responseSnippet' },
        // Add action to view full log later
    ];

    return (
        <>
            <Title level={2}>Conversation Logs</Title>
            <Table columns={columns} dataSource={data} scroll={{ x: 800 }} />
        </>
    );
};

export default ConversationLogs; 