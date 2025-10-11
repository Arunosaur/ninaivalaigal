# SPEC-116: Internal Frontend Migration
**Project:** Medhasys / Ninaivalaigal
**Status:** Draft
**Owner:** Frontend Guild
**Last Updated:** 2025-10-11

### components/Button.tsx
```tsx
export default function Button({ label }: { label: string }) {
  return <button className="bg-blue-500 text-white px-3 py-1 rounded">{label}</button>;
}
```

### app/actions/createMemory.ts
```ts
'use server';

export async function createMemory(data: FormData) {
  const title = data.get('title');
  // TODO: call backend API
  return { ok: true, title };
}
```
