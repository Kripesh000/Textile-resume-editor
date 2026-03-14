"use client";

import { useState } from "react";
import { useSortable } from "@dnd-kit/react/sortable";
import { Section, SectionItem } from "@/lib/types";
import { api } from "@/lib/api";
import ExperienceFields from "./fields/ExperienceFields";
import EducationFields from "./fields/EducationFields";
import ProjectFields from "./fields/ProjectFields";
import SkillsFields from "./fields/SkillsFields";
import GenericFields from "./fields/GenericFields";

interface TileProps {
  section: Section;
  index: number;
  resumeId: string;
  colorClass?: string;
  onUpdate: (data: { title?: string; items?: SectionItem[] }) => void;
  onDelete: () => void;
}

export default function Tile({ section, index, resumeId, colorClass, onUpdate, onDelete }: TileProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const { ref } = useSortable({ id: section.id, index });

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const fieldMap: Record<string, React.ComponentType<any>> = {
    experience: ExperienceFields,
    education: EducationFields,
    project: ProjectFields,
    skills: SkillsFields,
    generic: GenericFields,
  };
  const FieldComponent = fieldMap[section.section_type] || GenericFields;

  const handleSaveToProfile = async () => {
    setSaving(true);
    try {
      const result = await api.saveToProfile({
        resume_id: resumeId,
        section_id: section.id,
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div ref={ref} className="bg-white border border-gray-200 rounded-lg shadow-sm">
      {/* Tile header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
        <div className="flex items-center gap-2">
          <span className="cursor-grab text-gray-700 hover:text-gray-900" title="Drag to reorder">
            &#x2630;
          </span>
          <input
            type="text"
            value={section.title}
            onChange={(e) => onUpdate({ title: e.target.value })}
            className="font-semibold text-lg border-none outline-none bg-transparent"
          />
          <span className={`text-xs px-2 py-0.5 rounded ${colorClass || "bg-gray-100 text-gray-700"}`}>
            {section.section_type}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleSaveToProfile}
            disabled={saving || section.items.length === 0}
            className={`text-sm px-2 py-0.5 rounded ${saved
              ? "text-green-600 bg-green-50"
              : "text-green-600 hover:text-green-700 hover:bg-green-50"
              } disabled:opacity-40 disabled:cursor-default`}
          >
            {saving ? "Saving..." : saved ? "Saved!" : "Save to Profile"}
          </button>
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="text-gray-700 hover:text-gray-900 text-sm"
          >
            {collapsed ? "Expand" : "Collapse"}
          </button>
          <button
            onClick={() => {
              if (window.confirm(`Delete "${section.title}"? This cannot be undone.`)) {
                onDelete();
              }
            }}
            className="text-red-400 hover:text-red-600 text-sm"
          >
            Delete
          </button>
        </div>
      </div>

      {/* Tile body */}
      {!collapsed && (
        <div className="p-4">
          <FieldComponent
            items={section.items as never[]}
            onChange={(items: SectionItem[]) => onUpdate({ items })}
            resumeId={resumeId}
            sectionType={section.section_type}
          />
        </div>
      )}
    </div>
  );
}
