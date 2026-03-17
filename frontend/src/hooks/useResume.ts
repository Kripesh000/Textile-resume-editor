"use client";

import { useState, useCallback, useRef } from "react";
import { api } from "@/lib/api";
import { Resume, Section, SectionType, SectionItem, SECTION_DEFAULTS } from "@/lib/types";

export type SaveStatus = "idle" | "saving" | "saved" | "error";

export function useResume() {
  const [resume, setResume] = useState<Resume | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saveStatus, setSaveStatus] = useState<SaveStatus>("idle");
  const debounceTimers = useRef<Record<string, NodeJS.Timeout>>({});
  const savedTimer = useRef<NodeJS.Timeout | null>(null);

  const debouncedApiCall = useCallback((key: string, fn: () => Promise<void>, delay = 500) => {
    if (debounceTimers.current[key]) clearTimeout(debounceTimers.current[key]);
    if (savedTimer.current) clearTimeout(savedTimer.current);
    debounceTimers.current[key] = setTimeout(async () => {
      setSaveStatus("saving");
      try {
        await fn();
        setSaveStatus("saved");
        savedTimer.current = setTimeout(() => setSaveStatus("idle"), 2000);
      } catch {
        setSaveStatus("error");
        savedTimer.current = setTimeout(() => setSaveStatus("idle"), 3000);
      }
    }, delay);
  }, []);

  const loadResume = useCallback(async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const r = await api.getResume(id);
      setResume(r);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load resume");
    } finally {
      setLoading(false);
    }
  }, []);

  const updateHeader = useCallback(
    (headerData: Record<string, string>) => {
      if (!resume) return;
      const merged = { ...resume.header_data, ...headerData };
      setResume((prev) => (prev ? { ...prev, header_data: merged } : prev));
      debouncedApiCall("header", async () => { await api.updateResume(resume.id, { header_data: merged }); });
    },
    [resume, debouncedApiCall]
  );

  const updateResumeMeta = useCallback(
    (data: { title?: string; template_key?: string }) => {
      if (!resume) return;
      setResume((prev) => (prev ? { ...prev, ...data } : prev));
      debouncedApiCall("meta", async () => { await api.updateResume(resume.id, data); });
    },
    [resume, debouncedApiCall]
  );

  const addSection = useCallback(
    async (type: SectionType) => {
      if (!resume) return;
      const defaults = SECTION_DEFAULTS[type];
      const orderIndex = resume.sections.length;
      try {
        const section = await api.createSection(resume.id, {
          section_type: type,
          title: defaults.title,
          order_index: orderIndex,
        });
        setResume((prev) =>
          prev ? { ...prev, sections: [...prev.sections, section] } : prev
        );
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to add section");
      }
    },
    [resume]
  );

  const updateSection = useCallback(
    (sectionId: string, data: { title?: string; items?: SectionItem[] }) => {
      if (!resume) return;
      setResume((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          sections: prev.sections.map((s) =>
            s.id === sectionId ? { ...s, ...data } : s
          ),
        };
      });
      debouncedApiCall(`section-${sectionId}`, async () => {
        console.log("Saving section", sectionId, "with data:", data);
        await api.updateSection(resume.id, sectionId, data);
      });
    },
    [resume, debouncedApiCall]
  );

  const deleteSection = useCallback(
    async (sectionId: string) => {
      if (!resume) return;
      setResume((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          sections: prev.sections.filter((s) => s.id !== sectionId),
        };
      });
      try {
        await api.deleteSection(resume.id, sectionId);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to delete section");
      }
    },
    [resume]
  );

  const reorderSections = useCallback(
    async (newSections: Section[]) => {
      if (!resume) return;
      const reordered = newSections.map((s, i) => ({ ...s, order_index: i }));
      setResume((prev) => (prev ? { ...prev, sections: reordered } : prev));
      try {
        await api.reorderSections(
          resume.id,
          reordered.map((s) => ({ section_id: s.id, order_index: s.order_index }))
        );
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to reorder sections");
      }
    },
    [resume]
  );

  return {
    resume,
    loading,
    error,
    saveStatus,
    loadResume,
    updateHeader,
    updateResumeMeta,
    addSection,
    updateSection,
    deleteSection,
    reorderSections,
  };
}
