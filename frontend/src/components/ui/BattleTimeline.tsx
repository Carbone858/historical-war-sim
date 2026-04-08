"use client";

interface EventLog {
  tick: number;
  type: "movement" | "combat" | "supply" | "morale";
  message: string;
}

export default function BattleTimeline({ events }: { events: EventLog[] }) {
  const getTypeColor = (type: string) => {
    switch (type) {
      case "combat": return "text-red-400 border-red-800 bg-red-900/20";
      case "morale": return "text-yellow-400 border-yellow-800 bg-yellow-900/20";
      case "supply": return "text-green-400 border-green-800 bg-green-900/20";
      default: return "text-blue-400 border-blue-800 bg-blue-900/20";
    }
  };

  return (
    <div className="bg-gray-800/60 backdrop-blur rounded-xl border border-gray-700 p-4 h-full flex flex-col">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-xl">📜</span>
        <h3 className="font-bold text-gray-200">Battle Timeline</h3>
        <span className="ml-auto text-xs bg-gray-700 px-2 py-1 rounded text-gray-400">
          {events.length} events
        </span>
      </div>
      
      <div className="flex-1 overflow-y-auto space-y-2 pr-1 custom-scrollbar">
        {events.map((e, i) => (
          <div key={i} className={`text-xs p-2 rounded border ${getTypeColor(e.type)} font-mono`}>
            <span className="opacity-70">T+{e.tick}h</span> • {e.message}
          </div>
        ))}
        {events.length === 0 && (
          <div className="text-gray-500 text-center py-8 italic">
            Waiting for battle to begin...
          </div>
        )}
      </div>
    </div>
  );
}