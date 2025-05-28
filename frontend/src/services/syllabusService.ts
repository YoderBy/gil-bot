import { API_BASE_URL } from '../consts/consts';
import { SyllabusSummaryResponse, Syllabus, SyllabusVersion, StructuredSection } from '../types/syllabusTypes';

// Base URL for the API - replace with your actual backend URL if needed
// If running locally and using vite proxy, can be relative

// Helper to handle fetch responses
const handleResponse = async (response: Response) => {
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }
    return response.json();
};

// --- API Functions ---

export const getSyllabiList = async (): Promise<SyllabusSummaryResponse[]> => {
    const response = await fetch(`${API_BASE_URL}/syllabus`);
    return handleResponse(response);
};

export const getSyllabusDetails = async (syllabusId: string): Promise<Syllabus> => {
    const response = await fetch(`${API_BASE_URL}/syllabus/${syllabusId}`);
    return handleResponse(response);
};

export const getSyllabusVersionData = async (syllabusId: string, versionNumber: number): Promise<SyllabusVersion> => {
    const response = await fetch(`${API_BASE_URL}/syllabus/${syllabusId}/version/${versionNumber}`);
    return handleResponse(response);
};

export const updateSyllabusVersionData = async (
    syllabusId: string,
    updatedSections: StructuredSection[]
): Promise<SyllabusSummaryResponse> => {
    const response = await fetch(`${API_BASE_URL}/syllabus/${syllabusId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(updatedSections),
    });
    return handleResponse(response);
};

// Note: Upload is handled directly by the Ant Design Upload component's action prop,
// but you might add functions here for delete if needed later. 