export type DocumentState = 'STATE_ACTIVE' | 'STATE_PENDING' | 'STATE_FAILED';

export interface FileSearchStore {
  name: string;
  display_name: string;
  create_time?: string;
  update_time?: string;
  active_documents_count: number;
  pending_documents_count: number;
  failed_documents_count: number;
  size_bytes: number;
}

export interface Document {
  name: string;
  display_name: string;
  state: DocumentState;
  size_bytes?: number;
  mime_type?: string;
  create_time?: string;
  update_time?: string;
  selected?: boolean;
}

export interface Citation {
  document_name: string;
  chunk_id: string;
  score: number;
  text: string;
}

export interface ChatMessage {
  role: 'user' | 'model';
  content: string;
  citations?: Citation[];
}

export interface Report {
  title: string;
  content: string;
  generated_at: string;
}

export interface UploadProgress {
  file_id: string;
  filename: string;
  progress: number;
  status: 'uploading' | 'processing' | 'completed' | 'failed';
  error?: string;
}
