import os

def generate_markdown_report(findings, session_id, output_path=None):
    default_dir = "reports"
    target_dir = os.path.abspath(output_path) if output_path else default_dir

    os.makedirs(target_dir, exist_ok=True)
    filename = os.path.join(target_dir, f"report_{session_id}.md")
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write("# 🕵️ OSINT Report\n\n")
        for item in findings:
            f.write(f"- **Typ**: {item['type']}\n")
            f.write(f"  - Wert: `{item['value']}`\n")
            f.write(f"  - Quelle: {item['source']}\n")
            f.write(f"  - Zeit: {item['timestamp']}`\n\n")

    print(f"✅ Report erstellt: {filename}")
