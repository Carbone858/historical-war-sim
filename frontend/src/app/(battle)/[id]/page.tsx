"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

export default function DynamicBattlePage() {
  const { id } = useParams() as { id: string };
  const [manifest, setManifest] = useState<any>(null);
  const [armies, setArmies] = useState<Record<string, any>>({});
  const [tick, setTick] = useState(0);
  const [ws, setWs] = useState<WebSocket | null>(null);

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
        setTick(data.tick);
        setArmies(data.armies || {});
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
    <div className="min-h-screen bg-gray-950 text-white p-6">
      {/* Header */}
      <header className="mb-6 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">{manifest.name}</h1>
          <p className="text-gray-400">{manifest.year} • Tick {tick} / {manifest.duration_hours}</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => sendAction("resume")} className="bg-green-700 hover:bg-green-600 px-4 py-2 rounded">
            ▶ Play
          </button>
          <button onClick={() => sendAction("pause")} className="bg-yellow-700 hover:bg-yellow-600 px-4 py-2 rounded">
            ⏸ Pause
          </button>
        </div>
      </header>

      {/* Army Stats */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        {armyArray.map((army: any) => (
          <div key={army.id} className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className={`text-xl font-bold mb-2 ${army.faction.includes("Union") ? "text-blue-400" : "text-red-400"}`}>
              {army.faction}
            </div>
            <div className="text-sm text-gray-400">Commander: {army.commander || "Unknown"}</div>
            <div className="mt-2 space-y-1">
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Strength:</span>
                <span className="font-mono">{Math.round(army.strength).toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Morale:</span>
                <span className="font-mono">{Math.round(army.morale)}%</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Supply:</span>
                <span className="font-mono">{Math.round(army.supply)}%</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Info */}
      <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700 text-sm">
        <div className="flex justify-between py-1">
          <span className="text-gray-400">Source:</span>
          <span className="text-blue-400">National Park Service ✓</span>
        </div>
        <div className="flex justify-between py-1">
          <span className="text-gray-400">Verified:</span>
          <span className={manifest.is_verified ? "text-green-400" : "text-yellow-400"}>
            {manifest.is_verified ? "Yes" : "No"}
          </span>
        </div>
      </div>
    </div>
  );
}