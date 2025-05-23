import streamlit as st
import json
import os
from PIL import Image
import openai

# Load OpenAI API Key from Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Safe data load function
def load_data():
    if not os.path.exists("students.json"):
        return {}
    try:
        with open("students.json", "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_data(data):
    with open("students.json", "w") as f:
        json.dump(data, f, indent=4)

# Teaching content and visuals (Mock examples)
content_library = {
    "6": {
        "Science": {
            "chapter_1": {
                "title": "Our Body",
                "content": "Our body is made of different systems like digestive system, respiratory system, etc.",
                "image": "images/body.png",
                "quiz": {
                    "question": "What system helps us breathe?",
                    "options": ["Digestive", "Respiratory", "Nervous"],
                    "answer": "Respiratory"
                }
            }
        }
    }
}

# UI Header
st.markdown("<h1 style='text-align: center; color: #4FC3F7;'>🤖 CBSE AI Tutor</h1>", unsafe_allow_html=True)

# Load student data
students = load_data()

# Step 1: Collect student details
with st.form("student_form"):
    name = st.text_input("👦 Student Name")
    student_id = st.text_input("🆔 Student ID")
    student_class = st.selectbox("🏫 Class", ["6", "7", "8", "9", "10"])
    subject = st.selectbox("📚 Subject", ["Science", "Mathematics", "English"])
    submitted = st.form_submit_button("🚀 Start Learning")

if submitted:
    st.success(f"Welcome, {name} 👋")
    
    # Check if student already exists
    if student_id not in students:
        students[student_id] = {
            "name": name,
            "class": student_class,
            "subject": subject,
            "progress": {"chapter": "chapter_1"}
        }
        save_data(students)
    
    student_data = students[student_id]
    chapter_key = student_data["progress"]["chapter"]
    
    chapter = content_library[student_class][subject][chapter_key]
    
    st.header(f"📖 Chapter: {chapter['title']}")
    st.write(chapter["content"])

    # Show image if exists
    if os.path.exists(chapter["image"]):
        st.image(Image.open(chapter["image"]), use_column_width=True)

    # Quiz time
    st.subheader("🧠 Quiz Time")
    quiz = chapter["quiz"]
    user_answer = st.radio(quiz["question"], quiz["options"])
    if st.button("Submit Answer"):
        if user_answer == quiz["answer"]:
            st.success("✅ Correct! Well done!")
        else:
            st.error(f"❌ Oops! The correct answer is: {quiz['answer']}")

    # Update progress
    students[student_id]["progress"]["chapter"] = chapter_key  # Can later be next_chapter
    save_data(students)

