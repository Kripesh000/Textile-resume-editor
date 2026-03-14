"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { Resume, Section, SectionType, SectionItem, Profile, ProfileSection as PSection, ProfileItem as PItem } from "@/lib/types";
import { api } from "@/lib/api";
import TileList from "./TileList";
import HeaderFields from "./fields/HeaderFields";
import PdfPreview from "../Preview/PdfPreview";

interface EditorShellProps {
  resume: Resume;
  onUpdateHeader: (data: Record<string, string>) => void;
  onUpdateResumeMeta: (data: { title?: string; template_key?: string }) => void;
  onAddSection: (type: SectionType) => void;
  onUpdateSection: (sectionId: string, data: { title?: string; items?: SectionItem[] }) => void;
  onDeleteSection: (sectionId: string) => void;
  onReorderSections: (sections: Section[]) => void;
}

const TEMPLATES = [
  { key: "classic", label: "Classic" },
  { key: "modern", label: "Modern" },
  { key: "minimal", label: "Minimal" },
  { key: "custom", label: "Custom" },
];

const SECTION_OPTIONS: { type: SectionType; label: string; icon: string }[] = [
  { type: "experience", label: "Experience", icon: "💼" },
  { type: "education", label: "Education", icon: "🎓" },
  { type: "project", label: "Projects", icon: "🚀" },
  { type: "skills", label: "Skills", icon: "⚡" },
  { type: "generic", label: "Other", icon: "📝" },
];

// Color map for section type badges
const SECTION_COLORS: Record<string, string> = {
  experience: "bg-blue-100 text-blue-700",
  education: "bg-green-100 text-green-700",
  project: "bg-purple-100 text-purple-700",
  skills: "bg-amber-100 text-amber-700",
  generic: "bg-gray-100 text-gray-700",
};

