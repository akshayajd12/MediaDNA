import networkx as nx
from typing import List, Dict

def build_media_family_tree(evidence_list: List[dict], relationship_list: List[dict]) -> dict:
    """Build Media Family Tree DAG, compute topological genealogy, pinpoint Earliest Traceable Occurrence, and construct reverse lineage paths."""
    
    G = nx.DiGraph()

    # Add evidence nodes
    nodes_map = {}
    for ev in evidence_list:
        ev_id = ev["id"]
        nodes_map[ev_id] = {
            "id": ev_id,
            "evidence_code": ev.get("evidence_id_code", f"EVID-{ev_id[:6]}"),
            "filename": ev.get("original_filename", "media.jpg"),
            "sha256_hash": ev.get("sha256_hash", ""),
            "acquisition_timestamp": str(ev.get("acquisition_timestamp", "")),
            "media_type": ev.get("media_type", "IMAGE"),
            "source_platform": ev.get("source_platform", "DIRECT_UPLOAD"),
            "derived_file_path": ev.get("derived_file_path", ""),
            "manipulation_assessment": ev.get("analysis", {}).get("assessment", "AUTHENTIC"),
            "manipulation_probability": ev.get("analysis", {}).get("manipulation_probability", 0.1),
            "confidence_score": ev.get("analysis", {}).get("confidence_score", 0.9)
        }
        G.add_node(ev_id, **nodes_map[ev_id])

    # Add relationship edges
    edges_list = []
    for rel in relationship_list:
        src = rel["source_evidence_id"]
        tgt = rel["target_evidence_id"]
        if src in nodes_map and tgt in nodes_map:
            edge_info = {
                "id": rel.get("id", f"{src}-{tgt}"),
                "source": src,
                "target": tgt,
                "relationship_type": rel.get("relationship_type", "PARTIAL_DERIVATIVE"),
                "confidence_score": rel.get("confidence_score", 0.90),
                "supporting_evidence": rel.get("supporting_evidence_json", []),
                "detected_transformations": rel.get("detected_transformations_json", []),
                "visual_similarity": rel.get("visual_similarity", 0.9)
            }
            G.add_edge(src, tgt, **edge_info)
            edges_list.append(edge_info)

    # Determine Earliest Traceable Occurrence
    # Look for nodes with in_degree == 0 sorted by acquisition timestamp
    in_degrees = dict(G.in_degree())
    root_candidates = [n for n, deg in in_degrees.items() if deg == 0]
    
    if root_candidates:
        # Sort candidate roots by acquisition timestamp
        root_candidates.sort(key=lambda nid: nodes_map[nid]["acquisition_timestamp"])
        earliest_node_id = root_candidates[0]
    elif nodes_map:
        earliest_node_id = list(nodes_map.keys())[0]
    else:
        earliest_node_id = None

    earliest_occurrence = None
    if earliest_node_id and earliest_node_id in nodes_map:
        earliest_info = nodes_map[earliest_node_id]
        earliest_occurrence = {
            "node_id": earliest_node_id,
            "evidence_code": earliest_info["evidence_code"],
            "filename": earliest_info["filename"],
            "sha256_hash": earliest_info["sha256_hash"],
            "source_platform": earliest_info["source_platform"],
            "acquisition_timestamp": earliest_info["acquisition_timestamp"],
            "disclaimer": "Earliest traceable occurrence within available evidence, not necessarily true original source."
        }

    # Reverse genealogy paths for each node
    reverse_lineage_paths = {}
    for nid in nodes_map:
        if earliest_node_id and nx.has_path(G, earliest_node_id, nid):
            path = nx.shortest_path(G, earliest_node_id, nid)
            reverse_lineage_paths[nid] = path
        else:
            reverse_lineage_paths[nid] = [nid]

    return {
        "nodes": list(nodes_map.values()),
        "edges": edges_list,
        "earliest_traceable_occurrence": earliest_occurrence,
        "reverse_lineage_paths": reverse_lineage_paths,
        "is_dag": nx.is_directed_acyclic_graph(G),
        "total_nodes": len(nodes_map),
        "total_edges": len(edges_list)
    }
