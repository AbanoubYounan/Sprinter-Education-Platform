// pages/chat.js
'use client';
/* eslint-disable  @typescript-eslint/no-explicit-any */
import { useEffect, useState } from 'react';
import axios from 'axios';
export default function ChatPage() {
  const [sessions, setSessions] = useState<any>([]);
  const [selectedSession, setSelectedSession] = useState<any>(null);
  const [messages, setMessages] = useState<any>([]);
  const [messageInput, setMessageInput] = useState<any>('');
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    const token = localStorage.getItem('token');
    try {
        setIsLoading(true)    
        const res = await axios.get('https://sprinter-back.mes-design.com/api/chat', {
        headers: { Authorization: token },
        });
        setSessions(res.data.sessions);
    } catch (error) {
        console.error('Error fetching sessions:', error);
    } finally {
        setIsLoading(false)
    }
  };

  const startNewSession = () => {
    setSelectedSession(null);
    setMessages([]);
  };

  const fetchMessages = async (sessionId: any) => {
    const token = localStorage.getItem('token');
    try {
        setIsLoading(true)
        const res = await axios.get(`https://sprinter-back.mes-design.com/api/chat/${sessionId}`, {
        headers: { Authorization: token },
        });
        setSelectedSession(res.data.data.session_id);
        setMessages(res.data.data.messages);
    } catch (error) {
        console.error('Error fetching messages:', error);
    } finally {
        setIsLoading(false)
    }
  };

  const sendMessage = async () => {
    if (!messageInput) return;
    const token = localStorage.getItem('token');
    const formData = new FormData();
    formData.append('Message', messageInput);
    if (selectedSession) formData.append('SessionID', selectedSession);
    if(pdfFile) formData.append('uploaded_file', pdfFile)

    try {
        setIsLoading(true)
        const res = await axios.post('https://sprinter-back.mes-design.com/api/chat', formData, {
        headers: {
            Authorization: token,
        },
        });

        const newMessage = {
            user_message: messageInput,
            ai_response: res.data.Response,
            timestamp: new Date().toISOString(),
        };

        setMessages((prev:any) => [...prev, newMessage]);

        if (!selectedSession) {
        setSessions((prev:any) => [...prev, {
            session_ID: res.data.SessionID,
            title: res.data.SessionTitle,
        }]);
        setSelectedSession(res.data.SessionID);
        }

        setMessageInput('');
    } catch (error) {
        console.error('Error sending message:', error);
    } finally {
        setIsLoading(false)
    }
  };

  return (
    <div className="flex h-[92vh]">
      {/* Sidebar */}
      <div className="w-1/4 bg-gray-100 p-4 overflow-y-auto">
        <h2 className="text-xl font-bold mb-4">Sessions</h2>
        <button
          onClick={startNewSession}
          className="w-full mb-4 p-2 bg-green-500 text-white rounded hover:bg-green-600 cursor-pointer"
        >
          + New Chat
        </button>
        { isLoading && <p className='text-sm text-gray-600'>Loading...</p> }
        {sessions.map((s: any) => (
          <div
            key={s.session_ID}
            className={`p-2 rounded cursor-pointer ${selectedSession === s.session_ID ? 'bg-blue-200' : 'hover:bg-blue-100'}`}
            onClick={() => fetchMessages(s.session_ID)}
          >
            {s.title}
          </div>
        ))}
      </div>

      {/* Chat Area */}
      <div className="flex flex-col w-3/4 p-4">
        <div className="flex-1 overflow-y-auto p-4 rounded bg-white">
          {messages.map((m: any, index: any) => (
            <div key={index} className="mb-4">
              <p className="font-semibold">You:</p>
              <p className="mb-2">{m.user_message}</p>
              <p className="font-semibold">Sprinter:</p>
              <p className="bg-gray-100 p-2 rounded">{m.ai_response}</p>
              <p className="text-xs text-gray-500">{new Date(m.timestamp).toLocaleString()}</p>
            </div>
          ))}
          {isLoading && <p className='text-sm text-gray-600'>Loading Chat...</p>}
        </div>

        {/* Message Input */}
        <div className="mt-4 flex flex-col gap-2 items-start">
          <div className="flex w-full gap-2">
            <input
              type="text"
              value={messageInput}
              onChange={(e) => setMessageInput(e.target.value)}
              placeholder="Type your message..."
              className="flex-1 border p-2 rounded"
            />
            <label className="bg-gray-200 px-4 py-2 rounded cursor-pointer hover:bg-gray-300">
              Attach PDF
              <input
                type="file"
                accept="application/pdf"
                onChange={(e) => {
                  if (e.target.files && e.target.files.length > 0) {
                    setPdfFile(e.target.files[0]);
                  }
                }}
                className="hidden"
              />
            </label>
            <button
              onClick={sendMessage}
              className="bg-blue-600 text-white px-4 py-2 rounded"
              disabled={isLoading}
            >
              {isLoading ? 'Sending...' : 'Send'}
            </button>
          </div>
          {pdfFile && (
            <div className="text-sm text-gray-700 mt-1">
              📎 Attached: {pdfFile.name}
              <button onClick={() => setPdfFile(null)} className="ml-2 text-red-500 hover:underline">
                Remove
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}