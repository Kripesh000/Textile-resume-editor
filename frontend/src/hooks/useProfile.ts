"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { api } from "@/lib/api";
import { Profile } from "@/lib/types";

export type SaveStatus = "idle" | "saving" | "saved" | "error";

export function useProfile() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saveStatus, setSaveStatus] = useState<SaveStatus>("idle");
  
  const saveTimer = useRef<NodeJS.Timeout | null>(null);
  const statusTimer = useRef<NodeJS.Timeout | null>(null);

  const fetchProfile = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const p = await api.getProfile();
      setProfile(p);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load profile");
    } finally {
      setLoading(false);
    }
  }, []);

  const updateProfile = useCallback((newProfile: Profile) => {
    // 1. Update local state immediately for snappy UI
    setProfile(newProfile);
    setSaveStatus("saving");

    // 2. Debounce the API call
    if (saveTimer.current) clearTimeout(saveTimer.current);
    if (statusTimer.current) clearTimeout(statusTimer.current);

    saveTimer.current = setTimeout(async () => {
      try {
        await api.updateProfile(newProfile);
        setSaveStatus("saved");
        statusTimer.current = setTimeout(() => setSaveStatus("idle"), 2000);
      } catch (err) {
        console.error("Failed to save profile:", err);
        setSaveStatus("error");
      }
    }, 1000);
  }, []);

  const importResume = useCallback(async (file: File) => {
    setSaveStatus("saving");
    try {
      const newProfile = await api.importResume(file);
      setProfile(newProfile);
      setSaveStatus("saved");
      statusTimer.current = setTimeout(() => setSaveStatus("idle"), 2000);
      return newProfile;
    } catch (err) {
      setSaveStatus("error");
      throw err;
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  return {
    profile,
    loading,
    error,
    saveStatus,
    updateProfile,
    importResume,
    refetch: fetchProfile,
  };
}
