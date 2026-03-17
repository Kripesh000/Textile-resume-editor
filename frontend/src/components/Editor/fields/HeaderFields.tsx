"use client";

interface HeaderFieldsProps {
  data: Record<string, string>;
  onChange: (data: Record<string, string>) => void;
}

const FIELDS = [
  { key: "name", label: "Full Name", placeholder: "John Doe" },
  { key: "email", label: "Email", placeholder: "john@example.com" },
  { key: "phone", label: "Phone", placeholder: "(555) 123-4567" },
  { key: "linkedin", label: "LinkedIn", placeholder: "linkedin.com/in/johndoe" },
  { key: "github", label: "GitHub", placeholder: "github.com/johndoe" },
  { key: "website", label: "Website", placeholder: "johndoe.dev" },
];

export default function HeaderFields({ data, onChange }: HeaderFieldsProps) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 mb-4">
      <h3 className="font-semibold text-lg mb-3">Personal Information</h3>
      <div className="grid grid-cols-2 gap-3">
        {FIELDS.map((field) => (
          <div key={field.key}>
            <label className="block text-xs font-medium text-gray-700 mb-1">{field.label}</label>
            <input
              type="text"
              value={(data as unknown as Record<string, string>)?.[field.key] || ""}
              onChange={(e) => onChange({ [field.key]: e.target.value })}
              placeholder={field.placeholder}
              className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
        ))}
      </div>
    </div>
  );
}
