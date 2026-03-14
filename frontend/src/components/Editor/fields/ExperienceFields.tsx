"use client";

import { ExperienceItem } from "@/lib/types";
import ImproviseButton from "../../AI/ImproviseButton";

interface ExperienceFieldsProps {
  items: ExperienceItem[];
  onChange: (items: ExperienceItem[]) => void;
  resumeId: string;
  sectionType: string;
}

export default function ExperienceFields({ items, onChange, sectionType }: ExperienceFieldsProps) {
  const updateItem = (index: number, field: keyof ExperienceItem, value: unknown) => {
    const updated = [...items];
    updated[index] = { ...updated[index], [field]: value };
    onChange(updated);
  };

  const addItem = () => {
    onChange([...items, { company: "", role: "", location: "", start_date: "", end_date: "", bullets: [""] }]);
  };

  const removeItem = (index: number) => {
    onChange(items.filter((_, i) => i !== index));
  };

  const addBullet = (itemIndex: number) => {
    const updated = [...items];
    updated[itemIndex] = { ...updated[itemIndex], bullets: [...updated[itemIndex].bullets, ""] };
    onChange(updated);
  };

  const updateBullet = (itemIndex: number, bulletIndex: number, value: string) => {
    const updated = [...items];
    const bullets = [...updated[itemIndex].bullets];
    bullets[bulletIndex] = value;
    updated[itemIndex] = { ...updated[itemIndex], bullets };
    onChange(updated);
  };

  const removeBullet = (itemIndex: number, bulletIndex: number) => {
    const updated = [...items];
    updated[itemIndex] = {
      ...updated[itemIndex],
      bullets: updated[itemIndex].bullets.filter((_, i) => i !== bulletIndex),
    };
    onChange(updated);
  };

  return (
    <div className="space-y-4">
      {items.map((item, i) => (
        <div key={i} className="border border-gray-100 rounded-md p-3 bg-gray-50">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700">Entry {i + 1}</span>
            <button onClick={() => removeItem(i)} className="text-xs text-red-400 hover:text-red-600">
              Remove
            </button>
          </div>
          <div className="grid grid-cols-2 gap-2 mb-2">
            <input
              placeholder="Role / Title"
              value={item.role}
              onChange={(e) => updateItem(i, "role", e.target.value)}
              className="px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <input
              placeholder="Company"
              value={item.company}
              onChange={(e) => updateItem(i, "company", e.target.value)}
              className="px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <input
              placeholder="Location"
              value={item.location}
              onChange={(e) => updateItem(i, "location", e.target.value)}
              className="px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <div className="flex gap-1">
              <input
                placeholder="Start"
                value={item.start_date}
                onChange={(e) => updateItem(i, "start_date", e.target.value)}
                className="w-1/2 px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
              <input
                placeholder="End"
                value={item.end_date}
                onChange={(e) => updateItem(i, "end_date", e.target.value)}
                className="w-1/2 px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
          </div>
          <div className="space-y-1">
            {(item.bullets || []).map((bullet, bi) => (
              <div key={bi} className="flex items-center gap-1">
                <span className="text-gray-700 text-xs">-</span>
                <input
                  value={bullet}
                  onChange={(e) => updateBullet(i, bi, e.target.value)}
                  placeholder="e.g. Led a team of 5 to deliver a 30% increase in..."
                  className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
                <ImproviseButton
                  text={bullet}
                  context={{ role: item.role, company: item.company, section_type: sectionType }}
                  onResult={(text) => updateBullet(i, bi, text)}
                />
                <button
                  onClick={() => removeBullet(i, bi)}
                  className="text-red-400 hover:text-red-600 text-xs px-1"
                >
                  x
                </button>
              </div>
            ))}
            {(item.bullets || []).length === 0 && (
              <p className="text-xs text-gray-400 italic">💡 Tip: Start bullets with action verbs (Led, Built, Designed, Increased...)</p>
            )}
            <button
              onClick={() => addBullet(i)}
              className="text-xs text-blue-600 hover:text-blue-700 mt-1"
            >
              + Add bullet
            </button>
          </div>
        </div>
      ))}
      <button
        onClick={addItem}
        className="text-sm text-blue-600 hover:text-blue-700 font-medium"
      >
        + Add Experience
      </button>
    </div>
  );
}
