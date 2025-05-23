import streamlit as st
from openai import OpenAI

# Initialize OpenAI client with your API key stored in Streamlit secrets
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Sample subjects list (expand as needed)
SUBJECTS = [
    "Mathematics",
    "Science",
    "English",
    "Social Science",
    "Hindi",
    "Computer Science",
    "Sanskrit",
    "Physical Education",
    "Art",
]

def get_chapters(subject: str, student_class: str):
    prompt = (
        f"List the chapters for {subject} for class {student_class} as a numbered list with chapter number and title only."
        f"Format each chapter as 'Chapter X: Title'."
        "Return the result as a JSON array of objects like [{\"chapter\": \"1\", \"title\": \"Chapter Title\"}, ...]"
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

    # The response content is a JSON string, parse it safely
    import json
    try:
        chapters = json.loads(response.choices[0].message.content)
    except Exception as e:
        st.error("Failed to parse chapters response from API.")
        st.error(f"API response: {response.choices[0].message.content}")
        chapters = []
    return chapters

def get_chapter_content(subject: str, student_class: str, chapter_number: str, chapter_title: str):
    prompt = (
        f"Explain the chapter '{chapter_title}' (Chapter {chapter_number}) from {subject} class {student_class} in simple, engaging language "
        f"for young students. Provide a summary and then 3 follow-up quiz questions with options and answers."
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a friendly educational tutor."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.5,
        max_tokens=1000,
    )
    return response.choices[0].message.content

def main():
    st.title("📘 CBSE AI Tutor")

    # Input form for student data
    with st.form("student_info_form"):
        name = st.text_input("Enter your name")
        student_id = st.text_input("Enter your ID")
        student_class = st.text_input("Enter your class (e.g., 6, 7, 8)")
        subject = st.selectbox("Select Subject", SUBJECTS)
        submitted = st.form_submit_button("Start Learning")

    if submitted:
        if not (name and student_id and student_class and subject):
            st.warning("Please fill all fields to proceed.")
            return

        # Save student info in session state
        st.session_state["student_info"] = {
            "name": name,
            "id": student_id,
            "class": student_class,
            "subject": subject,
        }

        # Fetch chapters once and store
        if "chapters" not in st.session_state:
            with st.spinner("Fetching chapters..."):
                chapters = get_chapters(subject, student_class)
                st.session_state["chapters"] = chapters
                st.session_state["current_chapter_idx"] = 0
                st.session_state["completed_chapters"] = set()

    # If chapters loaded, show chapters and content
    if "chapters" in st.session_state and st.session_state["chapters"]:
        chapters = st.session_state["chapters"]
        idx = st.session_state.get("current_chapter_idx", 0)

        if idx >= len(chapters):
            st.success("🎉 You have completed all chapters!")
            return

        chapter = chapters[idx]
        chapter_num = chapter.get("chapter") or chapter.get("chapter_number") or str(idx + 1)
        chapter_title = chapter.get("title") or chapter.get("chapter_title") or "Unknown Title"

        st.markdown(f"### 📖 Chapter {chapter_num}: {chapter_title}")

        # Fetch chapter content only once per chapter
        content_key = f"chapter_content_{idx}"
        if content_key not in st.session_state:
            with st.spinner(f"Loading chapter content for Chapter {chapter_num}..."):
                content = get_chapter_content(subject, student_class, chapter_num, chapter_title)
                st.session_state[content_key] = content

        st.markdown(st.session_state[content_key])

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Mark Chapter Completed"):
                st.session_state["completed_chapters"].add(idx)
                st.success(f"Chapter {chapter_num} marked as completed.")

        with col2:
            if st.button("Next Chapter"):
                if idx < len(chapters) - 1:
                    st.session_state["current_chapter_idx"] = idx + 1
                    st.experimental_rerun()
                else:
                    st.info("You have reached the last chapter.")

        # Show completed chapters list
        if st.session_state.get("completed_chapters"):
            completed_nums = [chapters[i].get("chapter", str(i + 1)) for i in st.session_state["completed_chapters"]]
            st.write(f"✅ Completed chapters: {', '.join(completed_nums)}")

    elif submitted:
        st.info("No chapters found for your selection. Please check your inputs or try again.")

if __name__ == "__main__":
    main()
