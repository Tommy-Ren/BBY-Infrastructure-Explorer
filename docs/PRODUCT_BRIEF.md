# Product brief — Sprint 1

## Audience and promise

Parents, residents, and school communities can look up municipal infrastructure records around a school without GIS software. Planning-oriented visitors can inspect provenance and the measurement rule. The product describes recorded presence, not active inventory or school safety. It does not rank schools.

## First journey

Open the explorer → search a school name → select from the list or map → choose 100, 250, or 500 m → read the recorded count and nearest distances → inspect the source date and limitations → copy a link that reopens the same school and radius. Search and details remain usable when map tiles or WebGL fail. Failed API requests have a retry action; unknown shared IDs invite a new selection.

## Low-fidelity layouts

Desktop:

```text
┌ Brand                                      About the data ┐
│ What's around your school?                 Snapshot date  │
│ Straight-line distance; coverage is not a safety measure.  │
├─────────────────┬──────────────────────┬──────────────────┤
│ Find your school│ Neighbourhood map    │ Selected school  │
│ [Search…       ]│ School points        │ [100][250][500] m │
│ 64 schools      │ Feature points       │ Count + rule     │
│ [School name ↗ ]│ Radius outline       │ Nearest distances│
│ [School name ↗ ]│ Zoom + legend        │ [Copy link]      │
├─────────────────┴──────────────────────┴──────────────────┤
│ Measurement explanation             Sources + version    │
└──────────────────────────────────────────────────────────┘
```

Mobile:

```text
┌ Brand                 About ┐
│ Title + snapshot context   │
│ Straight-line limitation   │
│ [Find your school…        ]│
│ Scrollable school list     │
├────────────────────────────┤
│ Selected school            │
│ [100 m] [250 m] [500 m]     │
│ Count + status rule        │
│ Nearest distances          │
│ [Copy link]                │
├────────────────────────────┤
│ Map + radius + legend      │
├────────────────────────────┤
│ Method + sources + version │
└────────────────────────────┘
```

On mobile, details precede the map visually to make list selection immediately useful. Tablet uses two columns with details below. DOM order supports list → map → details keyboard navigation.

## Design system

| Element | Decision |
| --- | --- |
| Type | Manrope headings, DM Sans body, local sans-serif fallback |
| Canvas and cards | Warm white `#f6f7f3`, white panels, borders `#dce3dc` |
| Primary and text | Deep green `#163e36`, text `#203c35`, secondary `#61706a` |
| Map legend | Blue school points `#204b62`, rust recorded features `#b85e23`, dashed green radius `#16715b` |
| Spacing | 4/8/12/16/24/32/48 px rhythm; modest 5–10 px corner radii |
| Interaction | Native labelled search and radio controls, visible rust focus rings, text labels beside colour, no automatic animated travel |
| Feedback | Loading text, empty search recovery, API retry, map fallback, copy confirmation |

## Architecture decision

React + TypeScript + Vite and MapLibre GL JS; FastAPI reads one validated JSON snapshot. No database is needed for 64 schools and 1,494 features. Radius polygons are computed in the same projected CRS as the counts. Vercel is the selected preview host; two services share one origin. The original report pipeline and committed outputs stay in place. Clusters, comparisons, downloads, refresh promotion, and safety/outcome analysis are outside Sprints 1–2.
