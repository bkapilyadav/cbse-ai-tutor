import streamlit as st
import json
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI()

# Helper function to clean JSON from API responses with extra text
def extract_json_array(text: str) -> str:
    """
    Extract JSON array substring from a larger string that may contain extra text before/after.
    Returns the substring that starts with [ and ends with the matching ].
    """
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

def clean_json_response(text: str) -> str:
    # You can add further cleaning if needed
    return text.strip()

# Fetch chapters for the selected subject and class
def get_chapters(subject: str, student_class: str):
    prompt = (
        f"Provide a JSON array of chapters with 'chapter' and 'title' fields for {subject} class {student_class} "
        f"in this format: "
        f"[{{\"chapter\": \"1\", \"title\": \"Chapter Title 1\"}}, {{\"chapter\": \"2\", \"title\": \"Chapter Title 2\"}}, ...]"
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        max_tokens=700,
    )

    raw_text = response.choices[0].message.content
    cleaned_text = clean_json_response(raw_text)

    try:
        chapters = json.loads(cleaned_text)
        if not isinstance(chapters, list):
            raise ValueError("Chapters response is not a list")
        return chapters
    except Exception as e:
        st.error("Failed to parse chapters response from API.")
        st.error(f"API response: ```json\n{cleaned_text}\n```")
        return []

# Fetch chapter content summary
def get_chapter_summary(subject: str, student_class: str, chapter_number: str):
    prompt = (
        f"Give a short, kid-friendly summary of Chapter {chapter_number} for {subject} class {student_class}."
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=700,
    )
    return response.choices[0].message.content.strip()

# Fetch quiz questions for a chapter
def get_quiz_questions(subject: str, student_class: str, chapter_number: str):
    prompt = (
        f"Generate 3 simple multiple choice questions (question + 3 options + correct answer) "
        f"based on Chapter {chapter_number} of {subject} for class {student_class}. "
        f"Return ONLY a JSON array of objects with keys: question, options (list), answer."
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

    json_array_str = extract_json_array(cleaned_text)
    if not json_array_str:
        st.error("Failed to extract JSON array from quiz response.")
        st.error(f"API response was:\n{raw_text}")
        return []

    try:
        quiz = json.loads(json_array_str)
    except Exception as e:
        st.error(f"Failed to parse quiz JSON: {e}")
        st.error(f"JSON snippet:\n{json_array_str}")
        return []

    return quiz

def main():
    st.title("📘 CBSE AI Tutor")

    # Input fields for student data
    student_id = st.text_input("Enter Student ID:")
    student_name = st.text_input("Enter Student Name:")
    student_class = st.text_input("Enter Class (e.g., 6):")
    subject = st.selectbox(
        "Select Subject:",
        options=[
            "Mathematics", "Science", "Social Science", "English", "Hindi",
            "Sanskrit", "Computer Science", "Environmental Science"
        ],
        help="Scroll to select your subject."
    )

    if not (student_id and student_name and student_class and subject):
        st.info("Please fill in all student details and select subject.")
        return

    if "chapters" not in st.session_state:
        st.session_state.chapters = []
    if "current_chapter_index" not in st.session_state:
        st.session_state.current_chapter_index = 0
    if "completed_chapters" not in st.session_state:
        st.session_state.completed_chapters = set()
    if "quiz" not in st.session_state:
        st.session_state.quiz = []

    # Load chapters once per subject + class
    if not st.session_state.chapters:
        chapters = get_chapters(subject, student_class)
        if chapters:
            st.session_state.chapters = chapters
        else:
            st.warning("No chapters found for your selection. Please check inputs.")
            return

    chapters = st.session_state.chapters
    current_idx = st.session_state.current_chapter_index

    st.subheader(f"Chapters for {subject} - Class {student_class}:")
    chapter_titles = [f"Chapter {ch['chapter']}: {ch['title']}" for ch in chapters]
    st.write(", ".join(chapter_titles))

    current_chapter = chapters[current_idx]

    st.markdown(f"### 📖 Chapter {current_chapter['chapter']}: {current_chapter['title']}")

    # Show chapter summary
    if "chapter_summary" not in st.session_state:
        st.session_state.chapter_summary = get_chapter_summary(subject, student_class, current_chapter['chapter'])

    st.markdown(st.session_state.chapter_summary)

    # Show quiz for the chapter
    if not st.session_state.quiz:
        st.session_state.quiz = get_quiz_questions(subject, student_class, current_chapter['chapter'])

    if st.session_state.quiz:
        st.markdown("### 📝 Quiz Questions")
        for i, q in enumerate(st.session_state.quiz, start=1):
            st.markdown(f"**Q{i}: {q['question']}**")
            options = q.get("options", [])
            for opt in options:
                st.markdown(f"- {opt}")

    # Buttons for user actions
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Mark Chapter Completed"):
            st.session_state.completed_chapters.add(current_chapter['chapter'])
            st.success(f"Chapter {current_chapter['chapter']} marked as completed!")

    with col2:
        if st.button("Next Chapter"):
            if current_idx + 1 < len(chapters):
                st.session_state.current_chapter_index += 1
                # Reset cached data for next chapter
                st.session_state.chapter_summary = None
                st.session_state.quiz = []
                st.experimental_rerun()
            else:
                st.info("You have completed all chapters!")

    # Show completed chapters
    if st.session_state.completed_chapters:
        completed_list = ", ".join(sorted(st.session_state.completed_chapters))
        st.markdown(f"✅ Completed Chapters: {completed_list}")

if __name__ == "__main__":
    main()
