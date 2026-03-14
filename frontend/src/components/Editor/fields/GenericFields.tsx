"use client";

import { GenericItem } from "@/lib/types";

interface GenericFieldsProps {
  items: GenericItem[];
  onChange: (items: GenericItem[]) => void;
  resumeId: string;
  sectionType: string;
}

export default function GenericFields({ items, onChange }: GenericFieldsProps) {
  const updateItem = (index: number, value: string) => {
    const updated = [...items];
    updated[index] = { text: value };
    onChange(updated);
  };

  const addItem = () => {
    onChange([...items, { text: "" }]);
  };

  const removeItem = (index: number) => {
    onChange(items.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-1">
      {items.map((item, i) => (
        <div key={i} className="flex items-center gap-1">
          <span className="text-gray-700 text-xs">-</span>
          <input
            value={item.text}
            onChange={(e) => updateItem(i, e.target.value)}
            placeholder="Enter text..."
            className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
          <button
            onClick={() => removeItem(i)}
            className="text-red-400 hover:text-red-600 text-xs px-1"
          >
            x
          </button>
        </div>
      ))}
      <button
        onClick={addItem}
        className="text-xs text-blue-600 hover:text-blue-700 mt-1"
      >
        + Add item
      </button>
    </div>
  );
}
