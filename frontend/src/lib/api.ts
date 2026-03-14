const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || "Request failed");
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

// Auth
export const api = {
  register: (data: { email: string; name: string; password: string }) =>
    request<{ id: string; email: string; name: string }>("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  login: (data: { email: string; password: string }) =>
    request<{ access_token: string }>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getMe: () => request<{ id: string; email: string; name: string }>("/api/v1/auth/me"),

  // Resumes
  listResumes: () =>
    request<{ id: string; title: string; template_key: string; created_at: string; updated_at: string }[]>(
      "/api/v1/resumes"
    ),

  createResume: (data: { title?: string; template_key?: string }) =>
    request("/api/v1/resumes", { method: "POST", body: JSON.stringify(data) }),

  getResume: (id: string) => request<import("./types").Resume>(`/api/v1/resumes/${id}`),

  updateResume: (id: string, data: { title?: string; template_key?: string; header_data?: Record<string, string> }) =>
    request(`/api/v1/resumes/${id}`, { method: "PUT", body: JSON.stringify(data) }),

  deleteResume: (id: string) =>
    request(`/api/v1/resumes/${id}`, { method: "DELETE" }),

  // Sections
  createSection: (resumeId: string, data: { section_type: string; title: string; order_index: number }) =>
    request<import("./types").Section>(`/api/v1/resumes/${resumeId}/sections`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updateSection: (resumeId: string, sectionId: string, data: { title?: string; items?: unknown[] }) =>
    request<import("./types").Section>(`/api/v1/resumes/${resumeId}/sections/${sectionId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  deleteSection: (resumeId: string, sectionId: string) =>
    request(`/api/v1/resumes/${resumeId}/sections/${sectionId}`, { method: "DELETE" }),

  reorderSections: (resumeId: string, items: { section_id: string; order_index: number }[]) =>
    request(`/api/v1/resumes/${resumeId}/sections/reorder`, {
      method: "PUT",
      body: JSON.stringify(items),
    }),

  // PDF
  generatePdf: async (resumeId: string): Promise<Blob> => {
    const token = getToken();
    const res = await fetch(`${API_BASE}/api/v1/resumes/${resumeId}/pdf`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(body.detail || "PDF generation failed");
    }
    return res.blob();
  },

  // Upload
  uploadResume: async (file: File): Promise<import("./types").Resume> => {
    const token = getToken();
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${API_BASE}/api/v1/resumes/upload`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(body.detail || "Upload failed");
    }
    return res.json();
  },

  // Profile
  getProfile: () => request<import("./types").Profile>("/api/v1/profile"),

  updatePersonalInfo: (data: Partial<import("./types").PersonalInfo>) =>
    request<import("./types").PersonalInfo>("/api/v1/profile/personal", {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  createProfileSection: (data: { section_type: string; title: string; order_index?: number }) =>
    request<import("./types").ProfileSection>("/api/v1/profile/sections", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updateProfileSection: (sectionId: string, data: { title?: string; order_index?: number }) =>
    request<import("./types").ProfileSection>(`/api/v1/profile/sections/${sectionId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  deleteProfileSection: (sectionId: string) =>
    request(`/api/v1/profile/sections/${sectionId}`, { method: "DELETE" }),

  createProfileItem: (sectionId: string, data: { data: Record<string, unknown>; order_index?: number }) =>
    request<import("./types").ProfileItem>(`/api/v1/profile/sections/${sectionId}/items`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updateProfileItem: (itemId: string, data: { data?: Record<string, unknown>; order_index?: number }) =>
    request<import("./types").ProfileItem>(`/api/v1/profile/items/${itemId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  deleteProfileItem: (itemId: string) =>
    request(`/api/v1/profile/items/${itemId}`, { method: "DELETE" }),

  importToResume: (data: { resume_id: string; section_id: string; item_ids: string[] }) =>
    request<{ status: string; imported: number }>("/api/v1/profile/import-to-resume", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  saveToProfile: (data: { resume_id: string; section_id: string }) =>
    request<{ status: string; added: number; section_type: string }>("/api/v1/profile/save-from-resume", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // AI
  improvise: (data: { text: string; context?: { role?: string; company?: string; section_type?: string } }) =>
    request<import("./types").ImproviseResponse>("/api/v1/ai/improvise", {
      method: "POST",
      body: JSON.stringify(data),
    }),
};
