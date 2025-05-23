# app.py
# -*- coding: utf-8 -*-
import streamlit as st
import re
import json
from openai import OpenAI

client = OpenAI()

def clean_json_response(raw_text: str) -> str:
    # Improved regex to extract first JSON array in text robustly
    match = re.search(r'\[\s*\{.*?\}\s*\]', raw_text, re.DOTALL)
    return match.group(0).strip() if match else raw_text.strip()

def get_chapters(subject: str, student_class: str):
    prompt = (
        f"List the chapters for {subject} for class {student_class} as a JSON array of objects, "
        f"each object with keys 'chapter' and 'title'. The title should be the exact chapter title as per CBSE syllabus. "
        f"Only return the JSON array, no explanations or extra text."
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an educational assistant providing precise CBSE syllabus chapter data."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        max_tokens=500,
    )
    raw_text = response.choices[0].message.content
    cleaned_text = clean_json_response(raw_text)
    try:
        chapters = json.loads(cleaned_text)
        return chapters
    except Exception:
        st.error("Failed to parse chapters from API.")
        st.error(f"API response was:\n{raw_text}")
        return []

def get_chapter_content(subject: str, student_class: str, chapter_number: str, chapter_title: str):
    prompt = (
        f"Write a simple and engaging explanation in Hindi of Chapter {chapter_number} titled '{chapter_title}' "
        f"from {subject} for class {student_class}. "
        f"Use easy language suitable for kids and ensure content strictly matches the chapter title and topic."
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful Hindi teacher bot."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=700,
    )
    return response.choices[0].message.content.strip()

def validate_quiz_questions(quiz, chapter_number, subject, chapter_title):
    """
    Validate that each quiz question relates to chapter number or chapter title keywords (Hindi and English).
    Returns True if all questions pass, else False.
    """
    chapter_str = str(chapter_number)
    subject_lower = subject.lower()
    chapter_title_words = set(chapter_title.lower().replace("(", "").replace(")", "").split())

    for q in quiz:
        question_text = q.get("question", "").lower()
        # Check if question mentions chapter number, subject name or any chapter title word (relaxed but contextual)
        if not (chapter_str in question_text
                or subject_lower in question_text
                or any(word in question_text for word in chapter_title_words)):
            return False
    return True

def get_quiz_questions(subject: str, student_class: str, chapter_number: str, chapter_title: str, retries=2):
    prompt = (
        f"Generate 3 simple multiple choice questions (each with question text, 3 options, and the correct answer) "
        f"STRICTLY based on Chapter {chapter_number} titled '{chapter_title}' from {subject} for class {student_class}. "
        f"Questions must be kid-friendly, clear, and directly relevant to this chapter only. "
        f"Return ONLY the JSON array of objects with keys: question, options (list), answer."
    )
    for attempt in range(retries):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a quiz generator for kids with strict adherence to chapter topics."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=700,
        )
        raw_text = response.choices[0].message.content
        cleaned_text = clean_json_response(raw_text)
        try:
            quiz = json.loads(cleaned_text)
            if validate_quiz_questions(quiz, chapter_number, subject, chapter_title):
                return quiz
            else:
                st.warning("Quiz questions validation failed, retrying to generate relevant questions...")
        except Exception:
            st.warning("Failed to parse quiz questions, retrying...")
    st.error("Could not generate valid quiz questions related to the chapter after retries.")
    return []