export default function EditorShell({
  resume,
  onUpdateHeader,
  onUpdateResumeMeta,
  onAddSection,
  onUpdateSection,
  onDeleteSection,
  onReorderSections,
}: EditorShellProps) {
  const [showAddMenu, setShowAddMenu] = useState(false);
  const [showImport, setShowImport] = useState(false);
  const [changeVersion, setChangeVersion] = useState(0);

  // Track content changes with a version counter for auto-preview
  const prevResumeRef = useRef(resume);
  useEffect(() => {
    const prev = prevResumeRef.current;
    if (
      prev.header_data !== resume.header_data ||
      prev.sections !== resume.sections ||
      prev.template_key !== resume.template_key
    ) {
      setChangeVersion((v) => v + 1);
    }
    prevResumeRef.current = resume;
  }, [resume]);

  // Keyboard shortcut: Cmd+Enter to refresh preview
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
        e.preventDefault();
        setChangeVersion((v) => v + 1);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  return (
    <div className="flex h-[calc(100vh-4rem)] gap-0">
      {/* Left: Editor */}
      <div className="w-1/2 overflow-y-auto border-r border-gray-200 p-6">
        {/* Resume title */}
        <input
          type="text"
          value={resume.title}
          onChange={(e) => onUpdateResumeMeta({ title: e.target.value })}
          className="text-2xl font-bold w-full mb-4 border-none outline-none bg-transparent"
          placeholder="Resume Title"
        />

        {/* Template selector */}
        <div className="flex gap-2 mb-6">
          {TEMPLATES.map((t) => (
            <button
              key={t.key}
              onClick={() => onUpdateResumeMeta({ template_key: t.key })}
              className={`px-3 py-1 text-sm rounded-full border transition-all ${resume.template_key === t.key
                  ? "bg-blue-600 text-white border-blue-600 shadow-sm"
                  : "border-gray-300 hover:bg-gray-100 hover:border-gray-400"
                }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Header fields */}
        <HeaderFields
          data={resume.header_data}
          onChange={onUpdateHeader}
        />

        {/* Section tiles */}
        <TileList
          resumeId={resume.id}
          sections={resume.sections}
          sectionColors={SECTION_COLORS}
          onUpdateSection={onUpdateSection}
          onDeleteSection={onDeleteSection}
          onReorderSections={onReorderSections}
        />

        {/* Add section + Import */}
        <div className="mt-4 flex gap-2">
          <div className="flex-1 relative">
            <button
              onClick={() => setShowAddMenu(!showAddMenu)}
              className="w-full py-3 border-2 border-dashed border-gray-300 rounded-lg text-gray-700 hover:border-blue-400 hover:text-blue-600 transition-colors"
            >
              + Add Section
            </button>
            {showAddMenu && (
              <div className="absolute top-full mt-1 left-0 w-full bg-white border border-gray-200 rounded-lg shadow-lg z-10">
                {SECTION_OPTIONS.map((opt) => (
                  <button
                    key={opt.type}
                    onClick={() => {
                      onAddSection(opt.type);
                      setShowAddMenu(false);
                    }}
                    className="w-full px-4 py-2.5 text-left hover:bg-gray-50 first:rounded-t-lg last:rounded-b-lg flex items-center gap-2"
                  >
                    <span>{opt.icon}</span>
                    <span>{opt.label}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
          <button
            onClick={() => setShowImport(true)}
            className="py-3 px-4 border-2 border-dashed border-green-300 rounded-lg text-green-600 hover:border-green-500 hover:text-green-700 transition-colors text-sm whitespace-nowrap"
          >
            Import from Profile
          </button>
        </div>
      </div>

      {/* Right: PDF Preview */}
      <div className="w-1/2 h-full bg-gray-100">
        <PdfPreview resumeId={resume.id} changeVersion={changeVersion} />
      </div>

      {/* Import Modal */}
      {showImport && (
        <ImportModal
          resume={resume}
          onClose={() => setShowImport(false)}
          onImported={() => {
            setShowImport(false);
            window.location.reload();
          }}
        />
      )}
    </div>
  );
}

// --- Import from Profile Modal ---

function ImportModal({
  resume,
  onClose,
  onImported,
}: {
  resume: Resume;
  onClose: () => void;
  onImported: () => void;
}) {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedItems, setSelectedItems] = useState<Record<string, Set<string>>>({});
  const [importing, setImporting] = useState(false);

  const loadProfile = useCallback(async () => {
    try {
      const p = await api.getProfile();
      setProfile(p);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadProfile(); }, [loadProfile]);

  const toggleItem = (sectionId: string, itemId: string) => {
    setSelectedItems((prev) => {
      const section = new Set(prev[sectionId] || []);
      if (section.has(itemId)) section.delete(itemId);
      else section.add(itemId);
      return { ...prev, [sectionId]: section };
    });
  };

  const totalSelected = Object.values(selectedItems).reduce((n, s) => n + s.size, 0);

  const handleImport = async () => {
    if (!profile) return;
    setImporting(true);
    try {
      for (const pSection of profile.sections) {
        const ids = selectedItems[pSection.id];
        if (!ids || ids.size === 0) continue;

        let resumeSection = resume.sections.find(
          (s) => s.section_type === pSection.section_type
        );

        if (!resumeSection) {
          resumeSection = await api.createSection(resume.id, {
            section_type: pSection.section_type,
            title: pSection.title,
            order_index: resume.sections.length,
          });
        }

        await api.importToResume({
          resume_id: resume.id,
          section_id: resumeSection.id,
          item_ids: Array.from(ids),
        });
      }
      onImported();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Import failed");
    } finally {
      setImporting(false);
    }
  };

  const getItemLabel = (item: PItem, sectionType: string): string => {
    const d = item.data;
    switch (sectionType) {
      case "experience":
        return `${d.role || ""} at ${d.company || ""}`.trim() || "Untitled";
      case "education":
        return `${d.degree || ""} - ${d.institution || ""}`.trim() || "Untitled";
      case "project":
        return (d.name as string) || "Untitled";
      case "skills":
        return `${d.category || ""}: ${((d.items as string[]) || []).join(", ")}` || "Untitled";
      default:
        return (d.text as string) || "Untitled";
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center">
      <div className="bg-white rounded-lg shadow-xl w-[600px] max-h-[80vh] flex flex-col">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h3 className="font-semibold text-lg">Import from Profile</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">&times;</button>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin h-6 w-6 border-2 border-blue-600 border-t-transparent rounded-full" />
            </div>
          ) : !profile || profile.sections.length === 0 ? (
            <p className="text-gray-500 text-center py-8">
              No profile data yet. Go to your Profile to add experiences, education, and more.
            </p>
          ) : (
            <div className="space-y-4">
              {profile.sections.map((pSection) => (
                <div key={pSection.id}>
                  <h4 className="font-medium text-sm text-gray-700 mb-2">
                    {pSection.title}
                    <span className="text-xs text-gray-400 ml-2">{pSection.section_type}</span>
                  </h4>
                  {pSection.items.length === 0 ? (
                    <p className="text-xs text-gray-400 ml-4">No items</p>
                  ) : (
                    <div className="space-y-1">
                      {pSection.items.map((item) => {
                        const checked = selectedItems[pSection.id]?.has(item.id) || false;
                        return (
                          <label
                            key={item.id}
                            className={`flex items-center gap-3 px-3 py-2 rounded-md cursor-pointer border ${checked ? "border-blue-300 bg-blue-50" : "border-gray-200 hover:bg-gray-50"
                              }`}
                          >
                            <input
                              type="checkbox"
                              checked={checked}
                              onChange={() => toggleItem(pSection.id, item.id)}
                              className="accent-blue-600"
                            />
                            <span className="text-sm truncate">
                              {getItemLabel(item, pSection.section_type)}
                            </span>
                          </label>
                        );
                      })}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
          <span className="text-sm text-gray-500">{totalSelected} item(s) selected</span>
          <div className="flex gap-2">
            <button onClick={onClose} className="px-4 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50">
              Cancel
            </button>
            <button
              onClick={handleImport}
              disabled={totalSelected === 0 || importing}
              className="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {importing ? "Importing..." : `Import ${totalSelected} item(s)`}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
