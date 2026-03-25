import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Send, User, Bot, BookCopy, Loader2 } from 'lucide-react';

interface Message {
  role: 'user' | 'ai';
  content: string;
  sources?: string[];
}

const QAView = () => {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'ai', content: '您好！我是 IND 智慧助手。您可以向我提问关于药学注册资料的任何问题，我会结合已索引的文档为您提供准确的解答。' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await axios.post('http://localhost:8000/api/chat', {
        query: userMessage,
        top_k: 3
      });

      setMessages(prev => [...prev, { 
        role: 'ai', 
        content: response.data.answer,
        sources: response.data.sources
      }]);
    } catch (error) {
      console.error('Q&A Error:', error);
      setMessages(prev => [...prev, { 
        role: 'ai', 
        content: '抱歉，系统处理您的提问时出现了错误，请稍后再试。' 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="qa-view-container fade-in">
      <div className="chat-history">
        {messages.map((msg, i) => (
          <div key={i} className={`message-wrapper ${msg.role}`}>
            <div className="flex items-center gap-2 mb-1 px-2">
              {msg.role === 'user' ? (
                <>
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">User</span>
                  <User size={12} className="text-slate-500" />
                </>
              ) : (
                <>
                  <Bot size={12} className="text-indigo-400" />
                  <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest">IND AI Assistant</span>
                </>
              )}
            </div>
            
            <div className="message-bubble">
              {msg.content}
            </div>

            {msg.sources && msg.sources.length > 0 && (
              <div className="sources-panel">
                <div className="flex items-center gap-2 text-[10px] text-slate-500 mb-2 uppercase tracking-tighter">
                  <BookCopy size={10} /> 知识来源参考
                </div>
                <div className="flex flex-wrap gap-1">
                  {msg.sources.map((s, si) => (
                    <span key={si} className="source-item">
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
        {isLoading && (
          <div className="message-wrapper ai">
            <div className="message-bubble flex items-center gap-3">
              <Loader2 size={16} className="animate-spin text-indigo-400" />
              <span className="text-slate-400">正在检索知识库并生成回答...</span>
            </div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      <div className="chat-input-area">
        <div className="input-box-wrapper">
          <input 
            type="text" 
            className="qa-input"
            placeholder="输入您的问题，如：TQB2858 的临床研究进展如何？"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          />
          <button 
            className="qa-send-btn"
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
          >
            <Send size={20} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default QAView;
