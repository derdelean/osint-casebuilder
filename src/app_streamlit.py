import streamlit as st
import asyncio
import json
from datetime import datetime
from io import StringIO

from osint_casebuilder.controller import run_case
from osint_casebuilder.reporter import render_markdown_report
from utils.validation import validate_inputs

st.set_page_config(page_title="OSINT CaseBuilder", layout="wide")
st.title("🕵️‍♂️ OSINT CaseBuilder Demo")

with st.form("input_form"):
    target_col, hints_col = st.columns(2)
    with target_col:
        st.markdown("**Target**")
        username = st.text_input("Username", placeholder="Enter a username")
        email = st.text_input("Email", placeholder="Enter an email address")
        phone = st.text_input("Phone", placeholder="International format, e.g. +41441234567")
        phone_region = st.text_input("Phone Region", placeholder="2-letter region for national numbers, e.g. CH")
        domain = st.text_input("Domain", placeholder="Domain to look up (RDAP, DNS), e.g. example.com")
    with hints_col:
        st.markdown("**Identity hints**")
        fullname = st.text_input("Full Name", placeholder=" Enter the full name ")
        location = st.text_input("Location", placeholder="Enter a location, e.g. (Portland, OR)")
        keywords = st.text_input("Keywords (comma-separated)", placeholder="Enter keywords, e.g. (osint,linux,git,kernel,opensource)")
        target_domain = st.text_input("Target Domain", placeholder="Enter a target domain, e.g. (torvalds.dev)")

    st.markdown("**Options**")
    opt1, opt2, opt3 = st.columns(3)
    with opt1:
        top_sites = st.number_input("Top Sites", min_value=10, max_value=5000, value=500, step=100)
        all_sites = st.checkbox("All Sites (slow)")
    with opt2:
        pivot_depth = st.number_input("Pivot Depth", min_value=0, max_value=3, value=0)
        infra = st.checkbox("Infra/Breach Intel", help="crt.sh subdomains; HIBP/Shodan/Censys if their API keys are set")
    with opt3:
        save = st.checkbox("Save Case", value=True, help="Persist the run to cases.db")
    submitted = st.form_submit_button("🔍 Start Investigation")

if submitted:
    keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
    if not validate_inputs(username, fullname, location, keyword_list, target_domain, email, domain, phone):
        st.error("Please provide at least one input (username, email, phone, domain, or an identity hint).")
        st.stop()
    st.info("Running OSINT case... Please wait.")
    results = asyncio.run(run_case(
        username=username.strip() or None,
        email=email.strip() or None,
        phone=phone.strip() or None,
        phone_region=phone_region.strip() or None,
        domain=domain.strip() or None,
        fullname=fullname,
        location=location,
        keywords=keyword_list,
        target_domain=target_domain,
        top_sites=100000 if all_sites else int(top_sites),
        pivot_depth=int(pivot_depth),
        infra=infra,
        save=save,
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
