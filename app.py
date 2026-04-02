import streamlit as st
import requests
import json
import concurrent.futures

# הגדרות עמוד
st.set_page_config(page_title="AI Multi-Hub", layout="wide")
st.title("🌐 מנוע ה-AI המאוחד שלי")

# רשימת המודלים - וודא שהשמות נכונים לפי OpenRouter
MODELS = {
    "Gemini (Google)": "google/gemini-flash-1.5-free",
    "ChatGPT (OpenAI)": "openai/gpt-4o-mini",
    "Claude (Anthropic)": "anthropic/claude-3-haiku",
    "Perplexity (Search)": "perplexity/sonar-reasoning"
}

def call_ai(name, model_id, prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    # בדיקה אם המפתח קיים ב-Secrets
    if "MY_KEY" not in st.secrets:
        return name, "שגיאה: המפתח MY_KEY לא הוגדר ב-Advanced Settings של Streamlit"
    
    headers = {
        "Authorization": f"Bearer {st.secrets['MY_KEY']}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8501", # דרישה של חלק מהמודלים ב-OpenRouter
    }
    
    data = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=25)
        
        if response.status_code == 200:
            res_json = response.json()
            return name, res_json['choices'][0]['message']['content']
        elif response.status_code == 401:
            return name, "שגיאה 401: המפתח לא תקין או לא בתוקף. בדוק את ה-API Key ב-OpenRouter."
        elif response.status_code == 402:
            return name, "שגיאה 402: חסר קרדיט בחשבון (גם למודלים חינמיים לעיתים נדרש אימות)."
        else:
            return name, f"שגיאה {response.status_code}: {response.text}"
            
    except Exception as e:
        return name, f"שגיאה טכנית: {str(e)}"

# ממשק משתמש
if prompt := st.chat_input("שאל שאלה..."):
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("פונה לכל המודלים..."):
            results = {}
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = {executor.submit(call_ai, n, i, prompt): n for n, i in MODELS.items()}
                for f in concurrent.futures.as_completed(futures):
                    name, text = f.result()
                    results[name] = text

            # שלב הסינתזה (איחוד התשובות)
            st.subheader("📝 תשובה מאוחדת:")
            
            # בדיקה אם לפחות מודל אחד עבד
            valid_results = {k: v for k, v in results.items() if "שגיאה" not in v}
            
            if not valid_results:
                st.error("כל המודלים החזירו שגיאה. בדוק את ה-Logs ב-Streamlit.")
                for n, r in results.items():
                    st.warning(f"**{n}:** {r}")
            else:
                synth_prompt = f"אחד את התשובות הבאות לתשובה אחת בעברית עם ציון מקורות בסוגריים: {json.dumps(valid_results, ensure_ascii=False)}"
                _, final_answer = call_ai("Synthesizer", "google/gemini-flash-1.5-free", synth_prompt)
                st.markdown(final_answer)

            with st.expander("פירוט תשובות גולמיות"):
                for name, content in results.items():
                    st.write(f"**{name}:** {content}")
