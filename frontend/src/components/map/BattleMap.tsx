"use client";
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

// Fix Leaflet default icons in Next.js
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

interface Army {
  id: string;
  faction: string;
  pos: [number, number];
  strength: number;
  morale: number;
  supply: number;
}

interface BattleMapProps {
  armies: Record<string, Army>;
  center: [number, number];
}

export default function BattleMap({ armies, center }: BattleMapProps) {
  const getFactionColor = (faction: string) =>
    faction.includes("Union") || faction.includes("Allied") || faction.includes("Soviet")
      ? "#3b82f6"
      : "#ef4444";

  const getRadius = (strength: number) => Math.max(8, Math.min(20, strength / 5000));

  return (
    <MapContainer
      center={center}
      zoom={10}
      style={{ width: "100%", height: "100%", minHeight: "450px" }}
      className="rounded-xl border-2 border-gray-700 shadow-2xl bg-gray-900"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      
      {Object.values(armies).map((army) => (
        <CircleMarker
          key={army.id}
          center={[army.pos[1], army.pos[0]]} // Leaflet expects [lat, lng]
          radius={getRadius(army.strength)}
          fillColor={getFactionColor(army.faction)}
          color="#ffffff"
          weight={2}
          opacity={0.9}
          fillOpacity={0.65}
          className="transition-all duration-1000 ease-in-out"
        >
          <Popup closeButton={false} className="!bg-gray-800 !text-white !border-gray-600">
            <div className="text-sm">
              <div className="font-bold text-base mb-1">{army.faction}</div>
              <div>💪 Strength: <span className="font-mono text-white">{Math.round(army.strength).toLocaleString()}</span></div>
              <div>🎯 Morale: <span className="font-mono text-white">{Math.round(army.morale)}%</span></div>
              <div>📦 Supply: <span className="font-mono text-white">{Math.round(army.supply)}%</span></div>
            </div>
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}