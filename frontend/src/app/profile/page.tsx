"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import {
  Profile,
  PersonalInfo,
  ProfileSection,
  ProfileItem,
  SECTION_DEFAULTS,
  SectionType,
} from "@/lib/types";

const SECTION_TYPES: { type: string; label: string }[] = [
  { type: "experience", label: "Experience" },
  { type: "education", label: "Education" },
  { type: "project", label: "Projects" },
  { type: "skills", label: "Skills" },
  { type: "generic", label: "Other" },
];

export default function ProfilePage() {
  const { user, loading: authLoading, logout } = useAuth();
  const router = useRouter();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!authLoading && !user) router.push("/auth/login");
  }, [user, authLoading, router]);

  const loadProfile = useCallback(async () => {
    try {
      const p = await api.getProfile();
      setProfile(p);
    } catch {
      // Profile might be empty
      setProfile({ personal_info: { name: "", email: "", phone: "", linkedin: "", github: "", website: "" }, sections: [] });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (user) loadProfile();
  }, [user, loadProfile]);

  const savePersonalInfo = async (info: Partial<PersonalInfo>) => {
    setSaving(true);
    try {
      const updated = await api.updatePersonalInfo(info);
      setProfile((p) => p ? { ...p, personal_info: updated } : p);
    } finally {
      setSaving(false);
    }
  };

  const addSection = async (type: string) => {
    const defaults = SECTION_DEFAULTS[type as SectionType];
    const section = await api.createProfileSection({
      section_type: type,
      title: defaults?.title || "New Section",
      order_index: profile?.sections.length || 0,
    });
    setProfile((p) => p ? { ...p, sections: [...p.sections, { ...section, items: [] }] } : p);
  };

  const deleteSection = async (sectionId: string) => {
    await api.deleteProfileSection(sectionId);
    setProfile((p) => p ? { ...p, sections: p.sections.filter((s) => s.id !== sectionId) } : p);
  };

  const addItem = async (sectionId: string, sectionType: string) => {
    const defaults = SECTION_DEFAULTS[sectionType as SectionType];
    const item = await api.createProfileItem(sectionId, {
      data: defaults?.item ? { ...defaults.item } : { text: "" },
    });
    setProfile((p) => {
      if (!p) return p;
      return {
        ...p,
        sections: p.sections.map((s) =>
          s.id === sectionId ? { ...s, items: [...s.items, item] } : s
        ),
      };
    });
  };

  const updateItem = async (itemId: string, sectionId: string, data: Record<string, unknown>) => {
    await api.updateProfileItem(itemId, { data });
    setProfile((p) => {
      if (!p) return p;
      return {
        ...p,
        sections: p.sections.map((s) =>
          s.id === sectionId
            ? { ...s, items: s.items.map((i) => (i.id === itemId ? { ...i, data } : i)) }
            : s
        ),
      };
    });
  };

  const deleteItem = async (itemId: string, sectionId: string) => {
    await api.deleteProfileItem(itemId);
    setProfile((p) => {
      if (!p) return p;
      return {
        ...p,
        sections: p.sections.map((s) =>
          s.id === sectionId ? { ...s, items: s.items.filter((i) => i.id !== itemId) } : s
        ),
      };
    });
  };

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (!user || !profile) return null;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top bar */}
      <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6">
        <div className="flex items-center gap-4">
          <h1
            className="text-xl font-bold cursor-pointer"
            onClick={() => router.push("/editor")}
          >
            TeX<span className="text-blue-600">Tile</span>
          </h1>
          <nav className="flex gap-2 ml-4">
            <button
              onClick={() => router.push("/editor")}
              className="text-sm px-3 py-1.5 rounded-md text-gray-600 hover:bg-gray-100"
            >
              Editor
            </button>
            <button className="text-sm px-3 py-1.5 rounded-md bg-blue-50 text-blue-700 font-medium">
              Profile
            </button>
          </nav>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-700">{user.name}</span>
          <button
            onClick={() => { logout(); router.push("/"); }}
            className="text-sm text-gray-700 hover:text-gray-900"
          >
            Sign out
          </button>
        </div>
      </header>

      <div className="max-w-4xl mx-auto py-8 px-6">
        <h2 className="text-2xl font-bold mb-1">Your Profile</h2>
        <p className="text-gray-500 text-sm mb-8">
          Store all your information here. When building a resume, you can import items from your profile.
        </p>

        {/* Personal Information */}
        <PersonalInfoCard info={profile.personal_info} onSave={savePersonalInfo} saving={saving} />

        {/* Sections */}
        {profile.sections.map((section) => (
          <ProfileSectionCard
            key={section.id}
            section={section}
            onDeleteSection={() => deleteSection(section.id)}
            onAddItem={() => addItem(section.id, section.section_type)}
            onUpdateItem={(itemId, data) => updateItem(itemId, section.id, data)}
            onDeleteItem={(itemId) => deleteItem(itemId, section.id)}
          />
        ))}

        {/* Add section */}
        <div className="mt-6">
          <AddSectionMenu onAdd={addSection} />
        </div>
      </div>
    </div>
  );
}

