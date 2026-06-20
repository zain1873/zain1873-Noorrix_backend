# Cars API — Frontend Integration Guide

Base URL: `https://api.noorrixmotors.co.uk`

Set in your Next.js `.env.local`:
```
NEXT_PUBLIC_API_URL=https://api.noorrixmotors.co.uk
```

This API is the **single source of truth** for every car — the same object powers the
stock grid, the detail page, the brand page, the similar-cars slider and the checkout
flow. Replace `src/data/cars.js` (`stockData`, `makeModels`, `toBrandSlug`) with these calls.

---

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/cars/` | All **available** cars (plain array) — the stock list |
| GET | `/api/cars/?make=BMW` | Cars by make (exact, case-insensitive) |
| GET | `/api/cars/?brand=mercedes-benz` | Cars by brand **slug** — the Used Cars by Brand page |
| GET | `/api/cars/<id>/` | Single car, full detail (any status) |
| GET | `/api/cars/<id>/similar/` | Similar cars (same body type or make), `?limit=6` |
| GET | `/api/filters/` | Dynamic filter options (makes, makeModels, ranges…) |

No authentication required on any endpoint. Only cars with `status = "available"`
appear in list / brand / similar / filters; the detail endpoint returns any status so
that reserved or sold links still resolve.

> **Filtering model:** the list endpoint returns the **whole available inventory**.
> All 8 filters (make, model, body type, fuel, transmission, colour, price, mileage)
> and the per-option `(N)` counts run **client-side** on that array — exactly as they do
> today. The backend only narrows the list for the brand page (`?make=` / `?brand=`).

---

## Field Reference

### List / card fields (`/api/cars/`)

| Field | Type | Example | Notes |
|-------|------|---------|-------|
| `id` | number | `2` | Stable unique key — use for `/cars/:id` and `/checkout?car=:id` |
| `title` | string | `"BMW 3 Series"` | Card + detail title |
| `subtitle` | string | `"2.0 320d M Sport…"` | Trim/spec line |
| `make` | string | `"BMW"` | Filter, breadcrumb, brand page |
| `model` | string | `"3 Series"` | Filter, breadcrumb |
| `body_type` | string | `"Saloon"` | Filter |
| `fuel` | string | `"Diesel"` | Filter, card spec |
| `transmission` | string | `"Automatic"` | Filter, card spec |
| `colour` | string | `"Black"` | Filter, breadcrumb |
| `year` | number | `2019` | Filter + card spec — **format yourself** |
| `engine_cc` | number | `1995` | Card spec — render as `"1,995 CC"` |
| `mileage` | number | `42300` | **Mileage filter range math** + card — render `"42,300 Miles"` |
| `price` | number | `14495` | **Price filter range math** + card — render `"£14,495"` |
| `monthly` | string\|null | `"245.00"` | Decimal string — render `"£245.00"` (per month) |
| `mot_date` | string\|null | `"2026-06-01"` | ISO date — render `"01/06/2026"` |
| `image_url` | string\|null | `https://…/media/cars/2.jpg` | Card image (absolute URL) |
| `status` | string | `"available"` | `available` \| `reserved` \| `sold` |

> **Numbers, not strings.** The API sends raw numbers (`price`, `mileage`, `engine_cc`,
> `year`) so your filter range math works directly. There is no `priceNum` / `mileageNum`
> split any more — `price` **is** the number. Format for display on the front-end.

### Detail-only fields (`/api/cars/<id>/`)

Everything above, plus:

| Field | Type | Example | Replaces (hardcoded today) |
|-------|------|---------|----------------------------|
| `engine` | string | `"2.0L"` | `SPECS` engine |
| `doors` | number | `5` | `SPECS` doors |
| `seats` | number | `5` | `SPECS` seats |
| `history_check` | string | `"All passed"` | `SPECS` HPI |
| `images` | string[] | `["https://…/1.jpg", …]` | `SLIDES` gallery (falls back to `[image_url]`) |
| `features` | string[] | `["Bluetooth", …]` | `FEATURES` list |
| `description` | string | `"Full marketing text…"` | Description block |
| `details` | object | `{ summary, performance, interior, safety }` | `ACCORDION_CONTENT` |
| `video_url` | string | `https://youtube.com/…` | "View video walkthrough" |
| `location` | object\|null | `{ name, address }` | Vehicle location (null → use site default) |
| `created_at` / `updated_at` | ISO 8601 | | |

---

## Display Formatting Helpers

The API sends numbers; format them on the front-end. One small module covers every page:

