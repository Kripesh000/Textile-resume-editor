"use client";

import { Project } from "@/lib/types";
import ImproviseButton from "../../AI/ImproviseButton";

interface ProjectFieldsProps {
  items: Project[];
  onChange: (items: Project[]) => void;
  resumeId: string;
  sectionType: string;
}

export default function ProjectFields({ items, onChange, sectionType }: ProjectFieldsProps) {
  const updateItem = (index: number, field: keyof Project, value: unknown) => {
    const updated = [...items];
    updated[index] = { ...updated[index], [field]: value };
    onChange(updated);
  };

  const addItem = () => {
    onChange([...items, { id: Date.now().toString(), name: "", tech_stack: "", date: "", tags: [], bullets: [] }]);
  };

  const removeItem = (index: number) => {
    onChange(items.filter((_: unknown, i: number) => i !== index));
  };

  const addBullet = (itemIndex: number) => {
    const updated = [...items];
    const newBullet = { id: Date.now().toString(), text: "", tags: [], order: updated[itemIndex].bullets.length };
    updated[itemIndex] = { ...updated[itemIndex], bullets: [...updated[itemIndex].bullets, newBullet] as any };
    onChange(updated);
  };

  const updateBullet = (itemIndex: number, bulletIndex: number, value: string) => {
    const updated = [...items];
    const bullets = [...updated[itemIndex].bullets];
    bullets[bulletIndex] = { ...bullets[bulletIndex], text: value } as any;
    updated[itemIndex] = { ...updated[itemIndex], bullets };
    onChange(updated);
  };

  const removeBullet = (itemIndex: number, bulletIndex: number) => {
    const updated = [...items];
    updated[itemIndex] = {
      ...updated[itemIndex],
      bullets: updated[itemIndex].bullets.filter((_: unknown, i: number) => i !== bulletIndex),
    };
    onChange(updated);
  };

  return (
    <div className="space-y-4">
      {items.map((item, i) => (
        <div key={i} className="border border-gray-100 rounded-md p-3 bg-gray-50">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700">Project {i + 1}</span>
            <button onClick={() => removeItem(i)} className="text-xs text-red-400 hover:text-red-600">
              Remove
            </button>
          </div>
          <div className="grid grid-cols-1 gap-2 mb-2">
            <input
              placeholder="Project Name"
              value={item.name}
              onChange={(e) => updateItem(i, "name", e.target.value)}
              className="px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <div className="flex gap-2">
              <input
                placeholder="Technologies (e.g. React, Node.js)"
                value={item.tech_stack}
                onChange={(e) => updateItem(i, "tech_stack", e.target.value)}
                className="flex-1 px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
              <input
                placeholder="Date (e.g. Fall 2023)"
                value={item.date}
                onChange={(e) => updateItem(i, "date", e.target.value)}
                className="w-1/3 px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
          </div>
          <div className="space-y-1">
            {(item.bullets || []).map((bullet, bi) => (
              <div key={bi} className="flex items-center gap-1">
                <span className="text-gray-700 text-xs">-</span>
                <input
                  value={bullet.text || ""}
                  onChange={(e) => updateBullet(i, bi, e.target.value)}
                  placeholder="e.g. Developed a full-stack dashboard..."
                  className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
                <ImproviseButton
                  text={bullet.text || ""}
                  context={{ role: item.name, company: item.tech_stack, section_type: sectionType }}
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
        + Add Project
      </button>
    </div>
  );
}
