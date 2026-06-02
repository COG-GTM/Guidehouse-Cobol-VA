# Playbook 03 — interface wave fan-out (orchestrator)

**Goal.** Convert a whole wave of interfaces in parallel by launching one child
Devin session per interface, then roll up the reconciliation evidence into a
per-wave sign-off pack.

**When to use.** You are the orchestrator session for a wave. You do **not**
convert interfaces yourself — you plan, fan out, and roll up.

**Key principle.** Parallelism is **horizontal across interfaces**, never
vertical across the eight stages. Interfaces are independent; the eight stages
are one pass (see `factory/design/AIE-CRITIQUE.md` #1).

## Steps

1. **Build/refresh the interface inventory.** One row per interface using the
   schema in `factory/design/INTERFACE-WAVE-MODEL.md`. Compute `layout_hash` and
   flag schema drift for any interface converted in an earlier wave.
2. **Pack the wave.** Select the wave's interfaces by deployment group; balance
   `volume_class` and `criticality` so the slowest child fits the cutover window.
3. **Fan out — one child per interface.** For each `not-started`/`mapped` row,
   launch a cloud Devin session running Playbook 01 for that single
   `interface_id`:

   ```bash
   # DEVIN_API_KEY must be set in the environment; never print it.
   python scripts/create_devin_session.py \
     --prompt factory/prompts/interface-conversion-child.md \
     --var interface_id=GL-JV-001
   ```

   (See `scripts/create_devin_session.py` for the exact flags this repo's helper
   supports; adapt the prompt per interface.)
4. **Collect results.** Each child returns its reconciliation result
   (load-ready?, coverage, reject histogram, balance). Update the inventory
   `status`/`coverage` per row.
5. **Gate the wave.** A wave is sign-off-ready only when every row is
   `load-ready` or explicitly `sme-review`/`accepted`. Anything else blocks.
6. **Roll up the evidence pack.** Aggregate per-interface control evidence into
   one per-wave reconciliation pack (the artifact the customer/auditors sign —
   format per Q-GOV-2).
7. **Feed the fabric.** Consolidate new reject patterns and SME corrections from
   the wave into `factory/knowledge/` so the next wave starts smarter.

## Re-run safety

Resume an interrupted wave by re-fanning only rows not yet `accepted`. Emit and
load are idempotent, so a re-run neither double-posts nor drops (test angle #4).

## Done criteria

- Every wave interface is `accepted` (or consciously deferred with a reason).
- Per-wave reconciliation evidence pack produced.
- Inventory and knowledge updated.
