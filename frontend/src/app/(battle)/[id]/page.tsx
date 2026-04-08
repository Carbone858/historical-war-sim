import { useEffect, useState, useMemo } from "react";
import { useParams } from "next/navigation";
import dynamic from "next/dynamic";
import { Howl } from "howler";

const BattleMap = dynamic(() => import("@/components/map/BattleMap"), {
  ssr: false,
  loading: () => <div className="w-full h-full min-h-[500px] flex items-center justify-center bg-gray-900 border-2 border-gray-700 rounded-xl">Loading 3D Map...</div>
});

export default function DynamicBattlePage() {
  const { id } = useParams() as { id: string };
  const [manifest, setManifest] = useState<any>(null);
  const [armies, setArmies] = useState<Record<string, any>>({});
  const [tick, setTick] = useState(0);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [validation, setValidation] = useState<any>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [whatIfResult, setWhatIfResult] = useState<any>(null);
  const [reinfOffset, setReinfOffset] = useState(0);
  const [weather, setWeather] = useState<any>({ state: 'Clear' });

  // Sound triggers
  const sounds = useMemo(() => ({
    gunfire: new Howl({ src: ['https://actions.google.com/sounds/v1/weapons/musket_fire.ogg'], volume: 0.1 }),
    explosion: new Howl({ src: ['https://actions.google.com/sounds/v1/weapons/cannon_fire.ogg'], volume: 0.2 }),
  }), []);

  useEffect(() => {
    // Load manifest
    fetch(`http://localhost:8000/api/battles/${id}/manifest`)
      .then(r => r.json())
      .then(setManifest)
      .catch(err => console.error("Manifest load error:", err));

    // Connect to WebSocket
    const socket = new WebSocket(`ws://localhost:8000/ws/sim/${id}`);
    socket.onopen = () => console.log("✅ Connected to simulation");
    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.tick) setTick(data.tick);
        
        // Handle nested state from engine.get_state()
        if (data.armies) {
          const simState = data.armies;
          if (simState.units) setArmies(simState.units);
          if (simState.weather) setWeather(simState.weather);
          
          if (simState.events) {
            simState.events.forEach((ev: any) => {
              if (ev.type === 'COMBAT_FIRE') {
                if (ev.unit_type === 'Artillery') sounds.explosion.play();
                else sounds.gunfire.play();
              }
            });
          }
        }
        
        if (data.validation) setValidation(data.validation);
      } catch (e) {
        console.error("Parse error:", e);
      }
    };
    socket.onerror = (err) => console.error("WebSocket error:", err);
    setWs(socket);
    
    return () => socket.close();
  }, [id]);

  const sendAction = (action: string) => {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action }));
    }
  };

  const runWhatIf = async () => {
    setIsAnalyzing(true);
    setWhatIfResult(null);
    try {
      const scenario = {
        num_runs: 50,
        reinforcements: [
          {
            tick: 12 + reinfOffset, 
            faction: "Confederate",
            commander: "Gen. Ewell (Reinforcement)",
            strength: 8000,
            pos: [-77.23, 39.84] 
          }
        ]
      };
      
      const res = await fetch(`http://localhost:8000/api/battles/${id}/what-if`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(scenario)
      });
      const data = await res.json();
      setWhatIfResult(data);
    } catch (e) {
      console.error("What-If failed:", e);
    } finally {
      setIsAnalyzing(false);
    }
  };

  if (!manifest) {
    return (
      <div className="min-h-screen bg-gray-950 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="text-2xl mb-4">⏳ Loading Historical Data...</div>
          <div className="text-gray-400">Battle ID: {id}</div>
        </div>
      </div>
    );
  }

  const armyArray = Object.values(armies);

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6 font-['Inter']">
      {/* Header */}
      <header className="mb-8 flex justify-between items-end border-b border-gray-800 pb-6">
        <div>
          <div className="text-blue-500 font-bold tracking-widest text-xs mb-1">HISTORICAL BATTLE SIMULATION</div>
          <h1 className="text-5xl font-black italic tracking-tighter">{manifest.name}</h1>
          <p className="text-gray-500 font-medium">July 1-3, {manifest.year} • Gettysburg, Pennsylvania</p>
        </div>
        <div className="flex gap-4 items-center">
          <div className="text-right">
             <div className="text-xs text-gray-500 uppercase font-bold tracking-widest">Simulation Time</div>
             <div className="text-3xl font-mono leading-none">+{tick}h <span className="text-gray-600 text-lg">/ 72h</span></div>
          </div>
          <div className="flex gap-2 bg-gray-900 p-2 rounded-lg border border-gray-800 shadow-inner">
            <button onClick={() => sendAction("resume")} className="bg-green-600 hover:bg-green-500 text-white font-bold py-3 px-6 rounded-md transition-all active:scale-95 shadow-lg shadow-green-900/20">
              DEPLOY
            </button>
            <button onClick={() => sendAction("pause")} className="bg-gray-800 hover:bg-gray-700 text-white font-bold py-3 px-6 rounded-md transition-all active:scale-95">
              HALT
            </button>
          </div>
        </div>
      </header>

      {/* Accuracy Dashboard (Phase 2.5 Validation Mode) */}
      {validation && (
        <div className="grid grid-cols-3 gap-6 mb-8">
           <div className="col-span-1 bg-gray-900/50 border border-blue-500/30 rounded-xl p-5 shadow-2xl backdrop-blur-sm">
              <div className="flex justify-between items-start mb-4">
                 <h2 className="text-blue-400 font-bold text-sm tracking-widest uppercase">Historical Fidelity</h2>
                 <span className="bg-blue-500/20 text-blue-400 text-[10px] px-2 py-0.5 rounded font-black">VALIDATION ACTIVE</span>
              </div>
              <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-xs text-gray-500 mb-1">
                      <span>UNION CASUALTIES</span>
                      <span className={validation.union.delta_percent > 0 ? 'text-red-400' : 'text-green-400'}>
                        {validation.union.delta_percent > 0 ? '+' : ''}{validation.union.delta_percent}% HISTORICAL
                      </span>
                    </div>
                    <div className="flex items-end gap-2">
                       <span className="text-3xl font-mono leading-none">{validation.union.actual.toLocaleString()}</span>
                       <span className="text-gray-600 text-xs mb-1">vs {validation.union.historical.toLocaleString()} REAL</span>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-xs text-gray-500 mb-1">
                      <span>CONFEDERATE CASUALTIES</span>
                      <span className={validation.confederate.delta_percent > 0 ? 'text-red-400' : 'text-green-400'}>
                        {validation.confederate.delta_percent > 0 ? '+' : ''}{validation.confederate.delta_percent}% HISTORICAL
                      </span>
                    </div>
                    <div className="flex items-end gap-2">
                       <span className="text-3xl font-mono leading-none">{validation.confederate.actual.toLocaleString()}</span>
                       <span className="text-gray-600 text-xs mb-1">vs {validation.confederate.historical.toLocaleString()} REAL</span>
                    </div>
                  </div>
              </div>
           </div>

           <div className="col-span-2 bg-gradient-to-br from-gray-900 to-gray-950 border border-gray-800 rounded-xl p-5 relative overflow-hidden flex flex-col justify-center">
              {isAnalyzing ? (
                <div className="flex flex-col items-center justify-center space-y-4 py-4">
                  <div className="w-12 h-12 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin" />
                  <div className="text-gray-400 font-bold text-[10px] tracking-widest animate-pulse">RUNNING 50 MONTE CARLO SIMULATIONS...</div>
                </div>
              ) : whatIfResult ? (
                <div className="grid grid-cols-2 gap-8 items-center">
                  <div className="text-center border-r border-gray-800 pr-8">
                     <div className="text-gray-500 text-[10px] font-bold tracking-widest uppercase mb-1">Projected Victory</div>
                     <div className="text-4xl font-black text-blue-400">{whatIfResult.probabilities.union_victory}%</div>
                     <div className="text-[10px] text-gray-600 mt-1 uppercase">Union Prob.</div>
                  </div>
                  <div>
                    <div className="text-gray-500 text-[10px] font-bold tracking-widest uppercase mb-2">Scenario Conclusion</div>
                    <p className="text-sm text-gray-300 italic line-clamp-2">
                       "Average casualty projections favor {whatIfResult.probabilities.union_victory > 50 ? 'Union' : 'Confederate'} victory with a {Math.round(whatIfResult.probabilities.union_victory > 50 ? whatIfResult.probabilities.union_victory : whatIfResult.probabilities.confederate_victory)}% confidence interval."
                    </p>
                    <button onClick={() => setWhatIfResult(null)} className="mt-4 text-[10px] font-bold text-gray-600 hover:text-gray-400 uppercase tracking-widest">Reset Analysis</button>
                  </div>
                </div>
              ) : (
                <div className="flex justify-between items-center w-full">
                  <div className="max-w-xs">
                     <div className="text-gray-500 text-[10px] font-bold tracking-widest uppercase mb-2">Scenario Analysis Console</div>
                     <h3 className="text-lg font-bold mb-1">What-If: Early Reinforcements</h3>
                     <p className="text-xs text-gray-600">Adjust the timing of Lee's reinforcements to project strategic shifts.</p>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="flex flex-col items-center">
                       <span className="text-[10px] text-gray-500 font-bold mb-1">{reinfOffset > 0 ? '+' : ''}{reinfOffset}h</span>
                       <input 
                         type="range" min="-12" max="12" step="1" 
                         value={reinfOffset} onChange={(e) => setReinfOffset(parseInt(e.target.value))}
                         className="w-32 accent-blue-500 hover:accent-blue-400 cursor-pointer"
                       />
                    </div>
                    <button 
                      onClick={runWhatIf}
                      className="bg-blue-600 hover:bg-blue-500 text-white text-[10px] font-black px-6 py-3 rounded uppercase tracking-widest shadow-lg shadow-blue-500/20 active:scale-95 transition-all"
                    >
                      Process Prediction
                    </button>
                  </div>
                </div>
              )}
           </div>
        </div>
      )}

      <div className="grid grid-cols-12 gap-8">
        {/* Left: OOB / Army Structure */}
        <aside className="col-span-4 space-y-4">
          <div className="text-xs font-bold tracking-widest text-gray-500 uppercase mb-2">Order of Battle</div>
          <div className="space-y-3 max-h-[1000px] overflow-y-auto pr-2 custom-scrollbar">
            {armyArray.map((army: any) => (
              <div key={army.id} className="bg-gray-900/40 border border-gray-800 hover:border-gray-700 rounded-xl p-4 transition-all">
                <div className="flex justify-between items-center mb-3">
                  <div className={`text-sm font-black uppercase tracking-widest ${army.faction.includes("Union") ? "text-blue-500" : "text-red-500"}`}>
                    {army.unit_type || "Regiment"}
                  </div>
                  <div className="text-[10px] bg-gray-800 text-gray-400 px-2 py-0.5 rounded uppercase font-bold">{army.state}</div>
                </div>
                <h3 className="text-lg font-bold leading-tight mb-1">{army.name}</h3>
                <div className="text-xs text-gray-500 mb-4 line-clamp-1 italic">Under {army.commander}</div>
                
                <div className="grid grid-cols-3 gap-2 text-center border-t border-gray-800 pt-3">
                  <div>
                    <div className="text-[10px] text-gray-600 font-bold mb-0.5 uppercase">Force</div>
                    <div className="text-sm font-mono">{Math.round(army.strength).toLocaleString()}</div>
                  </div>
                  <div>
                    <div className="text-[10px] text-gray-600 font-bold mb-0.5 uppercase">Morale</div>
                    <div className="text-sm font-mono">{Math.round(army.morale)}%</div>
                  </div>
                  <div>
                    <div className="text-[10px] text-gray-600 font-bold mb-0.5 uppercase">Fatigue</div>
                    <div className="text-sm font-mono">{Math.round(army.fatigue)}%</div>
                  </div>
                </div>

                <div className="mt-4 h-1.5 w-full bg-gray-800 rounded-full overflow-hidden">
                   <div 
                     className={`h-full transition-all duration-1000 ${army.faction.includes("Union") ? "bg-blue-600" : "bg-red-600"}`}
                     style={{ width: `${(army.strength / (manifest.id === 'a1b2c3d4-1111-4444-aaaa-000000000001' ? 26000 : 5000)) * 100}%` }}
                   />
                </div>
              </div>
            ))}
          </div>
        </aside>

        {/* Right: Immersive 3D View */}
        <main className="col-span-8 flex flex-col gap-6">
          <div className="flex-1 min-h-[600px] relative rounded-xl overflow-hidden border border-gray-800 shadow-2xl">
            {/* Weather Overlay Layer */}
            {weather.state === 'Rain' && (
              <div className="absolute inset-0 pointer-events-none z-20 bg-blue-900/10 animate-pulse" />
            )}
            {weather.state === 'Fog' && (
              <div className="absolute inset-0 pointer-events-none z-20 bg-gray-500/20 backdrop-blur-[1px]" />
            )}
            
            <div className="absolute top-4 left-4 z-30 bg-black/60 backdrop-blur-md px-3 py-1.5 rounded-full border border-gray-700 flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${weather.state === 'Clear' ? 'bg-green-400' : 'bg-blue-400 animate-pulse'}`} />
              <span className="text-[10px] font-black uppercase tracking-tighter">MET: {weather.state} {weather.intensity > 0 ? `(${Math.round(weather.intensity * 100)}%)` : ''}</span>
            </div>

            <div className="absolute top-4 right-4 z-10 bg-gray-950/80 p-3 rounded-lg border border-gray-800 backdrop-blur-md text-[10px] font-bold tracking-widest text-gray-400 uppercase">
               Tactical Visualization Active
            </div>
            <BattleMap armies={armies} center={[manifest.map_bounds.east || -77.218, manifest.map_bounds.north || 39.824]} />
          </div>

          <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-4 text-[11px] leading-relaxed text-gray-500">
             <strong className="text-gray-400 uppercase tracking-tighter mr-2">Intelligence Source:</strong> 
             Historical data synchronized from SRTM-3 GeoTIFF and National Park Service Army Returns. Simulation resolution set to regiment-level with high-ground line-of-sight occlusion enabled.
          </div>
        </main>
      </div>
    </div>
  );
}