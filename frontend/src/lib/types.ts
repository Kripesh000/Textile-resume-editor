export interface User {
  id: string;
  email: string;
  name: string;
}

export interface Bullet {
  id: string;
  text: string;
  tags: string[];
  order: number;
}

export interface Experience {
  id: string;
  company: string;
  role: string;
  location: string;
  start: string;
  end: string;
  tags: string[];
  bullets: Bullet[];
}

export interface Project {
  id: string;
  name: string;
  tech_stack: string;
  date: string;
  tags: string[];
  bullets: Bullet[];
}

export interface Education {
  id: string;
  institution: string;
  degree: string;
  location: string;
  end: string;
  gpa: string | null;
  coursework: string | null;
  awards: string | null;
}

export interface SkillCategory {
  id: string;
  name: string;
  items: string[];
  tags: string[];
}

export interface Profile {
  user_id: string;
  name: string;
  email: string;
  phone: string;
  linkedin: string | null;
  github: string | null;
  website: string | null;
  experiences: Experience[];
  projects: Project[];
  education: Education[];
  skill_categories: SkillCategory[];
  sections?: ProfileSection[];
  created_at: string;
  updated_at: string;
}

export interface SectionOrder {
  title: string;
  type: string;
}

export interface ResumeVariant {
  id: string;
  user_id: string;
  profile_id: string;
  template_id: string;
  name: string;
  section_order: SectionOrder[];
  selected_experience_ids: string[];
  selected_project_ids: string[];
  selected_bullet_ids: string[];
  selected_skill_category_ids: string[];
  created_at: string;
  updated_at: string;
}

export interface TemplateConfig {
  id: string;
  name: string;
  tags: string[];
  max_experiences: number;
  max_projects: number;
  max_skill_categories: number;
  supports: {
    summary: boolean;
    photo: boolean;
    color_accent: boolean;
    two_column_skills: boolean;
  };
  section_order_locked: boolean;
  required_sections: string[];
}

export interface ImproviseResponse {
  improved_text: string;
  alternatives: string[];
}

// --- Legacy Types (to be migrated) ---

export type SectionType = "experience" | "education" | "projects" | "skills" | "summary" | "generic";

export interface SectionItem {
  id: string;
  [key: string]: any;
}

export interface Section {
  id: string;
  section_type: SectionType;
  title: string;
  order_index: number;
  items: SectionItem[];
}

export interface Resume {
  id: string;
  title: string;
  template_key: string;
  header_data: Record<string, string>;
  sections: Section[];
}

export interface ResumeListItem {
  id: string;
  title: string;
  updated_at: string;
}

export const SECTION_DEFAULTS: Record<SectionType, any> = {
  experience: { title: "Experience" },
  education: { title: "Education" },
  projects: { title: "Projects" },
  skills: { title: "Skills" },
  summary: { title: "Summary" },
  generic: { title: "Other" },
};

export interface ProfileItem {
  id: string;
  data: any;
}

export interface ProfileSection {
  id: string;
  section_type: string;
  title: string;
  items: ProfileItem[];
}
