import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link as RouterLink } from 'react-router-dom';
import { Typography, Spin, Alert, Button, Row, Col, Anchor, Card, Descriptions, List, Space, Tag } from 'antd';
import axios, { AxiosError } from 'axios';
import { EditOutlined } from '@ant-design/icons';

// Re-using the comprehensive SyllabusCourse interface from SyllabusEditPage.tsx
// (Ideally, this would be in a shared types file)
interface SyllabusPersonnelItem {
    name?: string;
    email?: string;
}
interface SyllabusStudentItem {
    first_name?: string;
    last_name?: string;
    email?: string;
}
interface LabGroupTableItem {
    table?: number | string;
    students?: SyllabusStudentItem[];
}
interface LabGroupCategory {
    [groupCategoryKey: string]: LabGroupTableItem[];
}
interface SyllabusStudentGroupItem {
    name?: string;
    details?: string;
    matzpen_groups?: Array<{ mentor?: string; meeting_room?: string; students?: string[]; }>;
    rrbg_groups?: Array<{ instructor?: string; first_meeting_date?: string; room?: string; students?: string[]; }>;
}
interface SyllabusAssignmentItem {
    name?: string; due_date?: string; due_time?: string; submission_method?: string; details?: string;
}
interface SyllabusTestMoadItem {
    moad_name?: string; date?: string; time?: string; location?: string;
}
interface SyllabusTestItem {
    name?: string; test_type?: string; notes?: string; moadim?: SyllabusTestMoadItem[];
}
interface SyllabusTimeSlotResourceItem { type?: string; title?: string; url?: string; }
interface SyllabusTimeSlotItem {
    start_time?: string; end_time?: string; subject?: string; activity_type?: string; location?: string;
    details?: string; instructors?: string[]; attending_groups?: string[]; resources?: SyllabusTimeSlotResourceItem[];
}
interface SyllabusCalendarEntryItem {
    date?: string; day_of_week_heb?: string; day_of_week_en?: string; daily_notes?: string; time_slots?: SyllabusTimeSlotItem[];
}
interface SyllabusCourse {
    id: string; name: string; heb_name: string; year: string; semester: string;
    description?: { [key: string]: string };
    personnel?: { coordinators?: SyllabusPersonnelItem[]; overall_lecturers?: SyllabusPersonnelItem[]; rv_lab_coordinator?: SyllabusPersonnelItem[]; };
    target_audience?: string[]; general_location?: string; general_day_time_info?: string;
    requirements?: string; grading_policy?: string; course_notes?: string;
    student_groups?: SyllabusStudentGroupItem[];
    lab_groups?: LabGroupCategory;
    assignments?: SyllabusAssignmentItem[];
    schedule?: { general_notes?: string; calendar_entries?: SyllabusCalendarEntryItem[] };
    tests?: SyllabusTestItem[];
}

const { Title, Paragraph, Text, Link: AnchorLink } = Typography;

// Using the same sectionTitles from EditPage for consistency
const sectionTitles = {
    general: { id: "view-general-info", title: "מידע כללי" },
    description: { id: "view-description-section", title: "תיאור הקורס" },
    personnel: { id: "view-personnel-section", title: "סגל הקורס" },
    additionalInfo: { id: "view-additional-info-section", title: "מידע נוסף ודרישות" },
    assignments: { id: "view-assignments-section", title: "מטלות" },
    tests: { id: "view-tests-section", title: "מבחנים והערכות" },
    schedule: { id: "view-schedule-section", title: "לוח זמנים" },
    studentGroups: { id: "view-student-groups-section", title: "קבוצות סטודנטים" },
    labGroups: { id: "view-lab-groups-section", title: "קבוצות מעבדה" },
};

