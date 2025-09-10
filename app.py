# app.py
import streamlit as st
from langdetect import detect
from deep_translator import GoogleTranslator
from openai import OpenAI

st.set_page_config(page_title="Clear Email Helper – Ireland", layout="wide")
st.title("📧 Clear Email Helper – Ireland")
st.write("Compose professional emails in English.")

# --- OpenAI client (reads your key from Streamlit Secrets) ---
# On Streamlit Cloud you'll add this in Settings → Secrets as OPENAI_API_KEY
client = OpenAI(
    api_key=st.secrets["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1"
)

def translate_text(text, target="en"):
    try:
        return GoogleTranslator(source="auto", target=target).translate(text)
    except Exception:
        return text

# --- Inputs ---
st.subheader("1) Your inputs")

native_input = st.text_area(
    "Write in your native language (we will auto-detect & translate)", height=150, key="native_input"
)

thread_text = st.text_area("Paste the previous email or thread (optional)", height=150, key="thread")

user_notes = st.text_area("Extra notes/keywords in English (optional)", height=100, key="notes")

tone = st.selectbox(
    "Choose tone",
    [
        "Neutral professional", "Polite & warm", "Clear & firm",
        "Very formal", "Concise", "Apologetic & solution-oriented", "Gratitude & follow-up"
    ],
)

details = st.text_input("Details to reference (e.g., address, reference number, dates)", "")

st.markdown("---")

if st.button("✨ Generate Email"):
    if not st.secrets.get("OPENAI_API_KEY"):
        st.error("Missing OPENAI_API_KEY. Add it in your Streamlit app Settings → Secrets.")
        st.stop()

    with st.spinner("Working..."):
        # 1) Detect & translate user’s native-language input to English
        detected_lang = None
        translated_native = ""
        if native_input.strip():
            try:
                detected_lang = detect(native_input)
            except Exception:
                detected_lang = "unknown"

            # If not English, translate to English
            if detected_lang and detected_lang not in ("en", "unknown"):
                translated_native = translate_text(native_input, "en")
            else:
                translated_native = native_input

        # 2) Build prompts for the email draft
        system_prompt = f"""
You write professional emails for recipients in Ireland.
Tone: {tone}.
Rules:
- Clear, polite English (CEFR B1–B2).
- Short sentences.
- Include only facts from THREAD, USER NOTES, or TRANSLATED NATIVE INPUT.
- Structure: Greeting, opening (cite thread if any), body, clear ask with date, courteous closing, signature.
"""

        user_prompt = f"""
THREAD:
{thread_text}

USER NOTES (English):
{user_notes}

TRANSLATED NATIVE INPUT (from user's language into English):
{translated_native}

DETAILS:
{details}
"""

        # 3) Call OpenAI to create the professional English email
        try:
            resp = client.chat.completions.create(
                model="llama-3.1-70b-versatile",  # Faster Groq model "llama-3.1-8b-instant"
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.5,
            )

            final_email = resp.choices[0].message.content.strip()
        except Exception as e:
            st.error(f"OpenAI error: {e}")
            st.stop()

        # 4) Back-translate the final email so user can preview in their own language
        # 4) Back-translate the final email so user can preview in their own language
        if detected_lang and detected_lang not in ("en", "unknown"):
            try:
                preview = translate_text(final_email, detected_lang)
            except Exception:
                preview = "(Could not translate preview. Showing English.)\n\n" + final_email
        else:
            preview = final_email

        # 5) Display results
        st.subheader("2) Professional Email (English – this is what you’ll send)")
        st.code(final_email, language="markdown")

        st.subheader("3) Preview in your language (read to confirm meaning)")
        st.write(preview)

        st.download_button("📥 Download email as .txt", final_email, file_name="email.txt")
        st.success("Review the preview carefully before sending or copying.")
