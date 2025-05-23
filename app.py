import streamlit as st
import json
import os
import uuid
import openai
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Path to student data
DATA_PATH = "students.json"

# Load or initialize student data
def load_data():
    if not os.path.exists(DATA_PATH):
        with open(DATA_PATH, "w") as f:
            json.dump({}, f)
    with open(DATA_PATH, "r") as f:
        return json.load(f)

# Save student data
def save_data(data):
    with open(DATA_PATH, "w") as f:
        json.dump(data, f, indent=4)

# Generate chapters using OpenAI
def generate_chapters(subject, grade):
    prompt = (
        f"Generate a list of chapters for Class {grade} {subject} based on CBSE syllabus. "
        "Return JSON with 'Chapter' and 'Title'."
    )
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return json.loads(response["choices"][0]["message"]["content"].strip())

# Generate lesson content
def generate_lesson(subject, chapter):
    prompt = (
        f"You're a friendly CBSE tutor. Write a student-friendly explanation for Class 6 {subject} - Chapter: {chapter['Title']}. "
        f"Make it engaging for 10-12 year olds."
    )
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response["choices"][0]["message"]["content"].strip()

# Generate quiz questions
def generate_quiz(subject, chapter):
    prompt = (
        f"Create 3 multiple choice quiz questions (with 3 options each and correct answer) for CBSE Class 6 {subject}, Chapter: {chapter['Title']}."
    )
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response["choices"][0]["message"]["content"].strip()

# Main app logic
st.set_page_config(page_title="CBSE AI Tutor", page_icon="📖")
st.title("📖 CBSE Interactive AI Tutor")

students = load_data()

if "student_id" not in st.session_state:
    with st.form("student_form"):
        name = st.text_input("Enter your name")
        student_class = st.selectbox("Select your class", ["6", "7", "8"])
        subject = st.selectbox("Choose a subject", ["Science", "Maths", "English"])
        submitted = st.form_submit_button("Start Learning")

        if submitted:
            student_id = str(uuid.uuid4())
            st.session_state.student_id = student_id
            st.session_state.subject = subject
            st.session_state.student_class = student_class
            students[student_id] = {
                "id": student_id,
                "name": name,
                "class": student_class,
                "subject": subject,
                "progress": 0
            }
            save_data(students)
            st.rerun()
else:
    student_id = st.session_state.student_id
    student = students[student_id]
    student_class = st.session_state.student_class
    subject = st.session_state.subject

    st.success(f"Welcome, {student['name']} 👋")

    if "chapters" not in st.session_state:
        st.session_state.chapters = generate_chapters(subject, student_class)

    chapters = st.session_state.chapters
    current_index = student["progress"]

    if current_index >= len(chapters):
        st.balloons()
        st.success("You've completed all chapters! Great job!")
    else:
        chapter = chapters[current_index]
        st.header(f"📖 Chapter {chapter['Chapter']}: {chapter['Title']}")

        if "lesson" not in st.session_state:
            st.session_state.lesson = generate_lesson(subject, chapter)

        st.write(st.session_state.lesson)

        st.subheader("🎮 Quiz Time!")
        if "quiz" not in st.session_state:
            st.session_state.quiz = generate_quiz(subject, chapter)

        st.write(st.session_state.quiz)

        if st.button("✅ Mark Chapter as Completed"):
            student["progress"] += 1
            students[student_id] = student
            save_data(students)
            for key in ["lesson", "quiz"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
