"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { useProfile } from "@/hooks/useProfile";
import { 
  Profile, 
  Experience, 
  Education, 
  Project, 
  SkillCategory, 
  Bullet 
} from "@/lib/types";
const uuidv4 = () => crypto.randomUUID();

export default function ProfilePage() {
  const { user, loading: authLoading, logout } = useAuth();
  const router = useRouter();
  const { profile, loading, error, saveStatus, updateProfile, importResume } = useProfile();
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!authLoading && !user) router.push("/auth/login");
  }, [user, authLoading, router]);

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (!user || !profile) return null;

  const handleUpdate = (updates: Partial<Profile>) => {
    updateProfile({ ...profile, ...updates });
  };

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      await importResume(file);
    } catch (err) {
      alert("Failed to import resume. Please try again.");
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top bar */}
      <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 sticky top-0 z-10 shadow-sm">
        <div className="flex items-center gap-6">
          <h1
            className="text-xl font-bold cursor-pointer hover:text-blue-600 transition-colors"
            onClick={() => router.push("/editor")}
          >
            LaTeXify
          </h1>
          <nav className="flex gap-1">
            <button
              onClick={() => router.push("/editor")}
              className="text-sm px-4 py-2 rounded-lg text-gray-600 hover:bg-gray-100 transition-colors"
            >
              My Resumes
            </button>
            <button className="text-sm px-4 py-2 rounded-lg bg-blue-50 text-blue-700 font-semibold">
              Master Profile
            </button>
          </nav>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="flex flex-col items-end">
            <span className="text-sm font-medium text-gray-900">{user.name}</span>
            <span className="text-[10px] text-gray-500">{saveStatus === 'saving' ? 'Saving...' : saveStatus === 'saved' ? 'All changes saved' : 'Idle'}</span>
          </div>
          <button
            onClick={() => { logout(); router.push("/"); }}
            className="text-sm text-gray-500 hover:text-red-600 transition-colors"
          >
            Sign out
          </button>
        </div>
      </header>

      <div className="max-w-5xl mx-auto py-12 px-6">
        <div className="flex justify-between items-start mb-8">
          <div>
            <h2 className="text-3xl font-bold text-gray-900">Master Profile</h2>
            <p className="text-gray-500 mt-1">
              Your "Single Source of Truth". All resume variants are built from this content.
            </p>
          </div>
          <div className="flex gap-2">
            <input 
              type="file" 
              ref={fileInputRef} 
              className="hidden" 
              accept=".pdf,.tex" 
              onChange={handleImport}
            />
            <button 
              onClick={() => fileInputRef.current?.click()}
              className="px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors shadow-sm"
            >
              Import from PDF/LaTeX
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 gap-8">
          {/* Personal Info */}
          <section className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100 bg-gray-50/50">
              <h3 className="font-bold text-gray-900 text-lg">Contact Information</h3>
            </div>
            <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
              <ProfileInput label="Full Name" value={profile.name} onChange={(val) => handleUpdate({ name: val })} />
              <ProfileInput label="Email" value={profile.email} onChange={(val) => handleUpdate({ email: val })} />
              <ProfileInput label="Phone" value={profile.phone} onChange={(val) => handleUpdate({ phone: val })} />
              <ProfileInput label="LinkedIn" value={profile.linkedin || ""} onChange={(val) => handleUpdate({ linkedin: val })} />
              <ProfileInput label="GitHub" value={profile.github || ""} onChange={(val) => handleUpdate({ github: val })} />
              <ProfileInput label="Website" value={profile.website || ""} onChange={(val) => handleUpdate({ website: val })} />
            </div>
          </section>

          {/* Experience */}
          <ProfileSectionList<Experience>
            title="Professional Experience"
            items={profile.experiences}
            onUpdate={(items) => handleUpdate({ experiences: items })}
            renderItem={(item, onUpdate, onDelete) => (
              <ExperienceItemEditor item={item} onUpdate={onUpdate} onDelete={onDelete} />
            )}
            newItem={() => ({
              id: uuidv4(),
              company: "",
              role: "",
              location: "",
              start: "",
              end: "",
              tags: [],
              bullets: []
            })}
          />

          {/* Education */}
          <ProfileSectionList<Education>
            title="Education"
            items={profile.education}
            onUpdate={(items) => handleUpdate({ education: items })}
            renderItem={(item, onUpdate, onDelete) => (
              <EducationItemEditor item={item} onUpdate={onUpdate} onDelete={onDelete} />
            )}
            newItem={() => ({
              id: uuidv4(),
              institution: "",
              degree: "",
              location: "",
              end: "",
              gpa: null,
              coursework: null,
              awards: null
            })}
          />

          {/* Projects */}
          <ProfileSectionList<Project>
            title="Projects"
            items={profile.projects}
            onUpdate={(items) => handleUpdate({ projects: items })}
            renderItem={(item, onUpdate, onDelete) => (
              <ProjectItemEditor item={item} onUpdate={onUpdate} onDelete={onDelete} />
            )}
            newItem={() => ({
              id: uuidv4(),
              name: "",
              tech_stack: "",
              date: "",
              tags: [],
              bullets: []
            })}
          />

          {/* Skills */}
          <ProfileSectionList<SkillCategory>
            title="Skills"
            items={profile.skill_categories}
            onUpdate={(items) => handleUpdate({ skill_categories: items })}
            renderItem={(item, onUpdate, onDelete) => (
              <SkillCategoryEditor item={item} onUpdate={onUpdate} onDelete={onDelete} />
            )}
            newItem={() => ({
              id: uuidv4(),
              name: "",
              items: [],
              tags: []
            })}
          />
        </div>
      </div>
    </div>
  );
}