```js
// src/lib/format.js
export const gbp   = (n) => `£${Number(n).toLocaleString("en-GB")}`;        // 14495   -> "£14,495"
export const money = (n) => (n == null ? null : `£${Number(n).toFixed(2)}`); // "245.00"-> "£245.00"
export const miles = (n) => `${Number(n).toLocaleString("en-GB")} Miles`;    // 42300   -> "42,300 Miles"
export const cc    = (n) => `${Number(n).toLocaleString("en-GB")} CC`;       // 1995    -> "1,995 CC"
export const ukDate = (iso) =>                                               // "2026-06-01" -> "01/06/2026"
  iso ? new Date(iso).toLocaleDateString("en-GB") : null;
```

---

## Usage Examples

### 1. Our Stock — list + dynamic filters  (`/stock`)

```js
// src/app/stock/page.js
const BASE = process.env.NEXT_PUBLIC_API_URL;

async function fetchStock() {
  const [carsRes, filtersRes] = await Promise.all([
    fetch(`${BASE}/api/cars/`,   { next: { revalidate: 60 } }),
    fetch(`${BASE}/api/filters/`, { next: { revalidate: 300 } }),
  ]);
  return { cars: await carsRes.json(), filters: await filtersRes.json() };
}

export default async function StockPage() {
  const { cars, filters } = await fetchStock();
  return <OurStock cars={cars} filters={filters} />;
}
```

Inside `OurStock.jsx`, keep your existing client-side filter logic — just point it at
`cars` (the prop) instead of `stockData`, and at `filters` instead of the hardcoded
`makes` / `makeModels` / `bodyTypes` / … arrays. The price/mileage **range math** now
uses `car.price` and `car.mileage` directly (no `priceNum` / `mileageNum`).

### 2. Hero filter → Stock  (home banner)

Push the chosen values to `/stock` as query params, then read them in `OurStock`:

```js
// src/components/HeroFilter/Filter.jsx — handleSearch()
const params = new URLSearchParams();
if (make)         params.set("make", make);
if (model)        params.set("model", model);
if (transmission) params.set("transmission", transmission);
if (budget)       params.set("priceMax", budget);   // numeric £ max
router.push(`/stock?${params.toString()}`);
```

```js
// OurStock.jsx — seed initial filter state from the URL
const sp = useSearchParams();
const [filters, setFilters] = useState({
  make:         sp.get("make")         || "",
  model:        sp.get("model")        || "",
  transmission: sp.get("transmission") || "",
  priceMax:     sp.get("priceMax")     ? Number(sp.get("priceMax")) : null,
  // …rest default ""
});
```

Because the hero filter's Make/Model dropdowns are now fed by the **same** `/api/filters/`
response as the stock page, a user can no longer pick a brand that isn't in stock — the
three lists (hero, stock, actual inventory) are one source. (Also switch the hero
currency from `$` to `£`, and map its numeric `priceMax` onto your range logic.)

### 3. Car Details  (`/cars/:id`)

```js
// src/app/cars/[id]/page.js
const BASE = process.env.NEXT_PUBLIC_API_URL;

async function fetchCar(id) {
  const [carRes, similarRes] = await Promise.all([
    fetch(`${BASE}/api/cars/${id}/`,          { next: { revalidate: 60 } }),
    fetch(`${BASE}/api/cars/${id}/similar/`,   { next: { revalidate: 60 } }),
  ]);
  if (!carRes.ok) return null;
  return { car: await carRes.json(), similar: await similarRes.json() };
}

export default async function CarDetailPage({ params }) {
  const data = await fetchCar(params.id);
  if (!data) notFound();
  return <CarDetails car={data.car} similar={data.similar} />;
}
```

Wire the previously-hardcoded blocks to the `car` object:

| Component / const | Bind to |
|-------------------|---------|
| `ImageSlider` / `SLIDES` | `car.images` |
| `SPECS` grid | `car.mileage`, `car.year`, `car.engine`, `car.doors`, `car.seats`, `car.history_check` |
| `FEATURES` | `car.features` |
| `VehicleDescriptionSection` | pass `car`; use `car.description` |
| Accordions | `car.details.summary` / `.performance` / `.interior` / `.safety` |
| Video button | `car.video_url` |
| Vehicle location | `car.location` (if `null`, show your site default) |

### 4. Used Cars by Brand  (`/used-cars/:brand`)

The URL slug goes straight to the API — no client-side `toBrandSlug` matching needed:

```js
// src/app/used-cars/[brand]/page.js
const BASE = process.env.NEXT_PUBLIC_API_URL;

async function fetchByBrand(brand) {
  const res = await fetch(`${BASE}/api/cars/?brand=${brand}`, {
    next: { revalidate: 60 },
  });
  return res.json();
}

export default async function BrandPage({ params }) {
  const cars = await fetchByBrand(params.brand);   // e.g. "mercedes-benz"
  return <UsedCarsByBrand brand={params.brand} cars={cars} />;
}
```

