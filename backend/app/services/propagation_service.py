def format_propagation_graph(nodes_raw: list, edges_raw: list) -> dict:
    """Format social media spread propagation network connecting public evidence posts, platforms, and accounts."""
    formatted_nodes = []
    for n in nodes_raw:
        formatted_nodes.append({
            "id": n.id,
            "label": n.node_label,
            "type": n.node_type, # MEDIA, POST, ACCOUNT, PLATFORM
            "platform": n.platform or "PUBLIC_WEB",
            "evidence_id": n.evidence_id,
            "author_account": n.author_account or "@Unknown",
            "post_url": n.post_url or "#",
            "published_at": str(n.published_at) if n.published_at else "Unknown",
            "reach_count": n.reach_count or 0
        })

    formatted_edges = []
    for e in edges_raw:
        formatted_edges.append({
            "id": e.id,
            "source": e.source_node_id,
            "target": e.target_node_id,
            "action_type": e.action_type, # POSTED, REPOSTED, DERIVED_FROM, SHARED
            "timestamp": str(e.timestamp) if e.timestamp else "",
            "confidence": e.confidence or "CONFIRMED_PUBLIC_EVIDENCE"
        })

    return {
        "nodes": formatted_nodes,
        "edges": formatted_edges,
        "total_nodes": len(formatted_nodes),
        "total_edges": len(formatted_edges),
        "disclaimer": "Propagation mapping is limited to accessible public or investigator-provided evidence."
    }
