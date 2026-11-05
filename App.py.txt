import streamlit as st
import google.generativeai as genai
 
# --- PAGE SETUP ---
st.set_page_config(
   page_title="SemperFit - USCG Tactical Readiness Trainer",
   page_icon="⚓",
   layout="wide"
)
 
# --- THEME & HEADER SECTION ---
st.title("⚓ SemperFit: USCG Tactical Readiness Trainer")
st.caption("Semper Paratus Conditioning | Physical Fitness Test (PFT) & Underway Readiness for U.S. Coast Guard Personnel")
 
# --- SIDEBAR: SECURE API KEY INPUT & REFERENCE ---
with st.sidebar:
   st.header("🔑 SemperFit Control Panel")
   api_key = st.text_input("Enter Gemini API Key", type="password", help="Get a free key from Google AI Studio")
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
       frequency = st.select_slider("Weekly Frequency", options=[3, 4, 5, 6], value=4)
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
 
# --- GENERATION LOGIC ---
if st.button("🚀 Generate SemperFit Program", type="primary"):
   if not api_key:
       st.error("Please enter your free Gemini API key in the left sidebar to proceed.")
   else:
       with st.spinner("SemperFit AI Coach is structuring your periodized program..."):
           try:
               genai.configure(api_key=api_key)
               model = genai.GenerativeModel("gemini-1.5-flash")
 
               # SYSTEM PROMPT INSTRUCTIONS
               system_prompt = f"""
               You are SemperFit AI, an elite military tactical strength and conditioning specialist (CSCS/TSAC-F) built specifically for the United States Coast Guard (USCG).
 
               ATHLETE PROFILE:
               - Gender: {gender}
               - Age Bracket: {age_bracket}
               - Operating Environment: {duty_location}
               - Program Scope: {weeks} at {frequency} days/week
               - Available Session Time: {duration}
               - Primary Weakness: {primary_weakness}
               - Available Equipment: {', '.join(equipment)}
 
               OPERATIONAL TRAINING PRINCIPLES:
               1. If duty location is Underway / Cutter Space: Strictly avoid high-box jumps, overhead snatches, or heavy barbell lifts subject to ship roll hazards. Emphasize floor-based stability, kettlebell loading, band work, EMOM sets, and isometric core endurance.
               2. If Program Scope is Multi-Week: Outline a clear periodization structure:
                  - Accumulation Phase (Volume & Movement Economy)
                  - Intensification Phase (Work Capacity & Target PFT Pacing)
                  - Peaking & Taper Phase (Max Output & Testing Protocol)
               3. Structure daily sessions with:
                  - Dynamic Prep & Mobility (5 mins)
                  - Primary Strength / Density Block
                  - PFT Conditioning / Tactical Capacity Block
                  - Down-regulation & Decompression
 
               Format the output strictly in professional, clean markdown with clear headers, tables, and bullet points.
               """
 
               response = model.generate_content(system_prompt)
 
               st.success("✅ SemperFit Plan Ready!")
               st.markdown("---")
 
               # DISPLAY THE PLAN
               st.markdown(response.text)
 
               # EXPORT / PRINT ADVICE
               st.info("💡 **Semper Paratus Tip:** Use your browser's Print feature (Ctrl+P / Cmd+P) to save this schedule as an offline PDF or physical sheet before deploying underway.")
 
           except Exception as e:
               st.error(f"Error communicating with Gemini API: {e}")
