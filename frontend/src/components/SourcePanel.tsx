import React, { useState, useRef } from 'react';
import { Plus, Search, Upload, X, File, Loader2 } from 'lucide-react';
import type { Document, UploadProgress } from '../types';

interface SourcePanelProps {
  documents: Document[];
  onUpload: (files: FileList) => void;
  onDelete: (documentName: string) => void;
  uploadProgress: UploadProgress[];
}

const SourcePanel: React.FC<SourcePanelProps> = ({
  documents,
  onUpload,
  onDelete,
  uploadProgress,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const filteredDocuments = documents.filter((doc) =>
    doc.display_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files.length > 0) {
      onUpload(e.dataTransfer.files);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onUpload(e.target.files);
    }
  };

  const getStateColor = (state: string) => {
    switch (state) {
      case 'STATE_ACTIVE':
        return 'text-green-500';
      case 'STATE_PENDING':
        return 'text-yellow-500';
      case 'STATE_FAILED':
        return 'text-red-500';
      default:
        return 'text-gray-500';
    }
  };

  const getStateIcon = (state: string) => {
    if (state === 'STATE_PENDING') {
      return <Loader2 className="w-3 h-3 animate-spin" />;
    }
    return null;
  };

  const getStateLabel = (state: string) => {
    // Remove STATE_ prefix for display
    return state.replace('STATE_', '');
  };

  return (
    <div className="w-80 bg-dark-surface border-r border-dark-border flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-dark-border">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-gray-200">ソース</h2>
        </div>

        {/* Add Source Button */}
        <button
          onClick={() => fileInputRef.current?.click()}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-dark-hover hover:bg-dark-border rounded-lg text-sm text-gray-300 transition-colors"
        >
          <Plus className="w-4 h-4" />
          ソースを追加
        </button>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.md,.txt"
          onChange={handleFileSelect}
          className="hidden"
        />
      </div>

      {/* Search */}
      <div className="p-4 border-b border-dark-border">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            placeholder="ソースを検索"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-dark-bg border border-dark-border rounded-lg text-sm text-gray-300 placeholder-gray-600 focus:outline-none focus:border-gray-500"
          />
        </div>
      </div>

      {/* Document List */}
      <div
        className={`flex-1 overflow-y-auto ${isDragOver ? 'bg-dark-hover' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {isDragOver && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <Upload className="w-12 h-12 mx-auto mb-2 text-gray-500" />
              <p className="text-sm text-gray-400">ファイルをドロップ</p>
            </div>
          </div>
        )}

        {!isDragOver && (
          <>
            {/* Upload Progress */}
            {uploadProgress.map((progress) => (
              <div
                key={progress.file_id}
                className="px-4 py-3 border-b border-dark-border"
              >
                <div className="flex items-center gap-3">
                  <File className="w-5 h-5 text-gray-500 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-300 truncate">
                      {progress.filename}
                    </p>
                    <div className="mt-1 w-full bg-dark-bg rounded-full h-1.5">
                      <div
                        className="bg-blue-500 h-1.5 rounded-full transition-all"
                        style={{ width: `${progress.progress}%` }}
                      />
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      {progress.status === 'uploading' && 'アップロード中...'}
                      {progress.status === 'processing' && '処理中...'}
                      {progress.status === 'completed' && '完了'}
                      {progress.status === 'failed' && `エラー: ${progress.error}`}
                    </p>
                  </div>
                </div>
              </div>
            ))}

            {/* Document Items */}
            {filteredDocuments.map((doc) => (
              <div
                key={doc.name}
                className="px-4 py-3 border-b border-dark-border hover:bg-dark-hover transition-colors group"
              >
                <div className="flex items-start gap-3">
                  <File className="w-5 h-5 text-gray-500 flex-shrink-0 mt-0.5" />

                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-300 truncate">
                      {doc.display_name}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className={`text-xs font-medium ${getStateColor(doc.state)}`}>
                        {getStateLabel(doc.state)}
                      </span>
                      {getStateIcon(doc.state)}
                      {doc.size_bytes && (
                        <span className="text-xs text-gray-600">
                          {(doc.size_bytes / 1024).toFixed(1)} KB
                        </span>
                      )}
                    </div>
                  </div>

                  <button
                    onClick={() => onDelete(doc.name)}
                    className="opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0"
                  >
                    <X className="w-4 h-4 text-gray-500 hover:text-red-500" />
                  </button>
                </div>
              </div>
            ))}

            {filteredDocuments.length === 0 && uploadProgress.length === 0 && (
              <div className="flex items-center justify-center h-full text-center p-8">
                <div>
                  <File className="w-12 h-12 mx-auto mb-3 text-gray-600" />
                  <p className="text-sm text-gray-500 mb-2">
                    ソースがありません
                  </p>
                  <p className="text-xs text-gray-600">
                    PDF、Markdown、テキストファイルを追加
                  </p>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default SourcePanel;
