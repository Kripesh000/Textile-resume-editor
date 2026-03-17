"use client";

import { SkillCategory } from "@/lib/types";

interface SkillsFieldsProps {
  items: SkillCategory[];
  onChange: (items: SkillCategory[]) => void;
  resumeId: string;
  sectionType: string;
}

export default function SkillsFields({ items, onChange }: SkillsFieldsProps) {
  const updateItem = (index: number, field: keyof SkillCategory, value: unknown) => {
    const updated = [...items];
    updated[index] = { ...updated[index], [field]: value };
    onChange(updated);
  };

  const addItem = () => {
    onChange([...items, { id: Date.now().toString(), name: "", items: [], tags: [] }]);
  };

  const removeItem = (index: number) => {
    onChange(items.filter((_: unknown, i: number) => i !== index));
  };

  return (
    <div className="space-y-3">
      {items.map((item, i) => (
        <div key={i} className="flex items-start gap-2">
          <input
            placeholder="Category (e.g., Languages)"
            value={item.name || ""}
            onChange={(e) => updateItem(i, "name", e.target.value)}
            className="w-1/3 px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
          <input
            placeholder="Skills (comma-separated)"
            value={(item.items || []).join(", ")}
            onChange={(e) =>
              updateItem(
                i,
                "items",
                e.target.value.split(",").map((s) => s.trim())
              )
            }
            className="flex-1 px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
          <button
            onClick={() => removeItem(i)}
            className="text-red-400 hover:text-red-600 text-xs px-1 pt-2"
          >
            x
          </button>
        </div>
      ))}
      <button
        onClick={addItem}
        className="text-sm text-blue-600 hover:text-blue-700 font-medium"
      >
        + Add Skill Category
      </button>
    </div>
  );
}
