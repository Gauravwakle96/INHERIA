# INHERIA workspace design contract

Product surface: an authenticated technical continuity workspace. Primary user: a manager transferring engineering responsibilities; incoming employees and reviewers use role-scoped views.

Primary action: run an evidence investigation, then review claims and prepare a handover. The first viewport must expose actual knowledge gaps, pending review and source health. CONNECT → RECONSTRUCT → VERIFY → REVIEW → HANDOVER → VALIDATE remains visible as a task-oriented flow, not eleven engine menus.

Visual hierarchy: fixed 232px quiet sidebar, project and identity topbar, small contextual eyebrow, descriptive page title, concise toolbar; measurable metrics above operational lists. Night uses deep neutral navy surfaces and cyan active states. Day uses pale blue-gray backgrounds, white surfaces and deeper teal actions. Muted violet graph relationships and amber review flags keep their meaning in both themes. The labelled Day/Night switch appears on sign-in and in the topbar; preference persists across visits and tabs. Native fields, dialogs and the graph follow the palette. Inter is self-hosted and OFL licensed. Tabular metrics, consistent 4px spacing scale, no decorative charts without data.

Target viewports: 390x844, 768x1024, 1440x900. At 390px sidebar becomes an overlay controlled by a labelled menu button, panels stack, controls wrap, tables scroll within containers; no document-level horizontal overflow. At 768px mobile navigation remains and two-column metrics fit. At 1440px overview has wide operational focus and narrower workflow summary.

States and safe actions:

| State | Trigger and feedback | Next action |
|---|---|---|
| Loading | API request pending; readable busy status and stable skeleton | Wait or navigate |
| Empty | No authorised sources/claims/transitions; contextual reason | Connect sources, investigate or create transition |
| Error | Network/API validation failure; specific detail and request ID when available | Retry or correct submitted fields |
| Partial | Bounded sync, incomplete citations or unverified knowledge | Inspect job/source status and remediate missing evidence |
| Success | Persisted mutation confirmed by toast and refreshed data | Next workflow step |
| Permission | Role lacks mutation rights or source denied | Browse permitted knowledge or ask an authorised reviewer |

Accessibility: landmarks, skip link, one h1 per page, visible focus, labelled inputs, semantic buttons, native dialog with focus return, keyboard-close drawer, text-plus-colour status, reduced-motion support, 40–44px touch targets. React Flow keyboard navigation and a text relationships list both expose the graph.

References: user's INHERIA requirements and API_CONTRACT.md; official React https://react.dev/learn and Vite https://vite.dev/guide/ reviewed at build start. This contract establishes intent; rendered evidence is recorded only after browser verification.
