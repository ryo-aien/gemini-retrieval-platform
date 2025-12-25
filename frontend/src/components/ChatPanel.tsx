import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2 } from 'lucide-react';
import type { ChatMessage } from '../types';
import CitationDisplay from './CitationDisplay';

interface ChatPanelProps {
  messages: ChatMessage[];
  onSendMessage: (message: string) => void;
  isLoading: boolean;
}

const ChatPanel: React.FC<ChatPanelProps> = ({
  messages,
  onSendMessage,
  isLoading,
}) => {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSendMessage(input.trim());
      setInput('');
      if (textareaRef.current) {
        textareaRef.current.style.height = '32px';
      }
    }
  };

  // Enterキーでの送信を無効化（送信ボタンのみで送信可能）
  // const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
  //   if (e.key === 'Enter' && !e.shiftKey) {
  //     e.preventDefault();
  //     handleSubmit(e);
  //   }
  // };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    // Auto-resize textarea with max height
    e.target.style.height = 'auto';
    const newHeight = Math.min(e.target.scrollHeight, 120);
    e.target.style.height = `${newHeight}px`;
  };

  return (
    <div className="flex-1 flex flex-col bg-dark-bg h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b border-dark-border">
        <h2 className="text-lg font-semibold text-gray-200">チャット</h2>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {messages.length === 0 && (
          <div className="flex items-center justify-center h-full text-center">
            <div>
              <h3 className="text-xl font-semibold text-gray-300 mb-2">
                ドキュメントについて質問してください
              </h3>
              <p className="text-sm text-gray-500 max-w-md">
                アップロードしたソースに基づいて、AIが質問に回答します
              </p>
            </div>
          </div>
        )}

        <div className="space-y-6 max-w-4xl mx-auto">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex gap-4 ${
                message.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              <div
                className={`flex-1 max-w-3xl ${
                  message.role === 'user' ? 'flex flex-col items-end' : ''
                }`}
              >
                <div
                  className={`rounded-lg px-4 py-3 ${
                    message.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-dark-surface text-gray-200'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{message.content}</p>
                </div>

                {message.role === 'model' && message.citations && (
                  <CitationDisplay citations={message.citations} />
                )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex gap-4">
              <div className="flex-1 max-w-3xl">
                <div className="rounded-lg px-4 py-3 bg-dark-surface">
                  <Loader2 className="w-5 h-5 text-gray-400 animate-spin" />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="px-6 py-6">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
          <div className="relative bg-gray-800 rounded-full border border-gray-700 flex items-center px-6 py-3 shadow-lg">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={handleInputChange}
              placeholder="入力を開始します..."
              disabled={isLoading}
              rows={1}
              className="flex-1 bg-transparent text-gray-200 placeholder-gray-500 focus:outline-none resize-none overflow-hidden"
              style={{
                minHeight: '32px',
                maxHeight: '120px'
              }}
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="flex-shrink-0 w-12 h-12 bg-white hover:bg-gray-100 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-full flex items-center justify-center transition-colors ml-3 shadow-md"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 text-gray-800 animate-spin" />
              ) : (
                <Send className="w-5 h-5 text-gray-800" />
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ChatPanel;
