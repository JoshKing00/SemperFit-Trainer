import streamlit as st
import google.generativeai as genai
import requests
import json
import time
import re

# --- PAGE SETUP ---
st.set_page_config(
    page_title="SemperFit - USCG Tactical Readiness Trainer",
    page_icon="⚓",
    layout="wide"
)

# --- INITIALIZE SESSION STATE ---
if "plan_text" not in st.session_state:
    st.session_state["plan_text"] = ""
if "used_engine" not in st.session_state:
    st.session_state["used_engine"] = ""

# --- THEME & HEADER SECTION ---
st.title("⚓ SemperFit: USCG Tactical Readiness Trainer")
st.caption("Semper Paratus Conditioning | Physical Fitness Test (PFT) & Underway Readiness for U.S. Coast Guard Personnel")

# --- SIDEBAR: SECURE AUTHENTICATION ---
with st.sidebar:
    st.header("🔑 Authentication & Engine")

    # Check for secrets first, else prompt user
    default_key = st.secrets.get("GEMINI_API_KEY", "")
    api_key = st.text_input("Enter API Key", value=default_key, type="password", help="Enter Google AI Studio key (AIza...) or DoD GenAI key (STARK...)")

    dod_endpoint = ""
    is_stark_key = api_key.strip().startswith("STARK")

    if is_stark_key:
        st.success("🎖️ Detected: DoD GenAI / STARK Enterprise Token")
        dod_endpoint = st.text_input(
            "DoD Gateway Base URL",
            value=st.secrets.get("DOD_GATEWAY_URL", "https://api.genai.mil/v1"),
            help="The endpoint base URL provided in your GenAI.mil developer documentation."
        )
    else:
        st.info("🌐 Using Public Google Generative AI Engine")

    st.markdown("---")
    st.markdown("### 📋 Quick Reference: USCG PFT")
    st.write("• **1-Min Push-ups:** Chest to deck, full lockout")
    st.write("• **Forearm Plank:** Flat spine, timed hold")
    st.write("• **Cardio Modalities:** 1.5-mi Run, 2,000m Row, or 500m Swim")
    st.markdown("---")
    st.info("SemperFit runs 100% free with no monthly subscription on Streamlit Community Cloud.")

# --- FORM SETUP ---
st.subheader("🛠️ Build Your SemperFit Training Program")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("#### 1. Scope & Timeline")
    program_mode = st.radio("Program Type", ["Multi-Week Training Plan", "Single Workout"])
    if program_mode == "Multi-Week Training Plan":
        weeks = st.selectbox("Program Duration", ["4 Weeks (Express Prep)", "8 Weeks (Standard Macrocycle)", "12 Weeks (Full Overhaul)"])
        frequency = st.select_slider("Weekly Frequency (Days/Week)", options=[2, 3, 4, 5, 6], value=4)
    else:
        weeks = "Single Day"
        frequency = 1

    duration = st.selectbox("Max Time per Session", ["15 minutes (Express)", "30 minutes", "45 minutes", "60 minutes"])

with col2:
    st.markdown("#### 2. Member Profile")
    gender = st.selectbox("Gender (for PFT Tables)", ["Male", "Female"])
    age_bracket = st.selectbox("Age Bracket", ["17-29", "30-39", "40-49", "50+"])
    duty_location = st.radio("Operating Environment", ["Ashore / Station Gym", "Underway / Cutter Space"])
    if duty_location == "Underway / Cutter Space":
        st.warning("⚠️ Cutter mode active: Restricted to stable groundings, kettlebells/dumbbells, bodyweight density, and zero ballistic box jumps.")

with col3:
    st.markdown("#### 3. Priorities & Gear")
    primary_weakness = st.selectbox("Primary Focus Area", [
        "Push-up Volume & Density",
        "Plank Core Endurance",
        "1.5-Mile Run Aerobic Capacity",
        "2,000m Row Pacing & Power",
        "Comprehensive Tactical Readiness"
    ])
    equipment = st.multiselect(
        "Available Equipment",
        ["Bodyweight Only", "Dumbbells", "Kettlebells", "Pull-up Bar", "RowErg / C2 Row", "Treadmill", "Full Weight Room"],
        default=["Bodyweight Only"]
    )

# --- AI ROUTING ENGINES ---

