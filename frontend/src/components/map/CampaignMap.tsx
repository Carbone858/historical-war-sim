"use client";
import React, { useMemo } from 'react';
import Map from 'react-map-gl/maplibre';
import DeckGL from '@deck.gl/react';
import { ScatterplotLayer, IconLayer, LineLayer } from '@deck.gl/layers';
import 'maplibre-gl/dist/maplibre-gl.css';

interface CampaignMapProps {
  nodes: any[];
  units: any[];
  campaignId: string;
  onNodeClick: (node: any) => void;
}

export default function CampaignMap({ nodes, units, campaignId, onNodeClick }: CampaignMapProps) {
  
  const initialViewState = {
    longitude: -77.2,
    latitude: 39.5,
    zoom: 7,
    pitch: 0,
    bearing: 0
  };

  // Convert GeoJSON units/nodes into Deck.gl format
  const nodeData = useMemo(() => nodes.map(n => ({
    position: [n.geo.coordinates[0], n.geo.coordinates[1]],
    name: n.name,
    type: n.node_type,
    color: n.control_faction === 'Union' ? [30, 60, 150] : [120, 30, 30]
  })), [nodes]);

  const unitData = useMemo(() => units.map(u => ({
    position: [u.geo.coordinates[0], u.geo.coordinates[1]],
    name: u.name,
    faction: u.faction,
    state: u.state,
    color: u.faction === 'Union' ? [60, 130, 246] : [239, 68, 68]
  })), [units]);

  const layers = [
    // Nodes (Cities/Forts)
    new ScatterplotLayer({
      id: 'nodes-layer',
      data: nodeData,
      getPosition: (d: any) => d.position,
      getFillColor: (d: any) => d.color,
      getRadius: (d: any) => d.type === 'Field' ? 1000 : 3000,
      pickable: true,
      opacity: 0.8,
      stroked: true,
      getLineColor: [255, 255, 255],
      lineWidthMinPixels: 1
    }),
    // Units (Army Markers)
    new ScatterplotLayer({
      id: 'strategic-units-layer',
      data: unitData,
      getPosition: (d: any) => d.position,
      getFillColor: (d: any) => d.color,
      getRadius: 5000,
      pickable: true,
      opacity: 1,
      stroked: true,
      getLineColor: [255, 255, 255],
      lineWidthMinPixels: 2
    })
  ];

  return (
    <div className="w-full h-full relative">
      <DeckGL
        initialViewState={initialViewState}
        controller={true}
        layers={layers}
        getTooltip={({object}) => object && `${object.name} (${object.faction || object.type})`}
        onClick={({object}) => {
          if (object && object.type) {
            // It's a node (City/Fort/Field)
            onNodeClick(object);
          }
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
