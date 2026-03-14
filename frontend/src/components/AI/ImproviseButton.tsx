"use client";

import { useState } from "react";
import { api } from "@/lib/api";

interface ImproviseButtonProps {
  text: string;
  context: { role?: string; company?: string; section_type?: string };
  onResult: (text: string) => void;
}

export default function ImproviseButton({ text, context, onResult }: ImproviseButtonProps) {
  const [loading, setLoading] = useState(false);
  const [showAlternatives, setShowAlternatives] = useState(false);
  const [alternatives, setAlternatives] = useState<string[]>([]);
  const [previousText, setPreviousText] = useState<string | null>(null);

  const handleImprovise = async () => {
    if (!text.trim() || loading) return;
    setLoading(true);
    setPreviousText(text);
    try {
      const result = await api.improvise({ text, context });
      onResult(result.improved_text);
      setAlternatives(result.alternatives);
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
  };

  const handleUndo = () => {
    if (previousText !== null) {
      onResult(previousText);
      setPreviousText(null);
      setAlternatives([]);
    }
  };

  return (
    <div className="relative flex items-center gap-1">
      <button
        onClick={handleImprovise}
        disabled={loading || !text.trim()}
        className="text-xs px-2 py-0.5 bg-purple-100 text-purple-700 rounded hover:bg-purple-200 disabled:opacity-50 whitespace-nowrap"
        title="AI Improvise"
      >
        {loading ? "..." : "Improvise"}
      </button>
      {previousText !== null && (
        <button
          onClick={handleUndo}
          className="text-xs text-gray-700 hover:text-gray-900"
          title="Undo"
        >
          ↩
        </button>
      )}
      {alternatives.length > 0 && (
        <button
          onClick={() => setShowAlternatives(!showAlternatives)}
          className="text-xs text-gray-700 hover:text-gray-900"
          title="Show alternatives"
        >
          ▾
        </button>
      )}
      {showAlternatives && alternatives.length > 0 && (
        <div className="absolute top-full right-0 mt-1 w-64 bg-white border border-gray-200 rounded-lg shadow-lg z-20 p-2">
          <p className="text-xs text-gray-700 mb-1">Alternatives:</p>
          {alternatives.map((alt, i) => (
            <button
              key={i}
              onClick={() => {
                onResult(alt);
                setShowAlternatives(false);
              }}
              className="w-full text-left text-xs p-1.5 hover:bg-gray-50 rounded"
            >
              {alt}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
