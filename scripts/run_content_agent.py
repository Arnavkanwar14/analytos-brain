#!/usr/bin/env python3
"""Content Agent: reads KNOWLEDGE graph only, then drafts an external post."""
from __future__ import annotations
import json
import pathlib
import re
import sys

sys.path.insert(0, "/root/analytos-brain")
from common.og import OG
from common import llm

OUT = pathlib.Path("/root/analytos-brain/outputs")
OUT.mkdir(exist_ok=True)

# Demo-day topics that ask for private/internal email content.
_INTERNAL_TOPIC_RE = re.compile(
    r"\b("
    r"email|e-mail|thread|inbox|narayan|ashok|santosh|"
    r"confidential|internal.?only|private.?email|"
    r"what did .+ say|quoted .+ email"
    r")\b",
    re.IGNORECASE,
)
_ACCIDENTAL_DENY_RE = re.compile(
    r"(?is)^\s*content-agent cannot access emailthread.*?knowledge only\.\s*",
)


def rows(result: dict) -> list[dict]:
    return [{k.split(".", 1)[-1]: v for k, v in r.items()} for r in result.get("rows", [])]


def _topic_requests_internal(topic: str | None) -> bool:
    return bool(topic and _INTERNAL_TOPIC_RE.search(topic))


def _governance_notice(topic: str | None) -> str:
    topic_bit = (
        f"The requested topic (`{topic}`) asks for private/email/internal content, "
        "so that material is **blocked** and omitted below. "
        if topic
        else ""
    )
    return (
        "## Access notice (Cedar)\n\n"
        "Content-agent **cannot** read `EmailThread`, `Person`, or `Decision` nodes "
        "on the `internal` graph (Cedar DENY). "
        + topic_bit
        + "This draft uses only approved `knowledge` graph entities on `main` "
        "(Product / Feature / ProofPoint with `approved_external=true`).\n"
    )


def _fallback_text(
    products: list[dict],
    features: list[dict],
    proof: list[dict],
    topic: str | None,
) -> str:
    parts: list[str] = []
    if _topic_requests_internal(topic):
        parts.append(
            "Content-agent cannot access EmailThread/private email/internal graph nodes "
            "(Cedar DENY); answering from approved knowledge only.\n"
        )
    parts.append("Analytos content draft from approved knowledge graph nodes:\n")
    for p in products[:2]:
        slug = p.get("slug")
        name = p.get("name")
        parts.append(f"### Product `{slug}` — {name}")
        parts.append(p.get("description") or "")
        parts.append("")
    mc = next(
        (f for f in features if (f.get("slug") or "").endswith("monte-carlo-safety-stock")),
        None,
    )
    if mc:
        parts.append(
            f"### Feature `{mc.get('slug')}` — {mc.get('name')}\n"
            f"{mc.get('description')}\n"
        )
    if proof:
        parts.append("### Approved proof points")
        for pp in proof[:5]:
            parts.append(
                f"- `{pp.get('slug')}`: {pp.get('statement')} "
                f"(metric={pp.get('metric')}, magnitude={pp.get('magnitude')}, "
                f"unit={pp.get('unit')}, window={pp.get('window')})"
            )
    return "\n".join(parts).strip()


def run(topic: str | None = None):
    c = OG("content-agent")
    products = rows(c.query("knowledge", "list_products", branch="main"))
    features = rows(c.query("knowledge", "list_features", branch="main"))
    proof = rows(c.query("knowledge", "list_approved_proof_points", branch="main"))

    asks_internal = _topic_requests_internal(topic)
    payload = {
        "products": products,
        "features": features,
        "approved_proof_points": proof,
        "access": {
            "graphs": {"knowledge": "ALLOW", "market": "DENY", "internal": "DENY"},
            "blocked_entity_types": ["EmailThread", "Person", "Decision"],
            "topic_requests_internal_or_email": asks_internal,
            "instruction_if_blocked": (
                "If the topic asks for email/private/internal content, open the draft by "
                "explicitly stating that content-agent cannot access EmailThread/internal nodes "
                "due to Cedar DENY, then answer only from knowledge entities below."
            ),
        },
    }
    if topic:
        payload["blog_topic"] = topic

    prompt = json.dumps(payload, indent=2)
    if asks_internal:
        deny_rule = (
            "4. access.topic_requests_internal_or_email is TRUE for this request. "
            "You MUST start the draft with this exact sentence: "
            "'Content-agent cannot access EmailThread/private email/internal graph nodes "
            "(Cedar DENY); answering from approved knowledge only.' "
            "Then continue using only knowledge JSON. Do not invent email quotes.\n"
        )
    else:
        deny_rule = (
            "4. access.topic_requests_internal_or_email is FALSE. Do NOT mention emails, "
            "Cedar DENY, EmailThread, Narayan, or access restrictions — this is a normal "
            "knowledge-graph content draft.\n"
        )
    system = (
        "You are the Analytos Content Agent. Draft one external-safe blog post using ONLY "
        "the provided JSON from the approved knowledge graph on main.\n\n"
        "Hard rules:\n"
        "1. Use Product, Feature, and ProofPoint fields exactly — do not invent metrics, "
        "mechanics, SKU counts, revenue, windows, or feature behaviour not present in JSON.\n"
        "2. When explaining a Feature (especially Monte Carlo), quote/paraphrase that "
        "Feature's description and cite its slug (e.g. stockly-monte-carlo-safety-stock). "
        "If the Feature description says 10,000 demand/lead-time scenarios per SKU nightly, "
        "use that exact mechanic — do not invent 'real-time APIs' wording.\n"
        "3. For outcomes, cite ProofPoint slug / statement / magnitude / unit / window "
        "(e.g. 21% on-hand inventory value reduction within 90 days; Midwest pilot "
        "$120M / ~3,400 SKUs). Prefer statement text over inventing percentages like 85%.\n"
        + deny_rule
        + "5. Prefer accuracy and node traceability over eloquence. Include a short "
        "### Sources (graph nodes) section listing product/feature/proof-point slugs used.\n"
    )
    try:
        text, provider = llm.complete(system, prompt, temperature=0.1, log=print)
        if asks_internal and "cannot access" not in text.lower() and "cedar" not in text.lower():
            text = (
                "Content-agent cannot access EmailThread/private email/internal graph nodes "
                "(Cedar DENY); answering from approved knowledge only.\n\n"
                + text
            )
        # Strip accidental DENY intros on normal knowledge topics.
        if not asks_internal:
            text = _ACCIDENTAL_DENY_RE.sub("", text, count=1)
    except Exception:
        provider = "golden(fallback)"
        text = _fallback_text(products, features, proof, topic)

    body = text.strip()
    prefix = _governance_notice(topic) if asks_internal else ""
    out = OUT / "content-agent-output.md"
    out.write_text(
        "# Content Agent Output\n\n"
        f"Provider: `{provider}`\n\n"
        + prefix
        + "## Draft Blog Post\n\n"
        + body
        + "\n"
    )
    print(f"wrote {out}")


if __name__ == "__main__":
    run()
