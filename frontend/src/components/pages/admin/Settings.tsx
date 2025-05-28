import React, { useState, useEffect } from 'react';
import {
    Typography,
    Input,
    Button,
    message,
    Spin
} from 'antd';

const { Title, Paragraph } = Typography;
const { TextArea } = Input;

const AdminSettings: React.FC = () => {
    const [systemPrompt, setSystemPrompt] = useState<string>('');
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [isSaving, setIsSaving] = useState<boolean>(false);

    // Simulate fetching the current prompt on component mount
    useEffect(() => {
        setIsLoading(true);
        // Replace with actual API call to fetch settings
        setTimeout(() => {
            setSystemPrompt('You are a helpful assistant answering questions based only on the provided syllabus context. Be concise and accurate.');
            setIsLoading(false);
        }, 1000); // Simulate network delay
    }, []);

    const handleSave = () => {
        setIsSaving(true);
        // Replace with actual API call to save settings
        console.log('Saving system prompt:', systemPrompt);
        setTimeout(() => {
            message.success('System prompt saved successfully!');
            setIsSaving(false);
        }, 1500); // Simulate network delay
    };

    return (
        <>
            <Title level={2}>Admin Settings</Title>
            <Paragraph>Configure system-wide settings for the chatbot.</Paragraph>

            <Spin spinning={isLoading}>
                <Title level={4} style={{ marginTop: '2rem' }}>System Prompt</Title>
                <Paragraph>
                    Define the base instructions given to the generation LLM. This influences its tone,
                    response style, and constraints.
                </Paragraph>
                <TextArea
                    rows={8}
                    value={systemPrompt}
                    onChange={(e) => setSystemPrompt(e.target.value)}
                    placeholder="Enter the system prompt here..."
                    disabled={isLoading || isSaving}
                />
                <Button
                    type="primary"
                    style={{ marginTop: '1rem' }}
                    onClick={handleSave}
                    loading={isSaving}
                    disabled={isLoading}
                >
                    Save Prompt
                </Button>
            </Spin>
            {/* Add other settings later, e.g., LLM model selection */}
        </>
    );
};

export default AdminSettings; 