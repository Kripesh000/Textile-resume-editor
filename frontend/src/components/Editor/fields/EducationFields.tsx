"use client";

import { Education } from "@/lib/types";

interface EducationFieldsProps {
  items: Education[];
  onChange: (items: Education[]) => void;
  resumeId: string;
  sectionType: string;
}

export default function EducationFields({ items, onChange }: EducationFieldsProps) {
  const updateItem = (index: number, field: keyof Education, value: unknown) => {
    const updated = [...items];
    updated[index] = { ...updated[index], [field]: value };
    onChange(updated);
  };

  const addItem = () => {
    onChange([
      ...items,
      {
        id: Date.now().toString(),
        institution: "",
        degree: "",
        location: "",
        end: "",
        gpa: "",
        coursework: "",
        awards: "",
      },
    ]);
  };

  const removeItem = (index: number) => {
    onChange(items.filter((_: unknown, i: number) => i !== index));
  };

  return (
    <div className="space-y-4">
      {items.map((item, i) => (
        <div key={i} className="border border-gray-100 rounded-md p-3 bg-gray-50">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700">Education {i + 1}</span>
            <button onClick={() => removeItem(i)} className="text-xs text-red-400 hover:text-red-600">
              Remove
            </button>
          </div>
          <div className="grid grid-cols-2 gap-2 mb-2">
            <input
              placeholder="Institution"
              value={item.institution || ""}
              onChange={(e) => updateItem(i, "institution", e.target.value)}
              className="px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <input
              placeholder="Degree"
              value={item.degree || ""}
              onChange={(e) => updateItem(i, "degree", e.target.value)}
              className="px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <input
              placeholder="Location"
              value={item.location || ""}
              onChange={(e) => updateItem(i, "location", e.target.value)}
              className="px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <div className="flex gap-1">
              <input
                placeholder="End Date"
                value={item.end || ""}
                onChange={(e) => updateItem(i, "end", e.target.value)}
                className="w-1/2 px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
              <input
                placeholder="GPA"
                value={item.gpa || ""}
                onChange={(e) => updateItem(i, "gpa", e.target.value)}
                className="w-1/2 px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
          </div>
          <div className="space-y-2">
            <input
              placeholder="Relevant Coursework..."
              value={item.coursework || ""}
              onChange={(e) => updateItem(i, "coursework", e.target.value)}
              className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <input
              placeholder="Awards & Honors..."
              value={item.awards || ""}
              onChange={(e) => updateItem(i, "awards", e.target.value)}
              className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
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