const SyllabusViewPage: React.FC = () => {
    const { courseId } = useParams<{ courseId: string }>();
    const navigate = useNavigate();
    const [syllabus, setSyllabus] = useState<SyllabusCourse | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'https://gil-bot-api.yosefbyd.com';

    useEffect(() => {
        if (courseId) {
            setLoading(true);
            setError(null);
            axios.get<SyllabusCourse>(`${API_BASE_URL}/api/v1/syllabus/${courseId}`)
                .then(response => {
                    setSyllabus(response.data);
                    setLoading(false);
                })
                .catch(err => {
                    console.error(`Error fetching syllabus ${courseId}:`, err);
                    const axiosError = err as AxiosError<any>;
                    setError(axiosError.response?.data?.detail || axiosError.message || 'Failed to load syllabus details.');
                    setLoading(false);
                });
        } else {
            setError("No course ID provided.");
            setLoading(false);
        }
    }, [courseId, API_BASE_URL]);

    if (loading) return <Spin tip={`טוען סילבוס ${courseId}...`} size="large"><div style={{ minHeight: '300px' }} /></Spin>;
    if (error) return <Alert message="שגיאה" description={error} type="error" showIcon />;
    if (!syllabus) return <Alert message="מידע לא זמין" description={`לא נמצא סילבוס עם מזהה '${courseId}'.`} type="warning" showIcon />;

    const tocItems = Object.values(sectionTitles).map(section => ({ key: section.id, href: `#${section.id}`, title: section.title }));

    const renderPersonnelList = (personnelList?: SyllabusPersonnelItem[], title?: string) => {
        if (!personnelList || personnelList.length === 0) return null;
        return (
            <>
                {title && <Title level={5} style={{ marginTop: 8, marginBottom: 4 }}>{title}</Title>}
                <List
                    size="small"
                    dataSource={personnelList}
                    renderItem={item => <List.Item>{item.name}{item.email && ` (${item.email})`}</List.Item>}
                />
            </>
        );
    };

    return (
        <div dir="rtl" style={{ padding: '0 24px' }}>
            <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
                <Col>
                    <Title level={2} style={{ margin: 0 }}>{syllabus.heb_name || syllabus.name || courseId}</Title>
                    <Text type="secondary">תצוגת סילבוס</Text>
                </Col>
                <Col>
                    <Space>
                        <Button onClick={() => navigate('/admin/syllabus')}>חזרה לרשימה</Button>
                        <Button type="primary" icon={<EditOutlined />} onClick={() => navigate(`/admin/syllabus/edit/${courseId}`)}>
                            ערוך סילבוס
                        </Button>
                    </Space>
                </Col>
            </Row>

            <Row gutter={24}>
                <Col xs={24} sm={24} md={6} style={{ position: 'sticky', top: '20px', maxHeight: 'calc(100vh - 40px)', overflowY: 'auto' }}>
                    <Title level={4} style={{ marginBottom: 16 }}>תוכן עניינים</Title>
                    <Anchor items={tocItems} direction="vertical" getContainer={() => document.getElementById('syllabus-view-content-area') || window} />
                </Col>
                <Col xs={24} sm={24} md={18} id="syllabus-view-content-area" style={{ maxHeight: 'calc(100vh - 100px)', overflowY: 'auto', paddingRight: '10px' }}>
                    <Space direction="vertical" style={{ width: '100%' }} size="large">
                        <Card title={sectionTitles.general.title} id={sectionTitles.general.id} hoverable>
                            <Descriptions bordered column={1} size="small">
                                <Descriptions.Item label="מזהה קורס (ID)">{syllabus.id}</Descriptions.Item>
                                <Descriptions.Item label="שם הקורס (עברית)">{syllabus.heb_name}</Descriptions.Item>
                                <Descriptions.Item label="שם הקורס (אנגלית)">{syllabus.name}</Descriptions.Item>
                                <Descriptions.Item label="שנה אקדמית">{syllabus.year}</Descriptions.Item>
                                <Descriptions.Item label="סמסטר">{syllabus.semester}</Descriptions.Item>
                            </Descriptions>
                        </Card>

                        <Card title={sectionTitles.description.title} id={sectionTitles.description.id} hoverable>
                            {syllabus.description?.he && <><Title level={5}>תיאור (עברית)</Title><Paragraph>{syllabus.description.he.split('\n').map((line, i) => <React.Fragment key={i}>{line}<br /></React.Fragment>)}</Paragraph></>}
                            {syllabus.description?.en && <><Title level={5}>תיאור (אנגלית)</Title><Paragraph>{syllabus.description.en.split('\n').map((line, i) => <React.Fragment key={i}>{line}<br /></React.Fragment>)}</Paragraph></>}
                            {syllabus.description?.goal && <><Title level={5}>מטרת הקורס</Title><Paragraph>{syllabus.description.goal.split('\n').map((line, i) => <React.Fragment key={i}>{line}<br /></React.Fragment>)}</Paragraph></>}
                        </Card>

                        <Card title={sectionTitles.personnel.title} id={sectionTitles.personnel.id} hoverable>
                            {renderPersonnelList(syllabus.personnel?.coordinators, "רכזים/ות")}
                            {renderPersonnelList(syllabus.personnel?.overall_lecturers, "מרצים/ות כוללים/ות")}
                            {renderPersonnelList(syllabus.personnel?.rv_lab_coordinator, "רכז/ת מעבדת RV")}
                        </Card>

                        <Card title={sectionTitles.additionalInfo.title} id={sectionTitles.additionalInfo.id} hoverable>
                            <Descriptions bordered column={1} size="small">
                                {syllabus.target_audience && syllabus.target_audience.length > 0 &&
                                    <Descriptions.Item label="קהל יעד">
                                        <List size="small" dataSource={syllabus.target_audience} renderItem={item => <List.Item>{item}</List.Item>} />
                                    </Descriptions.Item>}
                                {syllabus.general_location && <Descriptions.Item label="מיקום כללי">{syllabus.general_location}</Descriptions.Item>}
                                {syllabus.general_day_time_info && <Descriptions.Item label="מידע ימי/שעות הקורס">{syllabus.general_day_time_info}</Descriptions.Item>}
                                {syllabus.requirements && <Descriptions.Item label="דרישות הקורס"><Paragraph style={{ whiteSpace: 'pre-wrap' }}>{syllabus.requirements}</Paragraph></Descriptions.Item>}
                                {syllabus.grading_policy && <Descriptions.Item label="הרכב הציון הסופי"><Paragraph style={{ whiteSpace: 'pre-wrap' }}>{syllabus.grading_policy}</Paragraph></Descriptions.Item>}
                                {syllabus.course_notes && <Descriptions.Item label="הערות הקורס"><Paragraph style={{ whiteSpace: 'pre-wrap' }}>{syllabus.course_notes}</Paragraph></Descriptions.Item>}
                            </Descriptions>
                        </Card>

                        <Card title={sectionTitles.assignments.title} id={sectionTitles.assignments.id} hoverable>
                            {syllabus.assignments && syllabus.assignments.length > 0 ? (
                                <List
                                    itemLayout="vertical"
                                    dataSource={syllabus.assignments}
                                    renderItem={(item, index) => (
                                        <List.Item key={index}>
                                            <List.Item.Meta title={<Text strong>{item.name || "מטלה"}</Text>} />
                                            <Descriptions bordered size="small" column={1}>
                                                {item.due_date && <Descriptions.Item label="תאריך הגשה">{item.due_date}{item.due_time && ` ${item.due_time}`}</Descriptions.Item>}
                                                {item.submission_method && <Descriptions.Item label="אופן הגשה">{item.submission_method}</Descriptions.Item>}
                                                {item.details && <Descriptions.Item label="פרטים"><Paragraph style={{ whiteSpace: 'pre-wrap' }}>{item.details}</Paragraph></Descriptions.Item>}
                                            </Descriptions>
                                        </List.Item>
                                    )}
                                />
                            ) : <Text>אין מטלות מוגדרות.</Text>}
                        </Card>

                        <Card title={sectionTitles.tests.title} id={sectionTitles.tests.id} hoverable>
                            {syllabus.tests && syllabus.tests.length > 0 ? (
                                <List
                                    itemLayout="vertical"
                                    dataSource={syllabus.tests}
                                    renderItem={(item, index) => (
                                        <List.Item key={index}>
                                            <List.Item.Meta title={<Text strong>{item.name || "מבחן/הערכה"}</Text>} />
                                            <Descriptions bordered size="small" column={1}>
                                                {item.test_type && <Descriptions.Item label="סוג">{item.test_type}</Descriptions.Item>}
                                                {item.notes && <Descriptions.Item label="הערות"><Paragraph style={{ whiteSpace: 'pre-wrap' }}>{item.notes}</Paragraph></Descriptions.Item>}
                                            </Descriptions>
                                            {item.moadim && item.moadim.length > 0 &&
                                                <div style={{ marginTop: 10 }}>
                                                    <Text strong>מועדים:</Text>
                                                    <List size="small" dataSource={item.moadim} renderItem={moad => (
                                                        <List.Item>
                                                            {moad.moad_name}: {moad.date} {moad.time}
                                                            {moad.location && ` (${moad.location})`}
                                                        </List.Item>
                                                    )} />
                                                </div>
                                            }
                                        </List.Item>
                                    )}
                                />
                            ) : <Text>אין מבחנים מוגדרים.</Text>}
                        </Card>

                        <Card title={sectionTitles.schedule.title} id={sectionTitles.schedule.id} hoverable>
                            {syllabus.schedule?.general_notes && <><Title level={5}>הערות כלליות ללו"ז</Title><Paragraph style={{ whiteSpace: 'pre-wrap' }}>{syllabus.schedule.general_notes}</Paragraph></>}
                            {syllabus.schedule?.calendar_entries && syllabus.schedule.calendar_entries.length > 0 ? (
                                <List
                                    itemLayout="vertical"
                                    dataSource={syllabus.schedule.calendar_entries}
                                    renderItem={(entry, index) => (
                                        <List.Item key={index} style={{ borderBottom: '1px solid #f0f0f0', paddingBottom: 16 }}>
                                            <Title level={5}>{entry.date} ({entry.day_of_week_heb})</Title>
                                            {entry.daily_notes && <Paragraph type="secondary">{entry.daily_notes}</Paragraph>}
                                            {entry.time_slots && entry.time_slots.map((slot, slotIdx) => (
                                                <Card key={slotIdx} type="inner" size="small" title={slot.subject || `משבצת זמן ${slotIdx + 1}`} style={{ marginTop: 8, backgroundColor: '#fafafa' }}>
                                                    <Descriptions bordered column={1} size="small">
                                                        {(slot.start_time || slot.end_time) && <Descriptions.Item label="שעות">{slot.start_time} - {slot.end_time}</Descriptions.Item>}
                                                        {slot.activity_type && <Descriptions.Item label="סוג פעילות">{slot.activity_type}</Descriptions.Item>}
                                                        {slot.location && <Descriptions.Item label="מיקום">{slot.location}</Descriptions.Item>}
                                                        {slot.details && <Descriptions.Item label="פרטים"><Paragraph style={{ whiteSpace: 'pre-wrap' }}>{slot.details}</Paragraph></Descriptions.Item>}
                                                        {slot.instructors && slot.instructors.length > 0 && <Descriptions.Item label="מרצים/ות">{slot.instructors.join(', ')}</Descriptions.Item>}
                                                        {slot.attending_groups && slot.attending_groups.length > 0 && <Descriptions.Item label="קבוצות">{slot.attending_groups.join(', ')}</Descriptions.Item>}
                                                        {/* Add rendering for slot.resources if needed */}
                                                    </Descriptions>
                                                </Card>
                                            ))}
                                        </List.Item>
                                    )}
                                />
                            ) : <Text>אין מפגשים מוגדרים בלוח הזמנים.</Text>}
                        </Card>

                        <Card title={sectionTitles.studentGroups.title} id={sectionTitles.studentGroups.id} hoverable>
                            {syllabus.student_groups && syllabus.student_groups.length > 0 ? syllabus.student_groups.map((sGroup, sgIndex) => (
                                <div key={sgIndex} style={{ marginBottom: 20 }}>
                                    <Title level={4}>{sGroup.name || `קבוצה ראשית ${sgIndex + 1}`}</Title>
                                    {sGroup.details && <Paragraph type="secondary">{sGroup.details}</Paragraph>}
                                    {sGroup.matzpen_groups && sGroup.matzpen_groups.length > 0 &&
                                        <div style={{ paddingLeft: 20 }}>
                                            <Title level={5}>קבוצות מצפ"ן:</Title>
                                            {sGroup.matzpen_groups.map((mGroup, mgIndex) => (
                                                <Card key={mgIndex} type="inner" size="small" title={`מצפ"ן: ${mGroup.mentor || `קבוצה ${mgIndex + 1}`}`} style={{ marginBottom: 10 }}>
                                                    {mGroup.meeting_room && <Paragraph>חדר: {mGroup.meeting_room}</Paragraph>}
                                                    {mGroup.students && mGroup.students.length > 0 && <><Text strong>סטודנטים:</Text> <List size="small" dataSource={mGroup.students} renderItem={s => <List.Item>{s}</List.Item>} /></>}
                                                </Card>
                                            ))}
                                        </div>
                                    }
                                    {sGroup.rrbg_groups && sGroup.rrbg_groups.length > 0 &&
                                        <div style={{ paddingLeft: 20, marginTop: 10 }}>
                                            <Title level={5}>קבוצות ררב"ג:</Title>
                                            {sGroup.rrbg_groups.map((rGroup, rgIndex) => (
                                                <Card key={rgIndex} type="inner" size="small" title={`ררב"ג: ${rGroup.instructor || `קבוצה ${rgIndex + 1}`}`} style={{ marginBottom: 10 }}>
                                                    {rGroup.room && <Paragraph>חדר: {rGroup.room}</Paragraph>}
                                                    {rGroup.first_meeting_date && <Paragraph>מפגש ראשון: {rGroup.first_meeting_date}</Paragraph>}
                                                    {rGroup.students && rGroup.students.length > 0 && <><Text strong>סטודנטים:</Text> <List size="small" dataSource={rGroup.students} renderItem={s => <List.Item>{s}</List.Item>} /></>}
                                                </Card>
                                            ))}
                                        </div>
                                    }
                                </div>
                            )) : <Text>אין קבוצות סטודנטים מוגדרות.</Text>}
                        </Card>

                        <Card title={sectionTitles.labGroups.title} id={sectionTitles.labGroups.id} hoverable>
                            {syllabus.lab_groups && Object.keys(syllabus.lab_groups).length > 0 ? Object.entries(syllabus.lab_groups).map(([groupKey, tables]) => (
                                <div key={groupKey} style={{ marginBottom: 20 }}>
                                    <Title level={4}>{`קבוצת מעבדה: ${groupKey.replace('group_', '').toUpperCase()}`}</Title>
                                    {tables && tables.map((table, tableIndex) => (
                                        <Card key={tableIndex} type="inner" title={`שולחן ${table.table || (tableIndex + 1)}`} style={{ marginBottom: 10 }}>
                                            {table.students && table.students.length > 0 ? (
                                                <List
                                                    size="small"
                                                    dataSource={table.students}
                                                    renderItem={student => (
                                                        <List.Item>
                                                            {student.first_name} {student.last_name} {student.email && `(${student.email})`}
                                                        </List.Item>
                                                    )}
                                                />
                                            ) : <Text>אין סטודנטים משויכים לשולחן זה.</Text>}
                                        </Card>
                                    ))}
                                </div>
                            )) : <Text>אין קבוצות מעבדה מוגדרות.</Text>}
                        </Card>

                    </Space>
                </Col>
            </Row>
        </div>
    );
};

export default SyllabusViewPage; 