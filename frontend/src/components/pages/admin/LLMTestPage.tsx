import React, { useState, useEffect, useRef } from 'react';
import { Form, Input, Button, Typography, Spin, Alert, Select, InputNumber, Card, Row, Col, message } from 'antd';
import axios, { AxiosError } from 'axios';

const { Title, Paragraph } = Typography;
const { TextArea } = Input;
const { Option } = Select;

interface SyllabusSummary {
    id: string;
    name?: string;
    heb_name?: string;
}

// Predefined list of models for selection
const availableModels = [
    { value: "o4-mini", label: "GPT-o4 Mini" },
    { value: "gpt-4o", label: "GPT-4o" },
    { value: "gpt-4-turbo", label: "GPT-4 Turbo" },
    { value: "gpt-3.5-turbo", label: "GPT-3.5 Turbo" },
    { value: "gemini/gemini-2.5-pro", label: "Gemini 2.5 Pro" },
    { value: "gemini/gemini-1.5-pro", label: "Gemini 1.5 Pro" },
    { value: "gemini/gemini-1.0-pro", label: "Gemini 1.0 Pro" },
    // Add other models supported by LiteLLM as needed
];

const LLMTestPage: React.FC = () => {
    const [form] = Form.useForm();
    const [syllabi, setSyllabi] = useState<SyllabusSummary[]>([]);
    const [loadingSyllabi, setLoadingSyllabi] = useState<boolean>(true);
    const [isProcessing, setIsProcessing] = useState<boolean>(false); // Changed from isStreaming
    const [llmResponse, setLlmResponse] = useState<string>("");
    const [error, setError] = useState<string | null>(null);

    const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'https://gil-bot-api.yosefbyd.com';
    const responseEndRef = useRef<null | HTMLDivElement>(null);

    useEffect(() => {
        axios.get<SyllabusSummary[]>(`${API_BASE_URL}/api/v1/syllabus/`)
            .then(response => {
                setSyllabi(response.data);
                setLoadingSyllabi(false);
            })
            .catch(err => {
                console.error("Error fetching syllabi list:", err);
                setError("Failed to load syllabi list for selection.");
                setLoadingSyllabi(false);
            });
    }, [API_BASE_URL]);

    useEffect(() => {
        responseEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [llmResponse]);

    const handleTestSubmit = async (values: any) => {
        setIsProcessing(true);
        setLlmResponse("");
        setError(null);

        const requestBody = {
            syllabus_ids: values.syllabus_ids, // Now an array
            user_query: values.user_query,
            model_name: values.model_name, // Added model_name
            system_prompt_override: values.system_prompt_override || null,
            temperature: values.temperature,
            max_tokens: values.max_tokens,
        };

        try {
            const response = await axios.post(`${API_BASE_URL}/api/v1/admin/llm/test-naive-stream`, requestBody);
            setLlmResponse(response.data.response || "No response content.");
        } catch (err) {
            console.error("Error testing LLM:", err);
            const axiosError = err as AxiosError<any>;
            const errorMsg = axiosError.response?.data?.detail || axiosError.message || 'Error during LLM test.';
            setError(errorMsg);
            message.error(errorMsg);
        }
        setIsProcessing(false);
    };

    return (
        <div dir="rtl">
            <Title level={2}>בדיקת מודל שפה</Title>
            <Paragraph>
                בחר סילבוס אחד או יותר, הזן שאילתה, בחר מודל, והגדר פרמטרים אופציונליים לבדיקת תגובת המודל.
            </Paragraph>

            {loadingSyllabi && <Spin tip="טוען רשימת סילבוסים..."><div style={{ height: 50 }} /></Spin>}

            <Form
                form={form}
                layout="vertical"
                onFinish={handleTestSubmit}
                initialValues={{
                    temperature: 1.0,
                    max_tokens: 250, // Increased default slightly
                    model_name: availableModels[0].value, // Default to the first model in the list
                }}
            >
                <Form.Item
                    name="syllabus_ids"
                    label="בחר סילבוס/ים לבדיקה"
                    rules={[{ required: true, message: 'יש לבחור לפחות סילבוס אחד' }]}
                >
                    <Select
                        mode="multiple" // Allow multiple selections
                        allowClear
                        placeholder="בחר/י סילבוס/ים"
                        loading={loadingSyllabi}
                        showSearch
                        optionFilterProp="children"
                        filterOption={(input, option) =>
                            (option?.children as unknown as string ?? '').toLowerCase().includes(input.toLowerCase())
                        }
                    >
                        {syllabi.map(s => (
                            <Option key={s.id} value={s.id}>
                                {s.heb_name || s.name || s.id}
                            </Option>
                        ))}
                    </Select>
                </Form.Item>

                <Form.Item
                    name="user_query"
                    label="שאילתת משתמש"
                    rules={[{ required: true, message: 'יש להזין שאילתה' }]}
                >
                    <TextArea rows={3} placeholder="הזן כאן את שאלתך..." />
                </Form.Item>

                <Form.Item
                    name="model_name"
                    label="בחר מודל"
                    rules={[{ required: true, message: 'יש לבחור מודל' }]}
                >
                    <Select placeholder="בחר מודל">
                        {availableModels.map(model => (
                            <Option key={model.value} value={model.value}>
                                {model.label}
                            </Option>
                        ))}
                    </Select>
                </Form.Item>

                <Form.Item
                    name="system_prompt_override"
                    label="System Prompt (אופציונלי - יעקוף ברירת מחדל)"
                >
                    <TextArea rows={4} placeholder="לדוגמה: אתה עוזר וירטואלי המתמחה בנושאי רפואה..." />
                </Form.Item>

                <Row gutter={16}>
                    <Col xs={24} sm={12}>
                        <Form.Item name="temperature" label="טמפרטורה (0.0-2.0)">
                            <InputNumber min={0.0} max={2.0} step={0.1} style={{ width: '100%' }} />
                        </Form.Item>
                    </Col>
                    <Col xs={24} sm={12}>
                        <Form.Item name="max_tokens" label="מקסימום טוקנים">
                            <InputNumber min={1} style={{ width: '100%' }} />
                        </Form.Item>
                    </Col>
                </Row>

                <Form.Item>
                    <Button type="primary" htmlType="submit" loading={isProcessing}>
                        שלח שאילתה למודל
                    </Button>
                </Form.Item>
            </Form>

            {isProcessing && <Spin tip="מעבד תשובה..."><div style={{ height: 100 }} /></Spin>}

            {error &&
                <Alert message="שגיאה בבדיקת המודל" description={error} type="error" showIcon style={{ marginTop: 16 }} />
            }

            {llmResponse && !isProcessing && (
                <Card title="תגובת המודל" style={{ marginTop: 20, whiteSpace: 'pre-wrap', maxHeight: '400px', overflowY: 'auto' }}>
                    <Paragraph>{llmResponse}</Paragraph>
                    <div ref={responseEndRef} />
                </Card>
            )}
        </div>
    );
};

export default LLMTestPage; 