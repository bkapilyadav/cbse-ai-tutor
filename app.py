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
Format like:
1. Food: Where Does It Come From
2. Components of Food
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
Explain the CBSE Class {student_class} chapter "{chapter}" in {subject} for a 10-12 year old student in simple and fun language with examples. Use short paragraphs. Max 300 words.
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
Format:
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

# ✅ Parse quiz text to structure
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

# ✅ Streamlit App Starts
students = load_data()
st.title("🧠 CBSE AI Teaching Agent")

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
                "quiz_done": False,
                "chapter_completed": False
            }
        }
        students[student_id]["chapters"] = generate_chapters(subject, student_class)
        save_data(students)

    student = students[student_id]
    chapters = student["chapters"]
    progress = student["progress"]
    chapter_index = progress["chapter_index"]

    if chapter_index >= len(chapters):
        st.success("🎉 Congratulations! You’ve completed all chapters.")
        st.stop()

    current_chapter = chapters[chapter_index]
    st.subheader(f"📖 Chapter {chapter_index + 1}: {current_chapter}")

    # ✅ Lesson
    if not progress["lesson_done"]:
        lesson_text = generate_lesson(subject, current_chapter, student_class)
        st.markdown(lesson_text)
        if st.button("✅ Mark Lesson Completed"):
            progress["lesson_done"] = True
            save_data(students)
            st.experimental_rerun()

    # ✅ Quiz
    elif not progress["quiz_done"]:
        st.markdown("### 🧪 Quiz Time!")
        if "quiz" not in student:
            quiz_text = generate_quiz(subject, current_chapter, student_class)
            student["quiz"] = parse_quiz(quiz_text)
            save_data(students)

        score = 0
        for i, q in enumerate(student["quiz"]):
            st.markdown(f"**Q{i+1}: {q['question']}**")
            choice = st.radio(
                label="Choose your answer:",
                options=["a", "b", "c"],
                format_func=lambda x: f"{x}) {q['options'][x]}",
                key=f"quiz_{i}"
            )
            if choice == q["answer"]:
                score += 1

        if st.button("✅ Submit Quiz"):
            st.success(f"You scored {score} / {len(student['quiz'])}")
            progress["quiz_done"] = True
            student["score"] = score
            save_data(students)
            st.experimental_rerun()

    # ✅ Chapter Completion
    elif not progress["chapter_completed"]:
        if st.button("✅ Chapter Completed"):
            progress["chapter_completed"] = True
            save_data(students)
            st.experimental_rerun()

    # ✅ Move to next chapter
    else:
        if st.button("➡️ Go to Next Chapter"):
            progress["chapter_index"] += 1
            progress["lesson_done"] = False
            progress["quiz_done"] = False
            progress["chapter_completed"] = False
            student.pop("quiz", None)
            save_data(students)
            st.experimental_rerun()
