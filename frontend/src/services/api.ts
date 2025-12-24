import axios from 'axios';
import type {
  FileSearchStore,
  Document,
  ChatMessage,
  Citation,
  Report,
} from '../types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Store Management
export const createStore = async (displayName: string): Promise<FileSearchStore> => {
  const response = await api.post('/stores', { display_name: displayName });
  return response.data;
};

export const listStores = async (): Promise<FileSearchStore[]> => {
  const response = await api.get('/stores');
  return response.data.stores || [];
};

export const deleteStore = async (storeId: string): Promise<void> => {
  await api.delete(`/stores/${storeId}`);
};

// Document Management
export const uploadDocument = async (
  storeId: string,
  file: File,
  onProgress?: (progress: number) => void
): Promise<Document> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('chunk_size', '800');
  formData.append('chunk_overlap', '400');

  const response = await api.post(`/stores/${storeId}/upload`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (progressEvent.total) {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress?.(progress);
      }
    },
  });

  return response.data.document;
};

export const listDocuments = async (storeId: string): Promise<Document[]> => {
  const response = await api.get(`/stores/${storeId}/documents`);
  return response.data.documents || [];
};

export const deleteDocument = async (documentName: string): Promise<void> => {
  // documentName format: fileSearchStores/{store_id}/documents/{doc_id}
  // Use the full path without encoding since backend uses :path parameter
  await api.delete(`/documents/${documentName}`);
};

// Chat
export const sendChatMessage = async (
  message: string,
  storeName: string,
  history: ChatMessage[],
  documentNames?: string[]
): Promise<{ message: string; citations: Citation[] }> => {
  const response = await api.post('/chat', {
    message,
    store_name: storeName,
    history,
    document_names: documentNames || [],
  });
  return response.data;
};

// Report Generation
export const generateReport = async (
  storeName: string,
  chatHistory: ChatMessage[],
  reportType: string = 'comprehensive'
): Promise<Report> => {
  const response = await api.post('/generate-report', {
    store_name: storeName,
    chat_history: chatHistory,
    report_type: reportType,
  });
  return response.data;
};

export default api;