// --- Personal Info Card ---

function PersonalInfoCard({
  info,
  onSave,
  saving,
}: {
  info: PersonalInfo;
  onSave: (data: Partial<PersonalInfo>) => void;
  saving: boolean;
}) {
  const [form, setForm] = useState(info);
  const [dirty, setDirty] = useState(false);

  useEffect(() => { setForm(info); }, [info]);

  const update = (field: keyof PersonalInfo, value: string) => {
    setForm((f) => ({ ...f, [field]: value }));
    setDirty(true);
  };

  const handleSave = () => {
    onSave(form);
    setDirty(false);
  };

  const fields: { key: keyof PersonalInfo; label: string; placeholder: string }[] = [
    { key: "name", label: "Full Name", placeholder: "John Doe" },
    { key: "email", label: "Email", placeholder: "john@example.com" },
    { key: "phone", label: "Phone", placeholder: "(555) 123-4567" },
    { key: "linkedin", label: "LinkedIn", placeholder: "linkedin.com/in/johndoe" },
    { key: "github", label: "GitHub", placeholder: "github.com/johndoe" },
    { key: "website", label: "Website", placeholder: "johndoe.com" },
  ];

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
      <h3 className="font-semibold text-lg mb-4">Personal Information</h3>
      <div className="grid grid-cols-2 gap-4">
        {fields.map((f) => (
          <div key={f.key}>
            <label className="block text-xs text-gray-500 mb-1">{f.label}</label>
            <input
              value={form[f.key]}
              onChange={(e) => update(f.key, e.target.value)}
              placeholder={f.placeholder}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
        ))}
      </div>
      {dirty && (
        <button
          onClick={handleSave}
          disabled={saving}
          className="mt-4 px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {saving ? "Saving..." : "Save"}
        </button>
      )}
    </div>
  );
}

// --- Profile Section Card ---

function ProfileSectionCard({
  section,
  onDeleteSection,
  onAddItem,
  onUpdateItem,
  onDeleteItem,
}: {
  section: ProfileSection;
  onDeleteSection: () => void;
  onAddItem: () => void;
  onUpdateItem: (itemId: string, data: Record<string, unknown>) => void;
  onDeleteItem: (itemId: string) => void;
}) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="bg-white border border-gray-200 rounded-lg mb-4">
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-lg">{section.title}</span>
          <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
            {section.section_type}
          </span>
          <span className="text-xs text-gray-400">{section.items.length} items</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="text-gray-500 hover:text-gray-700 text-sm"
          >
            {collapsed ? "Expand" : "Collapse"}
          </button>
          <button onClick={onDeleteSection} className="text-red-400 hover:text-red-600 text-sm">
            Delete
          </button>
        </div>
      </div>

      {!collapsed && (
        <div className="p-4 space-y-3">
          {section.items.map((item) => (
            <ProfileItemCard
              key={item.id}
              item={item}
              sectionType={section.section_type}
              onUpdate={(data) => onUpdateItem(item.id, data)}
              onDelete={() => onDeleteItem(item.id)}
            />
          ))}
          <button
            onClick={onAddItem}
            className="text-sm text-blue-600 hover:text-blue-700"
          >
            + Add {section.section_type === "skills" ? "category" : "entry"}
          </button>
        </div>
      )}
    </div>
  );
}

