# app.py
import streamlit as st
from langdetect import detect
from deep_translator import GoogleTranslator
from openai import OpenAI

st.set_page_config(page_title="Clear Email Helper – Ireland", layout="wide")
st.title("📧 Email Helper – Ireland")
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
st.subheader("1) Input your email in English or your Native Language")

native_input = st.text_area(
    "Write in your NATIVE language (auto-detect language and translate)", height=150, key="native_input"
)

thread_text = st.text_area("Paste PREVIOUS EMAILS (optional)", height=150, key="thread")

user_notes = st.text_area("Extra notes in ENGLISH (optional)", height=150, key="notes")

# --- Tone selection ---
tone_choice = st.selectbox(
    "Choose the TONE of your email",
    [
        "Professional",
        "Friendly",
        "Formal (official/government)",
        "Urgent",
        "Apologetic",
        "Complaint",
        "Thank you"
    ],
)

# Expanded tone instructions for the AI
tone_prompts = {
    "Professional": "Write in a clear, neutral, and respectful style. Suitable for work, landlords, or services. Use simple but professional language.",
    "Friendly": "Write in a warm, kind, and polite way. Use soft and welcoming words. Good for schools, neighbours, or friendly situations.",
    "Formal (official/government)": "Write in very formal language, as used in letters to government, council, or immigration offices. Avoid contractions (use 'do not' instead of 'don’t'). Be precise and serious.",
    "Urgent": "Write in a polite but strong way. Emphasise that the matter is urgent and needs fast attention. Keep sentences clear and easy to understand.",
    "Apologetic": "Write in a polite way that says sorry and explains the reason. Show understanding, responsibility, and willingness to correct or improve.",
    "Complaint": "Write in a polite but serious way. Explain the problem clearly. Show that you expect action, but avoid aggressive or rude words. Focus on the facts and the solution.",
    "Thank you": "Write in a positive way that shows gratitude and appreciation. Keep the message polite and warm. Can also be used to follow up kindly."
}

details = st.text_input("Details to reference (e.g., address, reference number, dates)", "")

st.markdown("---")

if st.button("✨ Generate Email"):
    if not st.secrets.get("GROQ_API_KEY"):
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
Tone selected by user: {tone_choice}.
Expanded tone guidance: {tone_prompts[tone_choice]}.
Rules:
- Use clear, polite English (CEFR B1–B2).
- Sentences should be clear but not overly short; aim for natural flow.
- Include only facts from THREAD, USER NOTES, or TRANSLATED NATIVE INPUT.
- Structure: Greeting, opening (acknowledge previous message if provided), body (explain issue/request), closing (thank or polite ending), signature.
- Do NOT automatically add a deadline unless the user specifically requested one.
- Expand politely so the email feels complete and professional (2–4 short paragraphs).
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
                model="llama-3.1-8b-instant",  # Faster Groq model "llama-3.1-8b-instant"
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
        st.subheader("2) Copy and send this Email")
        st.markdown(f"> {final_email.replace('\n', '\n> ')}")



        st.subheader("3) Preview in your language (read to confirm meaning)")
        st.write(preview)

        st.download_button("📥 Download email as .txt", final_email, file_name="email.txt")
        st.success("Review the preview carefully before sending or copying.")
