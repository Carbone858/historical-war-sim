"use client";
import { useEffect } from "react";
import { useParams } from "next/navigation";
import { useSimStore } from "@/store/simStore";
import ReactMapGL, { Marker } from "react-map-gl";

export default function BattlePage() {
  const { id } = useParams() as { id: string };
  const { connect, sendAction, armies, isHypothetical, tick } = useSimStore();
  useEffect(() => { connect(id); }, [id]);
  return (
    <div className="h-screen bg-gray-950 text-white p-4">
      {isHypothetical && <div className="fixed top-4 left-1/2 -translate-x-1/2 bg-amber-600 px-4 py-2 rounded text-sm font-bold">⚠️ HYPOTHETICAL SCENARIO</div>}
      <div className="flex justify-between mb-2">
        <h1 className="text-xl font-bold">Battle: {id}</h1>
        <span className="text-gray-400">Tick: {tick}</span>
      </div>
      <div className="h-[60vh] rounded-xl overflow-hidden border border-gray-800">
        <ReactMapGL mapboxAccessToken={process.env.NEXT_PUBLIC_MAPBOX_TOKEN} initialViewState={{longitude:-77.21, latitude:39.82, zoom:9}} style={{width:"100%",height:"100%"}} mapStyle="mapbox://styles/mapbox/dark-v11">
          {Object.values(armies).map((a:any, i:number)=>(
            <Marker key={i} longitude={a.pos[0]} latitude={a.pos[1]}><div className={`w-8 h-8 rounded-full border-2 flex items-center justify-center text-xs font-bold ${a.faction.includes("Union")?"border-blue-500 bg-blue-700/50":"border-red-500 bg-red-700/50"}`}>{(a.strength/1000).toFixed(0)}k</div></Marker>
          ))}
        </ReactMapGL>
      </div>
      <div className="flex gap-2 mt-4">
        <button onClick={()=>sendAction("resume")} className="bg-green-600 px-4 py-2 rounded">▶ Play</button>
        <button onClick={()=>sendAction("pause")} className="bg-yellow-600 px-4 py-2 rounded">⏸ Pause</button>
        <button onClick={()=>sendAction("whatif_toggle", {enabled:!isHypothetical})} className="bg-purple-600 px-4 py-2 rounded">🔄 What-If</button>
      </div>
    </div>
  );
}
