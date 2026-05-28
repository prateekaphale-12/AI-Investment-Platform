/**
 * Market Sentiment Meter Component
 * 
 * Real-time market sentiment visualization
 * - Animated gauge meter
 * - Color-coded sentiment levels
 * - Live updates from WebSocket
 * - Market breadth indicators
 */

import React, { useEffect, useState } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { TrendingUp, TrendingDown, Activity } from 'lucide-react';

interface MarketHealth {
  market_breadth: number; // 0-1, where 0.5 is neutral
  total_tickers: number;
  gainers: number;
  losers: number;
  timestamp: string;
}

export const MarketSentimentMeter: React.FC = () => {
  const { lastMessage, subscribe, isConnected } = useWebSocket();
  const [marketHealth, setMarketHealth] = useState<MarketHealth | null>(null);
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    subscribe(['market:health']);
  }, [subscribe]);

  useEffect(() => {
    if (lastMessage?.channel === 'market:health') {
      setMarketHealth({
        market_breadth: lastMessage.market_breadth || 0.5,
        total_tickers: lastMessage.total_tickers || 0,
        gainers: lastMessage.gainers || 0,
        losers: lastMessage.losers || 0,
        timestamp: lastMessage.timestamp || new Date().toISOString(),
      });
      
      setIsAnimating(true);
      setTimeout(() => setIsAnimating(false), 500);
    }
  }, [lastMessage]);

  const getSentimentLabel = (breadth: number): string => {
    if (breadth >= 0.7) return 'Very Bullish';
    if (breadth >= 0.6) return 'Bullish';
    if (breadth >= 0.4) return 'Neutral';
    if (breadth >= 0.3) return 'Bearish';
    return 'Very Bearish';
  };

  const getSentimentColor = (breadth: number): string => {
    if (breadth >= 0.7) return 'text-green-600';
    if (breadth >= 0.6) return 'text-green-500';
    if (breadth >= 0.4) return 'text-gray-600';
    if (breadth >= 0.3) return 'text-red-500';
    return 'text-red-600';
  };

  const getGaugeColor = (breadth: number): string => {
    if (breadth >= 0.7) return 'bg-green-600';
    if (breadth >= 0.6) return 'bg-green-500';
    if (breadth >= 0.4) return 'bg-gray-500';
    if (breadth >= 0.3) return 'bg-red-500';
    return 'bg-red-600';
  };

  const breadth = marketHealth?.market_breadth || 0.5;
  const gaugeRotation = (breadth - 0.5) * 180; // -90 to +90 degrees

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Market Sentiment</h3>
        {isConnected ? (
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span className="text-xs text-gray-500">Live</span>
          </div>
        ) : (
          <span className="text-xs text-gray-400">Offline</span>
        )}
      </div>

      {/* Gauge Meter */}
      <div className="relative h-32 mb-4">
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="relative w-48 h-24 overflow-hidden">
            {/* Background arc */}
            <div className="absolute bottom-0 left-0 right-0 h-24 border-8 border-gray-200 rounded-t-full" />
            
            {/* Colored segments */}
            <div className="absolute bottom-0 left-0 w-1/5 h-24 border-8 border-red-600 rounded-tl-full opacity-30" />
            <div className="absolute bottom-0 left-1/5 w-1/5 h-24 border-t-8 border-red-400 opacity-30" />
            <div className="absolute bottom-0 left-2/5 w-1/5 h-24 border-t-8 border-gray-400 opacity-30" />
            <div className="absolute bottom-0 left-3/5 w-1/5 h-24 border-t-8 border-green-400 opacity-30" />
            <div className="absolute bottom-0 right-0 w-1/5 h-24 border-8 border-green-600 rounded-tr-full opacity-30" />
            
            {/* Needle */}
            <div
              className={`absolute bottom-0 left-1/2 w-1 h-20 origin-bottom transition-transform duration-500 ${
                isAnimating ? 'scale-110' : ''
              }`}
              style={{ transform: `translateX(-50%) rotate(${gaugeRotation}deg)` }}
            >
              <div className={`w-full h-full ${getGaugeColor(breadth)} rounded-full`} />
              <div className="absolute bottom-0 left-1/2 w-3 h-3 -translate-x-1/2 bg-gray-800 rounded-full" />
            </div>
          </div>
        </div>
      </div>

      {/* Sentiment Label */}
      <div className="text-center mb-4">
        <div className={`text-2xl font-bold ${getSentimentColor(breadth)} transition-colors duration-300`}>
          {getSentimentLabel(breadth)}
        </div>
        <div className="text-sm text-gray-500 mt-1">
          {(breadth * 100).toFixed(0)}% Market Breadth
        </div>
      </div>

      {/* Market Stats */}
      {marketHealth && (
        <div className="grid grid-cols-3 gap-4 pt-4 border-t">
          <div className="text-center">
            <div className="flex items-center justify-center gap-1 text-green-600 mb-1">
              <TrendingUp className="w-4 h-4" />
              <span className="text-lg font-bold">{marketHealth.gainers}</span>
            </div>
            <div className="text-xs text-gray-500">Gainers</div>
          </div>
          
          <div className="text-center">
            <div className="flex items-center justify-center gap-1 text-gray-600 mb-1">
              <Activity className="w-4 h-4" />
              <span className="text-lg font-bold">{marketHealth.total_tickers}</span>
            </div>
            <div className="text-xs text-gray-500">Total</div>
          </div>
          
          <div className="text-center">
            <div className="flex items-center justify-center gap-1 text-red-600 mb-1">
              <TrendingDown className="w-4 h-4" />
              <span className="text-lg font-bold">{marketHealth.losers}</span>
            </div>
            <div className="text-xs text-gray-500">Losers</div>
          </div>
        </div>
      )}

      {!isConnected && (
        <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded text-sm text-yellow-800">
          Waiting for live market data...
        </div>
      )}
    </div>
  );
};
