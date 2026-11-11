"""Per-visitor, expiring case-study workspaces. No shared real-user credentials."""

import hashlib
import secrets
from datetime import timedelta

from fastapi import HTTPException, Request
from sqlalchemy import select

from app import models as m
from app.config import settings
from app.ingestion import ingest_document
from app.security import hash_password

VISIT_COOKIE = "inheria_demo_visit"
PEOPLE = [
    ("Gaurav", "Departing DevOps engineer", "employee"),
    ("Savinay", "Incoming DevOps engineer", "incoming"),
    ("Rudransh", "Administrator & handover coordinator", "admin"),
]

DOCUMENTS = {
    "01-project-overview.md": """# ShopEase project overview
ShopEase is an authored DevOps case study of an online shopping application.
These records illustrate a workplace handover; they are not Wipro or client records.
Customers browse products, pay and place orders. The DevOps team maintains
release pipelines, monitoring and recovery. Gaurav leaves in two weeks.
Savinay takes over; Rudransh coordinates review, access and closure.
Three repository names: shopease-api, shopease-web, shopease-infra.
No real GitHub, AWS or payment account is connected by this example.

Architecture: ShopEase application environments
System: ShopEase
Staging uses test traffic. Production would serve customers. Learning exercises
are evidence walkthroughs or supervised staging tests, never production changes.
Stack: GitHub Actions, Docker, AWS, Terraform, PostgreSQL, CloudWatch.
""",
    "02-responsibility-register.md": """# DevOps responsibility register
Responsibility: Release pipeline maintenance
Owner: Gaurav
Backup: Rudransh
System: release-pipeline
Critical: yes
Documented: yes
Maintain approved GitHub Actions steps and release checks. Database migrations
need database-owner review; deployment success alone does not prove health.

Responsibility: Monitoring and incident triage
Owner: Gaurav
Backup: Rudransh
System: monitoring
Critical: yes
Documented: yes
Review alerts and error dashboards; escalate payment or database incidents to
the relevant authorised specialist. Do not silence unexplained alerts.

Responsibility: Backup recovery coordination
Owner: Gaurav
Backup: none
System: recovery
Critical: yes
Documented: no
Track backup jobs, locate restore-test evidence and coordinate safe recovery.
A successful backup job is not evidence of a successful restore.
""",
    "03-deployment-runbook.md": """# Current deployment runbook
Procedure: release-pipeline staging release walkthrough
System: release-pipeline
Status: current
Owner: Gaurav
1. Identify the approved release commit, target staging environment and reviewer.
2. Inspect build, tests and image scan results in GitHub Actions.
3. Obtain the release approver's permission before any execution.
4. For a supervised staging test, use the approved deploy workflow.
5. Check application health, error rate, order processing and logs afterwards.
6. If database migration is involved, involve the database owner before rollback.
Validation evidence: release commit, job reference, timestamp, health checks and
reviewer note. This source describes a procedure; it records no actual test run.
""",
    "04-rollback-runbook.md": """# Rollback restrictions
Procedure: release-pipeline rollback walkthrough
System: release-pipeline
Owner: Gaurav
Status: current
Find the last approved image and release evidence. Check schema compatibility.
Application rollback may be unsafe after a destructive database migration.
Consult the database owner and release approver; never invent recovery commands.
In a safe staging exercise, explain rollback preconditions, health checks and
abort/escalation decisions. No cloud execution is supplied by INHERIA.
""",
    "05-monitoring-guide.md": """# Monitoring guide
Procedure: monitoring alert triage
System: monitoring
Owner: Gaurav
Status: current
Open the approved error, latency and order-processing dashboards. Identify the
alert's component, deployment time and affected requests. Correlate logs before
choosing next checks. Escalate payment issues to the application owner and
database saturation to the database team. Record evidence and incident timeline.
Dashboard URLs must be provided by the real organisation; none are fabricated.
""",
    "06-recovery-guide.md": """# Recovery readiness draft
Procedure: recovery restore readiness review
System: recovery
Owner: Gaurav
Status: draft
Locate backup job evidence, retention policy and the latest approved restore test.
The restore-test record is missing. Staging access approval is also outstanding.
Do not claim recovery is verified until a supervisor reviews safe test evidence.
Use an isolated approved environment and identify recovery targets before testing.
""",
    "07-decision-rolling.md": """# Historical release decision
Decision: Rolling deployment for ShopEase
Topic: release-strategy
Status: historical
Rationale: Smaller configuration footprint for the first project stage.
Alternatives: Blue-green deployment needs additional environment resources.
This record conflicts with the later release decision. A human must establish
which decision is authoritative rather than approving both as current truth.
""",
    "08-decision-blue-green.md": """# Later release decision candidate
Decision: Blue-green deployment for ShopEase
Topic: release-strategy
Status: proposed
Rationale: Reduce rollback uncertainty for application-only releases.
Alternatives: Rolling deployment retained as an alternative.
Implementation confirmation is not supplied. Review current pipeline evidence
before establishing authority. A newer timestamp alone does not prove adoption.
""",
    "09-dependencies.md": """# Technical dependencies
Dependency: release-pipeline -> image-registry
Status: current
The release pipeline requires an approved container image and registry access.

Dependency: ShopEase -> PostgreSQL
Status: current
Orders rely on the database. Schema changes require database-owner review.

Dependency: recovery -> staging-access
Status: blocked
A supervised restore exercise requires approved isolated staging access.
""",
    "10-open-incidents.md": """# Open issues and next actions
Incident: Recurring release timeout
Owner: Gaurav
System: release-pipeline
Status: open
Pipeline timeout recurs intermittently. Inspect runner logs and registry latency;
the permanent fix is unresolved. Savinay needs issue context and escalation.

Task: Obtain staging recovery access
Owner: Rudransh
System: recovery
Status: open
Request company-approved access. INHERIA cannot grant AWS/IAM access.

Task: Locate last restore test evidence
Owner: Gaurav
System: recovery
Status: open
Find a permitted report or plan a supervised isolated test. Never invent success.
""",
    "11-tacit-knowledge.md": """# Questions for Gaurav
What do you inspect after a green deployment pipeline?
When does a database migration prevent normal application rollback?
What known workaround exists for the release timeout, and what are its limits?
Who covers backup recovery when you are unavailable?
Answers must be recorded by the departing employee and independently reviewed.
This interview outline contains no employee confirmation or approval.
""",
    "12-recovery-correction-example.md": """# Follow-up example for a recovery task
Use this outline to author a corrected procedure after investigating the gap.
Supply an approved staging-access record, safe restore-test reference, actual
observations, date and independent reviewer. If no real execution occurred,
submit an evidence walkthrough and mark it as such. Never fabricate a test log.
""",
    "13-restricted-coordinator-note.md": """# Coordinator-only case-study note
Decision: Temporary recovery escalation coordinator
Topic: recovery-coordination
Rationale: Keep the missing restore evidence visible until independent review.
Only Rudransh can view this demonstration source. Savinay's handover must not
include it. This illustrates source permissions, not a real confidential record.
""",
}


