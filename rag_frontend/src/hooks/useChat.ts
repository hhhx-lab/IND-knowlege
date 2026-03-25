import { useState, useCallback } from 'react';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: string[];
  isLoading?: boolean;
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isTyping, setIsTyping] = useState(false);

  const sendMessage = useCallback(async (query: string) => {
    if (!query.trim()) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: query,
    };

    const aiMsgPlaceholder: ChatMessage = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '',
      isLoading: true,
    };

    setMessages((prev) => [...prev, userMsg, aiMsgPlaceholder]);
    setIsTyping(true);

    try {
      const res = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, top_k: 3 }),
      });

      if (!res.ok) {
        throw new Error('Network response was not ok');
      }

      const data = await res.json();
      
      setMessages((prev) => 
        prev.map((msg) => 
          msg.id === aiMsgPlaceholder.id 
            ? { ...msg, content: data.answer, sources: data.sources, isLoading: false } 
            : msg
        )
      );
    } catch (error) {
      console.error("Chat Error:", error);
      setMessages((prev) => 
        prev.map((msg) => 
          msg.id === aiMsgPlaceholder.id 
            ? { ...msg, content: '抱歉，检索服务暂时不可用，请稍后再试。', isLoading: false } 
            : msg
        )
      );
    } finally {
      setIsTyping(false);
    }
  }, []);

  return { messages, isTyping, sendMessage };
}
