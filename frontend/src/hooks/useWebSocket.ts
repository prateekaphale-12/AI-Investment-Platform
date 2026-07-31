/**
 * WebSocket Hook for Real-time Market Data
 * 
 * Provides real-time updates from backend:
 * - Live price updates
 * - Market events
 * - Breaking news
 * - AI analysis results
 * 
 * Features:
 * - Automatic reconnection
 * - Subscription management
 * - Connection status
 * - Error handling
 */

import { useEffect, useRef, useState, useCallback } from 'react';

interface WebSocketMessage {
  type: string;
  channel?: string;
  ticker?: string;
  price?: number;
  data?: any;
  timestamp?: string;
}

interface UseWebSocketOptions {
  url?: string;
  autoConnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  lastMessage: WebSocketMessage | null;
  subscribe: (channels: string[]) => void;
  unsubscribe: (channels: string[]) => void;
  sendMessage: (message: any) => void;
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
}

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const {
    url = (() => {
      // Construct WebSocket URL based on current location
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host; // includes hostname:port
      return `${protocol}//${host}/api/v1/ws/market`;
    })(),
    autoConnect = false, // Changed default to false to prevent errors when WebSocket endpoint doesn't exist
    reconnectInterval = 3000,
    maxReconnectAttempts = 10,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const subscribedChannelsRef = useRef<Set<string>>(new Set());

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setConnectionStatus('connecting');

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setConnectionStatus('connected');
        reconnectAttemptsRef.current = 0;

        // Resubscribe to channels
        if (subscribedChannelsRef.current.size > 0) {
          ws.send(JSON.stringify({
            action: 'subscribe',
            channels: Array.from(subscribedChannelsRef.current),
          }));
        }
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          setLastMessage(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('error');
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        setConnectionStatus('disconnected');
        wsRef.current = null;

        // Attempt reconnection
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          console.log(`Reconnecting... (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      setConnectionStatus('error');
    }
  }, [url, reconnectInterval, maxReconnectAttempts]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setIsConnected(false);
    setConnectionStatus('disconnected');
  }, []);

  const subscribe = useCallback((channels: string[]) => {
    channels.forEach(channel => subscribedChannelsRef.current.add(channel));
    
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'subscribe',
        channels,
      }));
    }
  }, []);

  const unsubscribe = useCallback((channels: string[]) => {
    channels.forEach(channel => subscribedChannelsRef.current.delete(channel));
    
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'unsubscribe',
        channels,
      }));
    }
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  return {
    isConnected,
    lastMessage,
    subscribe,
    unsubscribe,
    sendMessage,
    connectionStatus,
  };
}

/**
 * Hook for live price updates
 */
export function useLivePrice(ticker: string) {
  const { lastMessage, subscribe, unsubscribe, isConnected } = useWebSocket();
  const [price, setPrice] = useState<number | null>(null);
  const [change, setChange] = useState<number>(0);
  const [changePercent, setChangePercent] = useState<number>(0);

  useEffect(() => {
    if (ticker) {
      subscribe([`market:price:${ticker}`]);
      return () => unsubscribe([`market:price:${ticker}`]);
    }
  }, [ticker, subscribe, unsubscribe]);

  useEffect(() => {
    if (lastMessage?.type === 'price' && lastMessage.ticker === ticker) {
      const newPrice = lastMessage.price;
      if (newPrice && price) {
        const diff = newPrice - price;
        const pct = (diff / price) * 100;
        setChange(diff);
        setChangePercent(pct);
      }
      setPrice(newPrice || null);
    }
  }, [lastMessage, ticker, price]);

  return {
    price,
    change,
    changePercent,
    isLive: isConnected && price !== null,
  };
}

/**
 * Hook for market events
 */
export function useMarketEvents() {
  const { lastMessage, subscribe, unsubscribe } = useWebSocket();
  const [events, setEvents] = useState<WebSocketMessage[]>([]);

  useEffect(() => {
    subscribe([
      'events:price_move',
      'events:volume_spike',
      'events:breaking_news',
    ]);
    
    return () => unsubscribe([
      'events:price_move',
      'events:volume_spike',
      'events:breaking_news',
    ]);
  }, [subscribe, unsubscribe]);

  useEffect(() => {
    if (lastMessage?.channel?.startsWith('events:')) {
      setEvents(prev => [...prev.slice(-19), lastMessage]); // Keep last 20 events
    }
  }, [lastMessage]);

  return { events };
}

/**
 * Hook for breaking news
 */
export function useBreakingNews() {
  const { lastMessage, subscribe, unsubscribe } = useWebSocket();
  const [news, setNews] = useState<any[]>([]);

  useEffect(() => {
    subscribe(['market:news:breaking']);
    return () => unsubscribe(['market:news:breaking']);
  }, [subscribe, unsubscribe]);

  useEffect(() => {
    if (lastMessage?.type === 'news') {
      setNews(prev => [lastMessage.data, ...prev.slice(0, 14)]); // Keep last 15
    }
  }, [lastMessage]);

  return { news };
}
