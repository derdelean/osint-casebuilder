import os
import json

def generate_markdown_report(findings, session_id, output_path=None):
    default_dir = "reports"
    target_dir = os.path.abspath(output_path) if output_path else default_dir
    os.makedirs(target_dir, exist_ok=True)

    # Prepare file names
    filename_md = os.path.join(target_dir, f"report_{session_id}.md")
    filename_json = os.path.join(target_dir, f"report_{session_id}.json")

    # 🔁 Nach Score sortieren
    findings_sorted = sorted(findings, key=lambda x: x.get("score", -1), reverse=True)

    profiles = []

    # write markdown
    with open(filename_md, "w", encoding="utf-8") as f:
        f.write("# 🕵️ OSINT Report\n\n")
        f.write(f"_Session ID: {session_id}_\n\n")

        for item in findings_sorted:
            f.write(f"## 🔍 Fundtyp: {item.get('type', 'unknown')}\n")
            f.write(f"- **Wert**: `{item.get('value', '')}`\n")
            f.write(f"- **Quelle**: {item.get('source', '')}\n")
            f.write(f"- **Zeit**: {item.get('timestamp', '')}\n")

            # Show score
            if "score" in item:
                score = item["score"]
                if score >= 0.85:
                    level = "high ✅"
                elif score >= 0.5:
                    level = "average ⚠️"
                else:
                    level = "low ❌"
                f.write(f"- **Score**: {score} (**{level}**)\n")
            else:
                f.write("- **Score**: (not calculated)\n")

            if "meta" in item and isinstance(item["meta"], dict):
                f.write("\n### 📄 Profile Data\n")
                for key, value in item["meta"].items():
                    f.write(f"- **{key.capitalize()}**: {value}\n")
                profiles.append(item["meta"])

            f.write("\n---\n\n")

        # Summary
        if profiles:
            f.write("# 📊 Summary: Profile Data\n\n")
            for profile in profiles:
                username = profile.get("username", "unknown")
                f.write(f"## {username}\n")
                for key, value in profile.items():
                    if value not in (None, "", [], {}):
                        f.write(f"- **{key.replace('_', ' ').capitalize()}**: {value}\n")

                matching_finding = next((f for f in findings_sorted if f.get("meta") == profile), None)
                if matching_finding and "score" in matching_finding:
                    score = matching_finding["score"]
                    if score >= 0.85:
                        level = "high ✅"
                    elif score >= 0.5:
                        level = "average ⚠️"
                    else:
                        level = "low ❌"
                    f.write(f"- **Score**: {score} (**{level}**)\n")

                f.write("\n")

    print(f"✅ Report created: {filename_md}")

    # Export JSON
    try:
        with open(filename_json, "w", encoding="utf-8") as jf:
            json.dump(findings_sorted, jf, indent=2, ensure_ascii=False)
        print(f"✅ JSON saved: {filename_json}")
    except Exception as e:
        print(f"❌ Error when saving JSON file: {e}")
