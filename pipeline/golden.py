"""Golden per-document extraction of the 5 seed docs.

Two roles:
  1. Offline / demo-safe extraction path (used when GEMINI_API_KEY is absent or
     --mock is passed), so the full governance loop runs without the LLM.
  2. Few-shot reference embedded in the Gemini prompt (what "good" looks like).

Each document maps to {"nodes": [...], "edges": [...]}. Node/edge slugs are stable
so re-ingestion is idempotent. approved_external is TRUE only where the source doc
explicitly approves external use; internal-only numbers live on the email graph.
"""

GOLDEN = {
    # ------------------------------------------------------------------ Stockly
    "stockly-product-overview.md": {
        "nodes": [
            {"graph": "knowledge", "type": "Product", "slug": "stockly", "data": {
                "slug": "stockly", "name": "Stockly",
                "category": "Pull Kanban inventory intelligence for discrete manufacturing",
                "site": "stockly.analytos.ai",
                "status": "In production with pilot customers",
                "description": "AI-driven Pull Kanban engine that replaces manual kanban cards and replenishment spreadsheets, continuously right-sizing kanban loops and safety stock so plants stop carrying excess inventory without risking stockouts.",
                "displacement_target": "NetStock and spreadsheet-based min/max planning",
                "licensing": "On-premises perpetual license option (no forced SaaS subscription)",
                "target_buyer": "Plant Managers and Supply Chain Directors at mid-market discrete manufacturers; economic buyer often the CFO or PE operating partner",
                "source_doc": "stockly-product-overview.md"}},
            {"graph": "knowledge", "type": "Feature", "slug": "stockly-pull-kanban-engine", "data": {
                "slug": "stockly-pull-kanban-engine", "name": "Pull Kanban engine", "product_slug": "stockly",
                "description": "Digital kanban loops per SKU/work-center with automatic card sizing and re-sizing as demand shifts.",
                "source_doc": "stockly-product-overview.md"}},
            {"graph": "knowledge", "type": "Feature", "slug": "stockly-monte-carlo-safety-stock", "data": {
                "slug": "stockly-monte-carlo-safety-stock", "name": "Monte Carlo safety-stock simulation", "product_slug": "stockly",
                "description": "Runs 10,000 demand/lead-time scenarios per SKU nightly to recommend optimal safety stock instead of static min/max rules.",
                "source_doc": "stockly-product-overview.md"}},
            {"graph": "knowledge", "type": "Feature", "slug": "stockly-demand-shift-detection", "data": {
                "slug": "stockly-demand-shift-detection", "name": "Demand-shift detection", "product_slug": "stockly",
                "description": "Flags SKUs whose consumption pattern changed and proposes loop adjustments with human approval.",
                "source_doc": "stockly-product-overview.md"}},
            {"graph": "knowledge", "type": "Feature", "slug": "stockly-erp-integration", "data": {
                "slug": "stockly-erp-integration", "name": "ERP integration", "product_slug": "stockly",
                "description": "Native connectors for NetSuite and SAP Business One; reads item masters, open POs, consumption; writes recommended reorder signals.",
                "source_doc": "stockly-product-overview.md"}},
            {"graph": "knowledge", "type": "Feature", "slug": "stockly-autonomy-tiers", "data": {
                "slug": "stockly-autonomy-tiers", "name": "Autonomy tiers", "product_slug": "stockly",
                "description": "Tier 1 recommend-only, Tier 2 auto-adjust with approval, Tier 3 fully autonomous replenishment; agent actions logged separately from human actions.",
                "source_doc": "stockly-product-overview.md"}},
            {"graph": "knowledge", "type": "Feature", "slug": "stockly-supplier-lead-time-intelligence", "data": {
                "slug": "stockly-supplier-lead-time-intelligence", "name": "Supplier lead-time intelligence", "product_slug": "stockly",
                "description": "Learns actual vs. quoted lead times per supplier and feeds the simulation.",
                "source_doc": "stockly-product-overview.md"}},
            {"graph": "knowledge", "type": "ProofPoint", "slug": "stockly-inventory-value-reduction", "data": {
                "slug": "stockly-inventory-value-reduction", "product_slug": "stockly",
                "statement": "21% reduction in on-hand inventory value within 90 days at a Midwest precision machining pilot ($120M revenue, ~3,400 active SKUs).",
                "metric": "on-hand inventory value", "magnitude": 21, "unit": "%", "direction": "reduction", "window": "90 days",
                "approved_external": True, "source_doc": "stockly-product-overview.md", "source_thread": "email-01-stockly-pilot-thread"}},
            {"graph": "knowledge", "type": "ProofPoint", "slug": "stockly-stockout-reduction", "data": {
                "slug": "stockly-stockout-reduction", "product_slug": "stockly",
                "statement": "35% fewer stockout events within 90 days at the precision machining pilot.",
                "metric": "stockout events", "magnitude": 35, "unit": "%", "direction": "reduction", "window": "90 days",
                "approved_external": True, "source_doc": "stockly-product-overview.md", "source_thread": "email-01-stockly-pilot-thread"}},
            {"graph": "knowledge", "type": "ProofPoint", "slug": "stockly-planner-time-reduction", "data": {
                "slug": "stockly-planner-time-reduction", "product_slug": "stockly",
                "statement": "Inventory planner time on replenishment reviews cut from 6 hours/week to under 1 hour/week.",
                "metric": "planner replenishment review time", "value_before": "6 hours/week", "value_after": "under 1 hour/week",
                "direction": "reduction", "approved_external": True, "source_doc": "stockly-product-overview.md",
                "source_thread": "email-01-stockly-pilot-thread"}},
            {"graph": "knowledge", "type": "ProofPoint", "slug": "stockly-deployment-timeline", "data": {
                "slug": "stockly-deployment-timeline", "product_slug": "stockly",
                "statement": "Typical deployment: 2-week POC, 90 days to full production (standard Analytos model).",
                "metric": "deployment timeline", "value_before": "2-week POC", "value_after": "90 days to full production",
                "direction": "absolute", "approved_external": True, "source_doc": "stockly-product-overview.md"}},
            {"graph": "knowledge", "type": "Competitor", "slug": "netstock", "data": {
                "slug": "netstock", "name": "NetStock",
                "note": "Primary displacement target for Stockly. Forecast-push planning; Stockly wins on Pull Kanban methodology, Monte Carlo depth, agentic autonomy, and on-prem perpetual licensing."}},
            {"graph": "knowledge", "type": "Competitor", "slug": "spreadsheet-minmax", "data": {
                "slug": "spreadsheet-minmax", "name": "Spreadsheet-based min/max planning",
                "note": "Manual min/max replenishment spreadsheets displaced by Stockly's Pull Kanban + Monte Carlo engine."}},
        ],
        "edges": [
            {"graph": "knowledge", "edge": "HasFeature", "from": "stockly", "to": "stockly-pull-kanban-engine"},
            {"graph": "knowledge", "edge": "HasFeature", "from": "stockly", "to": "stockly-monte-carlo-safety-stock"},
            {"graph": "knowledge", "edge": "HasFeature", "from": "stockly", "to": "stockly-demand-shift-detection"},
            {"graph": "knowledge", "edge": "HasFeature", "from": "stockly", "to": "stockly-erp-integration"},
            {"graph": "knowledge", "edge": "HasFeature", "from": "stockly", "to": "stockly-autonomy-tiers"},
            {"graph": "knowledge", "edge": "HasFeature", "from": "stockly", "to": "stockly-supplier-lead-time-intelligence"},
            {"graph": "knowledge", "edge": "ProvenBy", "from": "stockly", "to": "stockly-inventory-value-reduction"},
            {"graph": "knowledge", "edge": "ProvenBy", "from": "stockly", "to": "stockly-stockout-reduction"},
            {"graph": "knowledge", "edge": "ProvenBy", "from": "stockly", "to": "stockly-planner-time-reduction"},
            {"graph": "knowledge", "edge": "ProvenBy", "from": "stockly", "to": "stockly-deployment-timeline"},
            {"graph": "knowledge", "edge": "FeatureProvenBy", "from": "stockly-monte-carlo-safety-stock", "to": "stockly-inventory-value-reduction"},
            {"graph": "knowledge", "edge": "Displaces", "from": "stockly", "to": "netstock"},
            {"graph": "knowledge", "edge": "Displaces", "from": "stockly", "to": "spreadsheet-minmax"},
        ],
    },
    # ---------------------------------------------------------------- Inspectly
    "inspectly-product-overview.md": {
        "nodes": [
            {"graph": "knowledge", "type": "Product", "slug": "inspectly", "data": {
                "slug": "inspectly", "name": "Inspectly",
                "category": "Engineering drawing to inspection plan automation",
                "site": "inspectly.analytos.ai",
                "status": "In production with a medical device manufacturing customer",
                "description": "Reads engineering drawings (PDF/TIFF) and automatically generates ballooned inspection plan workbooks in Excel, extracting dimensions, tolerances, and GD&T callouts and mapping them to inspection characteristics with measurement methods.",
                "displacement_target": "Manual ballooning and legacy tools like InspectionXpert",
                "licensing": "Deployed per-client, on-prem friendly, same perpetual license structure as Stockly",
                "target_buyer": "Quality Managers and Quality Engineers at regulated discrete manufacturers (medical device, aerospace, precision machining); economic buyer Director of Quality or VP Operations",
                "source_doc": "inspectly-product-overview.md"}},
            {"graph": "knowledge", "type": "Feature", "slug": "inspectly-dimension-extraction", "data": {
                "slug": "inspectly-dimension-extraction", "name": "Automated dimension extraction", "product_slug": "inspectly",
                "description": "Vision model reads drawings and extracts dimensions, tolerances, GD&T symbols, notes, and title-block metadata.",
                "source_doc": "inspectly-product-overview.md"}},
            {"graph": "knowledge", "type": "Feature", "slug": "inspectly-balloon-numbering", "data": {
                "slug": "inspectly-balloon-numbering", "name": "Balloon numbering", "product_slug": "inspectly",
                "description": "Auto-balloons each characteristic on the drawing and keeps balloon numbers consistent across revisions.",
                "source_doc": "inspectly-product-overview.md"}},
            {"graph": "knowledge", "type": "Feature", "slug": "inspectly-excel-plan-generation", "data": {
                "slug": "inspectly-excel-plan-generation", "name": "Excel inspection plan generation", "product_slug": "inspectly",
                "description": "Outputs the customer's own inspection plan template (characteristic #, nominal, tolerance, method, gauge) ready for FAI/PPAP packages.",
                "source_doc": "inspectly-product-overview.md"}},
            {"graph": "knowledge", "type": "Feature", "slug": "inspectly-revision-diffing", "data": {
                "slug": "inspectly-revision-diffing", "name": "Revision diffing", "product_slug": "inspectly",
                "description": "Compares drawing rev B vs rev A and highlights only changed characteristics so quality teams re-inspect what changed.",
                "source_doc": "inspectly-product-overview.md"}},
            {"graph": "knowledge", "type": "Feature", "slug": "inspectly-human-verification", "data": {
                "slug": "inspectly-human-verification", "name": "Human verification step", "product_slug": "inspectly",
                "description": "Every extracted plan goes to a quality engineer for review before release; corrections feed back to improve extraction.",
                "source_doc": "inspectly-product-overview.md"}},
            {"graph": "knowledge", "type": "ProofPoint", "slug": "inspectly-plan-time-reduction", "data": {
                "slug": "inspectly-plan-time-reduction", "product_slug": "inspectly",
                "statement": "At a leading medical device manufacturer, inspection plan creation time reduced from 4-6 hours per part to under 20 minutes.",
                "metric": "inspection plan creation time", "value_before": "4-6 hours per part", "value_after": "under 20 minutes",
                "direction": "reduction", "approved_external": True, "source_doc": "inspectly-product-overview.md",
                "source_thread": "email-02-inspectly-medical-thread"}},
            {"graph": "knowledge", "type": "ProofPoint", "slug": "inspectly-extraction-accuracy", "data": {
                "slug": "inspectly-extraction-accuracy", "product_slug": "inspectly",
                "statement": "92% first-pass dimension extraction accuracy across the initial four production part numbers; remaining 8% caught in the human verification step.",
                "metric": "first-pass dimension extraction accuracy", "magnitude": 92, "unit": "%", "direction": "absolute",
                "approved_external": True, "source_doc": "inspectly-product-overview.md",
                "source_thread": "email-02-inspectly-medical-thread"}},
            {"graph": "knowledge", "type": "ProofPoint", "slug": "inspectly-quality-standards", "data": {
                "slug": "inspectly-quality-standards", "product_slug": "inspectly",
                "statement": "Supports ISO 13485 and AS9100 quality documentation contexts.",
                "metric": "quality standards supported", "direction": "absolute",
                "approved_external": True, "source_doc": "inspectly-product-overview.md"}},
            {"graph": "knowledge", "type": "Competitor", "slug": "inspectionxpert", "data": {
                "slug": "inspectionxpert", "name": "InspectionXpert",
                "note": "Legacy inspection tool that still requires heavy manual cleanup; Inspectly differentiates on end-to-end automation with a built-in human verification loop and revision-aware diffing."}},
        ],
        "edges": [
            {"graph": "knowledge", "edge": "HasFeature", "from": "inspectly", "to": "inspectly-dimension-extraction"},
            {"graph": "knowledge", "edge": "HasFeature", "from": "inspectly", "to": "inspectly-balloon-numbering"},
            {"graph": "knowledge", "edge": "HasFeature", "from": "inspectly", "to": "inspectly-excel-plan-generation"},
            {"graph": "knowledge", "edge": "HasFeature", "from": "inspectly", "to": "inspectly-revision-diffing"},
            {"graph": "knowledge", "edge": "HasFeature", "from": "inspectly", "to": "inspectly-human-verification"},
            {"graph": "knowledge", "edge": "ProvenBy", "from": "inspectly", "to": "inspectly-plan-time-reduction"},
            {"graph": "knowledge", "edge": "ProvenBy", "from": "inspectly", "to": "inspectly-extraction-accuracy"},
            {"graph": "knowledge", "edge": "ProvenBy", "from": "inspectly", "to": "inspectly-quality-standards"},
            {"graph": "knowledge", "edge": "FeatureProvenBy", "from": "inspectly-dimension-extraction", "to": "inspectly-extraction-accuracy"},
            {"graph": "knowledge", "edge": "FeatureProvenBy", "from": "inspectly-excel-plan-generation", "to": "inspectly-plan-time-reduction"},
            {"graph": "knowledge", "edge": "Displaces", "from": "inspectly", "to": "inspectionxpert"},
        ],
    },
    # --------------------------------------------------------------------- ICP
    "icp-analytos.md": {
        "nodes": [
            {"graph": "market", "type": "ICPSegment", "slug": "icp-mid-market-discrete-manufacturers", "data": {
                "slug": "icp-mid-market-discrete-manufacturers", "name": "Mid-Market Discrete Manufacturers (direct)",
                "description": "Primary direct-sales segment for Stockly and Inspectly.",
                "channel": "direct", "revenue_min_musd": 50, "revenue_max_musd": 500,
                "employees_range": "100-2,000 employees; 1-6 plants",
                "sectors": ["precision machining", "medical device manufacturing", "industrial equipment",
                            "packaging", "automotive tier-2 suppliers", "electronics assembly", "aerospace suppliers"],
                "erp_footprint": ["NetSuite", "SAP Business One", "Epicor", "Infor"],
                "geography": "US first (Midwest/Southeast manufacturing belts), then EU",
                "trigger_signals": ["still running kanban on physical cards or Excel min/max",
                                    "inventory write-downs or working-capital pressure from board/PE owner",
                                    "hiring posts for inventory planners or quality engineers",
                                    "ISO 13485 / AS9100 certified or pursuing, with manual FAI/inspection documentation",
                                    "recent NetStock evaluation or churn"],
                "disqualifiers": ["process/continuous manufacturing (chemicals, food)",
                                  "revenue < $30M", "Fortune 500 (procurement cycle too long)",
                                  "homegrown ERP with no API access"],
                "applies_to_products": ["stockly", "inspectly"], "source_doc": "icp-analytos.md"}},
            {"graph": "market", "type": "ICPSegment", "slug": "icp-pe-firms-operating-partners", "data": {
                "slug": "icp-pe-firms-operating-partners", "name": "PE Firms & Operating Partners (multiplier channel)",
                "description": "Lower-middle-market PE funds with 3+ manufacturing portfolio companies. Pitch: build once, deploy across the portfolio; one POC at a lighthouse portfolio company then standardized rollout.",
                "channel": "multiplier",
                "trigger_signals": ["lower-middle-market PE fund with 3+ manufacturing portfolio companies",
                                    "board/PE working-capital pressure across portfolio"],
                "applies_to_products": ["stockly", "inspectly"], "source_doc": "icp-analytos.md"}},
            {"graph": "market", "type": "Persona", "slug": "persona-plant-manager", "data": {
                "slug": "persona-plant-manager", "name": "Plant Manager", "role_in_deal": "Champion (Stockly)",
                "cares_about": "Stockouts, expediting chaos, floor discipline",
                "winning_message": "Fewer stockouts, less firefighting, your planners get their week back",
                "losing_message": "AI transformation", "economic_buyer": False,
                "product_slugs": ["stockly"], "source_doc": "icp-analytos.md"}},
            {"graph": "market", "type": "Persona", "slug": "persona-supply-chain-director", "data": {
                "slug": "persona-supply-chain-director", "name": "Supply Chain Director", "role_in_deal": "Champion/buyer (Stockly)",
                "cares_about": "Inventory turns, working capital",
                "winning_message": "21% inventory reduction in 90 days at a shop like yours",
                "losing_message": "Feature lists", "economic_buyer": False,
                "product_slugs": ["stockly"], "source_doc": "icp-analytos.md"}},
            {"graph": "market", "type": "Persona", "slug": "persona-quality-manager", "data": {
                "slug": "persona-quality-manager", "name": "Quality Manager / Engineer", "role_in_deal": "Champion (Inspectly)",
                "cares_about": "Audit readiness, documentation backlog",
                "winning_message": "4-6 hours per inspection plan down to 20 minutes, engineer stays in the loop",
                "losing_message": "Replace your team", "economic_buyer": False,
                "product_slugs": ["inspectly"], "source_doc": "icp-analytos.md"}},
            {"graph": "market", "type": "Persona", "slug": "persona-cfo-pe-operating-partner", "data": {
                "slug": "persona-cfo-pe-operating-partner", "name": "CFO / PE Operating Partner", "role_in_deal": "Economic buyer",
                "cares_about": "EBITDA, capex vs opex, risk",
                "winning_message": "Working capital release + perpetual license, 2-week POC proof",
                "losing_message": "Vague ROI", "economic_buyer": True,
                "product_slugs": ["stockly", "inspectly"], "source_doc": "icp-analytos.md"}},
        ],
        "edges": [
            {"graph": "market", "edge": "HasPersona", "from": "icp-mid-market-discrete-manufacturers", "to": "persona-plant-manager"},
            {"graph": "market", "edge": "HasPersona", "from": "icp-mid-market-discrete-manufacturers", "to": "persona-supply-chain-director"},
            {"graph": "market", "edge": "HasPersona", "from": "icp-mid-market-discrete-manufacturers", "to": "persona-quality-manager"},
            {"graph": "market", "edge": "HasPersona", "from": "icp-mid-market-discrete-manufacturers", "to": "persona-cfo-pe-operating-partner"},
            {"graph": "market", "edge": "HasPersona", "from": "icp-pe-firms-operating-partners", "to": "persona-cfo-pe-operating-partner"},
        ],
    },
    # ------------------------------------------------------- Email 01 (Stockly)
    "email-01-stockly-pilot-thread.md": {
        "nodes": [
            {"graph": "internal", "type": "Person", "slug": "person-santosh-thota", "data": {
                "slug": "person-santosh-thota", "name": "Santosh Thota", "email": "santosh@analytos.ai", "org": "Analytos"}},
            {"graph": "internal", "type": "Person", "slug": "person-narayan-laksham", "data": {
                "slug": "person-narayan-laksham", "name": "Narayan Laksham", "email": "narayan@analytos.ai", "org": "Analytos"}},
            {"graph": "internal", "type": "Person", "slug": "person-ashok-suthar", "data": {
                "slug": "person-ashok-suthar", "name": "Ashok Suthar", "email": "ashok@analytos.ai", "org": "Analytos"}},
            {"graph": "internal", "type": "EmailThread", "slug": "email-01-stockly-pilot-thread", "data": {
                "slug": "email-01-stockly-pilot-thread", "subject": "Stockly pilot — 90-day numbers are in",
                "summary": "90-day Stockly pilot readout at the Midwest precision machining company: 21% inventory value reduction, 35% fewer stockouts, planner time 6h->55min/week, 3,412 SKUs live, Monte Carlo ~14 min nightly. Demand-shift detector freed ~$85K dead stock; adoption clicked at Tier 2 autonomy. Positioning + PE + NetSuite-first decisions.",
                "date": "2026-06-15", "confidential": True,
                "participants": ["Santosh Thota", "Narayan Laksham", "Ashok Suthar"],
                "body": "INTERNAL / dummy data. Final 90-day readout from the precision machining pilot: on-hand inventory value down 21% (target 15%); stockout events down 35%; planner replenishment review time 6 hrs/week -> 55 min/week; 3,412 SKUs live on digital kanban loops; Monte Carlo sim running nightly in ~14 min. Learnings: demand-shift detector caught a phase-out SKU the planner missed, freeing ~$85K of dead stock; plant floor adoption only clicked after Tier 2 autonomy (auto-adjust with approval) — Tier 1 recommend-only was ignored. Narayan: proof points approved for external use but keep client anonymous ('Midwest precision machining company, $120M revenue'), never name them. Push 'Pull Kanban + Monte Carlo beats forecast-push' against NetStock. For PE, lead with working-capital release; perpetual license framing. Next pilots should be NetSuite shops first (SAP B1 integration took 3 weeks vs 1 week for NetSuite). Ashok: supplier lead-time module found quoted-vs-actual gaps averaging 9 days on the top 50 suppliers — feeding the sim now.",
                "source_doc": "email-01-stockly-pilot-thread.md"}},
            {"graph": "internal", "type": "Decision", "slug": "decision-keep-client-anonymous-stockly", "data": {
                "slug": "decision-keep-client-anonymous-stockly",
                "statement": "Stockly pilot proof points are approved for external use, but the client stays anonymous ('Midwest precision machining company, $120M revenue'). Never name them in content.",
                "rationale": "Client confidentiality is non-negotiable even for approved metrics.",
                "category": "positioning", "source_thread": "email-01-stockly-pilot-thread", "source_doc": "email-01-stockly-pilot-thread.md"}},
            {"graph": "internal", "type": "Decision", "slug": "decision-pull-kanban-vs-netstock", "data": {
                "slug": "decision-pull-kanban-vs-netstock",
                "statement": "Lead Stockly marketing with 'Pull Kanban + Monte Carlo beats forecast-push planning' as a direct contrast against NetStock's approach — the displacement wedge.",
                "category": "positioning", "source_thread": "email-01-stockly-pilot-thread", "source_doc": "email-01-stockly-pilot-thread.md"}},
            {"graph": "internal", "type": "Decision", "slug": "decision-pe-lead-working-capital", "data": {
                "slug": "decision-pe-lead-working-capital",
                "statement": "For PE conversations, lead with working-capital release (21% of inventory value on a $120M manufacturer is EBITDA-adjacent) and the perpetual-license framing (no new recurring SaaS line on the P&L).",
                "category": "gtm", "source_thread": "email-01-stockly-pilot-thread", "source_doc": "email-01-stockly-pilot-thread.md"}},
            {"graph": "internal", "type": "Decision", "slug": "decision-netsuite-first-poc", "data": {
                "slug": "decision-netsuite-first-poc",
                "statement": "Prioritize NetSuite shops for the next pilots; SAP Business One integration took 3 weeks vs 1 week for NetSuite — don't repeat that on a POC clock.",
                "category": "gtm", "source_thread": "email-01-stockly-pilot-thread", "source_doc": "email-01-stockly-pilot-thread.md"}},
        ],
        "edges": [
            {"graph": "internal", "edge": "AuthoredBy", "from": "email-01-stockly-pilot-thread", "to": "person-santosh-thota"},
            {"graph": "internal", "edge": "AuthoredBy", "from": "email-01-stockly-pilot-thread", "to": "person-narayan-laksham"},
            {"graph": "internal", "edge": "AuthoredBy", "from": "email-01-stockly-pilot-thread", "to": "person-ashok-suthar"},
            {"graph": "internal", "edge": "DiscussedIn", "from": "decision-keep-client-anonymous-stockly", "to": "email-01-stockly-pilot-thread"},
            {"graph": "internal", "edge": "DiscussedIn", "from": "decision-pull-kanban-vs-netstock", "to": "email-01-stockly-pilot-thread"},
            {"graph": "internal", "edge": "DiscussedIn", "from": "decision-pe-lead-working-capital", "to": "email-01-stockly-pilot-thread"},
            {"graph": "internal", "edge": "DiscussedIn", "from": "decision-netsuite-first-poc", "to": "email-01-stockly-pilot-thread"},
            {"graph": "internal", "edge": "DecidedBy", "from": "decision-keep-client-anonymous-stockly", "to": "person-narayan-laksham"},
            {"graph": "internal", "edge": "DecidedBy", "from": "decision-pull-kanban-vs-netstock", "to": "person-narayan-laksham"},
            {"graph": "internal", "edge": "DecidedBy", "from": "decision-pe-lead-working-capital", "to": "person-narayan-laksham"},
            {"graph": "internal", "edge": "DecidedBy", "from": "decision-netsuite-first-poc", "to": "person-narayan-laksham"},
        ],
    },
    # ----------------------------------------------------- Email 02 (Inspectly)
    "email-02-inspectly-medical-thread.md": {
        "nodes": [
            {"graph": "internal", "type": "Person", "slug": "person-santosh-thota", "data": {
                "slug": "person-santosh-thota", "name": "Santosh Thota", "email": "santosh@analytos.ai", "org": "Analytos"}},
            {"graph": "internal", "type": "Person", "slug": "person-narayan-laksham", "data": {
                "slug": "person-narayan-laksham", "name": "Narayan Laksham", "email": "narayan@analytos.ai", "org": "Analytos"}},
            {"graph": "internal", "type": "Person", "slug": "person-ashok-suthar", "data": {
                "slug": "person-ashok-suthar", "name": "Ashok Suthar", "email": "ashok@analytos.ai", "org": "Analytos"}},
            {"graph": "internal", "type": "EmailThread", "slug": "email-02-inspectly-medical-thread", "data": {
                "slug": "email-02-inspectly-medical-thread", "subject": "Inspectly — 4 parts processed, verification loop working",
                "summary": "Four production part numbers processed end-to-end at the medical device customer. 92% first-pass accuracy; verification caught the rest (stacked tolerances, one ambiguous GD&T datum). Plan time ~18 min vs 4-6 hours. Revision-diff highlighted 7 of 140 changed characteristics. Client stays anonymous; 'engineer stays in the loop' story; aerospace/AS9100 expansion; revision-diff into standard deck.",
                "date": "2026-06-18", "confidential": True,
                "participants": ["Ashok Suthar", "Narayan Laksham", "Santosh Thota"],
                "body": "INTERNAL / dummy data. Four production part numbers fully processed end-to-end at the medical device customer. Extraction accuracy held at 92% first-pass across all four; the quality engineer's verification caught the rest — mostly stacked tolerances and one ambiguous GD&T datum callout. Average plan generation time now 18 minutes vs 4-6 hours per part. Revision-diff is the sleeper hit: on the rev-change part we highlighted 7 changed characteristics out of 140 total, and they re-inspected only those 7. Narayan: client name stays confidential ('a leading medical device manufacturer'), non-negotiable. Story is NOT 'AI replaces quality engineers' — it's 'engineer stays in the loop, drudgery disappears'; the verification step is a feature for ISO 13485 / AS9100 buyers who need human sign-off anyway. Expansion targets: aerospace suppliers doing FAI under AS9100; prioritize shops posting quality-engineer job openings (documentation backlog is the tell). Get the revision-diff demo into the standard deck. Santosh: Inspectly deploys per-client, on-prem friendly, same perpetual license as Stockly — often the door-opener for medical/aero prospects.",
                "source_doc": "email-02-inspectly-medical-thread.md"}},
            {"graph": "internal", "type": "Decision", "slug": "decision-keep-client-anonymous-inspectly", "data": {
                "slug": "decision-keep-client-anonymous-inspectly",
                "statement": "Inspectly's medical device client name stays confidential externally — refer to 'a leading medical device manufacturer'. Non-negotiable.",
                "category": "positioning", "source_thread": "email-02-inspectly-medical-thread", "source_doc": "email-02-inspectly-medical-thread.md"}},
            {"graph": "internal", "type": "Decision", "slug": "decision-engineer-in-the-loop", "data": {
                "slug": "decision-engineer-in-the-loop",
                "statement": "Position Inspectly as 'engineer stays in the loop, drudgery disappears', never 'AI replaces quality engineers'. The verification step is a feature, not a limitation, for ISO 13485 / AS9100 buyers.",
                "category": "positioning", "source_thread": "email-02-inspectly-medical-thread", "source_doc": "email-02-inspectly-medical-thread.md"}},
            {"graph": "internal", "type": "Decision", "slug": "decision-aerospace-as9100-expansion", "data": {
                "slug": "decision-aerospace-as9100-expansion",
                "statement": "Expand Inspectly to aerospace suppliers doing FAI packages under AS9100 (same motion); prioritize shops posting quality-engineer job openings — documentation backlog is the tell.",
                "category": "gtm", "source_thread": "email-02-inspectly-medical-thread", "source_doc": "email-02-inspectly-medical-thread.md"}},
            {"graph": "internal", "type": "Decision", "slug": "decision-revision-diff-in-deck", "data": {
                "slug": "decision-revision-diff-in-deck",
                "statement": "Put the revision-diff demo (7 of 140 characteristics re-inspected) plus the 4-6hrs->20min number into the standard deck — that's the whole pitch.",
                "category": "gtm", "source_thread": "email-02-inspectly-medical-thread", "source_doc": "email-02-inspectly-medical-thread.md"}},
        ],
        "edges": [
            {"graph": "internal", "edge": "AuthoredBy", "from": "email-02-inspectly-medical-thread", "to": "person-ashok-suthar"},
            {"graph": "internal", "edge": "AuthoredBy", "from": "email-02-inspectly-medical-thread", "to": "person-narayan-laksham"},
            {"graph": "internal", "edge": "AuthoredBy", "from": "email-02-inspectly-medical-thread", "to": "person-santosh-thota"},
            {"graph": "internal", "edge": "DiscussedIn", "from": "decision-keep-client-anonymous-inspectly", "to": "email-02-inspectly-medical-thread"},
            {"graph": "internal", "edge": "DiscussedIn", "from": "decision-engineer-in-the-loop", "to": "email-02-inspectly-medical-thread"},
            {"graph": "internal", "edge": "DiscussedIn", "from": "decision-aerospace-as9100-expansion", "to": "email-02-inspectly-medical-thread"},
            {"graph": "internal", "edge": "DiscussedIn", "from": "decision-revision-diff-in-deck", "to": "email-02-inspectly-medical-thread"},
            {"graph": "internal", "edge": "DecidedBy", "from": "decision-keep-client-anonymous-inspectly", "to": "person-narayan-laksham"},
            {"graph": "internal", "edge": "DecidedBy", "from": "decision-engineer-in-the-loop", "to": "person-narayan-laksham"},
            {"graph": "internal", "edge": "DecidedBy", "from": "decision-aerospace-as9100-expansion", "to": "person-narayan-laksham"},
            {"graph": "internal", "edge": "DecidedBy", "from": "decision-revision-diff-in-deck", "to": "person-santosh-thota"},
        ],
    },
}


def golden_for(doc_name: str) -> dict:
    return GOLDEN.get(doc_name, {"nodes": [], "edges": []})