The backend slugifies each stored make and matches it against the slug, so
`mercedes-benz` correctly resolves to `"Mercedes-Benz"`.

### 5. Similar Cars Slider

Feed the slider from `similar` (fetched above) and link each "View this vehicle" button
to `/cars/${item.id}`:

```jsx
{similar.map((item) => (
  <a key={item.id} href={`/cars/${item.id}`}>{/* card */}</a>
))}
```

---

## Response Shapes

### List — `/api/cars/`

```json
[
  {
    "id": 2,
    "title": "BMW 3 Series",
    "subtitle": "2.0 320d M Sport Saloon Auto Euro 6 4dr",
    "make": "BMW",
    "model": "3 Series",
    "body_type": "Saloon",
    "fuel": "Diesel",
    "transmission": "Automatic",
    "colour": "Black",
    "year": 2019,
    "engine_cc": 1995,
    "mileage": 42300,
    "price": 14495,
    "monthly": "245.00",
    "mot_date": "2026-06-01",
    "image_url": "https://api.noorrixmotors.co.uk/media/cars/2.jpg",
    "status": "available"
  }
]
```

### Detail — `/api/cars/<id>/`

List shape **plus**:

```json
{
  "engine": "2.0L",
  "doors": 5,
  "seats": 5,
  "history_check": "All passed",
  "images": [
    "https://api.noorrixmotors.co.uk/media/cars/2-1.jpg",
    "https://api.noorrixmotors.co.uk/media/cars/2-2.jpg"
  ],
  "features": ["Bluetooth", "Reverse camera", "Cruise control"],
  "description": "Full marketing description…",
  "details": {
    "summary": "…",
    "performance": "…",
    "interior": "…",
    "safety": "…"
  },
  "video_url": "https://youtube.com/…",
  "location": { "name": "Noorrix Motors Bedford", "address": "…" },
  "created_at": "2026-06-18T08:53:33Z",
  "updated_at": "2026-06-18T08:53:33Z"
}
```

### Filters — `/api/filters/`

```json
{
  "makes": ["Audi", "BMW", "Mercedes-Benz"],
  "makeModels": { "BMW": ["3 Series", "X5"], "Audi": ["A3"] },
  "bodyTypes": ["SUV", "Saloon"],
  "fuelTypes": ["Diesel", "Petrol"],
  "transmissions": ["Automatic", "Manual"],
  "colours": ["Black", "White"],
  "priceRanges": [
    { "label": "Under £10,000", "min": 0, "max": 10000 },
    { "label": "£10,000 – £15,000", "min": 10000, "max": 15000 },
    { "label": "£15,000 – £20,000", "min": 15000, "max": 20000 },
    { "label": "£20,000 – £30,000", "min": 20000, "max": 30000 },
    { "label": "£30,000+", "min": 30000, "max": null }
  ],
  "mileageRanges": [
    { "label": "Under 20,000", "min": 0, "max": 20000 },
    { "label": "20,000 – 50,000", "min": 20000, "max": 50000 },
    { "label": "50,000 – 100,000", "min": 50000, "max": 100000 },
    { "label": "100,000+", "min": 100000, "max": null }
  ]
}
```

`makes` and `makeModels` are derived from the live inventory, so new brands added in the
Django admin appear in the filters automatically. Use `makeModels[selectedMake]` to drive
the dependent Model dropdown (replaces the hardcoded `makeModels` map). The range arrays
are static and match the stock page's existing Price/Mileage buckets.

---

## `cars.js` → API Field Map (migration cheat-sheet)

| Old `stockData` key | New API field | Change |
|---------------------|---------------|--------|
| `img` | `image_url` | rename |
| `bodyType` | `body_type` | rename |
| `cc` `"1,995 CC"` | `engine_cc` `1995` | number → `cc(n)` |
| `miles` `"42,300 Miles"` | `mileage` `42300` | number → `miles(n)` |
| `mileageNum` | `mileage` | merged into one number |
| `total` `"£14,495"` | `price` `14495` | number → `gbp(n)` |
| `priceNum` | `price` | merged into one number |
| `monthly` `"£245.00"` | `monthly` `"245.00"` | string decimal → `money(n)` |
| `mot` `"01/06/2026"` | `mot_date` `"2026-06-01"` | ISO date → `ukDate(n)` |
| `year` `"2019"` | `year` `2019` | string → number |
| `videoUrl` | `video_url` | rename |
| `historyCheck` | `history_check` | rename |
| `summary`/`performance`/`interior`/`safety` | `details.*` | grouped under `details` |

---

## ISR Revalidation

All fetch calls use `{ next: { revalidate: 60 } }` (filters: `300`) — Next.js rebuilds the
page in the background after a request. Cars added, edited or marked sold in the Django
admin appear on the site within ~60 seconds without a redeploy.
