"use client";
import React, { useMemo, useState, useEffect } from 'react';
import Map from 'react-map-gl/maplibre';
import DeckGL from '@deck.gl/react';
import { ColumnLayer, IconLayer, PointCloudLayer } from '@deck.gl/layers';
import { TerrainLayer } from '@deck.gl/geo-layers';
import 'maplibre-gl/dist/maplibre-gl.css';

const TERRAIN_IMAGE = 'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png';
const SURFACE_IMAGE = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}';

const ELEVATION_DECODER = {
  rScaler: 256,
  gScaler: 1,
  bScaler: 1 / 256,
  offset: -32768
};

interface Regiment {
  id: string;
  name: string;
  faction: string;
  commander: string;
  unit_type: string;
  pos: [number, number];
  strength: number;
  morale: number;
  fatigue: number;
  supply: number;
  formation: string;
  state: string;
  facing: [number, number];
  ammo: number;
}

interface BattleMapProps {
  armies: Record<string, Regiment>;
  center: [number, number];
}

export default function BattleMap({ armies, center }: BattleMapProps) {
  const [vfxSmoke, setVfxSmoke] = useState<any[]>([]);

  const initialViewState = {
    longitude: center[0],
    latitude: center[1],
    zoom: 12.5,
    pitch: 50,
    bearing: 0,
    maxPitch: 85
  };

  const armyData = useMemo(() => Object.values(armies), [armies]);

  // Expansion of Regiments into individual soldier points based on formation
  const soldierData = useMemo(() => {
    const points: any[] = [];
    armyData.forEach(reg => {
      const numPoints = 50; // Visual representation
      const isUnion = reg.faction.includes("Union");
      const [fx, fy] = reg.facing || [1, 0];
      const angle = Math.atan2(fy, fx);
      
      for (let i = 0; i < numPoints; i++) {
        let offsetX = 0;
        let offsetY = 0;
        
        if (reg.formation === "Line") {
          // 2x25 grid
          const row = i % 2;
          const col = Math.floor(i / 2) - 12.5;
          offsetX = col * 0.0001;
          offsetY = row * 0.0001;
        } else if (reg.formation === "Square") {
          // Hollow Square: 12 units per side with gaps
          const side = Math.floor(i / 12);
          const index = i % 12 - 6;
          if (side === 0) { offsetX = index * 0.0001; offsetY = 0.0006; } // North
          else if (side === 1) { offsetX = index * 0.0001; offsetY = -0.0006; } // South
          else if (side === 2) { offsetX = 0.0006; offsetY = index * 0.0001; } // East
          else { offsetX = -0.0006; offsetY = index * 0.0001; } // West
        } else {
          // Column: 10x5
          const row = Math.floor(i / 5) - 5;
          const col = i % 5 - 2.5;
          offsetX = col * 0.0001;
          offsetY = row * 0.0001;
        }
        
        // Rotate by facing
        const rx = offsetX * Math.cos(angle) - offsetY * Math.sin(angle);
        const ry = offsetX * Math.sin(angle) + offsetY * Math.cos(angle);
        
        points.push({
          position: [reg.pos[0] + rx, reg.pos[1] + ry, 2],
          color: isUnion ? [70, 130, 246] : [239, 68, 68],
          id: `${reg.id}_s_${i}`
        });
      }
    });
    return points;
  }, [armies]);

  // Generate simple smoke particles for Engaged units
  useEffect(() => {
    const activeSmoke = armyData
      .filter(a => a.state === "Engaged")
      .map(a => ({
        position: [a.pos[0] + (Math.random() - 0.5) * 0.001, a.pos[1] + (Math.random() - 0.5) * 0.001, 10],
        color: [200, 200, 200, 150],
        size: 5 + Math.random() * 10
      }));
    
    if (activeSmoke.length > 0) {
      setVfxSmoke(prev => [...prev.slice(-100), ...activeSmoke]);
    }
  }, [armies]);

  const layers = [
    new TerrainLayer({
      id: 'terrain',
      minZoom: 0,
      maxZoom: 14,
      strategy: 'no-overlap',
      elevationDecoder: ELEVATION_DECODER,
      elevationData: TERRAIN_IMAGE,
      texture: SURFACE_IMAGE,
      wireframe: false,
      color: [255, 255, 255]
    }),
    // The "Soldiers" - using instanced points in formations
    new PointCloudLayer({
      id: 'soldiers-layer',
      data: soldierData,
      getPosition: (d: any) => d.position,
      getNormal: [0, 0, 1],
      getColor: (d: any) => d.color,
      pointSize: 3,
      pickable: false,
    }),
    // The Regimental Standard / Marker
    new ColumnLayer({
      id: 'regiments-layer',
      data: armyData,
      diskResolution: 20,
      radius: 100, 
      extruded: true,
      pickable: true,
      elevationScale: 1,
      getPosition: (d: Regiment) => [d.pos[0], d.pos[1]],
      getFillColor: (d: Regiment) => {
        const isUnion = d.faction.includes("Union");
        if (d.state === "Routed") return [100, 100, 100, 150] as [number, number, number, number];
        return (isUnion ? [30, 60, 150, 200] : [120, 30, 30, 200]) as [number, number, number, number];
      },
      getElevation: (d: Regiment) => Math.max(20, d.strength / 20),
      getLineColor: [255, 255, 255],
      lineWidthMinPixels: 2,
      transitions: {
        getPosition: 1000,
        getElevation: 1000,
      }
    }),
    // VFX Smoke layer
    new PointCloudLayer({
      id: 'smoke-layer',
      data: vfxSmoke,
      getPosition: (d: any) => d.position,
      getColor: (d: any) => d.color,
      pointSize: 8, // Set to constant for now if types are failing
      opacity: 0.6,
    })
  ];

  return (
    <div className="w-full h-full min-h-[600px] rounded-2xl overflow-hidden border-2 border-gray-800 shadow-2xl relative">
      {/* Legend / Accuracy Overlay could go here */}
      <DeckGL
        initialViewState={initialViewState}
        controller={true}
        layers={layers}
        getTooltip={({object}) => {
          if (!object) return null;
          const reg = object as Regiment;
          return {
            html: `
              <div style="padding: 12px; background: rgba(15, 23, 42, 0.95); color: white; border-radius: 8px; border: 1px solid #334155; font-family: 'Inter', sans-serif; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.5);">
                <div style="font-weight: 800; border-bottom: 1px solid #334155; padding-bottom: 4px; margin-bottom: 8px; color: ${reg.faction.includes('Union') ? '#60a5fa' : '#f87171'}">${reg.name}</div>
                <div style="font-size: 11px; color: #94a3b8; margin-bottom: 4px;">Commander: ${reg.commander}</div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                   <div>
                     <div style="font-size: 10px; color: #64748b;">STRENGTH</div>
                     <div style="font-family: monospace;">${Math.round(reg.strength).toLocaleString()}</div>
                   </div>
                   <div>
                     <div style="font-size: 10px; color: #64748b;">MORALE</div>
                     <div style="font-family: monospace;">${Math.round(reg.morale)}%</div>
                   </div>
                   <div>
                     <div style="font-size: 10px; color: #64748b;">STATE</div>
                     <div style="font-weight: 700; color: ${reg.state === 'Routed' ? '#ef4444' : '#10b981'}">${reg.state}</div>
                   </div>
                   <div>
                     <div style="font-size: 10px; color: #64748b;">FORMATION</div>
                     <div style="font-family: monospace;">${reg.formation}</div>
                   </div>
                </div>
              </div>
            `
          };
        }}
      >
        <Map
          mapStyle="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"
          reuseMaps
        />
      </DeckGL>
    </div>
  );
}