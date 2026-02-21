# GridCast Frontend — CLAUDE.md

## Project Overview
Vite + React SPA deployed to GitHub Pages at `https://n3il-kb.github.io/gridcast/`.
- Base path: `/gridcast/` (set in `vite.config.js`)
- Always use `import.meta.env.BASE_URL` for asset/image paths, never hardcode `/gridcast/`
- Tailwind v3 with custom colors: `neon` (`#00ff80`), `dark-bg` (`#050505`), `glass`

## Map Architecture (`src/pages/D3ScoreMapPage.jsx`)
Two rendering layers stacked absolutely inside the same container div:
1. **Mapbox GL JS** — base tile map, handles all user interaction events (mouse, pan, zoom)
2. **D3 canvas** — renders hex grid on top of Mapbox; `pointer-events-none` so clicks/hovers pass through to Mapbox

The canvas mirrors the Mapbox canvas's CSS transform on every frame to stay pixel-aligned during pan/zoom.

### Why refs instead of state in the render loop
Map event callbacks (`map.on("move", ...)`) capture refs at mount time. If they read React state, they get stale values. All values needed inside the render loop or event handlers use refs (e.g., `metricRef`, `selectedARef`, `selectedBRef`, `hoveredFeatureRef`). State counterparts exist only to trigger re-renders for JSX (the compare panel, metric selector, etc.).

### Performance
- Canvas (not SVG) renders thousands of hexes per frame
- `requestAnimationFrame` throttling during pan (`scheduleRender`)
- Pre-computed centroids (`_centroid`) and bounds (`_bounds`) cached on each feature at load time
- 256-color palette lookup tables pre-built per metric — no per-frame D3 scale calls
- Quadtree rebuilt per render for O(log n) nearest-neighbor hover hit detection
- Viewport culling: only features whose centroid is within map bounds + 0.2° buffer are drawn

### Adding a New Metric
1. Add an entry to the `METRICS` object (label + description)
2. Optionally add it to `COMPARE_METRICS` array for the compare panel
3. The data property must exist in `public/data/score_map_hex.json` features
4. Color interpolator: defaults to `d3.interpolateRdYlGn`; override in `interpolatorFor()` for special cases

### Compare Feature
- Click a hex → selects as Hex A (cyan highlight); click another → Hex B (orange highlight)
- Clicking a selected hex deselects it; clicking a third hex replaces B (B→A, new→B)
- `ComparePanel` component (bottom of file) shows side-by-side metric diff with color-coded Δ column
- Selections stored in both state (`selectedA/B`) for JSX and refs (`selectedARef/BRef`) for canvas

## Token Setup
- **Local dev:** `frontend/.env` — use your default Mapbox public token (no URL restrictions). This file is gitignored.
- **Production:** GitHub Actions secret `VITE_MAPBOX_TOKEN` — use a token restricted to `https://n3il-kb.github.io`. Vite inlines this at build time.
- Never commit `frontend/.env`. There is no way to hide a Mapbox public token in a static site — use URL restrictions on Mapbox dashboard instead.

## Deployment
GitHub Actions workflow (`.github/workflows/deploy.yml`):
- Triggers on push to `main`
- Runs `npm install && npm run build` in `frontend/`
- Deploys `frontend/dist/` to `gh-pages` branch via `peaceiris/actions-gh-pages@v4`
- Requires `permissions: contents: write` for `GITHUB_TOKEN`

Manual deploy also available: `npm run deploy` from `frontend/` (uses `gh-pages` npm package).

## Image Paths
All images are in `frontend/public/images/`. Reference them as:
```js
const IMG = import.meta.env.BASE_URL + "images/";
// e.g., IMG + "datacenter-bg.jpg"
```

## Data Files
`frontend/public/data/score_map_hex.json` — GeoJSON FeatureCollection of hex cells.
Key feature properties: `hex_id`, `dc_score`, `sustainability`, `profitability`, `dc_score_temp`,
`temp_cool_score`, `local_temp_c`, `elevation_m`, `dist_to_region`, `region`, `lat`, `lon`,
`raw_renew`, `raw_price`, `raw_load`, `n_renew`, `n_price`, `n_load`, `n_volatility`.
