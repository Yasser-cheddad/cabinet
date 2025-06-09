import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const NotificationCenter = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isLoading, setIsLoading] = useState(false);

  // Track connection errors to avoid excessive polling when backend is down
  const [connectionError, setConnectionError] = useState(false);

  useEffect(() => {
    // Only fetch if user is logged in
    if (user) {
      fetchNotifications();
    }
    
    // Poll for new notifications - use a longer interval if there are connection issues
    const interval = setInterval(() => {
      if (user) {
        // If we had connection errors, poll less frequently (every 5 minutes)
        // to reduce console errors and network traffic
        if (!connectionError || Date.now() % (5 * 60000) < 60000) {
          fetchNotifications();
        }
      }
    }, connectionError ? 300000 : 60000); // 5 minutes if error, 1 minute otherwise
    
    return () => clearInterval(interval);
  }, [user, connectionError]);

  const fetchNotifications = async () => {
    try {
      setIsLoading(true);
      
      // Add a timeout to the fetch to prevent long hanging requests
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout
      
      const token = localStorage.getItem('accessToken');
      const response = await fetch('/api/notifications/', {
        signal: controller.signal,
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        throw new Error(`Server responded with ${response.status}`);
      }
      
      const data = await response.json();
      
      // Connection successful, reset error state
      setConnectionError(false);
      setNotifications(data);
      setUnreadCount(data.filter(notification => !notification.is_read).length);
    } catch (error) {
      // Only log to console if it's not an abort error (which we triggered)
      if (error.name !== 'AbortError') {
        // Set connection error state to reduce polling frequency
        setConnectionError(true);
        
        // Use a more subtle console message to avoid filling the console
        if (!connectionError) {
          console.warn('Unable to fetch notifications. Will retry later.');
        }
      }
      
      // If we can't connect, just show empty notifications
      if (notifications.length === 0) {
        setNotifications([]);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const markAsRead = async (id) => {
    try {
      // Update local state immediately for better UX
      setNotifications(notifications.map(notification => 
        notification.id === id ? { ...notification, is_read: true } : notification
      ));
      
      setUnreadCount(prev => Math.max(0, prev - 1));
      
      // Then try to update on the server
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 3000);
      
      const token = localStorage.getItem('accessToken');
      await fetch(`/api/notifications/${id}/read/`, {
        method: 'POST',
        signal: controller.signal,
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      clearTimeout(timeoutId);
    } catch (error) {
      // Only log if it's not an abort error
      if (error.name !== 'AbortError' && !connectionError) {
        console.warn('Error marking notification as read. Changes saved locally.');
        setConnectionError(true);
      }
      // Keep the local state change even if the API call fails
    }
  };

  const markAllAsRead = async () => {
    try {
      // Update local state immediately for better UX
      setNotifications(notifications.map(notification => ({ ...notification, is_read: true })));
      setUnreadCount(0);
      
      // Then try to update on the server
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 3000);
      
      await fetch('/api/notifications/read-all/', {
        method: 'POST',
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
    } catch (error) {
      // Only log if it's not an abort error
      if (error.name !== 'AbortError' && !connectionError) {
        console.warn('Error marking all notifications as read. Changes saved locally.');
        setConnectionError(true);
      }
      // Keep the local state change even if the API call fails
    }
  };

  const handleNotificationClick = (notification) => {
    markAsRead(notification.id);
    
    // Navigate based on notification type
    if (notification.type === 'appointment') {
      navigate(`/appointments/${notification.object_id}`);
    } else if (notification.type === 'message') {
      navigate('/messages');
    }
    
    setIsOpen(false);
  };

  const formatTimeAgo = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (diffInSeconds < 60) {
      return 'à l\'instant';
    } else if (diffInSeconds < 3600) {
      const minutes = Math.floor(diffInSeconds / 60);
      return `il y a ${minutes} minute${minutes > 1 ? 's' : ''}`;
    } else if (diffInSeconds < 86400) {
      const hours = Math.floor(diffInSeconds / 3600);
      return `il y a ${hours} heure${hours > 1 ? 's' : ''}`;
    } else {
      const days = Math.floor(diffInSeconds / 86400);
      return `il y a ${days} jour${days > 1 ? 's' : ''}`;
    }
  };

  const getNotificationIcon = (type) => {
    switch (type) {
      case 'appointment':
        return (
          <svg className="h-6 w-6 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        );
      case 'message':
        return (
          <svg className="h-6 w-6 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
        );
      default:
        return (
          <svg className="h-6 w-6 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
        );
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-gray-600 hover:text-gray-900 focus:outline-none"
        aria-label="Notifications"
      >
        <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        
        {unreadCount > 0 && (
          <span className="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white transform translate-x-1/2 -translate-y-1/2 bg-red-600 rounded-full">
            {unreadCount}
          </span>
        )}
      </button>
      
      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-white rounded-md shadow-lg overflow-hidden z-50">
          <div className="py-2 px-3 bg-gray-100 flex justify-between items-center">
            <h3 className="text-sm font-semibold text-gray-700">Notifications</h3>
            {unreadCount > 0 && (
              <button
                onClick={markAllAsRead}
                className="text-xs text-blue-600 hover:text-blue-800"
              >
                Tout marquer comme lu
              </button>
            )}
          </div>
          
          <div className="max-h-96 overflow-y-auto">
            {isLoading ? (
              <div className="flex justify-center items-center py-4">
                <div className="animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-blue-500"></div>
              </div>
            ) : connectionError ? (
              <div className="py-6 text-center text-gray-500">
                <p>Impossible de charger les notifications</p>
                <button 
                  onClick={(e) => {
                    e.stopPropagation();
                    setConnectionError(false);
                    fetchNotifications();
                  }}
                  className="mt-2 text-xs text-blue-600 hover:text-blue-800"
                >
                  Réessayer
                </button>
              </div>
            ) : notifications.length > 0 ? (
              <div>
                {notifications.map(notification => (
                  <div
                    key={notification.id}
                    onClick={() => handleNotificationClick(notification)}
                    className={`flex items-start p-3 border-b border-gray-200 cursor-pointer hover:bg-gray-50 ${!notification.is_read ? 'bg-blue-50' : ''}`}
                  >
                    <div className="flex-shrink-0">
                      {getNotificationIcon(notification.type)}
                    </div>
                    <div className="ml-3 flex-1">
                      <p className={`text-sm ${!notification.is_read ? 'font-semibold' : ''}`}>
                        {notification.message}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        {formatTimeAgo(notification.created_at)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-6 text-center text-gray-500">
                <p>Aucune notification</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationCenter;
