import os
from pathlib import Path

def generate_markdown_report(findings, session_id, output_path=None, summary=None):
    """
    Generate a markdown report from the findings list (and optional correlation summary).
    """
    output_dir = output_path or "reports"
    os.makedirs(output_dir, exist_ok=True)
    filename = f"report_{session_id}.md"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(render_markdown_report(findings, summary))

    print(f"✅ Report saved to {filepath}")
    return filepath


def render_correlation_section(summary):
    """Render the correlation summary: corroborated cross-platform attributes."""
    lines = ["\n## 🔗 Correlation"]
    lines.append(f"- **Distinct entities**: {summary.get('distinct_entities', 0)}")
    corroborated = summary.get("corroborated", [])
    if corroborated:
        lines.append("\n### Corroborated across ≥2 platforms")
        for c in corroborated:
            plats = ", ".join(c["platforms"])
            lines.append(f"- **{c['type']}** `{c['value']}` — {c['count']}× ({plats})")
    return lines


def render_markdown_report(findings, summary=None):
    """
    Returns a markdown string from the findings list (and optional correlation summary).
    Username hits are tiered: "linked by evidence" (the controller set `evidence`)
    are rendered in full; hits where only the handle exists are listed compactly.
    """
    usernames = [f for f in findings if f.get("type") == "username"]
    linked = [f for f in usernames if f.get("evidence")]
    handle_only = [f for f in usernames if not f.get("evidence")]
    others = [f for f in findings if f.get("type") != "username"]

    lines = ["# 🕵️ OSINT Case Report\n"]
    if usernames:
        lines.append(f"- **Linked by evidence**: {len(linked)}")
        lines.append(f"- **Handle exists only**: {len(handle_only)}")
    if summary:
        lines.extend(render_correlation_section(summary))

    if linked:
        lines.append(f"\n## ✅ Linked by evidence ({len(linked)})")
        lines.extend(_render_platform_blocks(linked))
    if others:
        lines.append(f"\n## 📇 Other findings ({len(others)})")
        lines.extend(_render_platform_blocks(others))
    if handle_only:
        lines.append(f"\n## ❔ Handle exists only — unverified ({len(handle_only)})")
        for f in handle_only:
            lines.append(f"- **{f.get('platform', 'Unknown')}** `{f.get('value', '-')}` — {f.get('source', '-')}")

    return "\n".join(lines)


def _render_platform_blocks(findings):
    grouped = {}

    for f in findings:
        platform = f.get("platform", "Unknown")
        grouped.setdefault(platform, []).append(f)

    lines = []
    for platform, items in grouped.items():
        lines.append(f"\n### 🔹 {platform}")
        for item in items:
            lines.append(f"- **{item.get('type', 'value').title()}**: `{item.get('value', '-')}`")
            lines.append(f"  - **Source**: {item.get('source', '-')}")
            if "score" in item:
                lines.append(f"  - **Score**: `{item['score']}`")
            if item.get("evidence"):
                lines.append(f"  - **Evidence**: {'; '.join(item['evidence'])}")
            if item.get("meta"):
                meta = item["meta"]
                for key in ["fullname", "location", "joined", "followers",
                            "carrier", "region", "line_type", "registrar",
                            "created", "expires", "parent_domain",
                            "breach", "breach_date", "data_classes"]:
                    if meta.get(key):
                        lines.append(f"  - **{key.replace('_', ' ').title()}**: {meta[key]}")
            lines.append("")

    return lines
