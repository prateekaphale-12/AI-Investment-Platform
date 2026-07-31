/**
 * Live Price Card Component
 * 
 * Displays real-time price updates with animated changes
 * - Live price ticker
 * - Animated price changes
 * - Visual indicators (up/down)
 * - Connection status
 */

import React, { useEffect, useState } from 'react';
import { useLivePrice } from '../hooks/useWebSocket';
import { TrendingUp, TrendingDown, Minus, Wifi, WifiOff } from 'lucide-react';

interface LivePriceCardProps {
  ticker: string;
  companyName?: string;
  showConnectionStatus?: boolean;
}

export const LivePriceCard: React.FC<LivePriceCardProps> = ({
  ticker,
  companyName,
  showConnectionStatus = false,
}) => {
  const { price, change, changePercent, isLive } = useLivePrice(ticker);
  const [isAnimating, setIsAnimating] = useState(false);
  const [priceDirection, setPriceDirection] = useState<'up' | 'down' | 'neutral'>('neutral');

  useEffect(() => {
    if (change !== 0) {
      setIsAnimating(true);
      setPriceDirection(change > 0 ? 'up' : change < 0 ? 'down' : 'neutral');
      
      const timer = setTimeout(() => setIsAnimating(false), 1000);
      return () => clearTimeout(timer);
    }
  }, [change]);

  const formatPrice = (value: number | null) => {
    if (value === null) return '--';
    return value.toFixed(2);
  };

  const formatChange = (value: number) => {
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}`;
  };

  const formatChangePercent = (value: number) => {
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
  };

  const getPriceColor = () => {
    if (priceDirection === 'up') return 'text-green-600';
    if (priceDirection === 'down') return 'text-red-600';
    return 'text-gray-900';
  };

  const getBackgroundColor = () => {
    if (!isAnimating) return 'bg-white';
    if (priceDirection === 'up') return 'bg-green-50';
    if (priceDirection === 'down') return 'bg-red-50';
    return 'bg-white';
  };

  const getTrendIcon = () => {
    if (priceDirection === 'up') return <TrendingUp className="w-4 h-4" />;
    if (priceDirection === 'down') return <TrendingDown className="w-4 h-4" />;
    return <Minus className="w-4 h-4" />;
  };

  return (
    <div
      className={`
        p-4 rounded-lg border transition-all duration-300
        ${getBackgroundColor()}
        ${isAnimating ? 'shadow-lg scale-105' : 'shadow'}
      `}
    >
      <div className="flex items-start justify-between mb-2">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-bold text-gray-900">{ticker}</h3>
            {showConnectionStatus && (
              <div className="flex items-center gap-1">
                {isLive ? (
                  <>
                    <Wifi className="w-3 h-3 text-green-500" />
                    <span className="text-xs text-green-600">Live</span>
                  </>
                ) : (
                  <>
                    <WifiOff className="w-3 h-3 text-gray-400" />
                    <span className="text-xs text-gray-500">Offline</span>
                  </>
                )}
              </div>
            )}
          </div>
          {companyName && (
            <p className="text-sm text-gray-600">{companyName}</p>
          )}
        </div>
        <div className={`flex items-center gap-1 ${getPriceColor()}`}>
          {getTrendIcon()}
        </div>
      </div>

      <div className="space-y-1">
        <div className={`text-3xl font-bold ${getPriceColor()} transition-colors duration-300`}>
          ${formatPrice(price)}
        </div>
        
        {price !== null && (
          <div className="flex items-center gap-2 text-sm">
            <span className={getPriceColor()}>
              {formatChange(change)}
            </span>
            <span className={`${getPriceColor()} font-medium`}>
              ({formatChangePercent(changePercent)})
            </span>
          </div>
        )}
      </div>

      {isLive && (
        <div className="mt-2 flex items-center gap-1">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          <span className="text-xs text-gray-500">Real-time updates</span>
        </div>
      )}
    </div>
  );
};
