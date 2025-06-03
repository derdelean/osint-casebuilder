import streamlit as st
import asyncio
import json
from datetime import datetime
from osint_casebuilder.controller import run_case
from osint_casebuilder.reporter import generate_markdown_report
from io import StringIO

st.set_page_config(page_title="OSINT CaseBuilder", layout="wide")
st.title("🕵️‍♂️ OSINT CaseBuilder Demo")

with st.form("input_form"):
    username = st.text_input("Username", "torvalds")
    fullname = st.text_input("Full Name", "Linus Torvalds")
    location = st.text_input("Location", "Portland, OR")
    keywords = st.text_input("Keywords (comma-separated)", "linux,git,kernel,opensource")
    target_domain = st.text_input("Target Domain", "torvalds.dev")
    submitted = st.form_submit_button("🔍 Start Investigation")

if submitted:
    st.info("Running OSINT case... Please wait.")

    results = asyncio.run(run_case(
        username=username,
        fullname=fullname,
        location=location,
        keywords=[k.strip() for k in keywords.split(",")],
        target_domain=target_domain,
        generate_report=False
    ))

    st.success(f"✅ {len(results)} profile(s) found")

    # Summary block
    github_profiles = [r for r in results if r.get("platform", "").lower() == "github.com"]
    highest_score = max(results, key=lambda x: x.get("score", 0.0), default=None)
    st.markdown("### 🔍 Summary")
    st.markdown(f"- **Total Results**: `{len(results)}`")
    if highest_score:
        st.markdown(f"- **Top Match**: `{highest_score.get('value')}` on `{highest_score.get('platform')}` with score `{highest_score.get('score')}`")
    if github_profiles:
        st.markdown(f"- **GitHub Match Found**: ✅")

    st.markdown("---")

    for item in results:
        with st.expander(f"🔎 {item.get('value')} — {item.get('platform', 'unknown').title()}"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Platform:** `{item.get('platform', 'unknown')}`")
                st.markdown(f"**Profile URL:** {item.get('source', '–')}")
                st.markdown(f"**Timestamp:** `{item.get('timestamp', '-')}`")
            with col2:
                score = item.get("score", 0.0)
                if score >= 0.85:
                    score_level = "🟢 High"
                elif score >= 0.5:
                    score_level = "🟠 Medium"
                else:
                    score_level = "🔴 Low"
                st.markdown(f"**Score:** `{score}` ({score_level})")

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
        file_name=f"osint_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )

    # Generate Markdown in memory
    md_buffer = StringIO()
    from osint_casebuilder.reporter import render_markdown_content
    session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    md_buffer.write(render_markdown_content(results))

    st.download_button(
        label="📝 Download as Markdown",
        data=md_buffer.getvalue(),
        file_name=f"osint_report_{session_id}.md",
        mime="text/markdown"
    )
