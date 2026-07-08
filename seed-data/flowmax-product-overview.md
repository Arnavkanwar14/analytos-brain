# FlowMax — Product Overview (Internal)

**Product site:** flowmax.analytos.ai
**Category:** Production scheduling and flow optimization for discrete manufacturing
**Owner:** Analytos Labs product team
**Status:** In pilot with early-access customers

## What FlowMax Does

FlowMax replaces static finite-capacity schedules and whiteboard routing with a continuously optimized production flow engine. It sequences jobs across work centers, balances WIP, and adapts to late material arrivals and machine downtime without manual replanning marathons.

## Core Features

1. **Constraint-aware flow scheduler** — builds finite-capacity schedules across work centers with precedence, tooling, and labor constraints; re-optimizes in minutes when disruptions occur.
2. **WIP flow balancer** — monitors queue depth and cycle-time variance per cell and recommends pull signals to prevent bottlenecks from starving downstream operations.
3. **Changeover optimizer** — groups jobs by tooling family and color/material grade to minimize setup time while honoring due dates and customer priority tiers.
4. **ERP/MES integration** — reads open work orders, routings, and real-time machine status from SAP Business One and Plex; writes revised start/finish dates and priority flags back to the schedule board.
5. **Autonomy tiers** — Tier 1 recommend-only schedule adjustments, Tier 2 auto-reschedule with supervisor approval, Tier 3 autonomous flow rebalancing within guardrails; every agent action is logged separately from human overrides in the activity log.

## Proof Points (approved for external use)

- Pilot at a Midwest contract manufacturer ($95M revenue, 4 plants, ~180 active work centers): **18% reduction in average WIP days** and **12% improvement in on-time completion** within 60 days. *(approved_external: true)*
- Planner time spent on daily schedule firefighting cut from **4 hours/day to under 45 minutes/day**. *(approved_external: true)*
- Typical deployment: **3-week POC, 120 days to full production** across two pilot cells before plant-wide rollout. *(approved_external: false — internal planning estimate only)*

## Competitive Positioning

Primary displacement target: **PlanetTogether** and spreadsheet-based finite scheduling. FlowMax wins on real-time flow rebalancing (vs. batch overnight replans), constraint modeling depth for mixed-model lines, agentic autonomy tiers, and on-premises perpetual licensing option (no forced SaaS subscription — important for PE-owned plants sensitive to recurring cost).

## Technical Stack (internal only)

React front-end, FastAPI orchestration layer, PostgreSQL, AWS. Optimization core is mixed-integer programming (OR-Tools) with deterministic heuristics; LLM layer used only for natural-language schedule explanations and exception summaries.

## Target Buyer

Operations Directors and Plant Managers at mid-market discrete manufacturers running high-mix, low-to-medium volume lines; economic buyer often the COO or PE operating partner. See ICP doc for full segmentation.
