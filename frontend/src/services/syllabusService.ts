import { SyllabusCourse, SyllabusSummaryResponse } from '../types/syllabusTypes';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'https://gil-bot-api.yosefbyd.com';

const handleResponse = async (response: Response) => {
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }
    return response.json();
};

// --- API Functions ---

export const getSyllabiList = async (params?: {
    search?: string;
    year?: string;
    semester?: string;
}): Promise<SyllabusSummaryResponse[]> => {
    const queryParams = new URLSearchParams();
    if (params?.search) queryParams.append('search', params.search);
    if (params?.year) queryParams.append('year', params.year);
    if (params?.semester) queryParams.append('semester', params.semester);

    const url = `${API_BASE_URL}/api/v1/syllabus${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    const response = await fetch(url);
    return handleResponse(response);
};

export const getSyllabusDetails = async (syllabusId: string, version?: number): Promise<SyllabusCourse> => {
    const queryParams = version ? `?version=${version}` : '';
    const response = await fetch(`${API_BASE_URL}/api/v1/syllabus/${syllabusId}${queryParams}`);
    return handleResponse(response);
};

interface SyllabusVersion {
    version: number;
    created_at: string;
    created_by: string;
    change_summary: string;
}

export const getSyllabusVersions = async (syllabusId: string): Promise<SyllabusVersion[]> => {
    const response = await fetch(`${API_BASE_URL}/api/v1/syllabus/${syllabusId}/versions`);
    return handleResponse(response);
};

interface UpdateSyllabusRequest {
    syllabus_data: SyllabusCourse;
    change_summary?: string;
}

interface UpdateSyllabusResponse {
    message: string;
    version: number;
    changes: number;
}

export const updateSyllabus = async (
    syllabusId: string,
    data: SyllabusCourse,
    changeSummary?: string
): Promise<UpdateSyllabusResponse> => {
    const response = await fetch(`${API_BASE_URL}/api/v1/syllabus/${syllabusId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            syllabus_data: data,
            change_summary: changeSummary
        }),
    });
    return handleResponse(response);
};

interface VersionDiff {
    from_version: number;
    to_version: number;
    changes: Array<{
        field_path: string;
        old_value: any;
        new_value: any;
        change_type: 'add' | 'update' | 'delete';
    }>;
}

export const getVersionDiff = async (
    syllabusId: string,
    version1: number,
    version2: number
): Promise<VersionDiff> => {
    const response = await fetch(`${API_BASE_URL}/api/v1/syllabus/${syllabusId}/diff/${version1}/${version2}`);
    return handleResponse(response);
};

// Note: Upload is handled directly by the Ant Design Upload component's action prop,
// but you might add functions here for delete if needed later. 