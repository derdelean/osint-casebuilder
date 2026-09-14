import streamlit as st
import asyncio
import json
from datetime import datetime
from io import StringIO

from osint_casebuilder.controller import run_case
from osint_casebuilder.reporter import render_markdown_report

st.set_page_config(page_title="OSINT CaseBuilder", layout="wide")
st.title("🕵️‍♂️ OSINT CaseBuilder Demo")

with st.form("input_form"):
    username = st.text_input("Username", placeholder="Enter a username")
    fullname = st.text_input("Full Name", placeholder=" Enter the full name ")
    location = st.text_input("Location", placeholder="Enter a location, e.g. (Portland, OR)")
    keywords = st.text_input("Keywords (comma-separated)", placeholder="Enter keywords, e.g. (osint,linux,git,kernel,opensource)")
    target_domain = st.text_input("Target Domain", placeholder="Enter a target domain, e.g. (torvalds.dev)")
    submitted = st.form_submit_button("🔍 Start Investigation")

if submitted:
    st.info("Running OSINT case... Please wait.")
    results = asyncio.run(run_case(
        username=username,
        fullname=fullname,
        location=location,
        keywords=[k.strip() for k in keywords.split(",") if k.strip()],
        target_domain=target_domain,
        generate_report=False
    ))
    st.session_state["results"] = results
    st.session_state["session_id"] = datetime.now().strftime('%Y%m%d_%H%M%S')

if "results" in st.session_state:
    results = st.session_state["results"]
    session_id = st.session_state["session_id"]

    st.success(f"✅ {len(results)} finding(s)")

    # Summary block
    usernames = [r for r in results if r.get("type") == "username"]
    linked = [r for r in usernames if r.get("evidence")]
    github_profiles = [r for r in results if r.get("platform", "").lower() == "github"]
    highest_score = max(results, key=lambda x: x.get("score", 0.0), default=None)
    st.markdown("### 🔍 Summary")
    st.markdown(f"- **Total Results**: `{len(results)}`")
    if usernames:
        st.markdown(f"- **Linked by evidence**: `{len(linked)}` · "
                    f"**Handle exists only**: `{len(usernames) - len(linked)}`")
    if highest_score:
        st.markdown(f"- **Top Match**: `{highest_score.get('value')}` on `{highest_score.get('platform')}` with score `{highest_score.get('score')}`")
    if github_profiles:
        st.markdown(f"- **GitHub Match Found**: ✅")

    st.markdown("---")

    # Same tier order as the Markdown report: evidence-linked hits, other lookups,
    # then username hits where only the handle exists.
    def tier(item):
        if item.get("evidence"):
            return 0, "✅"
        return (2, "❔") if item.get("type") == "username" else (1, "📇")

    for item in sorted(results, key=lambda r: tier(r)[0]):
        with st.expander(f"{tier(item)[1]} {item.get('value')} — {item.get('platform', 'unknown').title()}"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Platform:** `{item.get('platform', 'unknown')}`")
                st.markdown(f"**Profile URL:** {item.get('source', '–')}")
                st.markdown(f"**Timestamp:** `{item.get('timestamp', '-')}`")
            with col2:
                st.markdown(f"**Score:** `{item.get('score', '–')}`")
                if item.get("evidence"):
                    st.markdown("**Evidence:** " + "; ".join(item["evidence"]))
                elif item.get("type") == "username":
                    st.markdown("**Evidence:** none — handle exists only")

            meta = item.get("meta", {})
            if meta:
                st.markdown("### 📄 Metadata")
                for k, v in meta.items():
                    if v:
                        st.markdown(f"- **{k.capitalize()}**: {v}")

    # Export section
    st.markdown("---")
    st.markdown("### 📤 Export Results")

    json_data = json.dumps(results, indent=2)
    st.download_button(
        label="💾 Download as JSON",
        data=json_data,
        file_name=f"osint_results_{session_id}.json",
        mime="application/json"
    )

    md_buffer = StringIO()
    md_buffer.write(render_markdown_report(results))

    st.download_button(
        label="📝 Download as Markdown",
        data=md_buffer.getvalue(),
        file_name=f"osint_report_{session_id}.md",
        mime="text/markdown"
    )
