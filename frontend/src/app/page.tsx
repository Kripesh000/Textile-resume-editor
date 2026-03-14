"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";

export default function HomePage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && user) {
      router.push("/editor");
    }
  }, [user, loading, router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      {/* Hero */}
      <div className="flex-1 flex flex-col items-center justify-center p-8">
        <h1 className="text-5xl font-bold mb-4">
          TeX<span className="text-blue-600">Tile</span>
        </h1>
        <p className="text-xl text-gray-600 mb-2 text-center max-w-lg">
          Build beautiful LaTeX resumes with drag-and-drop tiles.
        </p>
        <p className="text-sm text-gray-400 mb-8">
          No LaTeX knowledge required. AI-powered bullet improvement included.
        </p>
        <div className="flex gap-4 mb-12">
          <Link
            href="/auth/register"
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium shadow-sm hover:shadow-md transition-all"
          >
            Get Started — it&apos;s free
          </Link>
          <Link
            href="/auth/login"
            className="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-100 font-medium"
          >
            Sign In
          </Link>
        </div>

        {/* How it works */}
        <div className="grid grid-cols-3 gap-8 max-w-2xl w-full">
          <div className="text-center">
            <div className="text-3xl mb-2">📄</div>
            <p className="font-medium text-gray-800 text-sm">Upload or Create</p>
            <p className="text-xs text-gray-400 mt-1">Start from a PDF or blank template</p>
          </div>
          <div className="text-center">
            <div className="text-3xl mb-2">✨</div>
            <p className="font-medium text-gray-800 text-sm">Edit with AI</p>
            <p className="text-xs text-gray-400 mt-1">Drag-and-drop tiles with AI-powered suggestions</p>
          </div>
          <div className="text-center">
            <div className="text-3xl mb-2">🎯</div>
            <p className="font-medium text-gray-800 text-sm">Export as PDF</p>
            <p className="text-xs text-gray-400 mt-1">Professional LaTeX quality, instantly</p>
          </div>
        </div>
      </div>
    </div>
  );
}
