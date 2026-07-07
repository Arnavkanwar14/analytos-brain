"""The extraction target ontology, shared by the Gemini prompt and the validator.
Mirrors cluster/schemas/*.pg. Keep in sync with the schemas."""

# graph -> node type -> {required: [...], optional: [...], list_fields: [...], bool_fields: [...]}
NODES = {
    "knowledge": {
        "Product": {
            "required": ["slug", "name"],
            "optional": ["category", "site", "status", "description",
                         "displacement_target", "licensing", "target_buyer", "source_doc"],
        },
        "Feature": {
            "required": ["slug", "name"],
            "optional": ["product_slug", "description", "source_doc"],
        },
        "ProofPoint": {
            "required": ["slug", "statement", "approved_external"],
            "optional": ["product_slug", "metric", "magnitude", "unit", "direction",
                         "value_before", "value_after", "window", "source_doc", "source_thread"],
            "bool_fields": ["approved_external"],
            "float_fields": ["magnitude"],
        },
        "Competitor": {"required": ["slug", "name"], "optional": ["note"]},
    },
    "market": {
        "ICPSegment": {
            "required": ["slug", "name"],
            "optional": ["description", "channel", "revenue_min_musd", "revenue_max_musd",
                         "employees_range", "geography", "source_doc"],
            "list_fields": ["sectors", "erp_footprint", "trigger_signals",
                            "disqualifiers", "applies_to_products"],
            "float_fields": ["revenue_min_musd", "revenue_max_musd"],
        },
        "Persona": {
            "required": ["slug", "name"],
            "optional": ["role_in_deal", "cares_about", "winning_message",
                         "losing_message", "economic_buyer", "source_doc"],
            "list_fields": ["product_slugs"],
            "bool_fields": ["economic_buyer"],
        },
    },
    "internal": {
        "EmailThread": {
            "required": ["slug", "subject", "confidential"],
            "optional": ["summary", "date", "body", "source_doc"],
            "list_fields": ["participants"],
            "bool_fields": ["confidential"],
        },
        "Person": {"required": ["slug", "name"], "optional": ["email", "org"]},
        "Decision": {
            "required": ["slug", "statement"],
            "optional": ["rationale", "category", "source_thread", "source_doc"],
        },
    },
}

EDGES = {
    "knowledge": ["HasFeature", "ProvenBy", "FeatureProvenBy", "Displaces"],
    "market": ["HasPersona"],
    "internal": ["AuthoredBy", "DiscussedIn", "DecidedBy"],
}


def graph_of_node(node_type: str) -> str | None:
    for g, types in NODES.items():
        if node_type in types:
            return g
    return None


def graph_of_edge(edge_type: str) -> str | None:
    for g, edges in EDGES.items():
        if edge_type in edges:
            return g
    return None
