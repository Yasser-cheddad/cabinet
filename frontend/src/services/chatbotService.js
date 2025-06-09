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

  // Get messages for a specific conversation
  getMessages: async (conversationId) => {
    try {
      const response = await api.get(`/chatbot/conversations/${conversationId}/messages/`);
      return response.data;
    } catch (error) {
      console.error('Error fetching messages:', error);
      throw error;
    }
  },

  // Send a message in a conversation
  sendMessage: async (conversationId, content) => {
    try {
      const response = await api.post(`/chatbot/conversations/${conversationId}/messages/`, { content });
      return response.data;
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  },

  // Delete a conversation
  deleteConversation: async (conversationId) => {
    try {
      await api.delete(`/chatbot/conversations/${conversationId}/`);
      return true;
    } catch (error) {
      console.error('Error deleting conversation:', error);
      throw error;
    }
  },

  // Update conversation details (title, active status)
  updateConversation: async (conversationId, data) => {
    try {
      const response = await api.patch(`/chatbot/conversations/${conversationId}/`, data);
      return response.data;
    } catch (error) {
      console.error('Error updating conversation:', error);
      throw error;
    }
  },

  // Provide feedback on a bot message
  provideFeedback: async (messageId, helpful) => {
    try {
      const response = await api.post(`/chatbot/messages/${messageId}/feedback/`, { helpful });
      return response.data;
    } catch (error) {
      console.error('Error providing feedback:', error);
      throw error;
    }
  }
};

export default chatbotService;
