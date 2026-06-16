<!-- Co-branded deliverable: Guidehouse + Cognition. In the formatted (.docx/.pdf)
     version, render the cover from the canonical Cognition template
     (COG-GTM/federal_RFP_responses/templates/) with the Guidehouse logo placed
     alongside the Cognition wordmark. This markdown is the content master. -->

# Accelerating VA's financial modernization with AI-driven delivery

### A Guidehouse and Cognition white paper

*Prepared for the Department of Veterans Affairs Financial Management Business
Transformation (FMBT) program*

*Guidehouse — program leadership, Momentum subject-matter expertise, and
business-rule ownership. Cognition — Devin, the autonomous software engineering
platform that generates the interface code, the data-conversion logic, and the
testing evidence.*

---

## The challenge and our approach

The VA's Financial Management Business Transformation is replacing a financial
management system that has been in service for roughly three decades with CGI
Momentum, the federally approved core financial platform. The transition is being
delivered in twelve waves, each one moving a portion of the VA's financial
operations onto the new platform.

Today that work is done by hand. More than 135 people write the data conversions
and the system-to-system connections manually, without AI assistance. The
remaining waves are substantial: each requires standing up 50 to 100 connections —
both inbound and outbound — and converting the active financial data drawn from
roughly 100 source tables onto the new platform. These connections are how the
VA's financial system exchanges
information with the systems that depend on it every day: internal systems such as
the electronic health record and payroll, and external partners such as the
Treasury and the medical suppliers the VA pays.

At the scale and pace the remaining waves demand, a fully manual approach is slow,
expensive, and difficult to prove correct to an auditor after the fact. Guidehouse
and Cognition propose a different path: an AI-driven approach built on Devin,
Cognition's autonomous software engineering platform. Devin follows the same
disciplined delivery lifecycle the VA already expects — understand the
requirement, build to it, test it thoroughly, validate the result, and document
everything — but performs the repetitive engineering work in a fraction of the
time, and produces the proof of correctness as a first-class output rather than an
afterthought.

The framing matters: **Devin is a force multiplier for the team, not a replacement
for it.** Guidehouse's financial and Momentum experts continue to own the business
rules, the design decisions, and the sign-offs. Devin does the heavy, repeatable
production work and surfaces the exceptions that genuinely need a human judgment.

---

## What Devin delivers — two core work streams

The work divides into two streams. Devin contributes to both, and a shared testing
discipline runs underneath them.

### Work stream 1 — Interface development

Devin analyzes the available business design documents together with the behavior
of the existing connections to understand what each inbound and outbound interface
must do. It then generates the actual interface software — the new modules that
connect to Momentum instead of to the legacy system.

Where current design documentation exists, Devin uses it to accelerate the build.
Where documentation is missing or incomplete — a common reality in a system this
old — Devin reconstructs the requirements from how the legacy system actually
behaves, so a gap in paperwork does not become a gap in delivery. These interfaces
span the VA's internal systems (the electronic health record, payroll, spending
verification) and its external partners (the Treasury, vendors, and medical
suppliers).

### Work stream 2 — One-time data conversion

For each wave, the VA's **open financial transactions** — the unpaid invoices, the
payments not yet closed out, and the reference data they depend on — must be moved
onto the new platform once, correctly. The program deliberately does not carry
decades of closed history forward; it converts only what is still active, which
both reduces risk and shrinks the migration. Devin generates the conversion logic
that transforms the legacy data exports into the format Momentum accepts. This
includes the detailed field-by-field mapping, the crosswalks that reconcile legacy
codes to their Momentum equivalents (for example, fund codes, standard
general-ledger accounts, and taxpayer-identifier conversions), date
standardization, and the validation rules that catch problems before they reach
the new system. Where source records are incomplete or inconsistent, Devin flags
them for cleansing so data-quality issues are resolved up front rather than
carried into the new platform. A single VHA wave alone draws on roughly 100 legacy
source tables, converted across four back-to-back runs.

### The test harness — testing is the product

The single most important idea in this approach is that **the testing is the
deliverable.** Moving financial data is only valuable if every dollar can be proven
correct. Devin builds that proof in two parts.

**Part 1 — validation before the data is loaded.** Before any record reaches
Momentum, automated checks prove three things: every record is accounted for, with
none silently dropped; the dollar amounts tie out exactly, to the cent; and the
data complies with the applicable business rules. When a record is set aside, it is
set aside with a documented, human-readable reason — never quietly discarded.

