import streamlit as st
import json
from openai import OpenAI

client = OpenAI()

def extract_json_array(text: str) -> str:
    """Extract JSON array substring from API response text."""
    start = text.find('[')
    if start == -1:
        return ""
    count = 0
    for i in range(start, len(text)):
        if text[i] == '[':
            count += 1
        elif text[i] == ']':
            count -= 1
            if count == 0:
                return text[start:i+1]
    return ""

def get_chapters(subject, student_class):
    prompt = (
        f"List chapters of {subject} for class {student_class} as JSON array of objects with fields 'chapter' and 'title'. "
        "Only return JSON array, for example:\n"
        '[{"chapter": "1", "title": "Chapter 1 Title"}, {"chapter": "2", "title": "Chapter 2 Title"}]'
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        max_tokens=700,
    )
    raw_text = response.choices[0].message.content.strip()

    json_str = extract_json_array(raw_text)
    if not json_str:
        st.error("Failed to parse chapters response from API.")
        st.error(f"API response: ```json\n{raw_text}\n```")
        return []

    try:
        chapters = json.loads(json_str)
        return chapters
    except Exception as e:
        st.error(f"JSON parsing error: {e}")
        st.error(f"JSON snippet:\n{json_str}")
        return []

def get_quiz(subject, student_class, chapter):
    prompt = (
        f"Generate 3 multiple choice questions with options and answers for {subject} class {student_class} "
        f"based on Chapter {chapter}. Return only a JSON array like:\n"
        '[{"question": "Q?", "options": ["a", "b", "c"], "answer": "correct answer"}, ...]'
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a quiz generator for school students."},
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        max_tokens=700,
    )
    raw_text = response.choices[0].message.content.strip()

    json_str = extract_json_array(raw_text)
    if not json_str:
        st.error("Failed to parse quiz questions from API.")
        st.error(f"API response was:\n{raw_text}")
        return []

    try:
        quiz = json.loads(json_str)
        return quiz
    except Exception as e:
        st.error(f"Quiz JSON parsing error: {e}")
        st.error(f"Quiz JSON snippet:\n{json_str}")
        return []

def main():
    st.title("CBSE AI Tutor")

    student_id = st.text_input("Student ID")
    student_name = st.text_input("Student Name")
    student_class = st.text_input("Class")
    subject = st.selectbox(
        "Select Subject",
        ["Mathematics", "Science", "English", "Hindi", "Sanskrit", "Social Science"],
        help="Use scroll to see all subjects"
    )

    if not student_id or not student_name or not student_class or not subject:
        st.warning("Please fill all the fields.")
        return

    if "chapters" not in st.session_state:
        st.session_state.chapters = []
    if "current_index" not in st.session_state:
        st.session_state.current_index = 0
    if "completed" not in st.session_state:
        st.session_state.completed = set()
    if "quiz" not in st.session_state:
        st.session_state.quiz = []

    if not st.session_state.chapters:
        st.session_state.chapters = get_chapters(subject, student_class)
        if not st.session_state.chapters:
            st.stop()

    chapters = st.session_state.chapters
    current_index = st.session_state.current_index

    st.write(f"### Chapters for {subject} - Class {student_class}:")
    for c in chapters:
        status = "✅" if c['chapter'] in st.session_state.completed else "❌"
        st.write(f"{status} Chapter {c['chapter']}: {c['title']}")

    current_chapter = chapters[current_index]
    st.header(f"Chapter {current_chapter['chapter']}: {current_chapter['title']}")

    # Chapter content placeholder (can integrate API call here)
    if "summary" not in st.session_state or st.session_state.get("summary_chapter") != current_chapter['chapter']:
        st.session_state.summary = f"Summary of Chapter {current_chapter['chapter']} - {current_chapter['title']} goes here."
        st.session_state.summary_chapter = current_chapter['chapter']

    st.write(st.session_state.summary)

    if not st.session_state.quiz or st.session_state.get("quiz_chapter") != current_chapter['chapter']:
        st.session_state.quiz = get_quiz(subject, student_class, current_chapter['chapter'])
        st.session_state.quiz_chapter = current_chapter['chapter']

    if st.session_state.quiz:
        st.subheader("Quiz")
        for i, q in enumerate(st.session_state.quiz, start=1):
            st.write(f"Q{i}: {q['question']}")
            for option in q["options"]:
                st.write(f"- {option}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Mark Completed"):
            st.session_state.completed.add(current_chapter['chapter'])
            st.success(f"Marked Chapter {current_chapter['chapter']} as completed.")

    with col2:
        if st.button("Next Chapter"):
            if current_index + 1 < len(chapters):
                st.session_state.current_index += 1
                st.session_state.quiz = []
                st.session_state.summary = ""
                st.experimental_rerun()
            else:
                st.info("You have completed all chapters.")

    if st.session_state.completed:
        completed_chapters = ", ".join(sorted(st.session_state.completed))
        st.write(f"Completed Chapters: {completed_chapters}")

if __name__ == "__main__":
    main()
