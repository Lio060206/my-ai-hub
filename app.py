import streamlit as st
import requests
import json
import concurrent.futures

# הגדרות עיצוב הממשק
st.set_page_config(page_title="AI Multi-Hub", layout="wide")
st.markdown("<h1 style='text-align: center;'>🌐 מנוע ה-AI המאוחד שלי</h1>", unsafe_allow_html=True)
st.write("---")

# רשימת המודלים לחיבור (כולל המנועים של Copilot ו-Perplexity)
MODELS = {
    "Gemini (Google)": "google/gemini-flash-1.5-free",
    "ChatGPT (OpenAI/Copilot)": "openai/gpt-4o-mini",
    "Claude (Anthropic)": "anthropic/claude-3-haiku",
    "Perplexity (Online Search)": "perplexity/sonar-reasoning"
}

# פונקציה לשליחת בקשה ל-OpenRouter
def call_ai(name, model_id, prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    # המפתח יימשך מה-Secrets של Streamlit Cloud
    headers = {
        "Authorization": f"Bearer {st.secrets['MY_KEY']}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=25)
        res_json = response.json()
        return name, res_json['choices'][0]['message']['content']
    except Exception as e:
        return name, f"שגיאה בחיבור למודל {name}"

# תצוגת המודלים הפעילים בתפריט צד
with st.sidebar:
    st.header("הבינות המחוברות")
    for m in MODELS.keys():
        st.write(f"✅ {m}")
    st.divider()
    if st.button("נקה היסטוריית צ'אט"):
        st.session_state.messages = []
        st.rerun()

# אתחול זיכרון שיחה
if "messages" not in st.session_state:
    st.session_state.messages = []

# תיבת קלט למשתמש
if prompt := st.chat_input("שאל שאלה לניתוח רב-מודלי..."):
    # הוספת שאלת המשתמש לתצוגה
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("מנתח נתונים מכל המקורות במקביל..."):
            # הרצה מקבילית של כל המודלים (Parallel Processing)
            results = {}
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = {executor.submit(call_ai, n, i, prompt): n for n, i in MODELS.items()}
                for future in concurrent.futures.as_completed(futures):
                    name, text = future.result()
                    results[name] = text

            # שלב הסינתזה - מבקשים מ-Gemini לאחד את הכל לתשובה אחת עם מקורות
            synthesis_prompt = f"""
            קיבלת תשובות מכמה מודלים לשאלה הבאה: "{prompt}"
            
            אלו התשובות הגולמיות:
            {json.dumps(results, ensure_ascii=False)}
            
            המשימה שלך:
            1. כתוב תשובה אחת מאוחדת, מקצועית וקולחת בעברית.
            2. בסוף כל פסקה או טענה מרכזית, ציין בסוגריים מאיזה מודל המידע הגיע.
               לדוגמה: (מקור: Perplexity) או (מקור: ChatGPT).
            3. אם יש סתירות בין המודלים, ציין זאת במפורש.
            """
            
            _, final_answer = call_ai("Synthesizer", "google/gemini-flash-1.5-free", synthesis_prompt)
            st.markdown(final_answer)

            # הצגת המקורות הגולמיים בתוך "אקורדיון" מתקפל
            with st.expander("ראה את התשובות המקוריות מכל בינה"):
                for name, content in results.items():
                    st.write(f"**{name}:**")
                    st.write(content)
                    st.divider()