# Blog API — Frontend Integration Guide

Base URL: `https://api.noorrixmotors.co.uk`

Set in your Next.js `.env.local`:
```
NEXT_PUBLIC_API_URL=https://api.noorrixmotors.co.uk
```

---

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/blogs/` | All published posts |
| GET | `/api/blogs/?featured=true` | Featured post only |
| GET | `/api/blogs/?category=Car Tips` | Posts by category |
| GET | `/api/blogs/<slug>/` | Single post with full body |

No authentication required on any endpoint.

---

## Usage Examples

### Fetch all posts (Server Component)

```js
// src/app/blogs/page.js

const BASE = process.env.NEXT_PUBLIC_API_URL;

async function fetchBlogs() {
  const [postsRes, featuredRes] = await Promise.all([
    fetch(`${BASE}/api/blogs/`,              { next: { revalidate: 60 } }),
    fetch(`${BASE}/api/blogs/?featured=true`, { next: { revalidate: 60 } }),
  ]);
  const posts    = await postsRes.json();
  const featured = await featuredRes.json();
  return { posts, featured: featured[0] || null };
}

export default async function BlogsPage() {
  const { posts, featured } = await fetchBlogs();
  return <Blogs posts={posts} featuredPost={featured} />;
}
```

---

### Fetch a single post (Server Component)

```js
// src/app/blogs/[slug]/page.js

const BASE = process.env.NEXT_PUBLIC_API_URL;

async function fetchPost(slug) {
  const res = await fetch(`${BASE}/api/blogs/${slug}/`, {
    next: { revalidate: 60 },
  });
  if (!res.ok) return null;
  return res.json();
}

export default async function BlogPostPage({ params }) {
  const post = await fetchPost(params.slug);
  if (!post) notFound();
  return <BlogDetail post={post} />;
}
```

---

### Fetch by category (Client Component)

```js
const BASE = process.env.NEXT_PUBLIC_API_URL;

async function fetchByCategory(category) {
  const res = await fetch(
    `${BASE}/api/blogs/?category=${encodeURIComponent(category)}`
  );
  return res.json();
}
```

---

## Response Shape

### List response — `/api/blogs/`

```json
[
  {
    "id": 1,
    "title": "10 Things to Check Before Buying a Used Car",
    "slug": "10-things-to-check-before-buying-a-used-car",
    "category": { "id": 1, "name": "Buying Guides" },
    "excerpt": "Purchasing a used car can be a great way to save money...",
    "image_url": "https://api.noorrixmotors.co.uk/media/blogs/cover.jpg",
    "read_time": 6,
    "is_featured": false,
    "published_at": "2026-06-02T10:00:00Z"
  }
]
```

### Detail response — `/api/blogs/<slug>/`

Same as list, plus:

```json
{
  "body": "Full article content in Markdown or HTML..."
}
```

---

## Field Reference

| Field | Type | Notes |
|-------|------|-------|
| `id` | number | Unique post ID |
| `title` | string | Post title |
| `slug` | string | URL-safe identifier — use for routing |
| `category` | `{ id, name }` | Null if uncategorised |
| `excerpt` | string | 1–3 sentence summary for cards |
| `body` | string | Full content — detail endpoint only |
| `image_url` | string | Absolute URL to cover image |
| `read_time` | number | Minutes |
| `is_featured` | boolean | Editor's pick |
| `published_at` | ISO 8601 string | Publication date |

---

## Suggested Blogs View Props

```jsx
// src/views/Blogs.jsx

function Blogs({ posts = [], featuredPost = null }) {
  // posts      → array from GET /api/blogs/
  // featuredPost → first item from GET /api/blogs/?featured=true (or null)
}
```

Remove any hardcoded `blogPosts` / `featuredPost` constants from the file.

---

## ISR Revalidation

All fetch calls use `{ next: { revalidate: 60 } }` — Next.js rebuilds the page in the background every 60 seconds after a request. New posts published in Django admin appear on the site within 60 seconds without a full redeploy.