// --- Profile Item Card ---

function ProfileItemCard({
  item,
  sectionType,
  onUpdate,
  onDelete,
}: {
  item: ProfileItem;
  sectionType: string;
  onUpdate: (data: Record<string, unknown>) => void;
  onDelete: () => void;
}) {
  const [form, setForm] = useState<Record<string, unknown>>(item.data);
  const [dirty, setDirty] = useState(false);

  useEffect(() => { setForm(item.data); }, [item.data]);

  const updateField = (key: string, value: unknown) => {
    const updated = { ...form, [key]: value };
    setForm(updated);
    setDirty(true);
  };

  const handleSave = () => {
    onUpdate(form);
    setDirty(false);
  };

  const renderFields = () => {
    switch (sectionType) {
      case "experience":
        return <ExperienceItemFields form={form} onChange={updateField} />;
      case "education":
        return <EducationItemFields form={form} onChange={updateField} />;
      case "project":
        return <ProjectItemFields form={form} onChange={updateField} />;
      case "skills":
        return <SkillsItemFields form={form} onChange={updateField} />;
      default:
        return <GenericItemFields form={form} onChange={updateField} />;
    }
  };

  const label =
    sectionType === "experience"
      ? (form.role as string) || (form.company as string) || "New Experience"
      : sectionType === "education"
        ? (form.institution as string) || (form.degree as string) || "New Education"
        : sectionType === "project"
          ? (form.name as string) || "New Project"
          : sectionType === "skills"
            ? (form.category as string) || "New Category"
            : (form.text as string) || "New Item";

  return (
    <div className="border border-gray-200 rounded-md p-3">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-700 truncate">{label}</span>
        <div className="flex gap-2">
          {dirty && (
            <button
              onClick={handleSave}
              className="text-xs text-blue-600 hover:text-blue-700 font-medium"
            >
              Save
            </button>
          )}
          <button onClick={onDelete} className="text-xs text-red-400 hover:text-red-600">
            Remove
          </button>
        </div>
      </div>
      {renderFields()}
    </div>
  );
}

// --- Field Components ---

function Input({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <div>
      <label className="block text-xs text-gray-500 mb-0.5">{label}</label>
      <input
        value={value || ""}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
      />
    </div>
  );
}

function BulletList({
  label,
  items,
  onChange,
}: {
  label: string;
  items: string[];
  onChange: (items: string[]) => void;
}) {
  const bullets = items || [];
  return (
    <div className="col-span-2">
      <label className="block text-xs text-gray-500 mb-0.5">{label}</label>
      {bullets.map((b, i) => (
        <div key={i} className="flex items-center gap-1 mb-1">
          <span className="text-gray-400 text-xs">-</span>
          <input
            value={b}
            onChange={(e) => {
              const updated = [...bullets];
              updated[i] = e.target.value;
              onChange(updated);
            }}
            className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
          <button
            onClick={() => onChange(bullets.filter((_, idx) => idx !== i))}
            className="text-red-400 hover:text-red-600 text-xs px-1"
          >
            x
          </button>
        </div>
      ))}
      <button
        onClick={() => onChange([...bullets, ""])}
        className="text-xs text-blue-600 hover:text-blue-700"
      >
        + Add bullet
      </button>
    </div>
  );
}

