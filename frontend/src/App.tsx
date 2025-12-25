import { useState, useEffect } from 'react';
import { Menu, X } from 'lucide-react';
import SourcePanel from './components/SourcePanel';
import ChatPanel from './components/ChatPanel';
import StudioPanel from './components/StudioPanel';
import type { Document, ChatMessage, Report, UploadProgress, FileSearchStore } from './types';
import * as api from './services/api';

// Helper function to extract store ID from full name
const getStoreId = (storeName: string): string => {
  return storeName.replace('fileSearchStores/', '');
};

function App() {
  const [store, setStore] = useState<FileSearchStore | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [uploadProgress, setUploadProgress] = useState<UploadProgress[]>([]);
  const [isLoadingChat, setIsLoadingChat] = useState(false);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [currentReport, setCurrentReport] = useState<Report | null>(null);
  const [showSources, setShowSources] = useState(true);

  // Initialize store on mount
  useEffect(() => {
    const initStore = async () => {
      try {
        const stores = await api.listStores();
        if (stores.length > 0) {
          setStore(stores[0]);
        } else {
          const newStore = await api.createStore('My Document Store');
          setStore(newStore);
        }
      } catch (error) {
        console.error('Failed to initialize store:', error);
      }
    };

    initStore();
  }, []);

  // Load documents when store changes
  useEffect(() => {
    if (store) {
      loadDocuments();
    }
  }, [store]);

  const loadDocuments = async () => {
    if (!store) return;

    try {
      const storeId = getStoreId(store.name);
      const docs = await api.listDocuments(storeId);
      setDocuments(docs);
    } catch (error) {
      console.error('Failed to load documents:', error);
    }
  };

  const handleUpload = async (files: FileList) => {
    if (!store) return;

    const fileArray = Array.from(files);

    for (const file of fileArray) {
      const fileId = `${Date.now()}-${file.name}`;
      const progress: UploadProgress = {
        file_id: fileId,
        filename: file.name,
        progress: 0,
        status: 'uploading',
      };

      setUploadProgress(prev => [...prev, progress]);

      try {
        const storeId = getStoreId(store.name);
        await api.uploadDocument(
          storeId,
          file,
          (progressPercent) => {
            setUploadProgress(prev =>
              prev.map(p =>
                p.file_id === fileId
                  ? { ...p, progress: progressPercent }
                  : p
              )
            );
          }
        );

        setUploadProgress(prev =>
          prev.map(p =>
            p.file_id === fileId
              ? { ...p, status: 'processing', progress: 100 }
              : p
          )
        );

        // Wait for processing
        await new Promise(resolve => setTimeout(resolve, 2000));

        setUploadProgress(prev =>
          prev.map(p =>
            p.file_id === fileId
              ? { ...p, status: 'completed' }
              : p
          )
        );

        // Remove from progress list after 2 seconds
        setTimeout(() => {
          setUploadProgress(prev => prev.filter(p => p.file_id !== fileId));
        }, 2000);

        // Reload documents
        await loadDocuments();
      } catch (error) {
        console.error('Upload failed:', error);
        setUploadProgress(prev =>
          prev.map(p =>
            p.file_id === fileId
              ? { ...p, status: 'failed', error: String(error) }
              : p
          )
        );
      }
    }
  };

  const handleDeleteDocument = async (documentName: string) => {
    try {
      await api.deleteDocument(documentName);
      setDocuments(prev => prev.filter(doc => doc.name !== documentName));
    } catch (error) {
      console.error('Failed to delete document:', error);
    }
  };

  const handleSendMessage = async (message: string) => {
    if (!store) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content: message,
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoadingChat(true);

    try {
      // Get all active document names
      const activeDocNames = documents
        .filter(doc => doc.state === 'STATE_ACTIVE')
        .map(doc => doc.name);

      const response = await api.sendChatMessage(
        message,
        store.name,
        messages,
        activeDocNames
      );

      const assistantMessage: ChatMessage = {
        role: 'model',
        content: response.message,
        citations: response.citations,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage: ChatMessage = {
        role: 'model',
        content: 'エラーが発生しました。もう一度お試しください。',
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoadingChat(false);
    }
  };

  const handleGenerateReport = async (reportType: string) => {
    if (!store) return;

    setIsGeneratingReport(true);

    try {
      const report = await api.generateReport(store.name, messages, reportType);
      setCurrentReport(report);
    } catch (error) {
      console.error('Failed to generate report:', error);
    } finally {
      setIsGeneratingReport(false);
    }
  };

  return (
    <div className="flex h-screen bg-dark-bg">
      {/* Mobile Menu Button */}
      <button
        onClick={() => setShowSources(!showSources)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-dark-surface rounded-lg border border-dark-border"
      >
        {showSources ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
      </button>

      {/* Source Panel */}
      <div
        className={`${
          showSources ? 'block' : 'hidden'
        } lg:block fixed lg:relative inset-y-0 left-0 z-40`}
      >
        <SourcePanel
          documents={documents}
          onUpload={handleUpload}
          onDelete={handleDeleteDocument}
          uploadProgress={uploadProgress}
        />
      </div>

      {/* Chat Panel */}
      <ChatPanel
        messages={messages}
        onSendMessage={handleSendMessage}
        isLoading={isLoadingChat}
      />

      {/* Studio Panel */}
      <div className="hidden lg:block">
        <StudioPanel
          onGenerateReport={handleGenerateReport}
          currentReport={currentReport}
          isGenerating={isGeneratingReport}
          disabled={messages.length === 0}
        />
      </div>
    </div>
  );
}

export default App;
