import { SyllabusCourse, SyllabusSummaryResponse } from '../types/syllabusTypes';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'https://gil-bot-api.yosefbyd.com';

const handleResponse = async (response: Response) => {
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));

        if (Array.isArray(errorData.detail)) {
            const errorMessage = errorData.detail
                .map((err: any) => err.msg || err.message || JSON.stringify(err))
                .join(', ');
            throw new Error(errorMessage);
        }

        throw new Error(errorData.detail || errorData.message || `HTTP error! status: ${response.status}`);
    }
    return response.json();
};


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
    const requestBody = {
        syllabus_data: data,
        change_summary: changeSummary
    };

    // Debug logging
    console.log('Updating syllabus with ID:', syllabusId);
    console.log('Request body:', requestBody);

    const response = await fetch(`${API_BASE_URL}/api/v1/syllabus/${syllabusId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
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