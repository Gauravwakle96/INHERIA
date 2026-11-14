"""Detailed planning and operational pages for the public product report."""


def enhance(pages, p, tbl, box, evidence):
    pages[16] = (
        "Product roadmap and delivery strategy",
        "PRIORITIES · DEPENDENCIES · EFFORT ESTIMATES · RELEASE GATES",
        [
            p(
                "Four milestones deepen the continuity workflow. Effort ranges are small-team planning estimates, not release dates. These are future capabilities; the three submitted improvements remain the delivered commitments.",
                "lead",
            ),
            tbl(
                [
                    "Milestone / estimate",
                    "User benefit and delivery",
                    "Dependency / release gate",
                ],
                [
                    [
                        "<b>M1 · Independent quality</b><br/>P0 · 2–3 development weeks",
                        "Independent permissioned labels, category quality and better owner/rationale/dependency extraction. Reviewers know where correction is needed.",
                        "Consent and label agreement precede changes. Untouched evaluation meets ≥90% precision and ≥85% field targets with misses disclosed.",
                    ],
                    [
                        "<b>M2 · Identity and onboarding</b><br/>P0 · 3–4 development weeks",
                        "Verified email, secure reset, approved identity provider and accessible role-guided onboarding. Successors join/recover access safely.",
                        "Freeze ACL contracts; email verification before reset/SSO. Permission/replay/concurrency tests and observed unfamiliar-user journeys.",
                    ],
                    [
                        "<b>M3 · Jobs and recovery</b><br/>P1 · 3–4 development weeks",
                        "Durable jobs, shared limits, scheduled review/retention and rehearsed application restore. Operators recover expected failures.",
                        "Measure workload/budget before queue choice. Restart/duplicate/revoke gates, approved RPO/RTO and published capacity results.",
                    ],
                    [
                        "<b>M4 · Permissioned pilot</b><br/>P2 · 4–6 development weeks per pilot",
                        "One needed connector, specialist review, staging artefacts and domain schemas for a real consenting team.",
                        "After M1–M3: real auth/sync/revocation/E2E and pilot feedback. No production remediation or fabricated operations.",
                    ],
                ],
                [0.24, 0.39, 0.37],
            ),
            p("Delivery ownership and risk control", "h2"),
            p(
                "Product coordination owns priority; data/AI engineering owns quality; backend/security owns access; platform engineering owns recovery; QA/UX owns release evidence. These are planned workstreams. Consent, identity policy, reviewer availability and hosting costs are dependencies, not assumed resources."
            ),
            box(
                "Milestone definition of done",
                "Ship user-visible scope, API/schema/environment contracts, permission/failure tests, appropriate user observations, migration/recovery instructions, licence/cost disclosures and clean setup. A failed gate delays expansion. Future targets are never presented as measured results.",
            ),
            evidence("docs/roadmap.md", "docs/operating-guide.md"),
        ],
    )
    additions = [
        (
            "M1 · Independent reconstruction quality",
            "DETAILED ROADMAP · DATA QUALITY · ATTRIBUTION · ACCEPTANCE",
            [
                p(
                    "Reviewers need reliability evidence for their sources. Current explicit English patterns and internal labels remain bounded; M1 establishes independent evidence before wider semantic claims.",
                    "lead",
                ),
                tbl(
                    ["Work package", "Planned implementation and artefact"],
                    [
                        [
                            "Permissioned corpus",
                            "Consent/redaction/retention register; proposed ≥100 documents from ≥2 categories, including ≥40 prose-heavy and ≥20 ambiguous/negative cases.",
                        ],
                        [
                            "Independent labels",
                            "Two reviewers label type, owner, current/historical state, rationale, dependency direction and exact span. Publish disagreement and adjudication.",
                        ],
                        [
                            "Frozen evaluation",
                            "Split by project/document lineage before changes. Separate training, tuned regression and untouched test data; publish manifest/hash.",
                        ],
                        [
                            "Extraction depth",
                            "Scoped pronouns, shared/unnamed ownership, causal reasons and multiword dependency fields. Missing evidence remains unresolved.",
                        ],
                        [
                            "Provider comparison",
                            "Same cases/ACLs, timeout and cost budget for rules/optional providers. Keep useful non-provider review available.",
                        ],
                    ],
                    [0.28, 0.72],
                ),
                p("Measurable release gates", "h2"),
                tbl(
                    ["Measure", "Proposed gate and denominator"],
                    [
                        [
                            "Precision",
                            "≥90%: correct candidates / extracted candidates on untouched labels.",
                        ],
                        [
                            "Field accuracy",
                            "≥85% each owner/rationale/dependency: correct / applicable labels; report category failures.",
                        ],
                        [
                            "Recall / abstention",
                            "Publish recovered / relevant candidates by category and conservative misses; do not conceal unanswered cases.",
                        ],
                        [
                            "Attribution / permission",
                            "Valid current spans; zero restricted/revoked disclosures across API, graph, reports and history acceptance cases.",
                        ],
                    ],
                    [0.30, 0.70],
                ),
                box(
                    "Dependencies and risk response",
                    "Independent reviewers and source consent can block the corpus. Keep internal labels disclosed and the bounded release usable; never rename them independent. Ambiguous ownership may remain unassigned. Optional provider performance does not block core review.",
                ),
                p(
                    "Release packet: permission register, label guide, agreement/adjudication, frozen manifest, first-run category results, preserved misses and regression suite. Estimate: 2–3 development weeks after source/reviewer availability.",
                    "small",
                ),
                evidence("docs/roadmap.md", "docs/postfix-internal-first-report.json"),
            ],
        ),
        (
            "M2 · Identity and accessible onboarding",
            "DETAILED ROADMAP · SECURITY · USER RESEARCH · ADOPTION",
            [
                p(
                    "Successors should join safely, recover credentials and understand missing access with minimal help. Extend current invitations and readiness while preserving tenant/source authority.",
                    "lead",
                ),
                tbl(
                    ["Sequence", "Implementation and dependency"],
                    [
                        [
                            "1 · Verify / deliver",
                            "Verified-email registration and invite delivery; hashed expiring one-use links, enumeration protection and resend/accept limits.",
                        ],
                        [
                            "2 · Recovery",
                            "Password reset, invalidation and notification. Test expiry/replay, simultaneous use and member revocation against PostgreSQL.",
                        ],
                        [
                            "3 · Identity",
                            "One approved identity provider/MFA policy; tenant binding, retained memberships and no silent account merging/role escalation.",
                        ],
                        [
                            "4 · Source authority",
                            "Justified OAuth/signed webhooks; signature/replay, expiry, repository removal and permission-loss handling.",
                        ],
                        [
                            "5 · Observed use",
                            "≥5 consented unfamiliar-user sessions across three roles; keyboard, focus, low-vision and representative screen-reader journeys.",
                        ],
                    ],
                    [0.27, 0.73],
                ),
                p("Acceptance must demonstrate usable access", "h2"),
                box(
                    "Security gates",
                    "Invite/verify/login/reset/expiry/replay/concurrency/revoke flows pass. Forbidden titles, text, citations and history stay hidden after access loss. Admin does not override source ACL; INHERIA membership grants no external AWS/IAM access.",
                ),
                box(
                    "Usability gates",
                    "Proposed target: ≥4 of 5 participants complete the assigned main task without facilitator help. Record task/time/help/confusion and unsuccessful outcomes. Fix/retest every blocker. Publish keyboard/screen-reader scope and limits; no certification inferred.",
                ),
                p(
                    "Dependencies: approved email provider, identity policy and participant consent. Test one configuration first and retain existing login through migration. Estimate: 3–4 development weeks after provider/policy access.",
                    "small",
                ),
                p(
                    "Release packet: threat model, provider guide, permission/replay/concurrency results, audit examples, actual user observations, accessibility scope and migration/recovery instructions.",
                    "small",
                ),
                evidence("docs/roadmap.md", "docs/usability-task-pack.md"),
            ],
        ),
        (
            "M3 · Durable jobs and recovery",
            "DETAILED ROADMAP · RELIABILITY · GOVERNANCE · CAPACITY",
            [
                p(
                    "Restarts, duplicate delivery and quota pressure must preserve one logical result and current authority. Infrastructure follows measured workload and an approved budget.",
                    "lead",
                ),
                tbl(
                    ["Work package", "Planned capability"],
                    [
                        [
                            "Measure first",
                            "Document counts, sync duration, DB transfer, memory, queue depth and API latency determine worker requirements.",
                        ],
                        [
                            "Durable execution",
                            "Transaction-safe enqueue, stable job IDs, atomic checkpoints, bounded retries/backoff, cancellation and dead-letter recovery.",
                        ],
                        [
                            "Governance",
                            "Shared limits/concurrency, permission versus transient failure, scheduled source freshness and retention/derived purge.",
                        ],
                        [
                            "App recovery",
                            "Operator-approved RPO/RTO and backup scope; owned test restore checks rows, tenant ACLs, source versions and transfer state.",
                        ],
                    ],
                    [0.28, 0.72],
                ),
                p("Failure acceptance matrix", "h2"),
                tbl(
                    ["Failure", "Required result"],
                    [
                        [
                            "Restart / duplicate",
                            "Committed progress and one logical artefact set; no duplicate job/source/claim.",
                        ],
                        [
                            "Revoke during retry",
                            "Recheck source authority; revoked knowledge never becomes current through replay.",
                        ],
                        [
                            "Budget / cancellation",
                            "Explicit terminal state/recovery; no infinite retry or partial success label.",
                        ],
                        [
                            "Purge / restore",
                            "Derived purge verified; test RPO/RTO met without tenant leakage or stale-evidence revival.",
                        ],
                    ],
                    [0.32, 0.68],
                ),
                box(
                    "Capacity target and limits",
                    "Proposed test profile: 10 concurrent users + 3 active investigations for 30 minutes. Publish hardware, inputs, p95 latency, failure rate, transfer and memory; select support limits after measurement. This is a future profile, not achieved throughput.",
                ),
                p(
                    "Risks: queue services may exceed free budgets; retain bounded mode until justified. Restore the encryption key alongside encrypted integrations. Database downgrade remains separately reviewed. Estimate: 3–4 development weeks. Release packet: failure-injection, retention/restore drill, capacity and operator/migration reports.",
                    "small",
                ),
                evidence("docs/roadmap.md", "docs/operating-guide.md"),
            ],
        ),
        (
            "Operating guide and release maintenance",
            "DEPLOYMENT · RECOVERY · SUPPORT · DOCUMENTATION CONTRACT",
            [
                p(
                    "An administrator needs recovery instructions as well as installation commands. These procedures describe the current bounded product; future automation remains in the roadmap.",
                    "lead",
                ),
                tbl(
                    ["Expected condition", "Safe operator or user response"],
                    [
                        [
                            "Cold start / quota",
                            "Allow service wake-up; retry when offered. Monitor quota without keep-alive or extra-project bypass.",
                        ],
                        [
                            "Missing permission",
                            "Successor requests knowledge; authorised independent reviewer checks ACL. External IAM stays separate.",
                        ],
                        [
                            "Blocked closure",
                            "Follow readiness links; resolve acceptance, assessment, current evidence and prerequisites; refresh.",
                        ],
                        [
                            "Interrupted / duplicate",
                            "Authorised investigator resumes checkpoint. Wait on 409 existing job; avoid repeat enqueue.",
                        ],
                        [
                            "429 / provider failure",
                            "Honour cooldown and safe connector warnings. Optional AI preserves history and labelled retrieval.",
                        ],
                        [
                            "Changed / rejected",
                            "Reinvestigate/review, regenerate/reapprove and reassess active transfer. Closed ownership uses follow-up.",
                        ],
                    ],
                    [0.31, 0.69],
                ),
                p("Deployment and migration checklist", "h2"),
                p(
                    "1. Locked dependencies, reviewed additive migrations and approved secrets.<br/>2. Production PostgreSQL/HTTPS, stable encryption key and disabled shared development login.<br/>3. Verify /api/health, explicit /api/ready, SPA deep link, login, CSRF rejection, ingestion and restricted read.<br/>4. Application rollback requires schema compatibility; database downgrade/restore is separately reviewed.<br/>5. Maintain operator recovery/key storage and quota monitoring."
                ),
                box(
                    "Documentation definition of done",
                    "Every release updates scope, API/schema/environment contracts, recovery steps, permission/failure tests, appropriate user observations, licence/service costs and limits. Recheck clean install and retain original evaluations. Source ACL and citation lineage are release invariants.",
                ),
                p(
                    "M4 pilot gate: after M1–M3, choose one consented source-system need. Real auth/sync/permission-loss/E2E and qualified supplied staging evidence precede expansion. Estimate: 4–6 development weeks per pilot. No production command execution implied.",
                    "small",
                ),
                evidence(
                    "docs/operating-guide.md", "docs/deployment.md", "docs/roadmap.md"
                ),
            ],
        ),
    ]
    pages[17:17] = additions
    items = pages[21][2]
    pages[21] = (
        "Team and submission responsibilities",
        "TEAM JAEGERS · CONTRIBUTION ATTRIBUTION · DOCUMENT CONTROL",
        items,
    )
