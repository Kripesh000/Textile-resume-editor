const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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

import { User, Profile, ResumeVariant, TemplateConfig, ImproviseResponse, Resume, ResumeListItem, ProfileSection } from "./types";

function mapProfileToLegacy(p: Profile): Profile {
  const sections: ProfileSection[] = [
    {
      id: "legacy-exp",
      title: "Experience",
      section_type: "experience",
      items: (p.experiences || []).map(e => ({ id: e.id, data: e }))
    },
    {
      id: "legacy-edu",
      title: "Education",
      section_type: "education",
      items: (p.education || []).map(e => ({ id: e.id, data: e }))
    },
    {
      id: "legacy-proj",
      title: "Projects",
      section_type: "projects",
      items: (p.projects || []).map(pj => ({ id: pj.id, data: pj }))
    },
    {
      id: "legacy-skills",
      title: "Skills",
      section_type: "skills",
      items: (p.skill_categories || []).map(s => ({ id: s.id, data: s }))
    }
  ];
  return { ...p, sections };
}

export const api = {
  // Auth
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

  getMe: () => request<User>("/api/v1/auth/me"),

  // Profile
  getProfile: () => request<Profile>("/api/v1/profile").then(mapProfileToLegacy),

  updateProfile: (data: Profile) =>
    request<Profile>("/api/v1/profile", {
      method: "PUT",
      body: JSON.stringify(data),
    }).then(mapProfileToLegacy),

  importResume: async (file: File): Promise<Profile> => {
    const token = getToken();
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${API_BASE}/api/v1/profile/import`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(body.detail || "Import failed");
    }
    return res.json().then(mapProfileToLegacy);
  },

  // Templates
  listTemplates: () => request<TemplateConfig[]>("/api/v1/templates"),
  getTemplate: (id: string) => request<TemplateConfig>(`/api/v1/templates/${id}`),
  getTemplateThumbnailUrl: (id: string) => `${API_BASE}/api/v1/templates/${id}/thumbnail`,

  // Variants
  listVariants: () => request<ResumeVariant[]>("/api/v1/variants"), // Note: Need to make sure this exists or use profile variants
  
  renderVariant: async (variantId: string): Promise<Blob> => {
    const token = getToken();
    const res = await fetch(`${API_BASE}/api/v1/variants/${variantId}/render`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(body.detail || "PDF generation failed");
    }
    return res.blob();
  },

  // AI
  improvise: (data: { text: string; context?: { role?: string; company?: string; section_type?: string } }) =>
    request<ImproviseResponse>("/api/v1/ai/improvise", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Legacy / Compatibility methods
  listResumes: () => request<any[]>("/api/v1/variants").then(list => list.map(v => ({ ...v, title: v.name, template_key: v.template_id }))),
  getResume: (id: string) => request<any>(`/api/v1/variants/${id}`).then(v => ({ ...v, title: v.name, template_key: v.template_id })),
  createResume: (data: any) => request<Resume>("/api/v1/variants", {
    method: "POST",
    body: JSON.stringify({ ...data, name: data.title || "New Resume", template_id: "jake_classic" }),
  }),
  updateResume: (id: string, data: any) => request<Resume>(`/api/v1/variants/${id}`, {
    method: "PUT",
    // Map template_key to template_id for the backend
    body: JSON.stringify({ ...data, name: data.title, ...(data.template_key ? { template_id: data.template_key } : {}) }),
  }),
  deleteResume: (id: string) => request<void>(`/api/v1/variants/${id}`, {
    method: "DELETE",
  }),
  
  createSection: (resumeId: string, data: any) => 
    request<any>(`/api/v1/variants/${resumeId}/sections`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  updateSection: (resumeId: string, sectionId: string, data: any) => 
    request<any>(`/api/v1/variants/${resumeId}/sections/${sectionId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  deleteSection: (resumeId: string, sectionId: string) => 
    request<any>(`/api/v1/variants/${resumeId}/sections/${sectionId}`, {
      method: "DELETE",
    }),
  reorderSections: (resumeId: string, data: any) => 
    request<any>(`/api/v1/variants/${resumeId}/reorder`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  uploadResume: async (file: File) => {
    const profile = await api.importResume(file);
    const variant = await api.createResume({ title: "Imported Resume" });
    return variant;
  },
  uploadLatex: async (file: File) => {
    const profile = await api.importResume(file);
    const variant = await api.createResume({ title: "Imported LaTeX Resume" });
    return variant;
  },
  generatePdf: async (id: string): Promise<Blob> => {
    const token = getToken();
    const headers: Record<string, string> = {
      ...(token ? { "Authorization": `Bearer ${token}` } : {}),
    };
    const res = await fetch(`${API_BASE}/api/v1/variants/${id}/render`, {
      method: "POST",
      headers,
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(body.detail || "PDF generation failed");
    }
    return res.blob();
  },
  importToResume: (data: { resume_id: string; item_ids: string[] }) => 
    request<any>(`/api/v1/variants/${data.resume_id}/import`, {
      method: "POST",
      body: JSON.stringify(data.item_ids),
    }),
};
