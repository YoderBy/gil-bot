import React from 'react';
import { Typography } from 'antd';

const { Title } = Typography;

const Dashboard: React.FC = () => {
    return (
        <>
            <Title level={2}>Admin Dashboard</Title>
            <p>Welcome to the Syllabus Bot admin panel.</p>
            {/* Add summary widgets or charts here later */}
        </>
    );
};

export default Dashboard; 