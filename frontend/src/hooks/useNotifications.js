import { useEffect, useState, useCallback } from 'react';
import webSocketService from '../services/websocket';
import { useAuth } from '../context/AuthContext';

const useNotifications = () => {
  const [notifications, setNotifications] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const { refreshToken } = useAuth();

  const handleTokenRefresh = useCallback(async () => {
    try {
      const newToken = await refreshToken();
      return newToken;
    } catch (error) {
      console.error('Token refresh failed:', error);
      setConnectionStatus('disconnected');
      return null;
    }
  }, [refreshToken]);

  useEffect(() => {
    // Set up token refresh handler
    webSocketService.setTokenRefreshHandler(handleTokenRefresh);

    const handleNotification = (data) => {
      switch(data.type) {
        case 'notification':
          setNotifications(prev => [data, ...prev]);
          break;
        case 'connection':
          setConnectionStatus('connected');
          break;
        case 'idle':
          setConnectionStatus('idle');
          break;
        case 'token_expired':
          handleTokenRefresh().then(token => {
            if (token) webSocketService.connect();
          });
          break;
        default:
          console.log('Unknown message type:', data.type);
      }
    };

    webSocketService.addCallback(handleNotification);
    webSocketService.connect();

    return () => {
      webSocketService.removeCallback(handleNotification);
      webSocketService.disconnect();
    };
  }, [handleTokenRefresh]);

  const clearNotifications = () => {
    setNotifications([]);
  };

  return { 
    notifications, 
    connectionStatus,
    clearNotifications 
  };
};

export { useNotifications };
export default useNotifications;