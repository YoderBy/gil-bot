import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Form, Input, Button, Typography, Spin, Alert, message, Card, Row, Col, Space, Collapse, Anchor } from 'antd';
import axios, { AxiosError } from 'axios';
import { PlusOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons';
import { SyllabusAssignmentItem, SyllabusCourse, SyllabusPersonnelItem, SyllabusStudentItem, SyllabusStudentGroupItem } from '../../../types/syllabusTypes';
import { updateSyllabus } from '../../../services/syllabusService';

const { Title, Link: AnchorLink } = Typography;
const { TextArea } = Input;
const { Panel } = Collapse;

const sectionTitles = {
    general: { id: "general-info", title: "מידע כללי" },
    description: { id: "description-section", title: "תיאור הקורס" },
    personnel: { id: "personnel-section", title: "סגל הקורס" },
    additionalInfo: { id: "additional-info-section", title: "מידע נוסף ודרישות" },
    assignments: { id: "assignments-section", title: "מטלות" },
    tests: { id: "tests-section", title: "מבחנים והערכות" },
    schedule: { id: "schedule-section", title: "לוח זמנים" },
    studentGroups: { id: "student-groups-section", title: "קבוצות סטודנטים" },
    labGroups: { id: "lab-groups-section", title: "קבוצות מעבדה (נוירו)" }, // Added Lab Groups
};

const SyllabusEditPage: React.FC = () => {
    const { courseId } = useParams<{ courseId: string }>();
    const navigate = useNavigate();
    const [form] = Form.useForm<SyllabusCourse>();
    const [syllabus, setSyllabus] = useState<SyllabusCourse | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [saving, setSaving] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);
    const [activeCollapseKeys, setActiveCollapseKeys] = useState<string[]>(Object.values(sectionTitles).map(s => s.id));

    const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'https://gil-bot-api.yosefbyd.com';

    useEffect(() => {
        if (courseId) {
            setLoading(true);
            setError(null);
            axios.get<SyllabusCourse>(`${API_BASE_URL}/api/v1/syllabus/${courseId}`)
                .then(response => {
                    let data = response.data;
                    // Ensure arrays are initialized for Form.List if they are undefined/null
                    data.personnel = data.personnel || {};
                    data.personnel.coordinators = data.personnel.coordinators || [];
                    data.personnel.overall_lecturers = data.personnel.overall_lecturers || [];
                    data.target_audience = Array.isArray(data.target_audience) ? data.target_audience : (data.target_audience ? [data.target_audience as string] : []);
                    data.assignments = data.assignments || [];
                    data.tests = data.tests || [];
                    data.tests.forEach(test => { test.moadim = test.moadim || []; });
                    data.schedule = data.schedule || {};
                    data.schedule.calendar_entries = data.schedule.calendar_entries || [];
                    data.schedule.calendar_entries.forEach(entry => {
                        entry.time_slots = entry.time_slots || [];
                        entry.time_slots.forEach(slot => {
                            slot.instructors = slot.instructors || [];
                            slot.attending_groups = slot.attending_groups || [];
                            slot.resources = slot.resources || [];
                        });
                    });
                    data.student_groups = data.student_groups || [];
                    data.student_groups.forEach(sg => {
                        sg.matzpen_groups = sg.matzpen_groups || [];
                        sg.matzpen_groups.forEach(mg => { mg.students = mg.students || []; });
                        sg.rrbg_groups = sg.rrbg_groups || [];
                        sg.rrbg_groups.forEach(rg => { rg.students = rg.students || []; });
                    });
                    data.lab_groups = data.lab_groups || {}; // Initialize lab_groups
                    // Ensure nested arrays within lab_groups are initialized (e.g., for group_a, group_b)
                    if (data.lab_groups) {
                        Object.keys(data.lab_groups).forEach(groupKey => {
                            data.lab_groups![groupKey] = data.lab_groups![groupKey] || [];
                            data.lab_groups![groupKey].forEach(table => {
                                table.students = table.students || [];
                            });
                        });
                    }

                    setSyllabus(data);
                    form.setFieldsValue(data);
                    setLoading(false);
                })
                .catch(err => {
                    console.error(`Error fetching syllabus ${courseId}:`, err);
                    const axiosError = err as AxiosError<any>;
                    setError(axiosError.response?.data?.detail || axiosError.message || 'Failed to load syllabus.');
                    setLoading(false);
                });
        } else {
            setError("No course ID provided.");
            setLoading(false);
        }
    }, [courseId, form, API_BASE_URL]);

    const handleSave = async (values: SyllabusCourse) => {
        if (!courseId) return;

        // Debug logging
        console.log('Form values received:', values);
        console.log('Course ID:', courseId);

        setSaving(true);
        setError(null);
        try {
            await updateSyllabus(courseId, values);

            // Configure message with longer duration and top position
            message.success({
                content: 'הסילבוס עודכן בהצלחה!', // Hebrew message
                duration: 5, // Show for 5 seconds instead of default 3
                style: {
                    marginTop: 20, // Add some margin from top
                    fontSize: '16px',
                },
            });


        } catch (error: any) {
            console.error(`Error updating syllabus ${courseId}:`, error);

            let errorMessage = 'Failed to update syllabus';

            // Handle fetch API errors (from syllabusService)
            if (error instanceof Error) {
                errorMessage = error.message;
            }
            // Handle axios-style errors if any
            else if (error.response?.data?.detail) {
                if (Array.isArray(error.response.data.detail)) {
                    errorMessage = error.response.data.detail
                        .map((err: any) => err.msg || err.message || JSON.stringify(err))
                        .join(', ');
                } else {
                    errorMessage = error.response.data.detail;
                }
            }

            // Set error state for display in Alert component
            setError(errorMessage);

            // Also show message
            message.error({
                content: errorMessage,
                duration: 5,
                style: {
                    marginTop: 20,
                    fontSize: '16px',
                },
            });
        }
        setSaving(false);
    };

    if (loading) return <Spin tip={`טוען סילבוס ${courseId}...`} size="large"><div style={{ minHeight: '300px' }} /></Spin>;
    if (error && !syllabus) return <Alert message="שגיאה" description={error} type="error" showIcon />;
    if (!syllabus) return <Alert message="שגיאה" description={`סילבוס עם מזהה '${courseId}' לא נמצא או לא נטען.`} type="warning" showIcon />;

    const tocItems = Object.values(sectionTitles).map(section => ({ key: section.id, href: `#${section.id}`, title: section.title }));

    return (
        <div dir="rtl">
            <Title level={2} style={{ marginBottom: 24 }}>עריכת סילבוס: {syllabus.heb_name || syllabus.name || courseId}</Title>
            {error && <Alert message="שגיאת שמירה" description={error} type="error" showIcon closable style={{ marginBottom: 16 }} />}
            <Row gutter={24}>
                <Col xs={24} sm={24} md={6} style={{ position: 'sticky', top: '20px', maxHeight: 'calc(100vh - 40px)', overflowY: 'auto' }}>
                    <Title level={4} style={{ marginBottom: 16 }}>ניווט מהיר</Title>
                    <Anchor items={tocItems} direction="vertical" getContainer={() => document.getElementById('syllabus-edit-content-area') || window} />
                </Col>
                <Col xs={24} sm={24} md={18} id="syllabus-edit-content-area" style={{ maxHeight: 'calc(100vh - 100px)', overflowY: 'auto' }}>
                    <Form form={form} layout="vertical" onFinish={handleSave} initialValues={syllabus}>
                        <Collapse activeKey={activeCollapseKeys} onChange={(keys) => setActiveCollapseKeys(keys as string[])} accordion={false}>
                            <Panel header={sectionTitles.general.title} key={sectionTitles.general.id} id={sectionTitles.general.id}>
                                <Row gutter={16}>
                                    <Col xs={24} sm={12} md={8}><Form.Item name="id" label="מזהה קורס (ID)"><Input readOnly disabled /></Form.Item></Col>
                                    <Col xs={24} sm={12} md={8}><Form.Item name="heb_name" label="שם הקורס (עברית)" rules={[{ required: true }]}><Input /></Form.Item></Col>
                                    <Col xs={24} sm={12} md={8}><Form.Item name="name" label="שם הקורס (אנגלית)"><Input /></Form.Item></Col>
                                    <Col xs={24} sm={12} md={8}><Form.Item name="year" label="שנה אקדמית" rules={[{ required: true }]}><Input /></Form.Item></Col>
                                    <Col xs={24} sm={12} md={8}><Form.Item name="semester" label="סמסטר" rules={[{ required: true }]}><Input /></Form.Item></Col>
                                </Row>
                            </Panel>
                            <Panel header={sectionTitles.description.title} key={sectionTitles.description.id} id={sectionTitles.description.id}>
                                <Form.Item name={['description', 'he']} label="תיאור (עברית)"><TextArea rows={4} /></Form.Item>
                                <Form.Item name={['description', 'en']} label="תיאור (אנגלית)"><TextArea rows={4} /></Form.Item>
                                <Form.Item name={['description', 'goal']} label="מטרת הקורס"><TextArea rows={3} /></Form.Item>
                            </Panel>
                            <Panel header={sectionTitles.personnel.title} key={sectionTitles.personnel.id} id={sectionTitles.personnel.id}>
                                <Form.List name={["personnel", "coordinators"]}>
                                    {(fields, { add, remove }) => (
                                        <><Title level={5} style={{ marginTop: 0, marginBottom: 8 }}>רכזים/ות</Title>
                                            {fields.map(({ key, name, ...restField }) => (
                                                <Space key={key} style={{ display: 'flex', marginBottom: 8 }} align="baseline">
                                                    <Form.Item {...restField} name={[name, 'name']} style={{ width: '300px' }} rules={[{ required: true }]}><Input placeholder="שם רכז/ת" /></Form.Item>
                                                    <Form.Item {...restField} name={[name, 'email']} style={{ width: '250px' }}><Input placeholder="אימייל" /></Form.Item>
                                                    <Button type="link" danger onClick={() => remove(name)}><DeleteOutlined /></Button>
                                                </Space>
                                            ))}<Form.Item><Button type="dashed" onClick={() => add({ name: '', email: '' })} block icon={<PlusOutlined />}>הוסף רכז/ת</Button></Form.Item></>)}
                                </Form.List>
                                <Form.List name={["personnel", "overall_lecturers"]}>
                                    {(fields, { add, remove }) => (
                                        <><Title level={5} style={{ marginTop: 16, marginBottom: 8 }}>מרצים/ות</Title>
                                            {fields.map(({ key, name, ...restField }) => (
                                                <Space key={key} style={{ display: 'flex', marginBottom: 8 }} align="baseline">
                                                    <Form.Item {...restField} name={[name, 'name']} style={{ width: '300px' }} rules={[{ required: true }]}><Input placeholder="שם מרצה" /></Form.Item>
                                                    <Button type="link" danger onClick={() => remove(name)}><DeleteOutlined /></Button>
                                                </Space>
                                            ))}<Form.Item><Button type="dashed" onClick={() => add({ name: '' })} block icon={<PlusOutlined />}>הוסף מרצה</Button></Form.Item></>)}
                                </Form.List>
                            </Panel>
                            <Panel header={sectionTitles.additionalInfo.title} key={sectionTitles.additionalInfo.id} id={sectionTitles.additionalInfo.id}>
                                <Form.Item label="קהל יעד">
                                    <Form.List name="target_audience">
                                        {(fields, { add, remove }) => (
                                            <>{fields.map((field, index) => (
                                                <Space key={field.key} align="baseline"><Form.Item {...field} name={[field.name]} style={{ width: 'calc(100% - 32px)' }}><Input placeholder={`קהל יעד ${index + 1}`} /></Form.Item><Button type="link" danger onClick={() => remove(field.name)}><DeleteOutlined /></Button></Space>
                                            ))}<Button type="dashed" onClick={() => add('')} block icon={<PlusOutlined />}>הוסף קהל יעד</Button></>)}
                                    </Form.List>
                                </Form.Item>
                                <Form.Item name="general_location" label="מיקום כללי"><Input /></Form.Item>
                                <Form.Item name="general_day_time_info" label="מידע כללי ימי/שעות הקורס"><Input /></Form.Item>
                                <Form.Item name="requirements" label="דרישות הקורס"><TextArea rows={4} /></Form.Item>
                                <Form.Item name="grading_policy" label="הרכב הציון הסופי"><TextArea rows={3} /></Form.Item>
                                <Form.Item name="course_notes" label="הערות הקורס"><TextArea rows={4} /></Form.Item>
                            </Panel>
                            <Panel header={sectionTitles.assignments.title} key={sectionTitles.assignments.id} id={sectionTitles.assignments.id}>
                                <Form.List name="assignments">
                                    {(fields, { add, remove }) => (<>{fields.map(({ key, name, ...restField }) => (<Card key={key} type="inner" title={`מטלה ${name + 1}`} style={{ marginBottom: 16 }} extra={<Button type="link" danger onClick={() => remove(name)}><DeleteOutlined /></Button>}>
                                        <Form.Item {...restField} name={[name, 'name']} label="שם המטלה" rules={[{ required: true }]}><Input /></Form.Item>
                                        <Row gutter={16}>
                                            <Col xs={24} sm={12}><Form.Item {...restField} name={[name, 'due_date']} label="תאריך הגשה"><Input type="date" /></Form.Item></Col>
                                            <Col xs={24} sm={12}><Form.Item {...restField} name={[name, 'due_time']} label="שעת הגשה"><Input type="time" /></Form.Item></Col>
                                        </Row>
                                        <Form.Item {...restField} name={[name, 'submission_method']} label="אופן הגשה"><Input /></Form.Item>
                                        <Form.Item {...restField} name={[name, 'details']} label="פרטי המטלה"><TextArea rows={3} /></Form.Item>
                                    </Card>))}<Form.Item><Button type="dashed" onClick={() => add({})} block icon={<PlusOutlined />}>הוסף מטלה</Button></Form.Item></>)}
                                </Form.List>
                            </Panel>
                            <Panel header={sectionTitles.tests.title} key={sectionTitles.tests.id} id={sectionTitles.tests.id}>
                                <Form.List name="tests">
                                    {(testFields, { add: addTest, remove: removeTest }) => (<>{testFields.map(({ key: testKey, name: testName, ...restTestField }) => (<Card key={testKey} type="inner" title={`מבחן/הערכה ${testName + 1}`} style={{ marginBottom: 24 }} extra={<Button type="link" danger onClick={() => removeTest(testName)}><DeleteOutlined /></Button>}>
                                        <Form.Item {...restTestField} name={[testName, 'name']} label="שם המבחן/הערכה" rules={[{ required: true }]}><Input /></Form.Item>
                                        <Form.Item {...restTestField} name={[testName, 'test_type']} label="סוג המבחן/הערכה"><Input /></Form.Item>
                                        <Form.Item {...restTestField} name={[testName, 'notes']} label="הערות למבחן"><TextArea rows={2} /></Form.Item>
                                        <Title level={5} style={{ marginTop: 16, marginBottom: 8 }}>מועדים</Title>
                                        <Form.List name={[testName, 'moadim']}>
                                            {(moadFields, { add: addMoad, remove: removeMoad }) => (<>{moadFields.map(({ key: moadKey, name: moadName, ...restMoadField }) => (<Card key={moadKey} type="inner" size="small" title={`מועד ${moadName + 1}`} style={{ marginBottom: 12, backgroundColor: '#f9f9f9' }} extra={<Button size="small" type="link" danger onClick={() => removeMoad(moadName)}><DeleteOutlined /></Button>}>
                                                <Form.Item {...restMoadField} name={[moadName, 'moad_name']} label="שם המועד" rules={[{ required: true }]}><Input /></Form.Item>
                                                <Row gutter={16}>
                                                    <Col xs={24} sm={12}><Form.Item {...restMoadField} name={[moadName, 'date']} label="תאריך"><Input type="date" /></Form.Item></Col>
                                                    <Col xs={24} sm={12}><Form.Item {...restMoadField} name={[moadName, 'time']} label="שעה"><Input type="time" /></Form.Item></Col>
                                                </Row>
                                                <Form.Item {...restMoadField} name={[moadName, 'location']} label="מיקום"><Input /></Form.Item>
                                            </Card>))}<Form.Item><Button type="dashed" onClick={() => addMoad({})} block icon={<PlusOutlined />}>הוסף מועד</Button></Form.Item></>)}
                                        </Form.List>
                                    </Card>))}<Form.Item><Button type="dashed" onClick={() => addTest({})} block icon={<PlusOutlined />}>הוסף מבחן/הערכה</Button></Form.Item></>)}
                                </Form.List>
                            </Panel>
                            <Panel header={sectionTitles.schedule.title} key={sectionTitles.schedule.id} id={sectionTitles.schedule.id}>
                                <Form.Item name={["schedule", "general_notes"]} label="הערות כלליות ללוח הזמנים"><TextArea rows={3} /></Form.Item>
                                <Title level={5} style={{ marginTop: 16, marginBottom: 8 }}>מפגשים (Calendar Entries)</Title>
                                <Form.List name={["schedule", "calendar_entries"]}>
                                    {(calendarFields, { add: addCalendarEntry, remove: removeCalendarEntry }) => (<>{calendarFields.map(({ key: calKey, name: calName, ...restCalField }) => (
                                        <Card key={calKey} type="inner" title={`מפגש ${calName + 1}`} style={{ marginBottom: 20, border: '1px solid #d9d9d9', padding: 10 }} extra={<Button type="link" danger onClick={() => removeCalendarEntry(calName)}><DeleteOutlined /></Button>}>
                                            <Row gutter={16}>
                                                <Col xs={24} sm={8}><Form.Item {...restCalField} name={[calName, 'date']} label="תאריך" rules={[{ required: true }]}><Input type="date" /></Form.Item></Col>
                                                <Col xs={24} sm={8}><Form.Item {...restCalField} name={[calName, 'day_of_week_heb']} label="יום בשבוע (עב')"><Input /></Form.Item></Col>
                                                <Col xs={24} sm={8}><Form.Item {...restCalField} name={[calName, 'day_of_week_en']} label="יום בשבוע (אנג')"><Input /></Form.Item></Col>
                                            </Row>
                                            <Form.Item {...restCalField} name={[calName, 'daily_notes']} label="הערות יומיות"><TextArea rows={2} /></Form.Item>
                                            <Title level={5} style={{ marginTop: 12, marginBottom: 8, fontSize: '1em', borderTop: '1px solid #f0f0f0', paddingTop: 10 }}>משבצות זמן (Time Slots)</Title>
                                            <Form.List name={[calName, 'time_slots']}>
                                                {(timeSlotFields, { add: addTimeSlot, remove: removeTimeSlot }) => (<>{timeSlotFields.map(({ key: tsKey, name: tsName, ...restTsField }) => (
                                                    <Card key={tsKey} size="small" type="inner" title={`משבצת זמן ${tsName + 1}`} style={{ marginBottom: 12, backgroundColor: '#fafafa' }} extra={<Button size="small" type="link" danger onClick={() => removeTimeSlot(tsName)}><DeleteOutlined /></Button>}>
                                                        <Row gutter={16}>
                                                            <Col xs={12} sm={6}><Form.Item {...restTsField} name={[tsName, 'start_time']} label="שעת התחלה"><Input type="time" /></Form.Item></Col>
                                                            <Col xs={12} sm={6}><Form.Item {...restTsField} name={[tsName, 'end_time']} label="שעת סיום"><Input type="time" /></Form.Item></Col>
                                                            <Col xs={24} sm={12}><Form.Item {...restTsField} name={[tsName, 'subject']} label="נושא/כותרת" rules={[{ required: true }]}><Input /></Form.Item></Col>
                                                        </Row>
                                                        <Form.Item {...restTsField} name={[tsName, 'activity_type']} label="סוג פעילות"><Input /></Form.Item>
                                                        <Form.Item {...restTsField} name={[tsName, 'location']} label="מיקום"><Input /></Form.Item>
                                                        <Form.Item {...restTsField} name={[tsName, 'details']} label="פרטים נוספים"><TextArea rows={2} /></Form.Item>
                                                        <Form.Item label="מרצים/ות">
                                                            <Form.List name={[tsName, 'instructors']}>
                                                                {(instrFields, { add: addInstr, remove: removeInstr }) => (<>{instrFields.map((field, index) => (<Space key={field.key} align="baseline"><Form.Item {...field} name={[field.name]} style={{ minWidth: '200px' }} rules={[{ required: true }]}><Input placeholder={`שם מרצה ${index + 1}`} /></Form.Item><Button type="link" danger onClick={() => removeInstr(field.name)}><DeleteOutlined /></Button></Space>))}<Button type="dashed" onClick={() => addInstr('')} block icon={<PlusOutlined />}>הוסף מרצה</Button></>)}
                                                            </Form.List>
                                                        </Form.Item>
                                                        <Form.Item label="קבוצות נוכחות">
                                                            <Form.List name={[tsName, 'attending_groups']}>
                                                                {(groupFields, { add: addGroup, remove: removeGroup }) => (<>{groupFields.map((field, index) => (<Space key={field.key} align="baseline"><Form.Item {...field} name={[field.name]} style={{ minWidth: '200px' }}><Input placeholder={`קבוצה ${index + 1}`} /></Form.Item><Button type="link" danger onClick={() => removeGroup(field.name)}><DeleteOutlined /></Button></Space>))}<Button type="dashed" onClick={() => addGroup('')} block icon={<PlusOutlined />}>הוסף קבוצה</Button></>)}
                                                            </Form.List>
                                                        </Form.Item>
                                                    </Card>))}<Form.Item style={{ marginTop: 10 }}><Button type="dashed" onClick={() => addTimeSlot({})} block icon={<PlusOutlined />}>הוסף משבצת זמן</Button></Form.Item></>)}
                                            </Form.List>
                                        </Card>))}<Form.Item style={{ marginTop: 10 }}><Button type="dashed" onClick={() => addCalendarEntry({})} block icon={<PlusOutlined />}>הוסף מפגש ללו"ז</Button></Form.Item></>)}
                                </Form.List>
                            </Panel>
                            <Panel header={sectionTitles.studentGroups.title} key={sectionTitles.studentGroups.id} id={sectionTitles.studentGroups.id}>
                                <Form.List name="student_groups">
                                    {(groupFields, { add: addStudentGroup, remove: removeStudentGroup }) => (<>
                                        {groupFields.map((groupField, groupIndex) => (
                                            <Card key={groupField.key} type="inner" title={`קבוצה ראשית ${groupIndex + 1}`} style={{ marginBottom: 16 }} extra={<Button type="link" danger onClick={() => removeStudentGroup(groupField.name)} icon={<DeleteOutlined />}>הסר קבוצה</Button>}>
                                                <Form.Item {...groupField} name={[groupField.name, 'name']} label="שם קבוצה ראשית (לדוגמה: גוש א')" rules={[{ required: true }]}><Input /></Form.Item>
                                                <Form.Item {...groupField} name={[groupField.name, 'details']} label="פרטי הקבוצה הראשית"><TextArea rows={2} /></Form.Item>

                                                <Title level={5} style={{ marginTop: 12, marginBottom: 8 }}>קבוצות מצפ"ן</Title>
                                                <Form.List name={[groupField.name, 'matzpen_groups']}>
                                                    {(matzpenFields, { add: addMatzpen, remove: removeMatzpen }) => (<>
                                                        {matzpenFields.map((matzpenField, matzpenIndex) => (
                                                            <Card key={matzpenField.key} type="inner" size="small" title={`קבוצת מצפן ${matzpenIndex + 1}`} style={{ marginBottom: 10, backgroundColor: '#f9f9f9' }} extra={<Button size="small" type="link" danger onClick={() => removeMatzpen(matzpenField.name)} icon={<DeleteOutlined />}>הסר</Button>}>
                                                                <Form.Item {...matzpenField} name={[matzpenField.name, 'mentor']} label="מנחה/ת מצפן"><Input /></Form.Item>
                                                                <Form.Item {...matzpenField} name={[matzpenField.name, 'meeting_room']} label="חדר מפגש (מצפן)"><Input /></Form.Item>
                                                                < Form.Item label="סטודנטים במצפן">
                                                                    < Form.List name={[matzpenField.name, 'students']} >
                                                                        {(studFields, { add: addStud, remove: remStud }) => (<>
                                                                            {studFields.map((sf, studIdx) => (
                                                                                <Space key={sf.key} align="baseline" style={{ display: 'flex', marginBottom: 8 }}>
                                                                                    <Form.Item {...sf} name={[sf.name]} style={{ flexGrow: 1 }} rules={[{ required: true, message: 'שם סטודנט חובה' }]}><Input placeholder={`שם סטודנט ${studIdx + 1}`} /></Form.Item>
                                                                                    <Button type="link" danger onClick={() => remStud(sf.name)} icon={<DeleteOutlined />} />
                                                                                </Space>
                                                                            ))}
                                                                            <Button type="dashed" onClick={() => addStud('')} block icon={<PlusOutlined />}>הוסף סטודנט למצפ"ן</Button>
                                                                        </>)}
                                                                    </Form.List>
                                                                </Form.Item>
                                                            </Card>
                                                        ))}
                                                        <Button type="dashed" onClick={() => addMatzpen({})} block icon={<PlusOutlined />}>הוסף קבוצת מצפ"ן</Button>
                                                    </>)}
                                                </Form.List>

                                                <Title level={5} style={{ marginTop: 12, marginBottom: 8 }}>קבוצות ררב"ג</Title>
                                                <Form.List name={[groupField.name, 'rrbg_groups']}>
                                                    {(rrbgFields, { add: addRrbg, remove: removeRrbg }) => (<>
                                                        {rrbgFields.map((rrbgField, rrbgIndex) => (
                                                            <Card key={rrbgField.key} type="inner" size="small" title={`קבוצת ררב"ג ${rrbgIndex + 1}`} style={{ marginBottom: 10, backgroundColor: '#f9f9f9' }} extra={<Button size="small" type="link" danger onClick={() => removeRrbg(rrbgField.name)} icon={<DeleteOutlined />}>הסר</Button>}>
                                                                <Form.Item {...rrbgField} name={[rrbgField.name, 'instructor']} label="מדריך/ת ררבג"><Input /></Form.Item>
                                                                <Form.Item {...rrbgField} name={[rrbgField.name, 'first_meeting_date']} label="תאריך מפגש ראשון"><Input type="date" /></Form.Item>
                                                                <Form.Item {...rrbgField} name={[rrbgField.name, 'room']} label="חדר (ררבג)"><Input /></Form.Item>
                                                                < Form.Item label="סטודנטים בררבג">
                                                                    < Form.List name={[rrbgField.name, 'students']} >
                                                                        {(studFields, { add: addStud, remove: remStud }) => (<>
                                                                            {studFields.map((sf, studIdx) => (
                                                                                <Space key={sf.key} align="baseline" style={{ display: 'flex', marginBottom: 8 }}>
                                                                                    <Form.Item {...sf} name={[sf.name]} style={{ flexGrow: 1 }} rules={[{ required: true, message: 'שם סטודנט חובה' }]}><Input placeholder={`שם סטודנט ${studIdx + 1}`} /></Form.Item>
                                                                                    <Button type="link" danger onClick={() => remStud(sf.name)} icon={<DeleteOutlined />} />
                                                                                </Space>
                                                                            ))}
                                                                            <Button type="dashed" onClick={() => addStud('')} block icon={<PlusOutlined />}>הוסף סטודנט לררב"ג</Button>
                                                                        </>)}
                                                                    </Form.List>
                                                                </Form.Item>
                                                            </Card>
                                                        ))}
                                                        <Button type="dashed" onClick={() => addRrbg({})} block icon={<PlusOutlined />}>הוסף קבוצת ררב"ג</Button>
                                                    </>)}
                                                </Form.List>
                                            </Card>
                                        ))}
                                        <Form.Item><Button type="dashed" onClick={() => addStudentGroup({})} block icon={<PlusOutlined />}>הוסף קבוצת סטודנטים ראשית</Button></Form.Item>
                                    </>)}
                                </Form.List>
                            </Panel >
                            <Panel header={sectionTitles.labGroups.title} key={sectionTitles.labGroups.id} id={sectionTitles.labGroups.id}>
                                {syllabus?.lab_groups && Object.keys(syllabus.lab_groups).map(groupKey => (
                                    <div key={groupKey} style={{ marginBottom: 20 }}>
                                        <Title level={4}>{`מעבדות ${groupKey === 'group_a' ? 'קבוצה א\'' : (groupKey === 'group_b' ? 'קבוצה ב\'' : groupKey)}`}</Title>
                                        <Form.List name={['lab_groups', groupKey]}>
                                            {(tableFields, { add: addTable, remove: removeTable }) => (
                                                <>
                                                    {tableFields.map((tableField, tableIndex) => (
                                                        <Card key={tableField.key} type="inner" title={`שולחן ${form.getFieldValue(['lab_groups', groupKey, tableField.name, 'table']) || (tableIndex + 1)}`} style={{ marginBottom: 16, backgroundColor: '#fdfdfd' }} extra={<Button type="link" danger onClick={() => removeTable(tableField.name)} icon={<DeleteOutlined />}>הסר שולחן</Button>}>
                                                            <Form.Item {...tableField} name={[tableField.name, 'table']} label="מספר/שם שולחן">
                                                                <Input placeholder="לדוגמה: 1, A1" />
                                                            </Form.Item>
                                                            <Title level={5} style={{ marginTop: 12, marginBottom: 8 }}>סטודנטים בשולחן</Title>
                                                            <Form.List name={[tableField.name, 'students']}>
                                                                {(studFields, { add: addStud, remove: remStud }) => (
                                                                    <>
                                                                        {studFields.map((sf, studIdx) => (
                                                                            <Row gutter={8} key={sf.key} style={{ marginBottom: 8 }}>
                                                                                <Col flex={1}><Form.Item {...sf} name={[sf.name, 'first_name']} noStyle><Input placeholder={`שם פרטי ${studIdx + 1}`} /></Form.Item></Col>
                                                                                <Col flex={1}><Form.Item {...sf} name={[sf.name, 'last_name']} noStyle><Input placeholder={`שם משפחה ${studIdx + 1}`} /></Form.Item></Col>
                                                                                <Col flex={1}><Form.Item {...sf} name={[sf.name, 'email']} noStyle><Input type="email" placeholder={`אימייל ${studIdx + 1}`} /></Form.Item></Col>
                                                                                <Col><Button type="link" danger onClick={() => remStud(sf.name)} icon={<DeleteOutlined />} /></Col>
                                                                            </Row>
                                                                        ))}
                                                                        <Button type="dashed" onClick={() => addStud({ first_name: '', last_name: '', email: '' })} block icon={<PlusOutlined />}>הוסף סטודנט לשולחן</Button>
                                                                    </>
                                                                )}
                                                            </Form.List>
                                                        </Card>
                                                    ))}
                                                    <Button type="dashed" onClick={() => addTable({})} block icon={<PlusOutlined />}>הוסף שולחן לקבוצה {groupKey}</Button>
                                                </>
                                            )}
                                        </Form.List>
                                    </div>
                                ))}
                            </Panel>
                        </Collapse >
                        <Form.Item style={{ marginTop: 24, textAlign: 'left' }}>
                            <Space>
                                <Button type="primary" htmlType="submit" loading={saving}>שמור שינויים</Button>
                                <Button onClick={() => navigate('/admin/syllabus')}>חזרה לרשימה</Button>
                            </Space>
                        </Form.Item>
                    </Form >
                </Col >
            </Row >

        </div >

    );
};

export default SyllabusEditPage; 