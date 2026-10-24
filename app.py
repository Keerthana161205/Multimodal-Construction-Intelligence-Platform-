import os
import json
import requests
import urllib.parse
import streamlit as st
from PIL import Image

# ==============================================================================
# 0. STREAMLIT PAGE CONFIGURATION & MODERN CUSTOM CSS
# ==============================================================================
st.set_page_config(
    page_title="Multimodal Construction Intelligence Platform",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    /* Theme Palette & Global Styles */
    :root {
        --primary-color: #0f172a;
        --accent-color: #0284c7;
        --bg-light: #f8fafc;
        --card-bg: #ffffff;
        --text-dark: #1e293b;
        --border-color: #e2e8f0;
    }
    
    .stApp {
        background-color: var(--bg-light);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Metric Cards Styling */
    .metric-card {
        background-color: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        text-align: center;
        margin-bottom: 15px;
    }
    .metric-value {
        font-size: 28px;
        font-weight: 700;
        color: var(--accent-color);
        margin-top: 5px;
    }
    .metric-label {
        font-size: 14px;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 600;
    }

    /* Status Badges */
    .status-badge {
        display: inline-block;
        padding: 6px 16px;
        border-radius: 50px;
        font-weight: 700;
        font-size: 14px;
        text-align: center;
        margin-bottom: 10px;
    }
    .badge-pass { background-color: #dcfce7; color: #15803d; border: 1px solid #86efac; }
    .badge-warn { background-color: #fef9c3; color: #a16207; border: 1px solid #fde047; }
    .badge-fail { background-color: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; }

    /* Custom Header Banner */
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: white;
        padding: 24px;
        border-radius: 16px;
        margin-bottom: 25px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    .main-header h1 {
        color: #f8fafc !important;
        margin: 0;
        font-size: 28px;
        font-weight: 800;
    }
    .main-header p {
        color: #94a3b8;
        margin: 5px 0 0 0;
        font-size: 15px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# ==============================================================================
# 1. HELPER FUNCTIONS & GEMINI INTEGRATION
# ==============================================================================

def get_gemini_client(api_key: str):
    """Initializes Google GenAI client safely with fallback checks."""
    if not api_key:
        return None
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except Exception as e:
        st.sidebar.error(f"Failed to initialize Gemini Client: {str(e)}")
        return None


def query_gemini_multimodal(client, image: Image.Image, prompt: str) -> str:
    """Queries Gemini 1.5/2.0 Vision model with image and structured prompt."""
    if not client:
        return ""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[image, prompt]
        )
        return response.text
    except Exception as e:
        st.error(f"AI Multimodal Processing Error: {str(e)}")
        return ""


def clean_json_response(raw_text: str) -> dict:
    """Extracts and parses JSON object from AI string response markdown blocks."""
    try:
        cleaned = raw_text.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()
        return json.loads(cleaned)
    except Exception as e:
        st.error(f"JSON Parsing Error: {str(e)}. Displaying raw output.")
        return {"raw_output": raw_text}

# ==============================================================================
# 2. MOCK DEMO FALLBACK DATA GENERATORS
# ==============================================================================

def get_mock_ppe_data() -> dict:
    return {
        "safety_score": 78,
        "overall_status": "NEEDS ATTENTION",
        "ppe_detection": {
            "helmets": {"detected": True, "compliance_rate": "85%", "status": "Compliant"},
            "high_vis_vests": {"detected": True, "compliance_rate": "100%", "status": "Compliant"},
            "steel_toe_boots": {"detected": True, "compliance_rate": "60%", "status": "Partial Non-Compliance"},
            "safety_harnesses": {"detected": False, "compliance_rate": "0%", "status": "Critical Non-Compliance"}
        },
        "hazards": [
            {
                "hazard": "Unsecured Work at Height",
                "severity": "Critical",
                "location": "Scaffolding Tier 3",
                "remedy": "Halt height operations immediately until OSHA/IS 456 compliant full-body harnesses and lifelines are anchored."
            },
            {
                "hazard": "Missing Hard Hat on Site Ground",
                "severity": "Medium",
                "location": "Near Rebar Storage Area",
                "remedy": "Issue mandatory site warning and re-issue safety helmets prior to reentry."
            }
        ]
    }


def get_mock_crack_data() -> dict:
    return {
        "defect_type": "Structural Shear Crack",
        "severity": "High",
        "estimated_width_mm": 3.8,
        "urgency": "Immediate (Within 48 Hours)",
        "root_causes": [
            "Excessive differential settlement of concrete footings",
            "Inadequate shear reinforcement steel during casting under IS 456 loading criteria",
            "Thermal stress expansion combined with heavy dynamic site loads"
        ],
        "recommended_repairs": [
            "Perform non-destructive ultrasonic pulse velocity (UPV) testing to determine crack depth.",
            "High-pressure structural epoxy injection along full crack trajectory.",
            "Install carbon fiber reinforced polymer (CFRP) wraps to restore shear capacity."
        ]
    }

# ==============================================================================
# 3. SIDEBAR & NAVIGATION SETUP
# ==============================================================================

st.sidebar.image("https://img.icons8.com/color/96/000000/crane.png", width=70)
st.sidebar.title("Construction AI Platform")
st.sidebar.caption("Skill Wallet Capstone Project 1")

# API Key Handling
api_key = st.sidebar.text_input(
    "Google Gemini API Key",
    type="password",
    help="Enter Gemini API key for live multimodal vision analysis. Leave empty for Demonstration Mode."
)

if api_key:
    client = get_gemini_client(api_key)
    demo_mode = False
    st.sidebar.success("Gemini API Connected")
else:
    client = None
    demo_mode = True
    st.sidebar.warning("Demo Mode Active (No API Key)")

st.sidebar.divider()

# Architecture Overview
with st.sidebar.expander(" Architecture Overview", expanded=False):
    st.markdown("""
    **Core Engine Specs:**
    - **Frontend:** Streamlit + Custom CSS
    - **Vision AI:** Multimodal Gemini Engine
    - **Compliance:** OSHA & IS 456 Standards
    - **Generative Rendering:** Pollinations/Flux API
    - **Data Contract:** Validated Strict JSON Schema
    """)

st.sidebar.divider()
st.sidebar.info("Designed for Site Engineers, Safety Auditors, and Real Estate Valuers.")

# Header Banner
st.markdown("""
    <div class="main-header">
        <h1>Multimodal Construction Intelligence Platform</h1>
        <p>AI-driven safety auditing, structural integrity diagnostic, financial estimation, and weather-aware site management.</p>
    </div>
""", unsafe_allow_html=True)

# Main Navigation Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "🦺 PPE Safety & Audit",
    "🔍 Crack Diagnostics",
    "📊 Planning & Valuation",
    "🌤️ Site Assistant & Weather"
])

# ==============================================================================
# TAB 1: SITE SAFETY & PPE AUDIT (EPIC 2)
# ==============================================================================
with tab1:
    st.header("Site Safety & PPE Compliance Audit")
    st.caption("Standards Applied: OSHA & Indian Standard IS 456 Construction Safety Codes")

    col_upload, col_display = st.columns([1, 1])

    with col_upload:
        uploaded_file = st.file_uploader(
            "Upload Site Photo (JPG/PNG)", type=["jpg", "jpeg", "png"], key="ppe_upload"
        )

        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Construction Site Image", use_container_width=True)
            analyze_btn = st.button("Run PPE Safety Audit", type="primary", use_container_width=True)
        else:
            st.info(" Please upload a site image to initiate PPE auditing.")
            analyze_btn = False

    with col_display:
        if uploaded_file and analyze_btn:
            with st.spinner("Analyzing site imagery against OSHA & IS 456 standards..."):
                if demo_mode:
                    results = get_mock_ppe_data()
                else:
                    prompt = """
                    Act as an expert OSHA and Indian Standard (IS 456) site safety auditor. 
                    Analyze the uploaded image for worker Personal Protective Equipment (PPE) compliance.
                    Inspect specifically for:
                    1. Safety Helmets
                    2. High-Visibility Vests
                    3. Steel-Toe Boots
                    4. Safety Harnesses / Fall Protection

                    Return ONLY a JSON response matching this exact schema:
                    {
                        "safety_score": <integer 0 to 100>,
                        "overall_status": "<SAFE | NEEDS ATTENTION | CRITICAL RISK>",
                        "ppe_detection": {
                            "helmets": {"detected": <bool>, "compliance_rate": "<str>", "status": "<str>"},
                            "high_vis_vests": {"detected": <bool>, "compliance_rate": "<str>", "status": "<str>"},
                            "steel_toe_boots": {"detected": <bool>, "compliance_rate": "<str>", "status": "<str>"},
                            "safety_harnesses": {"detected": <bool>, "compliance_rate": "<str>", "status": "<str>"}
                        },
                        "hazards": [
                            {
                                "hazard": "<description>",
                                "severity": "<Low | Medium | High | Critical>",
                                "location": "<estimated zone/area in image>",
                                "remedy": "<corrective action standard compliance requirement>"
                            }
                        ]
                    }
                    """
                    raw_res = query_gemini_multimodal(client, image, prompt)
                    results = clean_json_response(raw_res)

            # Display Results
            if "safety_score" in results:
                score = results.get("safety_score", 0)
                status = results.get("overall_status", "UNKNOWN")

                # Metric Cards
                m1, m2 = st.columns(2)
                with m1:
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">Safety Compliance Score</div>
                            <div class="metric-value">{score} / 100</div>
                        </div>
                    """, unsafe_allow_html=True)
                with m2:
                    badge_class = "badge-pass" if score >= 85 else ("badge-warn" if score >= 60 else "badge-fail")
                    st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">Site Risk Status</div>
                            <div style="margin-top:8px;"><span class="status-badge {badge_class}">{status}</span></div>
                        </div>
                    """, unsafe_allow_html=True)

                st.subheader("PPE Checklist Breakdown")
                ppe = results.get("ppe_detection", {})
                ppe_cols = st.columns(4)
                
                items = [
                    ("Helmets", "helmets", "🪖"),
                    ("High-Vis Vests", "high_vis_vests", "🦺"),
                    ("Steel-Toe Boots", "steel_toe_boots", "🥾"),
                    ("Harnesses", "safety_harnesses", "🪢")
                ]
                
                for idx, (label, key, emoji) in enumerate(items):
                    with ppe_cols[idx]:
                        item_data = ppe.get(key, {})
                        det = item_data.get("detected", False)
                        rate = item_data.get("compliance_rate", "N/A")
                        st.markdown(f"**{emoji} {label}**")
                        st.write(f"Status: {'✅ Found' if det else '❌ Missing'}")
                        st.write(f"Rate: {rate}")

                st.subheader("Identified Hazards & Corrective Remedies")
                hazards = results.get("hazards", [])
                if hazards:
                    for h in hazards:
                        sev = h.get("severity", "Low")
                        color = "#ef4444" if sev in ["Critical", "High"] else "#f59e0b"
                        st.markdown(f"""
                            <div style="border-left: 4px solid {color}; padding-left: 15px; margin-bottom: 12px; background: white; padding: 10px; border-radius: 4px;">
                                <strong style="color: {color};">[{sev.upper()}] {h.get('hazard')}</strong><br/>
                                <small><b>Zone:</b> {h.get('location')} | <b>Remedy:</b> {h.get('remedy')}</small>
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.success("No immediate safety hazards detected on site.")

                # Downloadable JSON Report
                st.divider()
                st.download_button(
                    label="📥 Download Structured JSON Safety Audit Report",
                    data=json.dumps(results, indent=2),
                    file_name="site_safety_audit_report.json",
                    mime="application/json",
                    use_container_width=True
                )

# ==============================================================================
# TAB 2: CRACK DIAGNOSTICS & STRUCTURAL INTEGRITY (EPIC 2)
# ==============================================================================
with tab2:
    st.header("Concrete Crack Diagnostics & Structural Integrity")
    st.caption("AI-powered concrete wall/surface fault identification and repair recommendation engine.")

    col_up2, col_res2 = st.columns([1, 1])

    with col_up2:
        crack_file = st.file_uploader(
            "Upload Structural Surface Photo", type=["jpg", "jpeg", "png"], key="crack_upload"
        )

        if crack_file:
            crack_img = Image.open(crack_file)
            st.image(crack_img, caption="Concrete Surface Image", use_container_width=True)
            diag_btn = st.button("Run Diagnostic Analysis", type="primary", use_container_width=True)
        else:
            st.info(" Please upload a clear close-up image of concrete/wall defects.")
            diag_btn = False

    with col_res2:
        if crack_file and diag_btn:
            with st.spinner("Analyzing concrete fracture mechanics and strain patterns..."):
                if demo_mode:
                    c_results = get_mock_crack_data()
                else:
                    prompt = """
                    Act as a structural engineering diagnostics expert. Analyze the uploaded photo of concrete/building surface for defects.
                    Classify the crack into one of the following types:
                    - Hairline Crack
                    - Settlement Crack
                    - Structural Shear Crack
                    - Thermal Expansion Crack
                    - Spalling / Concrete Degradation

                    Provide structural recommendations and estimated crack width in millimeters.
                    Return ONLY a JSON response matching this schema:
                    {
                        "defect_type": "<Type of defect>",
                        "severity": "<Low | Medium | High | Critical>",
                        "estimated_width_mm": <float>,
                        "urgency": "<Immediate | Within 14 Days | Routine Monitoring>",
                        "root_causes": ["<cause 1>", "<cause 2>"],
                        "recommended_repairs": ["<repair step 1>", "<repair step 2>"]
                    }
                    """
                    raw_res = query_gemini_multimodal(client, crack_img, prompt)
                    c_results = clean_json_response(raw_res)

            if "defect_type" in c_results:
                st.subheader("Diagnostic Diagnosis Report")
                
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("Defect Classification", c_results.get("defect_type", "N/A"))
                with c2:
                    st.metric("Estimated Width", f"{c_results.get('estimated_width_mm', 0)} mm")
                with c3:
                    st.metric("Action Urgency", c_results.get("urgency", "N/A"))

                st.markdown("### 🔬 Structural Root Causes")
                for cause in c_results.get("root_causes", []):
                    st.markdown(f"- {cause}")

                st.markdown("### 🛠️ Engineering Recommended Repairs")
                for repair in c_results.get("recommended_repairs", []):
                    st.markdown(f"- {repair}")

                # downloadable JSON
                st.divider()
                st.download_button(
                    label="📥 Download Diagnostic JSON Report",
                    data=json.dumps(c_results, indent=2),
                    file_name="structural_crack_report.json",
                    mime="application/json",
                    use_container_width=True
                )

# ==============================================================================
# TAB 3: PROJECT PLANNING & REAL ESTATE VALUATION (EPIC 3)
# ==============================================================================
with tab3:
    st.header("Project Financials & Real Estate Valuation (INR)")
    st.caption("Budget estimations, material quantities, and dynamic market valuation across Tier 1, 2, and 3 Indian cities.")

    p_col1, p_col2 = st.columns([1, 1])

    with p_col1:
        st.subheader("Project Inputs")
        struct_type = st.selectbox(
            "Structure Type",
            ["Residential Multi-Story", "Commercial Complex", "Industrial Warehouse", "Villa / Gated Community"]
        )
        built_up_sqft = st.number_input("Built-up Area (Sq. Ft.)", min_value=500, max_value=1000000, value=5000, step=500)
        location_tier = st.selectbox("Location Tier (Indian Market)", ["Tier 1 (Mumbai, Delhi, Blr)", "Tier 2 (Pune, Hyd, Ahmedabad)", "Tier 3 (Tier-3 Cities & Towns)"])
        completion_pct = st.slider("Construction Completion Stage (%)", min_value=0, max_value=100, value=45)

        # Baseline Financial Calculations
        cost_per_sqft = 2200 if "Residential" in struct_type else (2800 if "Commercial" in struct_type else 1800)
        if "Tier 1" in location_tier:
            val_multiplier = 2.5
        elif "Tier 2" in location_tier:
            val_multiplier = 1.8
        else:
            val_multiplier = 1.2

        total_budget_inr = built_up_sqft * cost_per_sqft
        capex_incurred = total_budget_inr * (completion_pct / 100.0)
        estimated_market_val = total_budget_inr * val_multiplier * (0.4 + (0.6 * completion_pct / 100.0))

        # Material Estimation (IS Code standard thumb rules)
        cement_bags = int(built_up_sqft * 0.4)  # ~0.4 bags per sqft
        steel_tons = round(built_up_sqft * 0.003, 1)  # ~3 kg per sqft

    with p_col2:
        st.subheader("Financial & Resource Summary")
        
        def format_inr(number):
            if number >= 10000079:
                return f"₹ {number / 10000000:.2f} Crores"
            elif number >= 100000:
                return f"₹ {number / 100000:.2f} Lakhs"
            else:
                return f"₹ {number:,.2f}"

        f1, f2 = st.columns(2)
        with f1:
            st.metric("Total Project Budget", format_inr(total_budget_inr))
            st.metric("Capex Incurred to Date", format_inr(capex_incurred))
        with f2:
            st.metric("Estimated Market Valuation", format_inr(estimated_market_val))
            st.metric("Est. Steel Requirement", f"{steel_tons} Metric Tons")

        st.metric("Est. Cement Requirement", f"{cement_bags:,} Bags (50kg)")

        st.subheader("Milestone Completion")
        st.progress(completion_pct / 100.0)
        st.caption(f"Project is currently {completion_pct}% structurally complete.")

    st.divider()
    st.subheader("🎨 Conceptual 3D Architectural Visualization (Pollinations AI)")
    
    prompt_input = st.text_input(
        "Architectural Rendering Prompt",
        value=f"Modern architectural photorealistic 3d render of a {struct_type}, clear daylight, photorealistic concrete and glass facade, construction architecture portfolio"
    )
    
    if st.button("Generate Architectural Rendering", type="secondary"):
        with st.spinner("Generating conceptual 3D render..."):
            encoded_prompt = urllib.parse.quote(prompt_input)
            image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=512&nologo=true"
            st.image(image_url, caption="AI Generated 3D Architectural Concept", use_container_width=True)

# ==============================================================================
# TAB 4: DAILY SITE ASSISTANT & WEATHER ADVISORY (EPIC 5)
# ==============================================================================
with tab4:
    st.header("Daily Site Weather Advisory & Engineering Chatbot")

    # Weather Protocol Section
    st.subheader(" Weather-Aware Protocol Generator")
    weather_cond = st.selectbox(
        "Select Current On-Site Weather Conditions",
        ["Normal / Clear Sky", "High Wind (> 40 km/h)", "Heavy Rain / Downpour", "Extreme Heat (> 40°C)"]
    )

    if weather_cond == "High Wind (> 40 km/h)":
        st.error("🚨 HIGH WIND SAFETY PROTOCOL ACTIVATED")
        st.markdown("""
        - **Crane & Hoist Operations:** Suspend all tower crane and mobile boom operations immediately.
        - **Scaffolding:** Secure loose formwork, tarps, and elevated scaffolding boards.
        - **Height Work:** Cease high-level facade work and roofing installations.
        """)
    elif weather_cond == "Heavy Rain / Downpour":
        st.warning("⚠️ HEAVY RAIN SAFETY PROTOCOL ACTIVATED")
        st.markdown("""
        - **Excavation & Trenching:** Inspect trench walls for soil instability and risk of cave-ins. Keep dewatering pumps ready.
        - **Electrical Safety:** De-energize exposed outdoor temporary distribution boards.
        - **Concrete Pouring:** Halt structural slab casting unless completely covered by rain shelters.
        """)
    elif weather_cond == "Extreme Heat (> 40°C)":
        st.warning("☀️ EXTREME HEAT SAFETY PROTOCOL ACTIVATED")
        st.markdown("""
        - **Concrete Curing:** Apply wet burlap covers continuously and execute curing protocols early morning / late evening.
        - **Worker Safety:** Mandatory 15-minute hydration rest breaks every 2 hours. Monitor for heat exhaustion.
        - **Admixtures:** Incorporate retarding admixtures in concrete mixes to delay setting time.
        """)
    else:
        st.success("✅ NORMAL OPERATING PROTOCOL")
        st.markdown("""
        - Standard work operations permitted across all site sectors.
        - Execute standard daily tool-box talk before shift commencement.
        """)

    st.divider()

    # Chatbot Section
    st.subheader("💬 Interactive Site Engineering Assistant")

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = [
            {"role": "assistant", "content": "Hello! I am your AI Construction Engineering Assistant. Ask me anything about IS 456 standards, mix designs, concrete curing times, or safety guidelines."}
        ]

    for msg in st.session_state["chat_history"]:
        st.chat_message(msg["role"]).write(msg["content"])

    if user_query := st.chat_input("Ask about site protocols, standards, or structural engineering..."):
        st.session_state["chat_history"].append({"role": "user", "content": user_query})
        st.chat_message("user").write(user_query)

        with st.chat_message("assistant"):
            if demo_mode:
                bot_response = f"**[Demo Mode]** Regarding your query '{user_query}': Under standard civil engineering protocols (IS 456 / OSHA), ensure quality control testing (cube compressive tests at 7 & 28 days) and proper compaction using needle vibrators."
            else:
                try:
                    chat_prompt = f"You are an expert civil and structural engineering consultant on a site. Answer this query concisely using standard engineering guidelines (such as IS 456 or OSHA): {user_query}"
                    res = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=chat_prompt
                    )
                    bot_response = res.text
                except Exception as e:
                    bot_response = f"Error processing query: {str(e)}"

            st.write(bot_response)
            st.session_state["chat_history"].append({"role": "assistant", "content": bot_response})