function ExperienceItemFields({
  form,
  onChange,
}: {
  form: Record<string, unknown>;
  onChange: (key: string, value: unknown) => void;
}) {
  return (
    <div className="grid grid-cols-2 gap-2">
      <Input label="Role" value={form.role as string} onChange={(v) => onChange("role", v)} />
      <Input label="Company" value={form.company as string} onChange={(v) => onChange("company", v)} />
      <Input label="Location" value={form.location as string} onChange={(v) => onChange("location", v)} />
      <div className="flex gap-2">
        <Input label="Start" value={form.start_date as string} onChange={(v) => onChange("start_date", v)} placeholder="Jan 2023" />
        <Input label="End" value={form.end_date as string} onChange={(v) => onChange("end_date", v)} placeholder="Present" />
      </div>
      <BulletList label="Bullets" items={(form.bullets as string[]) || []} onChange={(v) => onChange("bullets", v)} />
    </div>
  );
}

function EducationItemFields({
  form,
  onChange,
}: {
  form: Record<string, unknown>;
  onChange: (key: string, value: unknown) => void;
}) {
  return (
    <div className="grid grid-cols-2 gap-2">
      <Input label="Institution" value={form.institution as string} onChange={(v) => onChange("institution", v)} />
      <Input label="Degree" value={form.degree as string} onChange={(v) => onChange("degree", v)} />
      <Input label="Location" value={form.location as string} onChange={(v) => onChange("location", v)} />
      <div className="flex gap-2">
        <Input label="Start" value={form.start_date as string} onChange={(v) => onChange("start_date", v)} placeholder="Aug 2019" />
        <Input label="End" value={form.end_date as string} onChange={(v) => onChange("end_date", v)} placeholder="May 2023" />
      </div>
      <BulletList label="Details" items={(form.details as string[]) || []} onChange={(v) => onChange("details", v)} />
    </div>
  );
}

function ProjectItemFields({
  form,
  onChange,
}: {
  form: Record<string, unknown>;
  onChange: (key: string, value: unknown) => void;
}) {
  return (
    <div className="grid grid-cols-2 gap-2">
      <Input label="Name" value={form.name as string} onChange={(v) => onChange("name", v)} />
      <Input label="Tech Stack" value={form.tech_stack as string} onChange={(v) => onChange("tech_stack", v)} />
      <Input label="URL" value={form.url as string} onChange={(v) => onChange("url", v)} />
      <div />
      <BulletList label="Bullets" items={(form.bullets as string[]) || []} onChange={(v) => onChange("bullets", v)} />
    </div>
  );
}

function SkillsItemFields({
  form,
  onChange,
}: {
  form: Record<string, unknown>;
  onChange: (key: string, value: unknown) => void;
}) {
  const items = (form.items as string[]) || [];
  return (
    <div className="grid grid-cols-2 gap-2">
      <Input label="Category" value={form.category as string} onChange={(v) => onChange("category", v)} placeholder="Languages" />
      <div>
        <label className="block text-xs text-gray-500 mb-0.5">Items (comma-separated)</label>
        <input
          value={items.join(", ")}
          onChange={(e) => onChange("items", e.target.value.split(",").map((s) => s.trim()))}
          placeholder="Python, JavaScript, Go"
          className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
      </div>
    </div>
  );
}

function GenericItemFields({
  form,
  onChange,
}: {
  form: Record<string, unknown>;
  onChange: (key: string, value: unknown) => void;
}) {
  return (
    <Input label="Text" value={form.text as string} onChange={(v) => onChange("text", v)} placeholder="Enter text..." />
  );
}

// --- Add Section Menu ---

function AddSectionMenu({ onAdd }: { onAdd: (type: string) => void }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="w-full py-3 border-2 border-dashed border-gray-300 rounded-lg text-gray-500 hover:border-blue-400 hover:text-blue-600 transition-colors"
      >
        + Add Section
      </button>
      {open && (
        <div className="absolute top-full mt-1 left-0 w-full bg-white border border-gray-200 rounded-lg shadow-lg z-10">
          {SECTION_TYPES.map((opt) => (
            <button
              key={opt.type}
              onClick={() => { onAdd(opt.type); setOpen(false); }}
              className="w-full px-4 py-2 text-left hover:bg-gray-50 first:rounded-t-lg last:rounded-b-lg"
            >
              {opt.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
