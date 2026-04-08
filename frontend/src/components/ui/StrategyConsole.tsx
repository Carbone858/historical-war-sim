"use client";

import React, { useState, useEffect } from 'react';

interface StrategyConsoleProps {
  campaignId: string;
  onRefresh: () => void;
}

export default function StrategyConsole({ campaignId, onRefresh }: StrategyConsoleProps) {
  const [insights, setInsights] = useState<any>(null);
  const [events, setEvents] = useState<any[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [insightsRes, eventsRes] = await Promise.all([
          fetch(`http://localhost:8000/api/campaigns/${campaignId}/ai-insights`),
          fetch(`http://localhost:8000/api/campaigns/${campaignId}/events`)
        ]);
        setInsights(await insightsRes.json());
        setEvents(await eventsRes.json());
      } catch (err) {
        console.error("Failed to fetch strategic data:", err);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, [campaignId]);

  return (
    <div className="flex flex-col gap-6">
      {/* AI AI Strategy Advisor Section */}
      <div className="bg-blue-900/10 border border-blue-500/30 rounded-2xl p-6 relative overflow-hidden">
        <div className="absolute top-0 right-0 p-4 opacity-10">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>
        </div>
        
        <div className="flex items-center gap-2 mb-4">
          <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
          <h2 className="text-xs font-black text-blue-500 uppercase tracking-widest">AI Strategic Advisor</h2>
        </div>

        {insights ? (
          <div className="space-y-4">
            <div className="flex justify-between items-end">
              <div>
                <div className="text-[10px] text-gray-500 font-bold uppercase mb-1">Global Front Victory Probability</div>
                <div className="text-4xl font-black italic tracking-tighter text-white">
                  {(insights.prediction.victory_prob * 100).toFixed(0)}%
                </div>
              </div>
              <div className="text-right">
                <div className="text-[10px] text-gray-500 font-bold uppercase mb-1">Estimated Attrition</div>
                <div className="text-xl font-bold font-mono text-red-400">
                  +{(insights.prediction.est_casualty_rate * 100).toFixed(1)}%
                </div>
              </div>
            </div>

            <div className="w-full bg-gray-800 h-1.5 rounded-full overflow-hidden">
              <div 
                className="bg-blue-500 h-full transition-all duration-1000" 
                style={{ width: `${insights.prediction.victory_prob * 100}%` }}
              ></div>
            </div>

            <div className="pt-4 border-t border-blue-500/20">
              <div className="text-[10px] text-blue-400 font-bold uppercase mb-2">Tactical Recommendations</div>
              {insights.suggestions.length > 0 ? (
                <div className="space-y-2">
                  {insights.suggestions.map((s: any, i: number) => (
                    <div key={i} className="text-xs bg-blue-500/5 p-2 rounded border border-blue-500/10 text-gray-300">
                      <span className="text-blue-500 font-bold">{s.priority} Priority:</span> {s.reason}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-gray-500 italic">No critical reinforcement needed at current positions.</p>
              )}
            </div>
          </div>
        ) : (
          <div className="animate-pulse flex space-y-4 flex-col">
            <div className="h-4 bg-gray-800 rounded w-3/4"></div>
            <div className="h-8 bg-gray-800 rounded w-1/2"></div>
          </div>
        )}
      </div>

      {/* Global Event Log Section */}
      <div className="bg-gray-900/40 border border-gray-800 rounded-2xl p-6">
        <h2 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-6">Theater Intelligence Log</h2>
        <div className="space-y-4 max-h-[300px] overflow-y-auto pr-2 custom-scrollbar">
          {events.length > 0 ? events.map((event: any) => (
            <div key={event.id} className="group relative pl-4 border-l border-gray-800 hover:border-blue-500 transition-colors">
              <div className="text-[9px] text-gray-600 font-mono mb-1">
                {new Date(event.timestamp).toLocaleTimeString()}
              </div>
              <div className="text-sm font-bold text-gray-300 group-hover:text-white transition-colors">
                {event.name}
              </div>
              <div className="text-[10px] text-gray-500 uppercase tracking-tighter mt-1">
                Effect: {event.effect_data}
              </div>
            </div>
          )) : (
            <div className="text-center py-10">
              <div className="text-gray-700 italic text-xs">Awaiting strategic developments...</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