def call_google_commercial(api_key, prompt, output_placeholder):
    """Handles standard Google AI Studio keys (AIza...)."""
    genai.configure(api_key=api_key)
    candidate_models = ["gemini-3.8-flash", "gemini-2.0-flash", "gemini-1.5-flash-latest"]

    last_error = None
    for model_name in candidate_models:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt, stream=True)
            full_text = ""
            for chunk in response:
                if chunk and chunk.text:
                    full_text += chunk.text
                    output_placeholder.markdown(full_text + " ▌")
            output_placeholder.markdown(full_text)
            return full_text, f"Google Cloud ({model_name})"
        except Exception as err:
            err_str = str(err)
            last_error = err
            if "429" in err_str or "Quota exceeded" in err_str:
                match = re.search(r'retry in ([\d\.]+)s', err_str)
                delay = match.group(1) if match else "45"
                raise Exception(
                    f"RATE_LIMIT: Public Free Tier request limit reached. Please wait {delay}s before retrying."
                )
            continue
    raise Exception(f"All Google models failed. Last error: {last_error}")

def call_stark_dod_gateway(api_key, base_url, prompt, output_placeholder):
    """Handles DoD GenAI STARK Enterprise Gateway REST calls."""
    clean_url = base_url.rstrip("/")
    target_url = f"{clean_url}/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "gemini-1.5-pro",
        "messages": [
            {"role": "system", "content": "You are SemperFit AI, an elite military tactical strength specialist."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.4
    }

    try:
        response = requests.post(target_url, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            result = response.json()
            full_text = result["choices"][0]["message"]["content"]
            output_placeholder.markdown(full_text)
            return full_text, "DoD STARK GenAI Gateway"
        else:
            raise Exception(f"DoD Gateway Error (HTTP {response.status_code}): {response.text}")
    except requests.exceptions.ConnectionError:
        raise Exception(
            "CONNECTION_ERROR: Could not reach the DoD STARK endpoint from public Streamlit Cloud. "
            "If your STARK endpoint is restricted to NIPRNet/GovCloud, the app must run within the DoD network enclave."
        )

# --- GENERATION TRIGGER ---
if st.button("🚀 Generate SemperFit Program", type="primary"):
    if not api_key:
        st.error("Please enter your API key in the left sidebar to proceed.")
    else:
        system_prompt = f"""
        You are SemperFit AI, an elite military tactical strength and conditioning specialist (CSCS/TSAC-F) for the United States Coast Guard (USCG).

        ATHLETE PROFILE:
        - Gender: {gender} | Age: {age_bracket} | Location: {duty_location}
        - Scope: {weeks} at {frequency} days/week | Time per session: {duration}
        - Focus Weakness: {primary_weakness}
        - Available Equipment: {', '.join(equipment)}

        CONCISE OUTPUT DIRECTIVES:
        1. Deliver an actionable, periodized program without conversational filler.
        2. If Underway / Cutter Space: Restrict movements strictly to stable groundings, kettlebells/dumbbells, bodyweight density, and zero ballistic box jumps.
        3. Structure the response into 3 concise sections:
           - SECTION 1: Periodization Roadmap (Table showing Phase Name, Weekly Volume, RPE, and Milestone Targets).
           - SECTION 2: Weekly Microcycle Blueprint (Provide the detailed breakdown for each of the {frequency} weekly training days: Warmup, Main Strength/Density Block, PFT Conditioning Finisher, and Cooldown).
           - SECTION 3: Progressive Overload & USCG Testing Protocol (Clear progression rules week-to-week and final PFT test week preparation).
        """

        output_box = st.empty()
        with st.spinner("⚡ SemperFit AI is assembling your tactical program..."):
            try:
                if is_stark_key:
                    completed_plan, used_engine = call_stark_dod_gateway(
                        api_key, dod_endpoint, system_prompt, output_box
                    )
                else:
                    completed_plan, used_engine = call_google_commercial(
                        api_key, system_prompt, output_box
                    )

                st.session_state["plan_text"] = completed_plan
                st.session_state["used_engine"] = used_engine
                st.success(f"✅ SemperFit Plan Ready! (Engine: {used_engine})")
            except Exception as e:
                err_msg = str(e)
                if "RATE_LIMIT:" in err_msg:
                    st.warning(f"⏳ **Rate Limit Notice:** {err_msg.replace('RATE_LIMIT:', '')}")
                elif "CONNECTION_ERROR:" in err_msg:
                    st.error(f"🔒 **Network Boundary Notice:** {err_msg.replace('CONNECTION_ERROR:', '')}")
                else:
                    st.error(f"Error communicating with AI engine: {e}")

# --- PERSISTENT PLAN DISPLAY ---
if st.session_state["plan_text"]:
    st.markdown("---")
    st.markdown(st.session_state["plan_text"])
    st.info("💡 **Semper Paratus Tip:** Use your browser's Print feature (Ctrl+P / Cmd+P) to save this schedule as an offline PDF or physical sheet before deploying underway.")