def main():
    st.title("📘 CBSE AI Tutor")

    if "student" not in st.session_state:
        st.session_state.student = {}

    with st.form("student_info_form"):
        st.session_state.student['name'] = st.text_input("Enter your name", st.session_state.student.get('name', ''))
        st.session_state.student['id'] = st.text_input("Enter your ID", st.session_state.student.get('id', ''))
        st.session_state.student['class'] = st.text_input("Enter your class (e.g., 6)", st.session_state.student.get('class', ''))

        subjects = [
            "Science", "Mathematics", "English", "Social Science",
            "Computer Science", "Hindi", "Sanskrit", "Environmental Studies"
        ]
        st.session_state.student['subject'] = st.selectbox(
            "Select subject",
            subjects,
            index=subjects.index(st.session_state.student.get('subject', "Science")) if st.session_state.student.get('subject') in subjects else 0
        )

        submitted = st.form_submit_button("Submit")
        if submitted:
            if not all([st.session_state.student['name'], st.session_state.student['id'], st.session_state.student['class'], st.session_state.student['subject']]):
                st.warning("Please fill all the details.")
                return
            st.session_state.current_chapter_idx = 0
            st.session_state.completed_chapters = set()

            st.session_state.previous_subject = st.session_state.student['subject']
            st.session_state.previous_class = st.session_state.student['class']
            st.session_state.chapters = get_chapters(st.session_state.student['subject'], st.session_state.student['class'])

    if all(st.session_state.student.get(k) for k in ['name', 'id', 'class', 'subject']):
        # Refresh chapters if subject/class changed
        if (
            "previous_subject" not in st.session_state or
            "previous_class" not in st.session_state or
            st.session_state.previous_subject != st.session_state.student['subject'] or
            st.session_state.previous_class != st.session_state.student['class']
        ):
            st.session_state.chapters = get_chapters(st.session_state.student['subject'], st.session_state.student['class'])
            st.session_state.previous_subject = st.session_state.student['subject']
            st.session_state.previous_class = st.session_state.student['class']
            st.session_state.current_chapter_idx = 0
            st.session_state.completed_chapters = set()
            # Clear cached content and quizzes
            for k in list(st.session_state.keys()):
                if k.startswith("chapter_content_") or k.startswith("quiz_"):
                    del st.session_state[k]

        chapters = st.session_state.get("chapters", [])
        if not chapters:
            st.warning("No chapters found for your selection.")
            return

        total_chapters = len(chapters)
        st.markdown(f"### Chapters for {st.session_state.student['subject']} - Class {st.session_state.student['class']}:")

        for idx, chap in enumerate(chapters):
            chap_num = chap.get("chapter")
            chap_title = chap.get("title")
            if idx == st.session_state.current_chapter_idx:
                st.markdown(f"**📖 Chapter {chap_num}: {chap_title}**")
            else:
                if st.button(f"Go to Chapter {chap_num}: {chap_title}", key=f"chap_{idx}"):
                    st.session_state.current_chapter_idx = idx

        current_chap = chapters[st.session_state.current_chapter_idx]
        st.markdown(f"## 📖 Chapter {current_chap['chapter']}: {current_chap['title']}")

        key_content = f"chapter_content_{st.session_state.current_chapter_idx}"
        if key_content not in st.session_state:
            st.session_state[key_content] = get_chapter_content(
                st.session_state.student['subject'],
                st.session_state.student['class'],
                current_chap['chapter'],
                current_chap['title']
            )
        st.markdown(st.session_state[key_content])

        key_quiz = f"quiz_{st.session_state.current_chapter_idx}"
        if key_quiz not in st.session_state:
            st.session_state[key_quiz] = get_quiz_questions(
                st.session_state.student['subject'],
                st.session_state.student['class'],
                current_chap['chapter'],
                current_chap['title']
            )
        quiz = st.session_state[key_quiz]

        if quiz:
            st.markdown("### Quiz Time! 🎉")
            for i, q in enumerate(quiz):
                st.markdown(f"**Q{i+1}: {q['question']}**")
                options = q['options']
                user_answer = st.radio(f"Choose the correct answer for Q{i+1}:", options, key=f"quiz_{st.session_state.current_chapter_idx}_{i}")
                if st.button(f"Check Answer for Q{i+1}", key=f"check_{st.session_state.current_chapter_idx}_{i}"):
                    if user_answer == q['answer']:
                        st.success("Correct! 🎉")
                    else:
                        st.error(f"Incorrect. The correct answer is: {q['answer']}")

        if current_chap['chapter'] not in st.session_state.completed_chapters:
            if st.button("Mark Chapter Completed ✅"):
                st.session_state.completed_chapters.add(current_chap['chapter'])
                st.success(f"Chapter {current_chap['chapter']} marked as completed!")

        if st.session_state.current_chapter_idx < total_chapters - 1:
            if st.button("Next Chapter ▶️"):
                st.session_state.current_chapter_idx += 1
        else:
            st.info("You have completed all chapters!")

if __name__ == "__main__":
    main()
