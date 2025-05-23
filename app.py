import streamlit as st
import openai
import json
import os

# Set your OpenAI API Key from Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

DATA_FILE = "students.json"

def load_data():
    if os.path.exists(DATA_FILE) and os.path.getsize(DATA_FILE) > 0:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def generate_chapters(subject, student_class):
    prompt = f"List 5 important chapters from Class {student_class} CBSE {subject} syllabus."
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    chapters = response['choices'][0]['message']['content'].split("\n")
    return [chap.strip("1234567890. ") for chap in chapters if chap.strip()]

def generate_lesson(subject, chapter, student_class):
    prompt = f"Explain the chapter '{chapter}' from Class {student_class} CBSE {subject} in a simple and engaging way for a 12-year-old."
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response['choices'][0]['message']['content']

def generate_quiz(subject, chapter, student_class):
    prompt = f"Create 3 simple quiz questions with answers based on Class {student_class} CBSE {subject} chapter '{chapter}'. Format: Q, then A."
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response['choices'][0]['message']['content']

st.title("📚 CBSE AI Teaching Assistant")
st.markdown("Welcome! I’m your AI Tutor. Let’s start your learning journey! 🎓")

students = load_data()

# Initialize student variable here to avoid NameError
student = None

with st.form("student_info"):
    student_name = st.text_input("👦 Name")
    student_id = st.text_input("🆔 Student ID")
    student_class = st.selectbox("🏫 Class", ["6"])
    subject = st.selectbox("📘 Subject", ["Science", "Mathematics", "English"])
    submitted = st.form_submit_button("Start Learning")

if submitted and student_id:
    # Load or create student progress
    student = students.get(student_id, {
        "name": student_name,
        "class": student_class,
        "subject": subject,
        "progress": {}
    })
    
    st.success(f"Welcome, {student_name} 👋")

    if subject not in student["progress"]:
        chapters = generate_chapters(subject, student_class)
        student["progress"][subject] = {
            "chapters": chapters,
            "completed": [],
            "current": chapters[0] if chapters else ""
        }
        students[student_id] = student
        save_data(students)

    current_chapter = student["progress"][subject]["current"]

    if current_chapter:
        st.subheader(f"📖 Chapter: {current_chapter}")

        lesson = generate_lesson(subject, current_chapter, student_class)
        st.markdown(lesson)

        st.markdown("### 🧠 Quiz Time!")
        quiz = generate_quiz(subject, current_chapter, student_class)
        st.markdown(quiz)

        if st.button("Next Chapter ➡️"):
            chapters = student["progress"][subject]["chapters"]
            current_index = chapters.index(current_chapter)
            if current_index + 1 < len(chapters):
                student["progress"][subject]["current"] = chapters[current_index + 1]
                students[student_id] = student
                save_data(students)
                st.experimental_rerun()
            else:
                st.success("🎉 You've completed all chapters in this subject!")
                student["progress"][subject]["current"] = ""
                students[student_id] = student
                save_data(students)

# Save data if student was loaded or created
if student is not None and student_id:
    students[student_id] = student
    save_data(students)
