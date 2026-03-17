"use client";

import { DragDropProvider } from "@dnd-kit/react";
import { move } from "@dnd-kit/helpers";
import { useState, useEffect } from "react";
import { Section, SectionItem } from "@/lib/types";
import Tile from "./Tile";

interface TileListProps {
  resumeId: string;
  sections: Section[];
  sectionColors?: Record<string, string>;
  onUpdateSection: (sectionId: string, data: { title?: string; items?: SectionItem[] }) => void;
  onDeleteSection: (sectionId: string) => void;
  onReorderSections: (sections: Section[]) => void;
}

export default function TileList({
  resumeId,
  sections,
  sectionColors,
  onUpdateSection,
  onDeleteSection,
  onReorderSections,
}: TileListProps) {
  const [items, setItems] = useState(sections);

  useEffect(() => {
    setItems(sections);
  }, [sections]);

  return (
    <DragDropProvider
      onDragEnd={(event) => {
        const updated = move(items, event);
        setItems(updated);
        onReorderSections(updated);
      }}
    >
      <div className="space-y-3">
        {items.map((section, index) => (
          <Tile
            key={section.id}
            index={index}
            section={section}
            resumeId={resumeId}
            colorClass={sectionColors?.[section.section_type]}
            onUpdate={(data) => onUpdateSection(section.id, data)}
            onDelete={() => onDeleteSection(section.id)}
          />
        ))}
      </div>
    </DragDropProvider>
  );
}
