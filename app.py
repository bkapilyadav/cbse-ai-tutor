import streamlit as st
import openai
import json
import os
import re

# ✅ Load API key
openai.api_key = os.getenv("OPENAI_API_KEY") or st.secrets["OPENAI_API_KEY"]

# ✅ File to save student data
DATA_FILE = "students_data.json"

# ✅ Load or initialize student data
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ✅ Generate list of chapters
def generate_chapters(subject, student_class):
    prompt = f"""
List 5 chapters for CBSE Class {student_class} in {subject} with only title text. 
Format response as a plain numbered list like:
1. Chapter One Title
2. Chapter Two Title
    """
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    lines = response.choices[0].message.content.strip().split("\n")
    chapters = [re.sub(r'^\d+[\).]\s*', '', line).strip() for line in lines if line.strip()]
    return chapters

# ✅ Generate lesson content
def generate_lesson(subject, chapter, student_class):
    prompt = f"""
You are a friendly AI tutor for CBSE Class {student_class}. Explain the chapter "{chapter}" from {subject} in a simple and fun way suitable for students. Use short paragraphs and examples. Keep it under 300 words.
    """
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

# ✅ Generate multiple choice quiz
def generate_quiz(subject, chapter, student_class):
    prompt = f"""
Create 3 multiple choice questions for CBSE Class {student_class} chapter "{chapter}" in {subject}. 
Each should follow this format:
Q: question
Options:
a) option1
b) option2
c) option3
Answer: a
    """
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

# ✅ Parse quiz into structure
def parse_quiz(quiz_text):
    pattern = re.compile(
        r"Q:\s*(.*?)\s*Options:\s*a\)\s*(.*?)\s*b\)\s*(.*?)\s*c\)\s*(.*?)\s*Answer:\s*([abc])",
        re.DOTALL
    )
    questions = []
    for match in pattern.finditer(quiz_text):
        questions.append({
            "question": match.group(1).strip(),
            "options": {
                "a": match.group(2).strip(),
                "b": match.group(3).strip(),
                "c": match.group(4).strip(),
            },
            "answer": match.group(5).strip()
        })
    return questions

# ✅ Streamlit app UI starts here
students = load_data()
st.title("📚 CBSE AI Tutor")

with st.form("student_form"):
    name = st.text_input("Student Name")
    student_id = st.text_input("Student ID")
    student_class = st.selectbox("Class", ["6", "7", "8", "9", "10"])
    subject = st.selectbox("Subject", ["Science", "Mathematics", "English", "Social Science"])
    submitted = st.form_submit_button("Start Learning")

if submitted:
    if not name or not student_id:
        st.error("Please enter both name and student ID")
        st.stop()

    if student_id not in students:
        students[student_id] = {
            "name": name,
            "class": student_class,
            "subject": subject,
            "progress": {
                "chapter_index": 0,
                "lesson_done": False,
                "quiz_done": False
            }
        }
        students[student_id]["chapters"] = generate_chapters(subject, student_class)
        save_data(students)

    student = students[student_id]
    chapters = student["chapters"]
    progress = student["progress"]
    chapter_index = progress["chapter_index"]

    if chapter_index >= len(chapters):
        st.success("🎉 You've completed all chapters!")
        st.stop()

    chapter_title = chapters[chapter_index]
    st.subheader(f"📖 Chapter {chapter_index+1}: {chapter_title}")

    # ✅ Lesson content
    if not progress["lesson_done"]:
        lesson_content = generate_lesson(subject, chapter_title, student_class)
        st.markdown(lesson_content)
        if st.button("✅ Mark Lesson Completed"):
            progress["lesson_done"] = True
            save_data(students)
            st.experimental_rerun()

    # ✅ Quiz
    elif not progress["quiz_done"]:
        st.markdown("### 🧠 Quiz Time!")
        if "quiz" not in student:
            quiz_text = generate_quiz(subject, chapter_title, student_class)
            student["quiz"] = parse_quiz(quiz_text)
            save_data(students)

        quiz = student["quiz"]
        score = 0

        for i, q in enumerate(quiz):
            st.markdown(f"**Q{i+1}: {q['question']}**")
            choice = st.radio(
                label="Your Answer:",
                options=["a", "b", "c"],
                format_func=lambda x: f"{x}) {q['options'][x]}",
                key=f"quiz_{i}"
            )
            if choice == q["answer"]:
                score += 1

        if st.button("Submit Quiz"):
            st.success(f"✅ You scored {score} out of {len(quiz)}")
            progress["quiz_done"] = True
            student["score"] = score
            save_data(students)
            st.experimental_rerun()

    # ✅ Next chapter
    else:
        if st.button("➡️ Next Chapter"):
            progress["chapter_index"] += 1
            progress["lesson_done"] = False
            progress["quiz_done"] = False
            student.pop("quiz", None)
            save_data(students)
            st.experimental_rerun()
