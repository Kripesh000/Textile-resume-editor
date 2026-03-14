"use client";

import { EducationItem } from "@/lib/types";

interface EducationFieldsProps {
  items: EducationItem[];
  onChange: (items: EducationItem[]) => void;
  resumeId: string;
  sectionType: string;
}

export default function EducationFields({ items, onChange }: EducationFieldsProps) {
  const updateItem = (index: number, field: keyof EducationItem, value: unknown) => {
    const updated = [...items];
    updated[index] = { ...updated[index], [field]: value };
    onChange(updated);
  };

  const addItem = () => {
    onChange([...items, { institution: "", degree: "", location: "", start_date: "", end_date: "", details: [] }]);
  };

  const removeItem = (index: number) => {
    onChange(items.filter((_, i) => i !== index));
  };

  const addDetail = (itemIndex: number) => {
    const updated = [...items];
    updated[itemIndex] = { ...updated[itemIndex], details: [...updated[itemIndex].details, ""] };
    onChange(updated);
  };

  const updateDetail = (itemIndex: number, detailIndex: number, value: string) => {
    const updated = [...items];
    const details = [...updated[itemIndex].details];
    details[detailIndex] = value;
    updated[itemIndex] = { ...updated[itemIndex], details };
    onChange(updated);
  };

  const removeDetail = (itemIndex: number, detailIndex: number) => {
    const updated = [...items];
    updated[itemIndex] = {
      ...updated[itemIndex],
      details: updated[itemIndex].details.filter((_, i) => i !== detailIndex),
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
              placeholder="Institution"
              value={item.institution}
              onChange={(e) => updateItem(i, "institution", e.target.value)}
              className="px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <input
              placeholder="Degree"
              value={item.degree}
              onChange={(e) => updateItem(i, "degree", e.target.value)}
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
            {(item.details || []).map((detail, di) => (
              <div key={di} className="flex items-center gap-1">
                <span className="text-gray-700 text-xs">-</span>
                <input
                  value={detail}
                  onChange={(e) => updateDetail(i, di, e.target.value)}
                  placeholder="Additional detail..."
                  className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
                <button
                  onClick={() => removeDetail(i, di)}
                  className="text-red-400 hover:text-red-600 text-xs px-1"
                >
                  x
                </button>
              </div>
            ))}
            <button
              onClick={() => addDetail(i)}
              className="text-xs text-blue-600 hover:text-blue-700 mt-1"
            >
              + Add detail
            </button>
          </div>
        </div>
      ))}
      <button
        onClick={addItem}
        className="text-sm text-blue-600 hover:text-blue-700 font-medium"
      >
        + Add Education
      </button>
    </div>
  );
}
