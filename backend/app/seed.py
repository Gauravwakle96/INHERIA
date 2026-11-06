"""CC0 synthetic NEXORA dataset. No activity is attributed to real contributors."""

import hashlib
import secrets
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Audit, Chunk, Connection, Membership, Organisation, Project, Source, User, utcnow
from app.security import hash_password

DEMO_PEOPLE = [
    ("Alex Morgan", "alex", "Senior Backend Engineer", "employee"),
    ("Priya Shah", "priya", "DevOps Engineer", "lead"),
    ("Jordan Lee", "jordan", "Frontend Engineer", "incoming"),
    ("Sam Rivera", "sam", "Database Engineer", "employee"),
    ("Maya Chen", "maya", "Project Manager", "admin"),
]


def seed_demo(db: Session):
    existing = db.scalar(select(Organisation).where(Organisation.is_demo.is_(True)))
    if existing:
        return db.scalar(select(Project).where(Project.org_id == existing.id))
    org = Organisation(name="NEXORA TECHNOLOGIES", industry="technology", is_demo=True)
    db.add(org)
    db.flush()
    people = {}
    for name, handle, title, role in DEMO_PEOPLE:
        user = User(
            org_id=org.id,
            name=name,
            email=f"{handle}@nexora.example",
            title=title,
            role=role,
            password_hash=hash_password(secrets.token_urlsafe(40)),
            active=True,
        )
        db.add(user)
        db.flush()
        people[handle] = user
    project = Project(
        org_id=org.id,
        name="Atlas Commerce Platform",
        description="Synthetic commerce platform: billing API, event worker and operator console. "
        "Alex's departure reveals undocumented release work and unresolved incidents.",
        stack=["Python", "FastAPI", "PostgreSQL", "React", "GitHub Actions"],
        status="active",
        is_demo=True,
    )
    db.add(project)
    db.flush()
    for person in people.values():
        db.add(Membership(project_id=project.id, user_id=person.id, role=person.role))
    connections = {}
    for repo, description in [
        ("atlas-api", "billing-api and settlement jobs"),
        ("atlas-ops", "event-worker infrastructure and recovery"),
        ("atlas-console", "operator-console user interface"),
    ]:
        connection = Connection(
            org_id=org.id,
            project_id=project.id,
            name=f"Nexora / {repo}",
            provider="synthetic",
            repository=f"nexora-demo/{repo}",
            status="connected",
            config={"synthetic": True, "dataset": "Nexora v1", "license": "CC0-1.0"},
            last_sync_at=utcnow(),
        )
        db.add(connection)
        db.flush()
        connections[repo] = connection
        _source(
            db,
            project,
            connection,
            f"{repo} repository",
            "repository",
            f"Repository: nexora-demo/{repo}\nDescription: {description}\n"
            "Synthetic repository fixture; not a real GitHub repository.\n"
            "Structure: src/, tests/, docs/, .github/workflows/\n",
            age=3,
            metadata={"repository": connection.repository, "structure": ["src", "tests", "docs"]},
        )

    docs = [
        (
            "system-overview.md",
            450,
            "Architecture: Atlas platform topology\n"
            "System: billing-api\nThe billing-api writes settlement records to ledger-db.\n"
            "Dependency: billing-api -> ledger-db\n"
            "Dependency: operator-console -> billing-api\n"
            "Dependency: event-worker -> billing-api\n"
            "This diagram was last updated before the current webhook retry implementation. "
            "The queue relationship requires verification.",
        ),
        (
            "adr-001-datastore.md",
            200,
            "Decision: Primary settlement datastore\nSystem: ledger-db\n"
            "Rationale: Keep settlements in PostgreSQL for transactional consistency and rollback support.\n"
            "Alternatives: MongoDB was rejected because multi-record settlement transactions were required.\n"
            "Status: accepted\nOwner: Sam Rivera",
        ),
        (
            "adr-002-cache.md",
            15,
            "Decision: Primary settlement datastore\nSystem: ledger-db\n"
            "Rationale: A draft proposes Redis as the primary settlement store for latency.\n"
            "Status: draft, not approved\nThis conflicts with ADR-001. Do not replace the database on this draft.",
        ),
        (
            "adr-003-transport.md",
            80,
            "Decision: Event transport\nSystem: event-worker\n"
            "Rationale: Use a durable queue so failed webhook deliveries can be retried without losing settlements.\n"
            "Alternatives: Synchronous HTTP was rejected because partner outages blocked settlement writes.\n"
            "Owner: Alex Morgan\nStatus: accepted",
        ),
        (
            "adr-004-retries.md",
            40,
            "Decision: Webhook retry policy\nSystem: billing-api\n"
            "Rationale: Bound retries with backoff and preserve failed delivery IDs for operator review.\n"
            "Alternatives: Infinite retry was rejected due to queue exhaustion.\nOwner: Alex Morgan\nStatus: accepted",
        ),
        (
            "adr-005-boundaries.md",
            60,
            "Decision: Settlement service boundary\nSystem: billing-api\n"
            "Rationale: Keep settlement writes in the API until the outbox migration is completed.\n"
            "Alternatives: A separate microservice adds distributed transaction risks.\n"
            "Task: Complete the settlement outbox migration\nOwner: Alex Morgan\nStatus: unfinished",
        ),
        (
            "event-worker-rollback.md",
            25,
            "Procedure: Event worker rollback\nSystem: event-worker\nOwner: Priya Shah\n"
            "Steps: In the isolated test environment, locate the previous release tag, pause test delivery, "
            "restore the previous worker image, replay a test event and verify its delivery status.\n"
            "Escalation: Ask Priya before changing a production queue. This document does not authorise production access.\n"
            "Responsibility: Maintain event worker recovery\nOwner: Priya Shah\nBackup: Sam Rivera\nCritical: true",
        ),
        (
            "ledger-recovery.md",
            30,
            "Procedure: Ledger database recovery rehearsal\nSystem: ledger-db\nOwner: Sam Rivera\n"
            "Steps: Restore a sanitised backup to an isolated database; compare settlement counts with the "
            "backup manifest; run read-only integrity checks; record the rehearsal result.\n"
            "Escalation: Ask Sam to validate before any live database recovery.\n"
            "Responsibility: Validate ledger backups\nOwner: Sam Rivera\nBackup: Priya Shah\nCritical: true",
        ),
        (
            "transition-meeting.md",
            2,
            "Meeting notes: Alex Morgan plans to leave in 21 days. Maya Chen proposed Jordan Lee as incoming owner.\n"
            "Ownership is not accepted yet. Jordan needs release training and API incident history.\n"
            "The billing-api deployment procedure is missing; Alex must explain the canary checks.\n"
            "Unresolved question: Who will approve the unfinished settlement migration?",
        ),
        (
            "lessons-learned.md",
            7,
            "Lesson: Rehearse rollback before a release\nSystem: event-worker\n"
            "A staging retry incident was resolved by pinning the worker image and restoring the delivery checkpoint.\n"
            "Applicability: Worked in the isolated staging environment with an intact checkpoint; "
            "a damaged production queue requires independent assessment.\nOwner: Priya Shah",
        ),
    ]
    for name, age, body in docs:
        _source(
            db,
            project,
            None,
            name,
            "markdown",
            body,
            age=age,
            metadata={"document_title": name, "heading": name.removesuffix(".md")},
        )

    # Twelve realistic PR fixtures: three contain undeclared work observed in contextual evidence.
    undocumented = [
        (
            "Deploy billing-api releases",
            "billing-api",
            "Alex performed the canary release check in this PR. No operational deployment document was linked.",
        ),
        (
            "Maintain settlement migration",
            "ledger-db",
            "Alex checked incomplete outbox migration batches. Ownership was proposed in the review, not accepted.",
        ),
        (
            "Triage webhook delivery retries",
            "billing-api",
            "Alex handles the nightly retry queue triage although it is absent from the formal backend role checklist.",
        ),
    ]
    pr_titles = [
        "Canary gate for billing release",
        "Outbox migration checkpoint",
        "Nightly retry triage",
        "Queue monitoring labels",
        "Operator console incident link",
        "Database backup smoke check",
        "Staging rollback exercise",
        "Add settlement pagination",
        "Retry metric dimensions",
        "Console accessibility fixes",
        "Outbox integrity assertion",
        "Release note template",
    ]
    for index, title in enumerate(pr_titles):
        handle = ["alex", "alex", "alex", "priya", "jordan", "sam"][index % 6]
        repo = ["atlas-api", "atlas-ops", "atlas-console"][index % 3]
        body = f"Pull request #{index + 1}: {title}\nAuthor: {people[handle].name}\n"
        if index < 3:
            responsibility, component, context = undocumented[index]
            body += (
                f"Responsibility: {responsibility}\nOwner: Alex Morgan\nBackup: None\n"
                f"System: {component}\nCritical: true\nStatus: proposed owner, pending human verification\n"
                f"Context: {context}\n"
            )
        else:
            body += (
                "Review: Tests passed in staging; deployment and ownership decisions need supervisor approval.\n"
                f"Change: {title}.\n"
            )
        _source(
            db,
            project,
            connections[repo],
            f"PR #{index + 1} · {title}",
            "pull_request",
            body,
            age=24 - index,
            metadata={
                "number": index + 1,
                "author": people[handle].name,
                "author_id": people[handle].id,
                "state": "open" if index == 1 else "closed",
            },
        )

    problems = [
        ("Webhook deliveries remain stuck after partner timeout", "billing-api", "Alex Morgan"),
        ("Settlement outbox migration has incomplete batches", "ledger-db", "Alex Morgan"),
        ("Worker recovery rehearsal has no current supervisor sign-off", "event-worker", "Priya Shah"),
        ("API canary rollback criteria have not been documented", "billing-api", "Alex Morgan"),
        ("Cache draft contradicts approved settlement datastore decision", "ledger-db", "Sam Rivera"),
    ]
    issue_titles = [item[0] for item in problems] + [
        "Console search keyboard navigation",
        "API pagination contract",
        "Dashboard loading states",
        "Queue depth staging alarm",
        "Database index rehearsal",
        "Release checklist formatting",
        "Staging trace correlation",
        "Partner retry test fixture",
        "Backup manifest validation",
        "Document access review",
        "Console error boundary",
        "Settlement test sanitisation",
        "Service liveness annotation",
        "OpenAPI example correction",
        "Job status poll retry",
        "Operator report pagination",
        "Audit action label",
        "Deployment release note",
        "Rollback image retention",
        "Maintenance runbook refresh",
    ]
    for index, title in enumerate(issue_titles):
        if index < 5:
            _, component, owner = problems[index]
            body = (
                f"Incident: {title}\nSystem: {component}\nOwner: {owner}\n"
                "Status: unresolved\nRisk: This problem needs evidence and owner verification before a handover.\n"
            )
        else:
            body = (
                f"Task: {title}\nStatus: completed\nResolution: Verified in isolated staging test fixtures.\n"
            )
        _source(
            db,
            project,
            connections["atlas-api"],
            f"Issue #{index + 1} · {title}",
            "issue",
            body,
            age=15 + index,
            metadata={
                "number": index + 1,
                "state": "open" if index < 5 else "closed",
                "labels": ["continuity-risk"] if index < 5 else ["completed"],
            },
        )

    areas = [
        "billing-api retry handler",
        "event-worker health checks",
        "operator-console tables",
        "settlement outbox checkpoint",
        "ledger backup integrity",
    ]
    for index in range(75):
        handle = ["alex", "priya", "jordan", "alex", "sam"][index % 5]
        repo = ["atlas-api", "atlas-ops", "atlas-console"][index % 3]
        subject = f"Refine {areas[index % 5]} test case {index + 1}"
        sha = hashlib.sha256(f"nexora-synthetic-commit-{index}".encode()).hexdigest()[:40]
        body = (
            f"Commit: {subject}\nAuthor: {people[handle].name}\nRepository: nexora-demo/{repo}\n"
            f"Synthetic SHA: {sha}\nChanged paths: src/, tests/\n"
            "Review context: A commit alone does not establish responsibility or expertise.\n"
        )
        _source(
            db,
            project,
            connections[repo],
            f"Commit {sha[:7]} · {subject}",
            "commit",
            body,
            age=100 - index,
            metadata={"sha": sha, "author": people[handle].name, "author_id": people[handle].id},
        )
    db.add(
        Audit(
            org_id=org.id,
            project_id=project.id,
            actor_id=people["maya"].id,
            action="demo.seeded",
            resource_type="project",
            resource_id=project.id,
            details={
                "synthetic": True,
                "repositories": 3,
                "commits": 75,
                "pull_requests": 12,
                "issues": 25,
                "documents": 10,
                "license": "CC0-1.0",
            },
        )
    )
    db.commit()
    return project


def _source(db, project, connection, name, kind, body, age=1, metadata=None):
    # Fixtures contain no real secrets or personal data; .example emails are reserved demo identifiers.
    source = Source(
        org_id=project.org_id,
        project_id=project.id,
        connection_id=connection.id if connection else None,
        name=name,
        kind=kind,
        external_id=f"synthetic:{name}",
        url="",
        checksum=hashlib.sha256(body.encode()).hexdigest(),
        status="ready",
        acl=[],
        version=1,
        source_time=utcnow() - timedelta(days=age),
        synthetic=True,
        source_metadata={"synthetic": True, "license": "CC0-1.0", **(metadata or {})},
    )
    db.add(source)
    db.flush()
    db.add(
        Chunk(
            org_id=project.org_id,
            project_id=project.id,
            source_id=source.id,
            source_version=1,
            ordinal=0,
            locator=f"{name} · full text",
            text=body,
        )
    )
    return source
