import React, { useState } from 'react';
import { FileText, Download, Loader2, ChevronRight } from 'lucide-react';
import type { Report } from '../types';

interface StudioPanelProps {
  onGenerateReport: (reportType: string) => void;
  currentReport: Report | null;
  isGenerating: boolean;
  disabled: boolean;
}

const REPORT_TYPES = [
  {
    id: 'comprehensive',
    label: '概要',
    description: '包括的な分析レポート',
  },
  {
    id: 'summary',
    label: 'サマリー',
    description: 'エグゼクティブサマリー',
  },
  {
    id: 'faq',
    label: 'FAQ',
    description: 'よくある質問',
  },
  {
    id: 'briefing',
    label: 'ブリーフィング',
    description: 'ブリーフィングドキュメント',
  },
];

const StudioPanel: React.FC<StudioPanelProps> = ({
  onGenerateReport,
  currentReport,
  isGenerating,
  disabled,
}) => {
  const [selectedType, setSelectedType] = useState<string>('comprehensive');

  const handleDownload = () => {
    if (!currentReport) return;

    const blob = new Blob([currentReport.content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${currentReport.title.replace(/\s+/g, '_')}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="w-96 bg-dark-surface border-l border-dark-border flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-dark-border">
        <h2 className="text-lg font-semibold text-gray-200">Studio</h2>
      </div>

      {/* Report Types */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-3">
          <p className="text-sm text-gray-400 mb-4">
            チャット履歴とソースからレポートを生成
          </p>

          {REPORT_TYPES.map((type) => (
            <button
              key={type.id}
              onClick={() => {
                setSelectedType(type.id);
                onGenerateReport(type.id);
              }}
              disabled={isGenerating || disabled}
              className="w-full text-left p-3 bg-dark-bg hover:bg-dark-hover border border-dark-border rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed group"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <FileText className="w-4 h-4 text-blue-500 flex-shrink-0" />
                    <span className="text-sm font-medium text-gray-200">
                      {type.label}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500">{type.description}</p>
                </div>
                {isGenerating && selectedType === type.id ? (
                  <Loader2 className="w-4 h-4 text-blue-500 animate-spin flex-shrink-0 ml-2" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-gray-600 group-hover:text-gray-400 flex-shrink-0 ml-2" />
                )}
              </div>
            </button>
          ))}
        </div>

        {/* Current Report Preview */}
        {currentReport && !isGenerating && (
          <div className="mt-6 border-t border-dark-border pt-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-gray-300">
                生成されたレポート
              </h3>
              <button
                onClick={handleDownload}
                className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 rounded text-xs text-white transition-colors"
              >
                <Download className="w-3 h-3" />
                ダウンロード
              </button>
            </div>

            <div className="bg-dark-bg border border-dark-border rounded-lg p-4">
              <h4 className="text-sm font-semibold text-gray-200 mb-2">
                {currentReport.title}
              </h4>
              <div className="text-xs text-gray-500 mb-3">
                {new Date(currentReport.generated_at).toLocaleString('ja-JP')}
              </div>
              <div className="max-h-96 overflow-y-auto">
                <div className="markdown-content text-xs">
                  <pre className="whitespace-pre-wrap font-sans">
                    {currentReport.content.substring(0, 500)}
                    {currentReport.content.length > 500 && '...'}
                  </pre>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default StudioPanel;
