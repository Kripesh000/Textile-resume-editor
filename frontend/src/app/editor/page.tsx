"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { useResume } from "@/hooks/useResume";
import { api } from "@/lib/api";
import { ResumeListItem } from "@/lib/types";
import EditorShell from "@/components/Editor/EditorShell";

const SAVE_STATUS_MAP = {
  idle: null,
  saving: { text: "Saving...", color: "text-gray-400" },
  saved: { text: "All changes saved ✓", color: "text-green-600" },
  error: { text: "Save failed", color: "text-red-500" },
};

export default function EditorPage() {
  const { user, loading: authLoading, logout } = useAuth();
  const router = useRouter();
  const {
    resume,
    loading: resumeLoading,
    saveStatus,
    loadResume,
    updateHeader,
    updateResumeMeta,
    addSection,
    updateSection,
    deleteSection,
    reorderSections,
  } = useResume();
  const [resumeList, setResumeList] = useState<ResumeListItem[]>([]);
  const [showResumeList, setShowResumeList] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/auth/login");
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    if (user && !resume) {
      api.listResumes().then((list) => {
        setResumeList(list);
        if (list.length > 0) {
          loadResume(list[0].id);
        } else {
          setShowResumeList(true);
        }
      });
    }
  }, [user, resume, loadResume]);

  const handleCreateResume = async () => {
    const r = await api.createResume({ title: "New Resume" });
    const created = r as { id: string };
    loadResume(created.id);
    setShowResumeList(false);
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setUploadProgress("Uploading file...");
    try {
      setUploadProgress("Parsing resume...");
      const uploaded = await api.uploadResume(file);
      setUploadProgress("Loading editor...");
      loadResume(uploaded.id);
      const list = await api.listResumes();
      setResumeList(list);
      setShowResumeList(false);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
      setUploadProgress(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  if (authLoading || resumeLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (!user) return null;

  const statusInfo = SAVE_STATUS_MAP[saveStatus];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Upload Progress Overlay */}
      {uploading && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center">
          <div className="bg-white rounded-xl shadow-2xl p-8 w-80 text-center">
            <div className="animate-spin h-10 w-10 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4" />
            <p className="text-lg font-medium text-gray-800 mb-1">{uploadProgress}</p>
            <p className="text-sm text-gray-400">This usually takes a few seconds</p>
          </div>
        </div>
      )}

      {/* Top bar */}
      <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6">
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-bold cursor-pointer" onClick={() => router.push("/editor")}>
            TeX<span className="text-blue-600">Tile</span>
          </h1>
          <nav className="flex gap-2 ml-2">
            <button className="text-sm px-3 py-1.5 rounded-md bg-blue-50 text-blue-700 font-medium">
              Editor
            </button>
            <button
              onClick={() => router.push("/profile")}
              className="text-sm px-3 py-1.5 rounded-md text-gray-600 hover:bg-gray-100"
            >
              Profile
            </button>
          </nav>
          {resumeList.length > 0 && (
            <div className="relative">
              <button
                onClick={() => setShowResumeList(!showResumeList)}
                className="text-sm text-gray-900 hover:text-gray-800 px-3 py-1 border border-gray-200 rounded-md"
              >
                {resume?.title || "Select Resume"} ▾
              </button>
              {showResumeList && (
                <div className="absolute top-full mt-1 left-0 w-64 bg-white border border-gray-200 rounded-lg shadow-lg z-20">
                  {resumeList.map((r) => (
                    <button
                      key={r.id}
                      onClick={() => {
                        loadResume(r.id);
                        setShowResumeList(false);
                      }}
                      className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50"
                    >
                      {r.title}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
          {/* Save status */}
          {statusInfo && (
            <span className={`text-xs ${statusInfo.color} transition-opacity`}>
              {statusInfo.text}
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            onChange={handleUpload}
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="text-sm px-3 py-1.5 border border-blue-600 text-blue-600 rounded-md hover:bg-blue-50 disabled:opacity-50"
          >
            Upload PDF
          </button>
          <button
            onClick={handleCreateResume}
            className="text-sm px-3 py-1.5 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            New Resume
          </button>
          <span className="text-sm text-gray-700">{user.name}</span>
          <button
            onClick={() => { logout(); router.push("/"); }}
            className="text-sm text-gray-700 hover:text-gray-900"
          >
            Sign out
          </button>
        </div>
      </header>

      {/* Editor or Onboarding */}
      {resume ? (
        <EditorShell
          resume={resume}
          onUpdateHeader={updateHeader}
          onUpdateResumeMeta={updateResumeMeta}
          onAddSection={addSection}
          onUpdateSection={updateSection}
          onDeleteSection={deleteSection}
          onReorderSections={reorderSections}
        />
      ) : (
        <div className="flex flex-col items-center justify-center h-[calc(100vh-4rem)] px-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Welcome to TeXTile</h2>
          <p className="text-gray-500 mb-8 text-center max-w-md">
            Build a beautiful LaTeX resume in minutes. Choose how you&apos;d like to start:
          </p>
          <div className="grid grid-cols-3 gap-4 max-w-2xl w-full">
            {/* Path 1: Upload */}
            <button
              onClick={() => fileInputRef.current?.click()}
              className="flex flex-col items-center gap-3 p-6 bg-white border-2 border-gray-200 rounded-xl hover:border-blue-400 hover:shadow-md transition-all group"
            >
              <span className="text-3xl">📄</span>
              <span className="font-medium text-gray-800 group-hover:text-blue-600">Upload PDF</span>
              <span className="text-xs text-gray-400 text-center">Import an existing resume and start editing</span>
            </button>
            {/* Path 2: From scratch */}
            <button
              onClick={handleCreateResume}
              className="flex flex-col items-center gap-3 p-6 bg-white border-2 border-gray-200 rounded-xl hover:border-blue-400 hover:shadow-md transition-all group"
            >
              <span className="text-3xl">✨</span>
              <span className="font-medium text-gray-800 group-hover:text-blue-600">Start Fresh</span>
              <span className="text-xs text-gray-400 text-center">Create a new resume from a blank template</span>
            </button>
            {/* Path 3: From profile */}
            <button
              onClick={async () => {
                await handleCreateResume();
              }}
              className="flex flex-col items-center gap-3 p-6 bg-white border-2 border-gray-200 rounded-xl hover:border-green-400 hover:shadow-md transition-all group"
            >
              <span className="text-3xl">👤</span>
              <span className="font-medium text-gray-800 group-hover:text-green-600">From Profile</span>
              <span className="text-xs text-gray-400 text-center">Build from your saved profile data</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
