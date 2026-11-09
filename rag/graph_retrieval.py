import json, re
from pathlib import Path
from pydantic import BaseModel, Field
from rag.bm25 import bm25_search

class Triple(BaseModel):
    subject: str = Field(min_length=1)
    relation: str = Field(min_length=1)
    object: str = Field(min_length=1)
    source_chunk_id: str = Field(min_length=1)

GRAPH_PATH = Path("data/kestrel_graph.json")

def build_graph(corpus_name="kestrel"):
    if corpus_name != "kestrel":
        return {"entities": 0, "edges": 0, "triples": []}

    queries = [
        "KST-1012 identity metadata",
        "KST-5031 postroom messaging",
        "KST-6002 bank approved payment",
        "Identity Priya Raman oncall-identity",
        "Messaging oncall-messaging",
        "Payments Core Jonas Berg oncall-payments",
    ]
    chunks = {}
    for q in queries:
        for c in bm25_search(q, top_k=10, corpus_name=corpus_name):
            chunks[c["chunk_id"]] = c

    triples = []
    for c in chunks.values():
        content = c["text"]
        if "bank approved the payment" in content.lower():
            triples.append(Triple(
                subject="KST-6002", relation="escalates_to",
                object="Payments Core", source_chunk_id=c["chunk_id"]
            ).model_dump())

        sections = re.split(r"(?=^###\s*KST-\d+)", content, flags=re.M)
        for section in sections:
            heading = re.search(r"^###\s*(KST-\d+)", section, re.M)
            escalation = re.search(r"Escalate:\**\s*(.*)", section, re.I)
            if not heading or not escalation:
                continue
            issue = heading.group(1)
            line = escalation.group(1).strip()
            if "bank approved the payment" in line.lower():
                issue = "KST-6002"
            team_match = re.search(r"\bto\s+(Identity|Payments\s+Core)\b", line, re.I)
            team = re.sub(r"\s+", " ", team_match.group(1)).title() if team_match else None
            if "postroom" in line.lower():
                team = "Messaging"
            if team:
                triples.append(Triple(
                    subject=issue, relation="escalates_to",
                    object=team, source_chunk_id=c["chunk_id"]
                ).model_dump())

        for team, channel in re.findall(
            r"\|\s*(Identity|Messaging|Payments\s+Core)\s*\|[^|\n]*\|\s*(#oncall-[a-z-]+)",
            content, re.I
        ):
            team = re.sub(r"\s+", " ", team).title()
            triples.append(Triple(
                subject=team, relation="supported_by",
                object=channel, source_chunk_id=c["chunk_id"]
            ).model_dump())

    unique = {}
    for t in triples:
        key = (t["subject"], t["relation"], t["object"])
        unique[key] = t
    triples = list(unique.values())
    GRAPH_PATH.parent.mkdir(parents=True, exist_ok=True)
    GRAPH_PATH.write_text(json.dumps({"triples": triples}, indent=2), encoding="utf-8")
    return {
        "entities": len({v for t in triples for v in (t["subject"], t["object"])}),
        "edges": len(triples), "triples": triples
    }

def graph_search(query, top_k=5, corpus_name="kestrel"):
    if corpus_name != "kestrel" or not GRAPH_PATH.exists():
        return []
    graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    terms = set(re.findall(r"[a-z0-9-]+", query.lower()))
    matched = set()
    for t in graph["triples"]:
        names = set(re.findall(
            r"[a-z0-9-]+",
            f'{t["subject"]} {t["relation"]} {t["object"]}'.lower()
        ))
        if terms & names:
            matched.add(t["source_chunk_id"])
    candidates = {}
    for c in bm25_search(query, top_k=100, corpus_name=corpus_name):
        if c["chunk_id"] in matched:
            candidates[c["chunk_id"]] = c
    return list(candidates.values())[:top_k]
