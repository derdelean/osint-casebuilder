import os
import markdown
from pathlib import Path

def generate_markdown_report(findings, session_id, output_path=None):
    """
    Generate a markdown report from the findings list.
    """
    output_dir = output_path or "reports"
    os.makedirs(output_dir, exist_ok=True)
    filename = f"report_{session_id}.md"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(render_markdown_report(findings))

    print(f"✅ Report saved to {filepath}")
    return filepath


def render_markdown_report(findings):
    """
    Returns a markdown string from the findings list.
    """
    lines = ["# 🕵️ OSINT Case Report\n"]
    grouped = {}

    for f in findings:
        platform = f.get("platform", "Unknown")
        grouped.setdefault(platform, []).append(f)

    for platform, items in grouped.items():
        lines.append(f"\n## 🔹 Platform: {platform}")
        for item in items:
            lines.append(f"- **Username**: `{item.get('value', '-')}`")
            lines.append(f"  - **Source**: {item.get('source', '-')}")
            if "score" in item:
                lines.append(f"  - **Score**: `{item['score']}`")
            if item.get("meta"):
                meta = item["meta"]
                for key in ["fullname", "location", "joined", "followers"]:
                    if meta.get(key):
                        lines.append(f"  - **{key.capitalize()}**: {meta[key]}")
            lines.append("")

    return "\n".join(lines)


def render_markdown_content(findings):
    """
    Convert markdown report to HTML string for Streamlit display.
    """
    md = render_markdown_report(findings)
    html = markdown.markdown(md, extensions=["extra", "tables"])
    return html
