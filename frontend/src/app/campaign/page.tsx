"use client";

import { useEffect, useState, useMemo } from 'react';
import dynamic from 'next/dynamic';

const CampaignMap = dynamic(() => import('@/components/map/CampaignMap'), {
  ssr: false,
  loading: () => <div className="w-full h-full min-h-[500px] flex items-center justify-center bg-gray-950 border border-gray-800 rounded-2xl">Loading Strategic Map...</div>
});

import { useRouter } from 'next/navigation';
import StrategyConsole from '@/components/ui/StrategyConsole';

export default function CampaignDashboard() {
  const router = useRouter();
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [selectedCampaign, setSelectedCampaign] = useState<any>(null);
  const [state, setState] = useState<any>(null);
  const [isTransitioning, setIsTransitioning] = useState(false);

  useEffect(() => {
    fetch('http://localhost:8000/api/campaigns')
      .then(r => r.json())
      .then(data => {
        setCampaigns(data);
        if (data.length > 0) setSelectedCampaign(data[0]);
      });
  }, []);

  useEffect(() => {
    if (selectedCampaign) {
      fetch(`http://localhost:8000/api/campaigns/${selectedCampaign.id}/state`)
        .then(r => r.json())
        .then(setState);
    }
  }, [selectedCampaign]);

  const advanceTime = async () => {
    if (!selectedCampaign) return;
    await fetch(`http://localhost:8000/api/campaigns/${selectedCampaign.id}/advance`, { method: 'POST' });
    // Refresh state
    const res = await fetch(`http://localhost:8000/api/campaigns/${selectedCampaign.id}/state`);
    setState(await res.json());
  };

  const handleNodeClick = async (node: any) => {
    setIsTransitioning(true);
    try {
      // 1. Initialize tactical battle from strategic state
      const res = await fetch(`http://localhost:8000/api/campaigns/${selectedCampaign.id}/node/${node.id}/initialize-tactical`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ wikidata_id: 'Q162601' }) // Antietam fallback
      });
      
      if (res.ok) {
        // 2. Transition to Phase 4 Tactical View
        router.push(`/${node.id}`);
      }
    } catch (err) {
      console.error("Transition failed:", err);
      setIsTransitioning(false);
    }
  };

  if (!selectedCampaign || !state) return <div className="p-20 text-center text-gray-500">Initializing Campaign...</div>;

  return (
    <div className="min-h-screen bg-gray-950 text-white font-['Inter'] p-8">
      <header className="flex justify-between items-center mb-10 border-b border-gray-900 pb-8">
        <div>
          <div className="text-blue-500 font-black tracking-[0.2em] text-[10px] uppercase mb-1">Strategic Campaign Engine</div>
          <h1 className="text-4xl font-black italic tracking-tighter uppercase">{selectedCampaign.name}</h1>
          <div className="text-gray-500 font-mono text-sm mt-1">
            Current Date: {new Date(state.campaign.current_sim_date).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
          </div>
        </div>
        
        <div className="flex gap-4">
          <button 
            onClick={advanceTime}
            className="bg-blue-600 hover:bg-blue-500 text-white px-8 py-3 rounded-lg font-black uppercase text-xs tracking-widest shadow-lg shadow-blue-500/20 active:scale-95 transition-all"
          >
            Advance 6h
          </button>
        </div>
      </header>

      <div className="grid grid-cols-12 gap-8 h-[850px]">
        <aside className="col-span-3 space-y-6 overflow-y-auto pr-4 custom-scrollbar">
          <StrategyConsole campaignId={selectedCampaign.id} onRefresh={() => {}} />

          <div className="bg-gray-900/40 border border-gray-800 rounded-2xl p-6">
            <h2 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-6">Strategic Assets</h2>
            <div className="space-y-4">
              {state.units.map((unit: any) => (
                <div key={unit.id} className="border-l-2 border-blue-500 pl-4 py-1">
                   <div className="text-[10px] text-gray-500 font-bold uppercase">{unit.faction} {unit.state}</div>
                   <div className="font-bold text-sm tracking-tight">{unit.name}</div>
                   <div className="flex gap-4 mt-2 text-[10px] text-gray-400 font-mono">
                      <span>STR: {Math.round(unit.strength)}</span>
                      <span>SUP: {Math.round(unit.supply)}%</span>
                   </div>
                </div>
              ))}
            </div>
          </div>
          
          <div className="bg-gray-900/40 border border-gray-800 rounded-2xl p-6">
            <h2 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-4">Theater Nodes</h2>
            <div className="space-y-2">
              {state.nodes.map((node: any) => (
                <div key={node.id} className="flex justify-between items-center bg-gray-800/20 p-2 rounded cursor-pointer hover:bg-gray-800/40 transition-colors">
                  <span className="text-xs font-medium text-gray-300">{node.name}</span>
                  <span className="text-[10px] px-2 py-0.5 bg-gray-800 rounded text-gray-500 italic">{node.node_type}</span>
                </div>
              ))}
            </div>
          </div>
        </aside>

        <main className="col-span-9 bg-gray-900/20 border border-gray-800 rounded-3xl overflow-hidden relative group">
           {isTransitioning && (
             <div className="absolute inset-0 z-50 bg-black/80 backdrop-blur-2xl flex flex-col items-center justify-center transition-all animate-in fade-in duration-700">
                <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-6"></div>
                <div className="text-xl font-black italic uppercase tracking-widest text-blue-500">Engaging Tactical Engine</div>
                <div className="text-gray-500 font-mono text-xs mt-2 uppercase tracking-tighter">Transferring strategic orders to local divisions...</div>
             </div>
           )}
           <CampaignMap 
              nodes={state.nodes} 
              units={state.units} 
              campaignId={selectedCampaign.id}
              onNodeClick={handleNodeClick}
           />
           
           <div className="absolute bottom-6 left-6 right-6 z-10 bg-black/60 backdrop-blur-xl border border-gray-800 p-4 rounded-2xl flex justify-between items-center shadow-2xl">
              <div className="flex gap-10">
                <div>
                   <div className="text-[9px] font-black text-gray-600 uppercase tracking-widest mb-1">Forces Engaged</div>
                   <div className="text-xl font-bold tracking-tighter italic">24,300 Units</div>
                </div>
                <div>
                   <div className="text-[9px] font-black text-gray-600 uppercase tracking-widest mb-1">Combat Theaters</div>
                   <div className="text-xl font-bold tracking-tighter italic">03 Active</div>
                </div>
              </div>
              
              <div className="text-[10px] font-bold text-gray-500 uppercase tracking-tighter">
                Historical Context: Maryland Campaign 1862
              </div>
           </div>
        </main>
      </div>
    </div>
  );
}
