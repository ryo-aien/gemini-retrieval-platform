import React, { useState } from 'react';
import { ChevronDown, ChevronUp, FileText } from 'lucide-react';
import type { Citation } from '../types';

interface CitationDisplayProps {
  citations: Citation[];
}

const CitationDisplay: React.FC<CitationDisplayProps> = ({ citations }) => {
  const [expanded, setExpanded] = useState(false);

  if (citations.length === 0) {
    return null;
  }

  const getDocumentName = (fullName: string) => {
    const parts = fullName.split('/');
    return parts[parts.length - 1] || fullName;
  };

  const uniqueDocuments = Array.from(
    new Set(citations.map((c) => c.document_name))
  );

  return (
    <div className="mt-2 border border-dark-border rounded-lg overflow-hidden bg-dark-surface">
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-3 py-2 hover:bg-dark-hover transition-colors"
      >
        <div className="flex items-center gap-2 text-sm">
          <FileText className="w-4 h-4 text-gray-500" />
          <span className="text-gray-400">
            {citations.length}個のソース
          </span>
        </div>
        {expanded ? (
          <ChevronUp className="w-4 h-4 text-gray-500" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-500" />
        )}
      </button>

      {/* Expanded Content */}
      {expanded && (
        <div className="border-t border-dark-border">
          {/* Document List */}
          <div className="p-3 space-y-3">
            {uniqueDocuments.map((docName, index) => {
              const docCitations = citations.filter(
                (c) => c.document_name === docName
              );
              const avgScore =
                docCitations.reduce((sum, c) => sum + c.score, 0) /
                docCitations.length;

              return (
                <div
                  key={index}
                  className="bg-dark-bg rounded-lg p-3 border border-dark-border"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      <FileText className="w-4 h-4 text-blue-500 flex-shrink-0" />
                      <span className="text-sm font-medium text-gray-300 truncate">
                        {getDocumentName(docName)}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-gray-500 flex-shrink-0 ml-2">
                      <span className="bg-dark-surface px-2 py-0.5 rounded">
                        関連度: {(avgScore * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>

                  {/* Citations for this document */}
                  <div className="space-y-2">
                    {docCitations.map((citation, citIndex) => (
                      <div
                        key={citIndex}
                        className="text-sm text-gray-400 pl-6 border-l-2 border-gray-700"
                      >
                        <p className="line-clamp-3">{citation.text}</p>
                        <div className="flex items-center gap-2 mt-1 text-xs text-gray-600">
                          <span>チャンク: {citation.chunk_id.slice(-8)}</span>
                          <span>•</span>
                          <span>スコア: {(citation.score * 100).toFixed(1)}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default CitationDisplay;