**Part 2 — verification after the data is loaded.** Once the data is in Momentum,
Devin generates transaction-level test scripts that confirm the data actually
supports real financial operations — that accounts-payable transactions process,
purchase orders function, and the chain from commitment to payment holds together.
This post-load verification is where roughly three-quarters of the real testing
value is realized, because it proves the system works, not merely that the data
moved.

Across successive waves, the goal this testing discipline drives toward is a
**99% first-pass success rate** — meaning that, as the approach matures wave over
wave, the overwhelming majority of records and interfaces pass cleanly the first
time, with human attention reserved for the small remainder. When a test does fail,
the result feeds into the VA's existing change-control process for review and
disposition, consistent with how the program governs changes today.

### A complete audit trail

Every record's journey is traceable from its source file all the way to its load
status in Momentum. If 100,000 records are loaded and five do not, the system can
show exactly which file each came from, on which date, what was corrected, and the
specific rule that flagged it. This is the evidence that survives an audit — and it
is the level of traceability the VA has specifically asked for. Rather than
reconstructing what happened months later, the program has the answer the moment
it is needed.

### An evolving knowledge base

Each wave makes the platform smarter. The mapping patterns that work, the reasons
records are rejected, and the corrections made by Guidehouse's experts all feed
back into Devin's knowledge base. Early waves establish the patterns; later waves
reuse them and run faster, with less manual intervention. This learning loop is the
mechanism behind the program's efficiency target — the work compounds rather than
restarting each time.

---

## Roadmap, responsibilities, and outcomes

### A phased, wave-by-wave roadmap

Delivery is organized wave by wave, aligned to the FMBT deployment groups. The
trajectory is deliberate:

- **Early waves** establish the patterns and build the knowledge base, with heavier
  involvement from Guidehouse's subject-matter experts. These waves prove the
  approach.
- **Middle waves** hit their stride as the accumulated knowledge takes hold and the
  pace increases.
- **Later waves** are largely automated, with experts reviewing exceptions rather
  than producing every artifact by hand.

The target across this trajectory is a **70% reduction in manual effort** compared
with the current hand-coding approach.

### Who does what

This is a team effort with clear lanes of responsibility.

| Party | Responsibility |
| --- | --- |
| **Guidehouse** | Program management and operations; Momentum subject-matter expertise; the business design documents and interface inventory; and business-rule validation and final sign-off. |
| **Cognition (Devin)** | AI-driven generation of both the interface software and the data-conversion logic; the automated test harness (pre-load and post-load); the audit-trail evidence; the evolving knowledge base; and the per-wave reconciliation evidence packages. |
| **CGI** | The Momentum platform, its import specifications, and environment access. |
| **CACI** | The legacy data exports drawn from the existing financial system. |

### The bottom line

Instead of 135 people hand-coding every conversion and every interface, Devin
produces the interface software, the conversion logic, the test harness, and the
audit evidence — and people review the exceptions rather than writing every line.
The result is faster delivery, higher quality (because testing is built in from the
start rather than bolted on at the end), defensible audit trails that hold up under
review, and a 70% reduction in manual effort.

The approach can be proven without touching production systems. Every demonstration
runs on obfuscated, synthetic data — so the VA can see the capability work, end to
end, before any production access is granted.

> **Companion technical perspective.** Rama, a Guidehouse architect, has authored a
> companion technical white paper. Alignment between that technical perspective and
> this business-level paper is being confirmed; this document is the business-level
> companion intended for program leadership.

---

## About Cognition

Cognition AI is an applied AI company building production-grade autonomous systems
for enterprise use, empowering thousands of developers across large organizations,
including teams at Infosys and Itaú, through a security-first, enterprise-ready
platform.

At the core of Cognition's offerings is Devin, an autonomous software engineering
agent designed to plan and execute complex, multi-step engineering workflows across
real codebases and tools, and used by customers in production environments.

Devin is part of a broader Cognition ecosystem — including Windsurf, DeepWiki, CLI
tooling, and pull request review — that integrates seamlessly into existing
developer workflows while emphasizing reliability, safety, and control.

---

*© 2026 Guidehouse Inc. and Cognition AI. This document is for general information
purposes only. All demonstrations referenced herein use obfuscated, synthetic data
and do not require access to production systems.*
