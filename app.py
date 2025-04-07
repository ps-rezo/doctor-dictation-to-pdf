import streamlit as st
import openai
from fpdf import FPDF
import os
import tempfile

# Set your OpenAI API Key
openai.api_key = st.secrets.get("OPENAI_API_KEY") or "your-openai-api-key"

st.set_page_config(page_title="Doctor Dictation to PDF", layout="centered")
st.title("🩺 Doctor Dictation to PDF Report")

# --- Upload Audio File ---
st.header("1. Upload Doctor Voice Note")
audio_file = st.file_uploader("Upload an audio file (MP3/WAV)", type=["mp3", "wav"])

transcript_text = ""

if audio_file:
    st.audio(audio_file, format="audio/wav")
    st.info("Processing transcription...")

    # Save the audio file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(audio_file.read())
        temp_audio_path = tmp.name

    # Placeholder transcription using Whisper
    try:
        with open(temp_audio_path, "rb") as file:
            transcript_response = openai.Audio.transcribe("whisper-1", file)
            transcript_text = transcript_response["text"]
    except Exception as e:
        st.error(f"Transcription failed: {e}")
    finally:
        os.remove(temp_audio_path)

# --- Generate SOAP Report using GPT ---
if transcript_text:
    st.header("2. Transcription")
    st.text_area("Doctor's Notes (editable)", value=transcript_text, height=200, key="transcription")

    st.header("3. Generate SOAP Report")
    if st.button("🧠 Structure with GPT"):
        prompt = f"""
        You are a helpful medical assistant. Convert the following doctor note into a SOAP-style clinical report:

        "{transcript_text}"

        Format:
        Subjective:
        Objective:
        Assessment:
        Plan:
        """

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",  # or "gpt-3.5-turbo"
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            report_text = response['choices'][0]['message']['content']
            st.text_area("Structured SOAP Report", value=report_text, height=300, key="report")

            st.session_state['report'] = report_text

        except Exception as e:
            st.error(f"Error generating report: {e}")

# --- Create and Download PDF ---
if 'report' in st.session_state:
    st.header("4. Download Report as PDF")

    def generate_pdf(soap_text):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        for line in soap_text.split("\n"):
            if line.strip() == "":
                continue
            if ":" in line:
                section, content = line.split(":", 1)
                pdf.set_font("Arial", 'B', size=12)
                pdf.cell(200, 10, txt=section + ":", ln=True)
                pdf.set_font("Arial", size=12)
                pdf.multi_cell(0, 10, txt=content.strip())
                pdf.ln(2)
            else:
                pdf.multi_cell(0, 10, txt=line)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            pdf.output(tmp_pdf.name)
            return tmp_pdf.name

    if st.button("📄 Generate PDF"):
        pdf_path = generate_pdf(st.session_state['report'])
        with open(pdf_path, "rb") as f:
            st.download_button("⬇️ Download Clinical Report", f, file_name="doctor_report.pdf", mime="application/pdf")
