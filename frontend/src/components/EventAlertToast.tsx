/**
 * Event Alert Toast Component
 * 
 * Toast notifications for significant market events
 * - Price movements
 * - Volume spikes
 * - Breaking news
 * - AI analysis updates
 */

import React, { useEffect, useState } from 'react';
import { useMarketEvents } from '../hooks/useWebSocket';
import { X, TrendingUp, TrendingDown, Volume2, Newspaper, Brain } from 'lucide-react';

interface Toast {
  id: string;
  type: string;
  ticker: string;
  message: string;
  severity: string;
  timestamp: Date;
}

export const EventAlertToast: React.FC = () => {
  const { events } = useMarketEvents();
  const [toasts, setToasts] = useState<Toast[]>([]);

  useEffect(() => {
    if (events.length > 0) {
      const latestEvent = events[events.length - 1];
      
      // Create toast from event
      const toast: Toast = {
        id: `${latestEvent.ticker}-${Date.now()}`,
        type: latestEvent.event_type || 'unknown',
        ticker: latestEvent.ticker || 'MARKET',
        message: formatEventMessage(latestEvent),
        severity: latestEvent.data?.severity || 'medium',
        timestamp: new Date(),
      };
      
      setToasts(prev => [...prev, toast]);
      
      // Auto-dismiss after 5 seconds
      setTimeout(() => {
        setToasts(prev => prev.filter(t => t.id !== toast.id));
      }, 5000);
    }
  }, [events]);

  const formatEventMessage = (event: any): string => {
    const type = event.event_type;
    const data = event.data || {};
    
    switch (type) {
      case 'price_move':
        const direction = data.direction === 'up' ? 'up' : 'down';
        const pct = Math.abs(data.pct_change * 100).toFixed(2);
        return `${event.ticker} moved ${direction} ${pct}%`;
      
      case 'volume_spike':
        const ratio = data.spike_ratio?.toFixed(1) || '?';
        return `${event.ticker} volume spike: ${ratio}x average`;
      
      case 'breaking_news':
        return data.title || 'Breaking market news';
      
      case 'ai_analysis':
        return `AI analysis updated for ${event.ticker}`;
      
      default:
        return `Market event: ${event.ticker}`;
    }
  };

  const getIcon = (type: string) => {
    switch (type) {
      case 'price_move':
        return <TrendingUp className="w-5 h-5" />;
      case 'volume_spike':
        return <Volume2 className="w-5 h-5" />;
      case 'breaking_news':
        return <Newspaper className="w-5 h-5" />;
      case 'ai_analysis':
        return <Brain className="w-5 h-5" />;
      default:
        return <TrendingUp className="w-5 h-5" />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-600 text-white';
      case 'high':
        return 'bg-orange-500 text-white';
      case 'medium':
        return 'bg-blue-500 text-white';
      case 'low':
        return 'bg-gray-600 text-white';
      default:
        return 'bg-gray-600 text-white';
    }
  };

  const dismissToast = (id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  };

  if (toasts.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2 max-w-sm">
      {toasts.map(toast => (
        <div
          key={toast.id}
          className={`
            ${getSeverityColor(toast.severity)}
            rounded-lg shadow-lg p-4 
            animate-slide-in-right
            flex items-start gap-3
          `}
        >
          <div className="flex-shrink-0 mt-0.5">
            {getIcon(toast.type)}
          </div>
          
          <div className="flex-1 min-w-0">
            <div className="font-semibold text-sm mb-1">
              {toast.ticker}
            </div>
            <div className="text-sm opacity-90">
              {toast.message}
            </div>
            <div className="text-xs opacity-75 mt-1">
              {toast.timestamp.toLocaleTimeString()}
            </div>
          </div>
          
          <button
            onClick={() => dismissToast(toast.id)}
            className="flex-shrink-0 hover:opacity-75 transition-opacity"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      ))}

      <style>{`
        @keyframes slide-in-right {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
        
        .animate-slide-in-right {
          animation: slide-in-right 0.3s ease-out;
        }
      `}</style>
    </div>
  );
};
