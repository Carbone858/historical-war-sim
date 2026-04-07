import { create } from 'zustand';
type SimState = { tick: number; isHypothetical: boolean; armies: Record<string, any>; connect: (id: string) => void; sendAction: (action: string, p?: any) => void; };
let ws: WebSocket | null = null;
export const useSimStore = create<SimState>((set) => ({
  tick: 0, isHypothetical: false, armies: {},
  connect: (id) => {
    if(ws) ws.close();
    ws = new WebSocket(`${process.env.NEXT_PUBLIC_WS_URL}/ws/sim/${id}`);
    ws.onmessage = (e) => set(JSON.parse(e.data));
  },
  sendAction: (action, payload={}) => ws?.send(JSON.stringify({action, ...payload}))
}));
