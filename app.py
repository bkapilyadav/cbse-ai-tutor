import streamlit as st
import openai

# Set your OpenAI API key in Streamlit secrets or environment variable
openai.api_key = st.secrets.get("OPENAI_API_KEY")

# Initialize session state
if "student" not in st.session_state:
    st.session_state.student = {}

if "current_chapter_index" not in st.session_state:
    st.session_state.current_chapter_index = 0

if "chapters" not in st.session_state:
    st.session_state.chapters = []

def get_chapters(subject: str, student_class: str):
    # Generate chapter list from OpenAI
    prompt = f"""
You are a helpful CBSE tutor assistant.
Provide a numbered list of chapter titles for Class {student_class} {subject} subject as JSON array.
Example:
[
  "Chapter 1: Food: Where Does It Come From?",
  "Chapter 2: Components of Food",
  "Chapter 3: Fibre to Fabric",
  ...
]
Only provide JSON array.
"""
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=500,
    )
    text = response.choices[0].message.content.strip()
    try:
        chapters = st.experimental_json.loads(text)
    except Exception:
        # fallback to parsing as plain text list if json parsing fails
        chapters = []
        lines = text.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line:
                chapters.append(line)
    return chapters

def get_chapter_content(chapter_title: str, subject: str, student_class: str):
    prompt = f"""
You are a friendly and engaging CBSE tutor assistant.
Explain the following chapter in simple language suitable for Class {student_class} students learning {subject}:

{chapter_title}

Please provide a clear, readable explanation with examples.
"""
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1000,
    )
    return response.choices[0].message.content.strip()

def get_quiz_questions(chapter_title: str, subject: str, student_class: str):
    prompt = f"""
You are a CBSE tutor assistant.
Generate 3 simple multiple-choice quiz questions for Class {student_class} students on the chapter "{chapter_title}" of {subject}.
Provide output as a JSON list of objects with question, options (list), and correct_answer fields.

Example:
[
  {{
    "question": "What is ...?",
    "options": ["A", "B", "C"],
    "correct_answer": "B"
  }},
  ...
]
"""
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=700,
    )
    text = response.choices[0].message.content.strip()
    try:
        quiz = st.experimental_json.loads(text)
    except Exception:
        quiz = []
    return quiz

def main():
    st.title("📘 CBSE AI Tutor")

    # Input form for student details
    with st.form("student_info_form"):
        name = st.text_input("Enter your name")
        student_id = st.text_input("Enter your ID")
        student_class = st.text_input("Enter your class (e.g., 6, 7, 8)")
        subject = st.text_input("Enter the subject (e.g., Science, Mathematics, English)")
        submitted = st.form_submit_button("Start Learning")

    if submitted:
        if not (name and student_id and student_class and subject):
            st.error("Please fill in all fields.")
            return
        # Save student data and reset progress
        st.session_state.student = {
            "name": name,
            "id": student_id,
            "class": student_class,
            "subject": subject,
            "completed_chapters": []
        }
        st.session_state.current_chapter_index = 0
        st.session_state.chapters = get_chapters(subject, student_class)
        st.experimental_rerun()

    if st.session_state.get("student"):

        student = st.session_state.student
        st.write(f"Welcome, **{student['name']}** (ID: {student['id']})")
        st.write(f"Class: {student['class']}, Subject: {student['subject']}")
        chapters = st.session_state.chapters
        current_idx = st.session_state.current_chapter_index

        if not chapters:
            st.info("No chapters found for this subject and class.")
            return

        # Show all chapters with completion status
        st.subheader(f"Chapters for {student['subject']} - Class {student['class']}:")
        for idx, chap in enumerate(chapters):
            completed = "✅" if idx in student.get("completed_chapters", []) else "❌"
            st.write(f"{completed} {chap}")

        # Display current chapter content
        current_chapter = chapters[current_idx]
        st.markdown(f"## 📖 {current_chapter}")

        # Fetch and show chapter explanation
        content = get_chapter_content(current_chapter, student['subject'], student['class'])
        st.write(content)

        # Show quiz questions for current chapter
        quiz = get_quiz_questions(current_chapter, student['subject'], student['class'])
        if quiz:
            st.markdown("### Quiz Time! 📝")
            for i, q in enumerate(quiz):
                st.write(f"**Q{i+1}: {q['question']}**")
                options = q.get("options", [])
                if options:
                    selected = st.radio(f"Select answer for Q{i+1}", options, key=f"q{i+1}")
                    # You can add feedback logic here if desired
        else:
            st.write("No quiz available for this chapter.")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Mark Chapter Completed"):
                if current_idx not in student["completed_chapters"]:
                    student["completed_chapters"].append(current_idx)
                st.success(f"Marked '{current_chapter}' as completed!")
                st.session_state.student = student
                st.experimental_rerun()

        with col2:
            if st.button("Next Chapter"):
                if current_idx + 1 < len(chapters):
                    st.session_state.current_chapter_index += 1
                    st.experimental_rerun()
                else:
                    st.info("You have reached the last chapter.")

        with col3:
            if st.button("Previous Chapter"):
                if current_idx > 0:
                    st.session_state.current_chapter_index -= 1
                    st.experimental_rerun()
                else:
                    st.info("This is the first chapter.")

if __name__ == "__main__":
    main()
