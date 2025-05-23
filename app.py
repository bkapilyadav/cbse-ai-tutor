import streamlit as st
import openai
import json
import os
import re

# Set your OpenAI API key securely as environment variable or Streamlit secrets
openai.api_key = os.getenv("OPENAI_API_KEY") or st.secrets["OPENAI_API_KEY"]

DATA_FILE = "students_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def generate_lessons(subject, student_class):
    prompt = f"""
You are an expert CBSE tutor teaching Class {student_class} students in {subject}.
List 3 important chapters with brief titles.
Format as JSON array of chapter titles.
"""
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    chapters_text = response.choices[0].message.content
    try:
        chapters = json.loads(chapters_text)
    except:
        # fallback parsing if not valid json
        chapters = re.findall(r'"(.*?)"', chapters_text)
    return chapters

def generate_lesson_content(subject, chapter, student_class):
    prompt = f"""
You are an expert CBSE tutor teaching Class {student_class} students in {subject}.
Explain the chapter '{chapter}' in an easy, interactive way with examples suitable for kids.
Limit to about 300 words.
"""
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def generate_quiz(subject, chapter, student_class):
    prompt = f"""
Create 3 multiple choice quiz questions for Class {student_class} CBSE {subject} chapter '{chapter}'.
Format each question as:
Q: question text
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
    return response.choices[0].message.content

def parse_quiz(quiz_text):
    # regex to parse quiz formatted as specified
    pattern = re.compile(
        r"Q:\s*(.+?)\s*Options:\s*a\)\s*(.+?)\s*b\)\s*(.+?)\s*c\)\s*(.+?)\s*Answer:\s*([abc])",
        re.DOTALL
    )
    questions = []
    for match in pattern.finditer(quiz_text):
        question = match.group(1).strip()
        options = {
            "a": match.group(2).strip(),
            "b": match.group(3).strip(),
            "c": match.group(4).strip(),
        }
        answer = match.group(5).strip()
        questions.append({
            "question": question,
            "options": options,
            "answer": answer
        })
    return questions

# Load student progress data
students = load_data()

st.title("🧑‍🏫 CBSE AI Tutor - Interactive Learning")

# Student info input
with st.form("student_form"):
    name = st.text_input("Enter your Name")
    student_id = st.text_input("Enter your Student ID")
    student_class = st.selectbox("Select Class", options=["6", "7", "8", "9", "10"])
    subject = st.selectbox("Select Subject", options=["Science", "Mathematics", "English"])
    submitted = st.form_submit_button("Start Learning")

if submitted:
    if not (name and student_id):
        st.error("Please enter both Name and Student ID.")
        st.stop()

    # Load or initialize student data
    if student_id not in students:
        students[student_id] = {
            "name": name,
            "class": student_class,
            "subject": subject,
            "progress": {
                "chapter_index": 0,
                "lesson_done": False,
                "quiz_done": False,
                "quiz_score": 0
            }
        }
    else:
        # Update subject/class if changed
        students[student_id]["class"] = student_class
        students[student_id]["subject"] = subject
        students[student_id]["name"] = name

    student = students[student_id]
    st.success(f"Welcome, {student['name']} 👋")
    
    # Generate chapters for selected subject/class
    if "chapters" not in student:
        chapters = generate_lessons(subject, student_class)
        student["chapters"] = chapters
        save_data(students)
    else:
        chapters = student["chapters"]

    chapter_index = student["progress"]["chapter_index"]
    if chapter_index >= len(chapters):
        st.success("🎉 You have completed all chapters available for this subject!")
        st.stop()

    current_chapter = chapters[chapter_index]
    st.header(f"📘 Chapter {chapter_index + 1}: {current_chapter}")

    # Show lesson content if not done
    if not student["progress"]["lesson_done"]:
        lesson_content = generate_lesson_content(subject, current_chapter, student_class)
        st.markdown(lesson_content)
        if st.button("Mark Lesson as Completed"):
            student["progress"]["lesson_done"] = True
            save_data(students)
            st.experimental_rerun()

    # Quiz section
    elif not student["progress"]["quiz_done"]:
        st.markdown("### 🧠 Quiz Time!")
        if "quiz_content" not in student:
            quiz_text = generate_quiz(subject, current_chapter, student_class)
            student["quiz_content"] = quiz_text
            save_data(students)
        else:
            quiz_text = student["quiz_content"]

        questions = parse_quiz(quiz_text)

        all_correct = True
        score = 0
        for i, q in enumerate(questions):
            st.markdown(f"**Q{i+1}: {q['question']}**")
            user_answer = st.radio(
                label=f"Select answer for Q{i+1}",
                options=["a", "b", "c"],
                format_func=lambda x: f"{x}) {q['options'][x]}",
                key=f"quiz_{i}"
            )
            if user_answer:
                if user_answer == q['answer']:
                    st.success("✅ Correct!")
                    score += 1
                else:
                    st.error(f"❌ Wrong! Correct answer is: {q['answer']}) {q['options'][q['answer']]}")
                    all_correct = False

        if st.button("Submit Quiz"):
            student["progress"]["quiz_done"] = True
            student["progress"]["quiz_score"] = score
            save_data(students)
            st.success(f"Your score: {score} out of {len(questions)}")
            st.experimental_rerun()

    # Move to next chapter option
    else:
        if st.button("Go to Next Chapter"):
            student["progress"]["chapter_index"] += 1
            student["progress"]["lesson_done"] = False
            student["progress"]["quiz_done"] = False
            student.pop("quiz_content", None)  # remove old quiz
            save_data(students)
            st.experimental_rerun()
