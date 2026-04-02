import streamlit as st
import requests
import json
import concurrent.futures

st.set_page_config(page_title="AI Multi-Hub", layout="wide")
st.title("🌐 מנוע ה-AI המאוחד שלי")

# רשימה מעודכנת של מודלים חינמיים לחלוטין (נכון ל-2026)
MODELS = {
    "Google Gemini 1.5": "google/gemini-2.0-flash-exp:free",
    "Meta Llama 3.3": "meta-llama/llama-3.3-70b-instruct:free",
    "Mistral Pixtral": "mistralai/pixtral-12b:free",
    "HuggingFace (Search)": "qwen/qwen-2-72b-instruct:free"
}

def call_ai(name, model_id, prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {st.secrets['MY_KEY']}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8501", 
    }
    data = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=25)
        if response.status_code == 200:
            return name, response.json()['choices'][0]['message']['content']
        else:
            return name, f"שגיאה {response.status_code}: {response.text}"
    except Exception as e:
        return name, f"תקלה: {str(e)}"

if prompt := st.chat_input("שאל שאלה..."):
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("אוסף תשובות..."):
            results = {}
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = {executor.submit(call_ai, n, i, prompt): n for n, i in MODELS.items()}
                for f in concurrent.futures.as_completed(futures):
                    name, text = f.result()
                    results[name] = text

            # סינון תשובות תקינות
            valid_results = {k: v for k, v in results.items() if "שגיאה" not in v and "תקלה" not in v}
            
            if not valid_results:
                st.error("לא התקבלו תשובות תקינות מהמודלים החינמיים.")
                for n, r in results.items():
                    st.warning(f"**{n}:** {r}")
            else:
                st.subheader("📝 תשובה מאוחדת:")
                # Gemini מבצע את האיחוד
                synth_prompt = f"אחד את התשובות הבאות לתשובה אחת טובה בעברית עם מקורות בסוגריים: {json.dumps(valid_results, ensure_ascii=False)}"
                _, final_answer = call_ai("Synthesizer", "google/gemini-2.0-flash-exp:free", synth_prompt)
                st.markdown(final_answer)

            with st.expander("ראה תשובות מקוריות"):
                for name, content in results.items():
                    st.write(f"**{name}:** {content}")
