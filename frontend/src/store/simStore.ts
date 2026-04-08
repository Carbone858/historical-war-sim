import { create } from 'zustand';

type Army = {
  id: string;
  faction: string;
  pos: [number, number];
  strength: number;
  morale: number;
  supply: number;
  fatigue: number;
};

type SimState = {
  tick: number;
  isHypothetical: boolean;
  armies: Record<string, Army>;
  isPlaying: boolean;
  connect: (id: string) => void;
  sendAction: (action: string, payload?: any) => void;
  ws: WebSocket | null;
};

let ws: WebSocket | null = null;

export const useSimStore = create<SimState>((set) => ({
  tick: 0,
  isHypothetical: false,
  armies: {},
  isPlaying: false,
  ws: null,
  
  connect: (battleId: string) => {
    // Close existing connection
    if (ws) ws.close();
    
    // Get WebSocket URL from environment or use default
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
    
    // Create new WebSocket connection
    ws = new WebSocket(`${wsUrl}/ws/sim/${battleId}`);
    
    // Handle incoming messages
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        set({
          tick: data.tick,
          isHypothetical: data.is_hypothetical,
          armies: data.armies,
          isPlaying: true
        });
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    };
    
    // Handle connection close
    ws.onclose = () => {
      set({ isPlaying: false });
    };
    
    // Handle connection error
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  },
  
  sendAction: (action: string, payload: any = {}) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action, ...payload }));
    }
  }
}));