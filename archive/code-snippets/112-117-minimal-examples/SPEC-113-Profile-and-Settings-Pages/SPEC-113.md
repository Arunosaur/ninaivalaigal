# SPEC-113: Profile & Settings Pages
**Project:** Medhasys / Ninaivalaigal
**Status:** Draft
**Owner:** Frontend Guild
**Last Updated:** 2025-10-11

### components/ProfileForm.tsx
```tsx
'use client';
import React from 'react';

export default function ProfileForm() {
  return (
    <form className="space-y-4 p-4 max-w-md mx-auto">
      <label className="block">
        <span className="text-sm font-medium text-gray-700">Name</span>
        <input type="text" className="mt-1 w-full border rounded p-2" />
      </label>
      <button className="bg-blue-600 text-white px-4 py-2 rounded">Save</button>
    </form>
  );
}
```

### components/SettingsLayout.tsx
```tsx
import React from 'react';

export default function SettingsLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <aside className="w-64 bg-gray-100 p-4">Sidebar</aside>
      <main className="flex-1 p-6">{children}</main>
    </div>
  );
}
```
