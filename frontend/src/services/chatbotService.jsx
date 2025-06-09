import api from './api.jsx';

const chatbotService = {
  // Get all conversations for the current user
  getConversations: async () => {
    try {
      const response = await api.get('/chatbot/conversations/');
      return response.data;
    } catch (error) {
      console.error('Error fetching conversations:', error);
      throw error;
    }
  },

  // Create a new conversation
  createConversation: async (title, initialMessage) => {
    try {
      const response = await api.post('/chatbot/conversations/', {
        title: title || 'Nouvelle conversation',
        initial_message: initialMessage
      });
      return response.data;
    } catch (error) {
      console.error('Error creating conversation:', error);
      throw error;
    }
  },

  // Get a specific conversation by ID
  getConversation: async (conversationId) => {
    try {
      const response = await api.get(`/chatbot/conversations/${conversationId}/`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching conversation ${conversationId}:`, error);
      throw error;
    }
  },

  // Send a message to a conversation
  sendMessage: async (conversationId, message) => {
    try {
      const response = await api.post(`/chatbot/conversations/${conversationId}/messages/`, {
        content: message
      });
      return response.data;
    } catch (error) {
      console.error(`Error sending message to conversation ${conversationId}:`, error);
      throw error;
    }
  },

  // Delete a conversation
  deleteConversation: async (conversationId) => {
    try {
      await api.delete(`/chatbot/conversations/${conversationId}/`);
      return true;
    } catch (error) {
      console.error(`Error deleting conversation ${conversationId}:`, error);
      throw error;
    }
  }
};

export default chatbotService;
