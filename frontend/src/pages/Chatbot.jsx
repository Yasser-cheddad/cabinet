import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api.jsx';
import chatbotService from '../services/chatbotService.jsx';
import { FiSend, FiPlus, FiTrash2, FiLoader } from 'react-icons/fi';

const Chatbot = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [conversations, setConversations] = useState([]);
  const [activeConversation, setActiveConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingConversations, setLoadingConversations] = useState(true);
  const messagesEndRef = useRef(null);

  // Fetch conversations on component mount
  useEffect(() => {
    fetchConversations();
  }, []);

  // Scroll to bottom of messages when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Fetch messages when active conversation changes
  useEffect(() => {
    if (activeConversation) {
      fetchMessages(activeConversation.id);
    }
  }, [activeConversation]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchConversations = async () => {
    try {
      setLoadingConversations(true);
      const response = await api.get('/chatbot/conversations/');
      setConversations(response.data);
      
      // Set active conversation to the most recent one if it exists
      if (response.data.length > 0 && !activeConversation) {
        setActiveConversation(response.data[0]);
      }
    } catch (error) {
      console.error('Error fetching conversations:', error);
    } finally {
      setLoadingConversations(false);
    }
  };

  const fetchMessages = async (conversationId) => {
    try {
      setLoading(true);
      const response = await api.get(`/chatbot/conversations/${conversationId}/messages/`);
      setMessages(response.data);
    } catch (error) {
      console.error('Error fetching messages:', error);
    } finally {
      setLoading(false);
    }
  };

  const createNewConversation = async () => {
    try {
      setLoading(true);
      const response = await api.post('/chatbot/conversations/create/', {
        title: 'Nouvelle conversation',
        initial_message: 'Bienvenue au service de chat du Cabinet Médical. Comment puis-je vous aider aujourd\'hui?'
      });
      
      // Add new conversation to the list and set it as active
      setConversations([response.data, ...conversations]);
      setActiveConversation(response.data);
      
      // Clear messages for the new conversation
      setMessages([]);
    } catch (error) {
      console.error('Error creating conversation:', error);
    } finally {
      setLoading(false);
    }
  };

  const deleteConversation = async (id) => {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer cette conversation?')) {
      return;
    }
    
    try {
      await api.delete(`/chatbot/conversations/${id}/delete/`);
      
      // Remove conversation from list
      const updatedConversations = conversations.filter(conv => conv.id !== id);
      setConversations(updatedConversations);
      
      // If the active conversation was deleted, set a new active conversation
      if (activeConversation && activeConversation.id === id) {
        if (updatedConversations.length > 0) {
          setActiveConversation(updatedConversations[0]);
        } else {
          setActiveConversation(null);
          setMessages([]);
        }
      }
    } catch (error) {
      console.error('Error deleting conversation:', error);
    }
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    
    if (!newMessage.trim() || !activeConversation) {
      return;
    }
    
    // Create a new conversation if none exists
    if (!activeConversation) {
      await createNewConversation();
    }
    
    const messageContent = newMessage;
    setNewMessage('');
    
    // Optimistically add user message to UI
    const tempUserMessage = {
      id: 'temp-' + Date.now(),
      message_type: 'user',
      content: messageContent,
      timestamp: new Date().toISOString(),
      is_read: true
    };
    
    setMessages(prev => [...prev, tempUserMessage]);
    
    try {
      // Add loading message
      const tempBotMessage = {
        id: 'temp-bot-' + Date.now(),
        message_type: 'bot',
        content: '...',
        timestamp: new Date().toISOString(),
        is_read: true,
        isLoading: true
      };
      
      setMessages(prev => [...prev, tempBotMessage]);
      
      // Send message to API
      const response = await api.post(`/chatbot/conversations/${activeConversation.id}/messages/send/`, {
        content: messageContent
      });
      
      // Remove loading message and add actual response
      setMessages(prev => 
        prev
          .filter(msg => !msg.isLoading)
          .concat([response.data.user_message, response.data.bot_message])
      );
      
      // Update conversation list to show latest message
      fetchConversations();
    } catch (error) {
      console.error('Error sending message:', error);
      // Remove loading message on error
      setMessages(prev => prev.filter(msg => !msg.isLoading));
    }
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('fr-FR', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: false 
    });
  };

  const formatConversationDate = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  return (
    <div className="flex flex-col h-full">
      <h1 className="text-2xl font-bold mb-4">Assistant Médical</h1>
      
      <div className="flex flex-1 bg-white rounded-lg shadow overflow-hidden">
        {/* Sidebar with conversations */}
        <div className="w-64 bg-gray-50 border-r border-gray-200 flex flex-col">
          <div className="p-4 border-b border-gray-200">
            <button
              onClick={createNewConversation}
              className="w-full flex items-center justify-center gap-2 bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 transition-colors"
              disabled={loading}
            >
              <FiPlus /> Nouvelle conversation
            </button>
          </div>
          
          <div className="flex-1 overflow-y-auto">
            {loadingConversations ? (
              <div className="flex justify-center items-center h-32">
                <FiLoader className="animate-spin text-blue-600 text-xl" />
              </div>
            ) : conversations.length === 0 ? (
              <div className="text-center text-gray-500 p-4">
                Aucune conversation. Commencez-en une nouvelle!
              </div>
            ) : (
              <ul className="divide-y divide-gray-200">
                {conversations.map(conversation => (
                  <li key={conversation.id} className="relative">
                    <button
                      onClick={() => setActiveConversation(conversation)}
                      className={`w-full text-left p-4 hover:bg-gray-100 transition-colors ${
                        activeConversation?.id === conversation.id ? 'bg-blue-50' : ''
                      }`}
                    >
                      <div className="font-medium truncate">{conversation.title}</div>
                      <div className="text-xs text-gray-500">
                        {formatConversationDate(conversation.updated_at)}
                      </div>
                      {conversation.last_message && (
                        <div className="text-sm text-gray-600 truncate mt-1">
                          {conversation.last_message}
                        </div>
                      )}
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteConversation(conversation.id);
                      }}
                      className="absolute right-2 top-2 text-gray-400 hover:text-red-500 p-2"
                      title="Supprimer la conversation"
                    >
                      <FiTrash2 size={16} />
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
        
        {/* Chat area */}
        <div className="flex-1 flex flex-col">
          {activeConversation ? (
            <>
              {/* Chat header */}
              <div className="p-4 border-b border-gray-200">
                <h2 className="font-semibold">{activeConversation.title}</h2>
              </div>
              
              {/* Messages */}
              <div className="flex-1 p-4 overflow-y-auto bg-gray-50">
                {messages.length === 0 ? (
                  <div className="flex items-center justify-center h-full text-gray-500">
                    {loading ? (
                      <FiLoader className="animate-spin text-blue-600 text-xl" />
                    ) : (
                      "Commencez à discuter avec l'assistant médical"
                    )}
                  </div>
                ) : (
                  <div className="space-y-4">
                    {messages.map(message => (
                      <div
                        key={message.id}
                        className={`flex ${
                          message.message_type === 'user' ? 'justify-end' : 'justify-start'
                        }`}
                      >
                        <div
                          className={`max-w-[80%] rounded-lg px-4 py-2 ${
                            message.message_type === 'user'
                              ? 'bg-blue-600 text-white'
                              : message.isLoading
                              ? 'bg-gray-200 text-gray-600 animate-pulse'
                              : 'bg-white border border-gray-200 text-gray-800'
                          }`}
                        >
                          {message.isLoading ? (
                            <div className="flex items-center space-x-1">
                              <div className="w-2 h-2 bg-gray-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                              <div className="w-2 h-2 bg-gray-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                              <div className="w-2 h-2 bg-gray-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                            </div>
                          ) : (
                            <>
                              <div className="whitespace-pre-wrap">{message.content}</div>
                              <div className="text-xs opacity-70 text-right mt-1">
                                {formatTimestamp(message.timestamp)}
                              </div>
                            </>
                          )}
                        </div>
                      </div>
                    ))}
                    <div ref={messagesEndRef} />
                  </div>
                )}
              </div>
              
              {/* Message input */}
              <div className="p-4 border-t border-gray-200">
                <form onSubmit={sendMessage} className="flex gap-2">
                  <input
                    type="text"
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    placeholder="Tapez votre message ici..."
                    className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    disabled={loading}
                  />
                  <button
                    type="submit"
                    className="bg-blue-600 text-white p-2 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                    disabled={!newMessage.trim() || loading}
                  >
                    <FiSend size={20} />
                  </button>
                </form>
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-500">
              {loadingConversations ? (
                <FiLoader className="animate-spin text-blue-600 text-xl" />
              ) : (
                <div className="text-center p-4">
                  <p className="mb-4">Aucune conversation active</p>
                  <button
                    onClick={createNewConversation}
                    className="bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 transition-colors"
                  >
                    Démarrer une nouvelle conversation
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Chatbot;
