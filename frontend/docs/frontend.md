# INHERIA frontend

React, TypeScript and Vite render the FastAPI contracts in `../../API_CONTRACT.md`. React Query caches authorised project requests and invalidates them after mutations; a project or user change remounts feature state. Session tokens stay in HttpOnly cookies; only the CSRF token stays in memory. Browser local storage holds the selected project ID and day/night theme preference, never authentication tokens.

`ThemeProvider` owns the dark/light palette and browser-tab synchronization. `ThemeToggle` is shared by sign-in and the workspace topbar. The small bootstrap in `index.html` applies the saved theme before painting. Night remains the default when no valid preference exists. Semantic day colors and the existing night shades are paired with CSS `light-dark()`; native controls use the matching `color-scheme`. The graph uses the same theme context and CSS color tokens. References: [MDN light-dark()](https://developer.mozilla.org/en-US/docs/Web/CSS/color_value/light-dark) and [React Flow colorMode](https://reactflow.dev/api-reference/react-flow).

Run `npm ci`, `npm run dev` and open http://127.0.0.1:5173. The API must run on 127.0.0.1:8010; `/api` is proxied. `npm run typecheck`, `npm run lint` and `npm run build` verify the client. `npm run test:e2e` runs against the local demo-enabled API and installed Google Chrome; it intentionally creates one labelled UI-validation document and approves its evidence. Use an isolated demo database for repeatable tests. `INHERIA_FRONTEND_URL` can override the test URL.

Source data, metrics, knowledge, simulations and transitions come from the API. Future connectors are not presented as working. Sources remain permission-filtered; unsupported successor answers and hypothetical stress-test results are labelled. Admins can create project members without an email delivery integration. Gap answers are employee testimony pending verification. Responsibility acceptance does not validate practical readiness.

Inter is self-hosted under SIL OFL. The MVP uses its Latin subset for the English interface. React Flow is loaded separately when the graph opens. The scoped `minimatch` dependency override applies the patched >=11.0.1 release to the TypeScript ESLint parser; lint validation checks its compatibility.

Rendered screenshots and browser findings are in `docs/ui-artifacts/` and `docs/ui-evidence.json`; the design contract is in `docs/design-contract.md`. A source review or successful build alone does not establish accessible rendered behaviour.