def create_demo(db):
    expired = list(db.scalars(select(m.DemoVisit).where(m.DemoVisit.expires_at <= m.utcnow())))
    for visit in expired:
        org = db.get(m.Organisation, visit.org_id)
        if org and org.is_demo:
            # Database cascades delete only the expired visitor's isolated workspace.
            db.delete(org)
    db.flush()
    active = list(db.scalars(select(m.DemoVisit.id).where(m.DemoVisit.expires_at > m.utcnow())))
    if len(active) >= settings.judge_demo_max_visits:
        raise HTTPException(429, "Demo capacity is busy. Try later or create your own workspace.")
    nonce = secrets.token_hex(12)
    org = m.Organisation(name="ShopEase DevOps case study", industry="technology", is_demo=True)
    db.add(org)
    db.flush()
    people = {}
    random_hash = hash_password(secrets.token_urlsafe(48))
    for name, title, role in PEOPLE:
        person = m.User(
            org_id=org.id,
            name=name,
            title=title,
            role=role,
            email=f"{name.lower()}-{nonce}@judge.inheria.example",
            password_hash=random_hash,
        )
        db.add(person)
        db.flush()
        people[name] = person
    project = m.Project(
        org_id=org.id,
        name="ShopEase · DevOps handover",
        is_demo=True,
        description="Gaurav leaves; Savinay takes over with evidence and review.",
        stack=["GitHub Actions", "Docker", "AWS", "Terraform", "PostgreSQL", "CloudWatch"],
    )
    db.add(project)
    db.flush()
    for person in people.values():
        db.add(m.Membership(project_id=project.id, user_id=person.id, role=person.role))
    db.flush()
    admin = people["Rudransh"]
    for filename, body in DOCUMENTS.items():
        source, _ = ingest_document(
            db,
            admin,
            project.id,
            filename=filename,
            content=body.encode(),
            acl=[admin.id] if filename.startswith("13-") else [],
        )
        source.synthetic = True
        if filename.startswith("07-"):
            source.source_time = m.utcnow() - timedelta(days=240)
    db.add(
        m.Transition(
            org_id=org.id,
            project_id=project.id,
            departing_id=people["Gaurav"].id,
            successor_id=people["Savinay"].id,
            title="Gaurav → Savinay DevOps handover",
            departure_date=(m.utcnow() + timedelta(days=14)).date().isoformat(),
            status="planned",
            report={
                "prerequisites": [
                    {
                        "id": m.new_id(),
                        "title": "Recovery gap reviewed and follow-up owner recorded",
                        "required": True,
                        "status": "pending",
                        "note": "",
                        "evidence_ids": [],
                        "source_versions": {},
                    }
                ]
            },
        )
    )
    token = secrets.token_urlsafe(48)
    db.add(
        m.DemoVisit(
            org_id=org.id,
            token_hash=hashlib.sha256(token.encode()).hexdigest(),
            expires_at=m.utcnow() + timedelta(hours=settings.judge_demo_hours),
        )
    )
    db.flush()
    return admin, token


def visitor(db, request: Request):
    token = request.cookies.get(VISIT_COOKIE, "")
    if not token or len(token) > 200:
        raise HTTPException(404, "No active demo in this browser. Start a new demo.")
    visit = db.scalar(
        select(m.DemoVisit).where(
            m.DemoVisit.token_hash == hashlib.sha256(token.encode()).hexdigest(),
            m.DemoVisit.expires_at > m.utcnow(),
        )
    )
    if not visit:
        raise HTTPException(404, "Demo expired. Start a new demo; your real account is unaffected.")
    return visit
