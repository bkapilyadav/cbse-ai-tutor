# app.py
# -*- coding: utf-8 -*-
import streamlit as st
import re
import json
from openai import OpenAI

client = OpenAI()

def clean_json_response(raw_text: str) -> str:
    match = re.search(r'\[\s*{.*?}\s*\]', raw_text, re.DOTALL)
    return match.group(0).strip() if match else raw_text.strip()

def get_chapters(subject: str, student_class: str):
    prompt = (
        f"List the chapters for {subject} for class {student_class} as a JSON array of objects,"
        f" each object with keys 'chapter' and 'title', like:\n"
        f"[{{\"chapter\": \"1\", \"title\": \"Chapter Title\"}}, ...]\n"
        f"Only return the JSON array, no extra text."
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an assistant that provides educational chapters."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        max_tokens=500,
    )
    raw_text = response.choices[0].message.content
    cleaned_text = clean_json_response(raw_text)
    try:
        return json.loads(cleaned_text)
    except Exception:
        st.error("Failed to parse chapters response from API.")
        st.error(f"API response was:\n{raw_text}")
        return []

def get_chapter_content(subject: str, student_class: str, chapter_number: str):
    prompt = (
        f"Write a simple, engaging explanation of Chapter {chapter_number} of {subject} for class {student_class}."
        f" Use easy language suitable for kids."
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful teacher bot."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=700,
    )
    return response.choices[0].message.content.strip()

def get_quiz_questions(subject: str, student_class: str, chapter_number: str):
    prompt = (
        f"Generate 3 simple multiple choice questions (question + 3 options + correct answer) "
        f"based on Chapter {chapter_number} of {subject} for class {student_class}."
        f" Return as a JSON array of objects with keys: question, options (list), answer."
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a quiz generator for kids."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=700,
    )
    raw_text = response.choices[0].message.content
    cleaned_text = clean_json_response(raw_text)
    try:
        return json.loads(cleaned_text)
    except Exception:
        st.error("Failed to parse quiz questions from API.")
        st.error(f"API response was:\n{raw_text}")
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

            # Store previous subject/class to detect changes
            st.session_state.previous_subject = st.session_state.student['subject']
            st.session_state.previous_class = st.session_state.student['class']
            st.session_state.chapters = get_chapters(st.session_state.student['subject'], st.session_state.student['class'])

    if all(st.session_state.student.get(k) for k in ['name', 'id', 'class', 'subject']):
        # Refresh chapters if subject/class changed after initial form submission
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
                current_chap['chapter']
            )
        st.markdown(st.session_state[key_content])

        key_quiz = f"quiz_{st.session_state.current_chapter_idx}"
        if key_quiz not in st.session_state:
            st.session_state[key_quiz] = get_quiz_questions(
                st.session_state.student['subject'],
                st.session_state.student['class'],
                current_chap['chapter']
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
