class WebSocketService {
  constructor() {
    this.callbacks = [];
    this.socket = null;
    this.retryCount = 0;
    this.maxRetries = 3;
    this.heartbeatInterval = 30000; // 30 seconds
    this.idleTimeout = 60000; // 60 seconds
    this.lastActivity = null;
    this.heartbeatTimer = null;
    this.idleTimer = null;
    this.tokenRefreshHandler = null;
  }

  getValidToken = async () => {
    let token = localStorage.getItem('access_token');
    
    // Simple check for token expiration (JWT timestamp)
    if (token) {
      const payload = JSON.parse(atob(token.split('.')[1]));
      if (payload.exp * 1000 < Date.now()) {
        console.log('Token expired - attempting refresh');
        if (this.tokenRefreshHandler) {
          token = await this.tokenRefreshHandler();
        }
      }
    }
    
    return token;
  };

  setTokenRefreshHandler = (handler) => {
    this.tokenRefreshHandler = handler;
  };

  connect = async () => {
    try {
      const token = await this.getValidToken();
      if (!token) {
        throw new Error('No valid token available');
      }

      this.socket = new WebSocket(`ws://localhost:8000/ws/notifications/?token=${encodeURIComponent(token)}`);

      this.socket.onopen = () => {
        console.log('WebSocket connected');
        this.retryCount = 0;
        this.startHeartbeat();
        this.resetIdleTimer();
      };

      this.socket.onmessage = (event) => {
        this.resetIdleTimer();
        if (event.data === 'pong') {
          return; // Ignore heartbeat responses
        }
        try {
          const data = JSON.parse(event.data);
          this.callbacks.forEach(callback => callback(data));
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      this.socket.onclose = () => {
        console.log('WebSocket disconnected');
        this.cleanupTimers();
        this.attemptReconnect();
      };

      this.socket.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.cleanupTimers();
      };
    } catch (error) {
      console.error('WebSocket connection error:', error);
      this.attemptReconnect();
    }
  };

  startHeartbeat = () => {
    this.heartbeatTimer = setInterval(() => {
      if (this.socket?.readyState === WebSocket.OPEN) {
        this.socket.send('ping');
      }
    }, this.heartbeatInterval);
  };

  resetIdleTimer = () => {
    this.lastActivity = Date.now();
    if (this.idleTimer) clearTimeout(this.idleTimer);
    this.idleTimer = setTimeout(() => {
      console.log('No notifications received - triggering idle callback');
      this.callbacks.forEach(callback => callback({
        type: 'idle',
        message: 'No notifications received in the last 60 seconds'
      }));
    }, this.idleTimeout);
  };

  cleanupTimers = () => {
    if (this.heartbeatTimer) clearInterval(this.heartbeatTimer);
    if (this.idleTimer) clearTimeout(this.idleTimer);
  };

  attemptReconnect = () => {
    if (this.retryCount < this.maxRetries) {
      this.retryCount++;
      setTimeout(() => {
        console.log(`Attempting to reconnect (${this.retryCount}/${this.maxRetries})`);
        this.connect();
      }, 3000);
    }
  };

  disconnect = () => {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  };

  addCallback = (callback) => {
    this.callbacks.push(callback);
  };

  removeCallback = (callback) => {
    this.callbacks = this.callbacks.filter(cb => cb !== callback);
  };
}

const webSocketService = new WebSocketService();
export { webSocketService };
export default webSocketService;