// --- Helper Components ---

function ProfileInput({ label, value, onChange, placeholder }: { label: string, value: string, onChange: (v: string) => void, placeholder?: string }) {
  return (
    <div>
      <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">{label}</label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full px-4 py-2.5 bg-white border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all shadow-sm"
      />
    </div>
  );
}

interface SectionListProps<T> {
  title: string;
  items: T[];
  onUpdate: (items: T[]) => void;
  renderItem: (item: T, onUpdate: (item: T) => void, onDelete: () => void) => React.ReactNode;
  newItem: () => T;
}

function ProfileSectionList<T extends { id: string }>({ title, items, onUpdate, renderItem, newItem }: SectionListProps<T>) {
  const [isExpanded, setIsExpanded] = useState(true);

  const handleUpdateItem = (updatedItem: T) => {
    onUpdate(items.map(i => i.id === updatedItem.id ? updatedItem : i));
  };

  const handleDeleteItem = (id: string) => {
    onUpdate(items.filter(i => i.id !== id));
  };

  const handleAdd = () => {
    onUpdate([...items, newItem()]);
  };

  return (
    <section className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <div 
        className="px-6 py-4 border-b border-gray-100 bg-gray-50/50 flex justify-between items-center cursor-pointer hover:bg-gray-100/50 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-3">
          <h3 className="font-bold text-gray-900 text-lg">{title}</h3>
          <span className="text-xs font-semibold bg-gray-200 text-gray-600 px-2.5 py-1 rounded-full">{items.length}</span>
        </div>
        <button className="text-gray-400 hover:text-gray-600 transition-colors">
          {isExpanded ? 'Collapse' : 'Expand'}
        </button>
      </div>

      {isExpanded && (
        <div className="p-6">
          <div className="flex flex-col gap-6">
            {items.map((item, index) => (
              <div key={`${item.id}-${index}`}>
                {renderItem(
                  item, 
                  handleUpdateItem, 
                  () => handleDeleteItem(item.id)
                )}
              </div>
            ))}
          </div>
          <button 
            onClick={handleAdd}
            className="mt-6 w-full py-4 border-2 border-dashed border-gray-200 rounded-xl text-gray-400 hover:border-blue-400 hover:text-blue-600 hover:bg-blue-50 transition-all font-medium flex items-center justify-center gap-2"
          >
            <span className="text-xl">+</span> Add {title.replace('Professional ', '').slice(0, -1)}
          </button>
        </div>
      )}
    </section>
  );
}

// --- Item Editors ---

function ExperienceItemEditor({ item, onUpdate, onDelete }: { item: Experience, onUpdate: (i: Experience) => void, onDelete: () => void }) {
  const updateField = (field: keyof Experience, value: any) => {
    onUpdate({ ...item, [field]: value });
  };

  return (
    <div className="group border border-gray-200 rounded-xl p-6 bg-white hover:border-blue-300 hover:shadow-md transition-all relative">
      <button 
        onClick={onDelete}
        className="absolute top-4 right-4 text-gray-300 hover:text-red-600 transition-colors"
      >
        Remove
      </button>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <ProfileInput label="Company" value={item.company} onChange={(v) => updateField('company', v)} />
        <ProfileInput label="Role" value={item.role} onChange={(v) => updateField('role', v)} />
        <ProfileInput label="Location" value={item.location} onChange={(v) => updateField('location', v)} />
        <div className="flex gap-4">
          <ProfileInput label="Start" value={item.start} onChange={(v) => updateField('start', v)} placeholder="MM/YYYY" />
          <ProfileInput label="End" value={item.end} onChange={(v) => updateField('end', v)} placeholder="MM/YYYY or Present" />
        </div>
      </div>

      <BulletEditor bullets={item.bullets} onUpdate={(b) => updateField('bullets', b)} />
    </div>
  );
}

