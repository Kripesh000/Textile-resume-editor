export interface User {
  id: string;
  email: string;
  name: string;
  created_at: string;
}

export interface ExperienceItem {
  company: string;
  role: string;
  location: string;
  start_date: string;
  end_date: string;
  bullets: string[];
}

export interface EducationItem {
  institution: string;
  degree: string;
  location: string;
  start_date: string;
  end_date: string;
  details: string[];
}

export interface ProjectItem {
  name: string;
  tech_stack: string;
  url: string;
  bullets: string[];
}

export interface SkillItem {
  category: string;
  items: string[];
}

export interface GenericItem {
  text: string;
}

export type SectionItem = ExperienceItem | EducationItem | ProjectItem | SkillItem | GenericItem;

export type SectionType = "education" | "experience" | "project" | "skills" | "generic";

export interface Section {
  id: string;
  resume_id: string;
  section_type: SectionType;
  title: string;
  order_index: number;
  items: SectionItem[];
  created_at: string;
  updated_at: string;
}

export interface HeaderData {
  name: string;
  email: string;
  phone: string;
  linkedin: string;
  github: string;
  website: string;
}

export interface Resume {
  id: string;
  user_id: string;
  title: string;
  template_key: string;
  header_data: HeaderData;
  sections: Section[];
  created_at: string;
  updated_at: string;
}

export interface ResumeListItem {
  id: string;
  title: string;
  template_key: string;
  created_at: string;
  updated_at: string;
}

export interface ImproviseResponse {
  improved_text: string;
  alternatives: string[];
}

// --- Profile types ---

export interface ProfileItem {
  id: string;
  section_id: string;
  order_index: number;
  data: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface ProfileSection {
  id: string;
  user_id: string;
  section_type: string;
  title: string;
  order_index: number;
  items: ProfileItem[];
  created_at: string;
  updated_at: string;
}

export interface PersonalInfo {
  name: string;
  email: string;
  phone: string;
  linkedin: string;
  github: string;
  website: string;
}

export interface Profile {
  personal_info: PersonalInfo;
  sections: ProfileSection[];
}

export const SECTION_DEFAULTS: Record<SectionType, { title: string; item: SectionItem }> = {
  education: {
    title: "Education",
    item: { institution: "", degree: "", location: "", start_date: "", end_date: "", details: [] },
  },
  experience: {
    title: "Experience",
    item: { company: "", role: "", location: "", start_date: "", end_date: "", bullets: [] },
  },
  project: {
    title: "Projects",
    item: { name: "", tech_stack: "", url: "", bullets: [] },
  },
  skills: {
    title: "Skills",
    item: { category: "", items: [] },
  },
  generic: {
    title: "Section",
    item: { text: "" },
  },
};
