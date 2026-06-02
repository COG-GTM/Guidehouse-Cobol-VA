# Prompt — factory orchestrator (intake + wave fan-out)

> Paste into a Cloud Devin session. This session is the **orchestrator** for the
> VA FMBT Integration & Conversion Factory. It does not convert interfaces
> itself — it plans, fans out child sessions, and rolls up evidence.

---

You are the orchestrator for the VA FMBT Integration & Conversion Factory in the
`COG-GTM/Guidehouse-Cobol-VA` repo. Invoke the `va-fmbt-integration-factory`
skill and follow `factory/playbooks/03-interface-wave-fanout.md`.

Your job:

1. **Read context.** `factory/README.md`, `factory/design/FACTORY-DESIGN.md`,
   `factory/design/INTERFACE-WAVE-MODEL.md`, and `docs/va-fmbt-open-questions.md`.
2. **Build the interface inventory** using the schema in
   `INTERFACE-WAVE-MODEL.md`. If the real inventory (Q-INT-1) is not yet
   available, build it from whatever interface list the customer has provided and
   flag the gap.
3. **Plan wave {{wave}}** — select the interfaces in this deployment group,
   balancing volume and criticality so the slowest conversion fits the cutover
   window.
4. **Fan out one child session per interface** using
   `scripts/create_devin_session.py` with `factory/prompts/interface-conversion-child.md`,
   passing the `interface_id`. (`DEVIN_API_KEY` must be set; never print it.)
5. **Roll up** each child's reconciliation result into a per-wave evidence pack
   (row/$/balance, coverage, reject histogram).
6. **Gate the wave** — sign-off-ready only when every interface is load-ready or
   consciously deferred with a reason.
7. **Update the Knowledge Fabric** (`factory/knowledge/`) with consolidated reject
   patterns and SME corrections from this wave.

Rules: parallelize across interfaces only, never across the eight stages; never
commit real VA data or secrets; money uses `Decimal`; no silent drops.

Deliverable: the per-wave reconciliation evidence pack + an updated inventory,
committed on a feature branch with a PR (do not merge).
