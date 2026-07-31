/**
 * Live Ticker Tape Component
 * 
 * Scrolling ticker tape showing live market updates
 * - Continuous scrolling animation
 * - Live price updates
 * - Color-coded changes
 * - Responsive design
 */

import React, { useEffect, useState } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';

interface TickerData {
  ticker: string;
  price: number;
  change: number;
  changePercent: number;
}

interface LiveTickerTapeProps {
  tickers?: string[];
  speed?: number; // pixels per second
}

export const LiveTickerTape: React.FC<LiveTickerTapeProps> = ({
  tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX'],
  speed = 50,
}) => {
  const { lastMessage, subscribe, isConnected } = useWebSocket();
  const [tickerData, setTickerData] = useState<Map<string, TickerData>>(new Map());

  useEffect(() => {
    // Subscribe to all tickers
    const channels = tickers.map(t => `market:price:${t}`);
    subscribe(channels);
  }, [tickers, subscribe]);

  useEffect(() => {
    if (lastMessage?.type === 'price' && lastMessage.ticker) {
      const ticker = lastMessage.ticker;
      const price = lastMessage.price || 0;
      
      setTickerData(prev => {
        const newData = new Map(prev);
        const existing = newData.get(ticker);
        
        const change = existing ? price - existing.price : 0;
        const changePercent = existing && existing.price !== 0 
          ? ((price - existing.price) / existing.price) * 100 
          : 0;
        
        newData.set(ticker, {
          ticker,
          price,
          change,
          changePercent,
        });
        
        return newData;
      });
    }
  }, [lastMessage]);

  const formatPrice = (value: number) => value.toFixed(2);
  const formatChange = (value: number) => {
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
  };

  const getChangeColor = (change: number) => {
    if (change > 0) return 'text-green-600';
    if (change < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  return (
    <div className="bg-gray-900 text-white py-2 overflow-hidden relative">
      {!isConnected && (
        <div className="absolute inset-0 bg-gray-800 bg-opacity-90 flex items-center justify-center z-10">
          <span className="text-sm text-gray-400">Connecting to live data...</span>
        </div>
      )}
      
      <div className="flex animate-scroll-left whitespace-nowrap">
        {/* Duplicate content for seamless loop */}
        {[...Array(2)].map((_, idx) => (
          <div key={idx} className="flex items-center gap-8 px-4">
            {tickers.map(ticker => {
              const data = tickerData.get(ticker);
              
              return (
                <div key={`${ticker}-${idx}`} className="flex items-center gap-3">
                  <span className="font-bold text-sm">{ticker}</span>
                  <span className="text-sm">
                    ${data ? formatPrice(data.price) : '--'}
                  </span>
                  {data && (
                    <span className={`text-sm font-medium ${getChangeColor(data.change)}`}>
                      {formatChange(data.changePercent)}
                    </span>
                  )}
                  <span className="text-gray-600">|</span>
                </div>
              );
            })}
          </div>
        ))}
      </div>

      <style>{`
        @keyframes scroll-left {
          0% {
            transform: translateX(0);
          }
          100% {
            transform: translateX(-50%);
          }
        }
        
        .animate-scroll-left {
          animation: scroll-left ${tickers.length * 2}s linear infinite;
        }
      `}</style>
    </div>
  );
};