function EducationItemEditor({ item, onUpdate, onDelete }: { item: Education, onUpdate: (i: Education) => void, onDelete: () => void }) {
  const updateField = (field: keyof Education, value: any) => {
    onUpdate({ ...item, [field]: value });
  };

  return (
    <div className="group border border-gray-200 rounded-xl p-6 bg-white hover:border-blue-300 hover:shadow-md transition-all relative">
      <button 
        onClick={onDelete}
        className="absolute top-4 right-4 text-gray-300 hover:text-red-600 transition-colors"
      >
        Remove
      </button>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <ProfileInput label="Institution" value={item.institution} onChange={(v) => updateField('institution', v)} />
        <ProfileInput label="Degree" value={item.degree} onChange={(v) => updateField('degree', v)} />
        <ProfileInput label="Location" value={item.location} onChange={(v) => updateField('location', v)} />
        <ProfileInput label="End Date" value={item.end} onChange={(v) => updateField('end', v)} placeholder="MM/YYYY" />
        <ProfileInput label="GPA" value={item.gpa || ""} onChange={(v) => updateField('gpa', v)} />
        <ProfileInput label="Coursework" value={item.coursework || ""} onChange={(v) => updateField('coursework', v)} />
      </div>
    </div>
  );
}

function ProjectItemEditor({ item, onUpdate, onDelete }: { item: Project, onUpdate: (i: Project) => void, onDelete: () => void }) {
  const updateField = (field: keyof Project, value: any) => {
    onUpdate({ ...item, [field]: value });
  };

  return (
    <div className="group border border-gray-200 rounded-xl p-6 bg-white hover:border-blue-300 hover:shadow-md transition-all relative">
      <button 
        onClick={onDelete}
        className="absolute top-4 right-4 text-gray-300 hover:text-red-600 transition-colors"
      >
        Remove
      </button>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <ProfileInput label="Project Name" value={item.name} onChange={(v) => updateField('name', v)} />
        <ProfileInput label="Tech Stack" value={item.tech_stack} onChange={(v) => updateField('tech_stack', v)} placeholder="React, Python, etc." />
        <ProfileInput label="Date" value={item.date} onChange={(v) => updateField('date', v)} placeholder="MM/YYYY" />
      </div>

      <BulletEditor bullets={item.bullets} onUpdate={(b) => updateField('bullets', b)} />
    </div>
  );
}

function SkillCategoryEditor({ item, onUpdate, onDelete }: { item: SkillCategory, onUpdate: (i: SkillCategory) => void, onDelete: () => void }) {
  return (
    <div className="group border border-gray-200 rounded-xl p-6 bg-white hover:border-blue-300 hover:shadow-md transition-all relative">
      <button 
        onClick={onDelete}
        className="absolute top-4 right-4 text-gray-300 hover:text-red-600 transition-colors"
      >
        Remove
      </button>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <ProfileInput label="Category" value={item.name} onChange={(v) => onUpdate({ ...item, name: v })} placeholder="Languages, Frameworks, etc." />
        <div>
          <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1.5">Items (comma separated)</label>
          <input
            type="text"
            value={item.items.join(', ')}
            onChange={(e) => onUpdate({ ...item, items: e.target.value.split(',').map(s => s.trim()).filter(s => s) })}
            placeholder="Python, JavaScript, SQL"
            className="w-full px-4 py-2.5 bg-white border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all shadow-sm"
          />
        </div>
      </div>
    </div>
  );
}

function BulletEditor({ bullets, onUpdate }: { bullets: Bullet[], onUpdate: (b: Bullet[]) => void }) {
  const handleUpdateBullet = (id: string, text: string) => {
    onUpdate(bullets.map(b => b.id === id ? { ...b, text } : b));
  };

  const handleAdd = () => {
    onUpdate([...bullets, { id: uuidv4(), text: "", tags: [], order: bullets.length }]);
  };

  const handleDelete = (id: string) => {
    onUpdate(bullets.filter(b => b.id !== id));
  };

  return (
    <div className="mt-4">
      <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Bullet Points</label>
      <div className="space-y-2">
        {bullets.map((bullet, idx) => (
          <div key={bullet.id} className="flex gap-2 group/bullet">
            <span className="text-gray-300 pt-2.5 select-none font-medium">{idx + 1}.</span>
            <textarea
              value={bullet.text}
              onChange={(e) => handleUpdateBullet(bullet.id, e.target.value)}
              className="flex-1 px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all resize-none h-10 min-h-[40px] focus:h-24 hover:bg-white focus:bg-white"
              rows={1}
            />
            <button 
              onClick={() => handleDelete(bullet.id)}
              className="text-gray-300 hover:text-red-500 opacity-0 group-hover/bullet:opacity-100 transition-opacity p-2"
            >
              &times;
            </button>
          </div>
        ))}
        <button 
          onClick={handleAdd}
          className="text-xs font-bold text-blue-600 hover:text-blue-700 transition-colors flex items-center gap-1 mt-2"
        >
          <span>+</span> Add Bullet Point
        </button>
      </div>
    </div>
  );
}
