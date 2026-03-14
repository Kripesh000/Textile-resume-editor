"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { api } from "@/lib/api";

interface PdfPreviewProps {
  resumeId: string;
  changeVersion?: number; // increments when resume content changes
}

export default function PdfPreview({ resumeId, changeVersion = 0 }: PdfPreviewProps) {
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isStale, setIsStale] = useState(false);
  const debounceRef = useRef<NodeJS.Timeout | null>(null);
  const lastVersion = useRef(0);
  const hasGenerated = useRef(false);

  const generatePreview = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const blob = await api.generatePdf(resumeId);
      if (pdfUrl) URL.revokeObjectURL(pdfUrl);
      setPdfUrl(URL.createObjectURL(blob) + "#zoom=page-width");
      setIsStale(false);
      hasGenerated.current = true;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate PDF");
    } finally {
      setLoading(false);
    }
  }, [resumeId, pdfUrl]);

  // Auto-generate on first load
  useEffect(() => {
    if (!hasGenerated.current) {
      generatePreview();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resumeId]);

  // Auto-regenerate when content changes (debounced 3s)
  useEffect(() => {
    if (changeVersion <= lastVersion.current) return;
    lastVersion.current = changeVersion;

    // Mark as stale immediately
    if (hasGenerated.current) setIsStale(true);

    // Debounce the regeneration
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      generatePreview();
    }, 3000);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [changeVersion, generatePreview]);

  const downloadPdf = () => {
    if (!pdfUrl) return;
    const a = document.createElement("a");
    a.href = pdfUrl;
    a.download = "resume.pdf";
    a.click();
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between p-3 bg-white border-b border-gray-200">
        <div className="flex items-center gap-2">
          <h3 className="font-medium text-sm">Preview</h3>
          {isStale && !loading && (
            <span className="text-xs text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full animate-pulse">
              Updating...
            </span>
          )}
        </div>
        <div className="flex gap-2">
          <button
            onClick={generatePreview}
            disabled={loading}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-md hover:bg-gray-100 disabled:opacity-50"
            title="⌘ + Enter"
          >
            {loading ? (
              <span className="flex items-center gap-1.5">
                <span className="animate-spin h-3.5 w-3.5 border-2 border-blue-600 border-t-transparent rounded-full" />
                Generating...
              </span>
            ) : (
              "Refresh"
            )}
          </button>
          {pdfUrl && (
            <button
              onClick={downloadPdf}
              className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              ↓ Download
            </button>
          )}
        </div>
      </div>
      <div className="flex-1 min-h-0 p-4">
        {error && (
          <div className="text-red-600 text-sm p-3 bg-red-50 rounded-md mb-2">{error}</div>
        )}
        {pdfUrl ? (
          <iframe
            src={pdfUrl}
            className={`w-full h-full min-h-[500px] rounded-md border border-gray-200 transition-opacity ${isStale ? "opacity-60" : "opacity-100"
              }`}
            title="Resume Preview"
          />
        ) : loading ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-400 gap-3">
            <div className="animate-spin h-8 w-8 border-3 border-blue-600 border-t-transparent rounded-full" />
            <p>Generating your resume preview...</p>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full text-gray-400">
            <p className="text-center">Preview will appear here</p>
          </div>
        )}
      </div>
    </div>
  );
}
