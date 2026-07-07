#!/usr/bin/env python3
"""Content Agent: reads KNOWLEDGE graph only, then drafts an external post."""
from __future__ import annotations
import json
import pathlib
import sys

sys.path.insert(0, "/root/analytos-brain")
from common.og import OG
from common import llm

OUT = pathlib.Path("/root/analytos-brain/outputs")
OUT.mkdir(exist_ok=True)


def rows(result: dict) -> list[dict]:
    return [{k.split(".", 1)[-1]: v for k, v in r.items()} for r in result.get("rows", [])]


def run(topic: str | None = None):
    c = OG("content-agent")
    products = rows(c.query("knowledge", "list_products", branch="main"))
    proof = rows(c.query("knowledge", "list_approved_proof_points", branch="main"))

    payload = {"products": products, "approved_proof_points": proof}
    if topic:
        payload["blog_topic"] = topic
    prompt = json.dumps(payload, indent=2)
    system = (
        "You are the Analytos Content Agent. Draft one external-safe blog post using only "
        "the provided JSON (approved proof points only). No internal content."
    )
    try:
        text, provider = llm.complete(system, prompt, temperature=0.2, log=print)
    except Exception:
        provider = "golden(fallback)"
        bullets = []
        for p in products[:2]:
            bullets.append(f"- {p.get('name')}: {p.get('description')}")
        text = (
            "Analytos helps discrete manufacturers modernize planning and inspection.\n\n"
            "Key products:\n" + "\n".join(bullets) + "\n\n"
            "Proof points are sourced from externally approved records."
        )

    out = OUT / "content-agent-output.md"
    out.write_text(
        "# Content Agent Output\n\n"
        f"Provider: `{provider}`\n\n"
        "## Draft Blog Post\n\n"
        + text.strip()
        + "\n"
    )
    print(f"wrote {out}")


if __name__ == "__main__":
    run()
