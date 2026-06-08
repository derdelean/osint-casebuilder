"""Correlation engine: link a flat list of findings into an entity graph.

Pure stdlib (works in every environment). Extracts typed entities from each
finding, finds attributes corroborated across multiple platforms, and groups
findings into identity clusters by shared entities. The optional HTML graph
export uses pyvis if it happens to be installed (engine venv)."""

import re
from urllib.parse import urlparse

print("✅ Modul `correlation` (Entity-Graph) aktiv")

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _norm(s) -> str:
    return str(s).strip().lower()


def _domain_of(url) -> str:
    """Best-effort registrable host from a URL or bare domain."""
    s = str(url).strip()
    if "//" not in s:
        s = "//" + s
    host = urlparse(s).netloc or urlparse(s).path
    return host.lower().lstrip("www.").split("/")[0].strip()


def extract_entities(finding: dict) -> list:
    """Return a list of (entity_type, value) pairs extracted from one finding.
    Values are normalized so the same attribute from different sources collides."""
    ents = []
    ftype = finding.get("type")
    val = finding.get("value")
    meta = finding.get("meta") or {}

    # the finding's own subject
    if ftype == "username" and val:
        ents.append(("username", _norm(val)))
    elif ftype == "email" and val:
        ents.append(("email", _norm(val)))
    elif ftype == "phone" and val:
        ents.append(("phone", str(val).strip()))
    elif ftype == "domain" and val:
        ents.append(("domain", _norm(val)))
    elif ftype == "breach" and val:
        ents.append(("email", _norm(val)))
    elif ftype == "host" and val:
        ents.append(("host", str(val).strip()))

    # identity attributes carried in meta
    if meta.get("email") and _EMAIL_RE.match(str(meta["email"])):
        ents.append(("email", _norm(meta["email"])))
    if meta.get("fullname"):
        ents.append(("name", _norm(meta["fullname"])))
    if meta.get("location"):
        ents.append(("location", _norm(meta["location"])))
    if meta.get("website"):
        d = _domain_of(meta["website"])
        if d:
            ents.append(("domain", d))
    if meta.get("domain"):  # email MX / breach / shodan finding
        ents.append(("domain", _norm(meta["domain"])))
    if meta.get("parent_domain"):  # crt.sh subdomain → link to its parent
        ents.append(("domain", _norm(meta["parent_domain"])))

    # maigret pivot material
    for uname in (finding.get("ids_usernames") or {}):
        ents.append(("username", _norm(uname)))
    for link in (finding.get("ids_links") or []):
        ents.append(("url", str(link).strip()))

    # holehe recovery hints (often masked → keep as hints unless a full address)
    rec = meta.get("emailrecovery")
    if rec:
        ents.append(("email" if _EMAIL_RE.match(str(rec)) else "email_hint", _norm(rec)))
    if meta.get("phoneNumber"):
        ents.append(("phone_hint", str(meta["phoneNumber"]).strip()))

    # dedupe while preserving order
    seen = set()
    out = []
    for e in ents:
        if e not in seen and e[1]:
            seen.add(e)
            out.append(e)
    return out


def _finding_label(finding: dict, idx: int) -> str:
    return f"{finding.get('platform', '?')}#{idx}"


def correlate(findings: list) -> dict:
    """Build the correlation summary from all findings.

    Returns entity counts, attributes corroborated across ≥2 findings (the
    high-confidence facts), the identity-cluster count (findings linked by shared
    entities), and the raw edge list for visualization."""
    entity_findings = {}   # (type, value) -> set of finding-label
    edges = []             # (finding_label, etype, value)
    type_counts = {}

    for i, f in enumerate(findings):
        label = _finding_label(f, i)
        for etype, value in extract_entities(f):
            entity_findings.setdefault((etype, value), set()).add(label)
            edges.append((label, etype, value))
            type_counts[etype] = type_counts.get(etype, 0) + 1

    corroborated = []
    for (etype, value), labels in entity_findings.items():
        if len(labels) >= 2:
            corroborated.append({
                "type": etype,
                "value": value,
                "count": len(labels),
                "platforms": sorted({lbl.split("#")[0] for lbl in labels}),
            })
    corroborated.sort(key=lambda c: (-c["count"], c["type"], c["value"]))

    clusters = _count_clusters(findings, entity_findings)

    return {
        "entity_counts": type_counts,
        "distinct_entities": len(entity_findings),
        "corroborated": corroborated,
        "clusters": clusters,
        "edges": edges,
    }


def _count_clusters(findings: list, entity_findings: dict) -> int:
    """Connected components of findings linked when they share any entity (union-find)."""
    labels = [_finding_label(f, i) for i, f in enumerate(findings)]
    parent = {lbl: lbl for lbl in labels}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        parent[find(a)] = find(b)

    for shared in entity_findings.values():
        members = list(shared)
        for other in members[1:]:
            union(members[0], other)

    return len({find(lbl) for lbl in labels}) if labels else 0


def export_graph_html(findings: list, path: str) -> bool:
    """Write an interactive entity graph to `path` using pyvis. Returns False if
    pyvis isn't installed (graceful: the rest of the report is unaffected)."""
    try:
        from pyvis.network import Network
    except ImportError:
        return False

    # cdn_resources="in_line" embeds JS/CSS in the HTML → one self-contained file,
    # and avoids pyvis dumping a local lib/ folder into the working directory.
    net = Network(height="750px", width="100%", notebook=False, directed=False,
                  cdn_resources="in_line")
    added = set()
    for i, f in enumerate(findings):
        flabel = _finding_label(f, i)
        if flabel not in added:
            net.add_node(flabel, label=flabel, color="#6c8ebf", shape="box")
            added.add(flabel)
        for etype, value in extract_entities(f):
            nid = f"{etype}:{value}"
            if nid not in added:
                net.add_node(nid, label=f"{value}\n({etype})", color="#d79b00")
                added.add(nid)
            net.add_edge(flabel, nid)

    net.write_html(path, notebook=False)
    return True
