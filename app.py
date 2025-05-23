import streamlit as st
import openai
import os

# Set your OpenAI API key securely
openai.api_key = st.secrets["OPENAI_API_KEY"] if "OPENAI_API_KEY" in st.secrets else os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="CBSE AI Tutor", layout="centered")

# System prompt for explanation
EXPLANATION_PROMPT = """
You are a helpful CBSE school tutor AI. Your task is to explain this chapter to a Grade 10 student in simple language.
Use examples and clear concepts. Chapter:
"{chapter_content}"
"""

# System prompt for quiz generation
QUIZ_PROMPT = """
You are an AI quiz generator for CBSE Grade 10. Create a 5-question multiple choice quiz from the following chapter.
Each question should have 4 options (A, B, C, D) and mark the correct option. Chapter:
"{chapter_content}"

Format:
Q1. ...
A. ...
B. ...
C. ...
D. ...
Correct Answer: ...
"""

def get_openai_response(prompt: str) -> str:
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}],
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ Error generating response: {e}"

# Sample subject and chapters (mock structure)
SUBJECTS = {
    "Science": {
        "Chapter 1 - Chemical Reactions": "Chemical reactions involve transformation of substances...",
        "Chapter 2 - Acids, Bases and Salts": "Acids are sour and turn blue litmus red...",
        "Chapter 3 - Metals and Non-Metals": "Metals are good conductors of heat and electricity...",
    },
    "Math": {
        "Chapter 1 - Real Numbers": "Real numbers include both rational and irrational numbers...",
        "Chapter 2 - Polynomials": "A polynomial is an algebraic expression with variables...",
    },
    "Social Science": {
        "Chapter 1 - The Rise of Nationalism in Europe": "The French Revolution gave rise to nationalism...",
        "Chapter 2 - Resources and Development": "Resources are materials available in our environment...",
    }
}

def display_explanation_and_quiz(chapter_text: str):
    with st.spinner("Generating explanation..."):
        explanation = get_openai_response(EXPLANATION_PROMPT.format(chapter_content=chapter_text))
        st.subheader("📘 Explanation")
        st.write(explanation)

    with st.spinner("Generating quiz..."):
        quiz = get_openai_response(QUIZ_PROMPT.format(chapter_content=chapter_text))
        st.subheader("📝 Quiz")
        st.markdown(quiz)

def main():
    st.title("CBSE AI Tutor")  # Changed title to avoid UnicodeEncodeError

    st.markdown("Welcome! Select a subject and chapter to get started with interactive learning. 📚")

    subject = st.selectbox("Choose a subject:", list(SUBJECTS.keys()))
    chapters = list(SUBJECTS[subject].keys())
    selected_chapter = st.selectbox("Choose a chapter:", chapters)

    if st.button("Generate Explanation + Quiz"):
        chapter_text = SUBJECTS[subject][selected_chapter]
        display_explanation_and_quiz(chapter_text)

    st.markdown("---")
    st.markdown("Built with ❤️ using Streamlit and OpenAI GPT")

if __name__ == "__main__":
    main()
