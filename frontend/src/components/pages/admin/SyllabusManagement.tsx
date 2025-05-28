import React, { useState, useEffect } from 'react';
import { Table, Button, Typography, Alert, Spin, Input, Space } from 'antd';
import { Link } from 'react-router-dom';
import axios, { AxiosError } from 'axios';
import { EyeOutlined, EditOutlined } from '@ant-design/icons';

const { Title } = Typography;
const { Search } = Input; // Correct: Search is a component of Input

interface SyllabusSummary {
    id: string;
    name?: string;
    heb_name?: string;
}

const SyllabusManagement: React.FC = () => {
    const [syllabi, setSyllabi] = useState<SyllabusSummary[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const [searchTerm, setSearchTerm] = useState<string>("");

    const fetchSyllabi = async (currentSearchTerm?: string) => {
        setLoading(true);
        setError(null);
        try {
            const params = currentSearchTerm ? { search: currentSearchTerm } : {};
            const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';
            const response = await axios.get<SyllabusSummary[]>(`${API_BASE_URL}/api/v1/syllabus/`, { params });
            setSyllabi(response.data);
        } catch (err) {
            console.error("Error fetching syllabi:", err);
            const axiosError = err as AxiosError<any>;
            if (axiosError.isAxiosError && axiosError.response) {
                setError(`Failed to load syllabi: ${axiosError.response.data.detail || axiosError.message}`);
            } else {
                setError('Failed to load syllabi. Please check the console for more details.');
            }
        }
        setLoading(false);
    };

    useEffect(() => {
        fetchSyllabi();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const handleSearch = (value: string) => {
        setSearchTerm(value);
        fetchSyllabi(value);
    };

    const columns = [
        {
            title: 'Course ID / Filename',
            dataIndex: 'id',
            key: 'id',
            sorter: (a: SyllabusSummary, b: SyllabusSummary) => a.id.localeCompare(b.id),
        },
        {
            title: 'Course Name (English)',
            dataIndex: 'name',
            key: 'name',
            sorter: (a: SyllabusSummary, b: SyllabusSummary) => (a.name || "").localeCompare(b.name || ""),
            responsive: ['md'] as any,
        },
        {
            title: 'Course Name (Hebrew)',
            dataIndex: 'heb_name',
            key: 'heb_name',
            sorter: (a: SyllabusSummary, b: SyllabusSummary) => (a.heb_name || "").localeCompare(b.heb_name || ""),
            responsive: ['md'] as any,
        },
        {
            title: 'Actions',
            key: 'actions',
            render: (_: any, record: SyllabusSummary) => (
                <Space>
                    <Link to={`/admin/syllabus/view/${record.id}`}>
                        <Button type="default" icon={<EyeOutlined />}>
                            View
                        </Button>
                    </Link>
                    <Link to={`/admin/syllabus/edit/${record.id}`}>
                        <Button type="primary" icon={<EditOutlined />}>
                            Edit
                        </Button>
                    </Link>
                </Space>
            ),
        },
    ];

    return (
        <div>
            <Title level={2}>Syllabus Management</Title>
            <Search
                placeholder="Search by ID or Name"
                onSearch={handleSearch}
                onChange={(e) => setSearchTerm(e.target.value)}
                value={searchTerm}
                style={{ marginBottom: 16, width: 400 }}
                enterButton
                allowClear
            />
            {loading && <Spin tip="Loading Syllabi..." size="large"><div style={{ minHeight: '200px' }} /></Spin>}
            {error && !loading && <Alert message="Error" description={error} type="error" showIcon style={{ marginBottom: 16 }} />}
            {!loading && !error && (
                <Table
                    columns={columns}
                    dataSource={syllabi}
                    rowKey="id"
                    bordered
                    size="middle"
                />
            )}
        </div>
    );
};

export default SyllabusManagement;

