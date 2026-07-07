#!/usr/bin/env python3
"""GTM Agent: reads KNOWLEDGE + MARKET and generates prospecting output."""
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


def run(product_slug: str | None = None):
    g = OG("gtm-agent")
    products = rows(g.query("knowledge", "list_products", branch="main"))
    segments = rows(g.query("market", "list_icp_segments", branch="main"))
    personas = rows(g.query("market", "list_personas", branch="main"))

    system = (
        "You are the Analytos GTM Agent. Using the data, return JSON with keys: "
        "target_accounts (array), segment_rationale (array), outreach_angles (array)."
    )
    payload = {"products": products, "segments": segments, "personas": personas}
    if product_slug:
        payload["prospect_product"] = product_slug
    prompt = json.dumps(payload, indent=2)
    try:
        data, provider = llm.complete_json(system, prompt, temperature=0.1, log=print)
    except Exception:
        provider = "golden(fallback)"
        data = {
            "target_accounts": [s.get("name") for s in segments[:5]],
            "segment_rationale": [s.get("description") for s in segments[:3]],
            "outreach_angles": [p.get("name") for p in personas[:5]],
        }

    out = OUT / "gtm-agent-output.json"
    out.write_text(json.dumps({"provider": provider, "output": data}, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    run()
