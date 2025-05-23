import streamlit as st
import openai
import os

# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# App title
st.set_page_config(page_title="CBSE AI Tutor", page_icon="📚", layout="centered")
st.title("🤖 CBSE AI Tutor for Class 6 Students")

# Initialize session state
if "student" not in st.session_state:
    st.session_state.student = {}
if "current_chapter" not in st.session_state:
    st.session_state.current_chapter = 1
if "subject" not in st.session_state:
    st.session_state.subject = "Science"
if "chapter_data" not in st.session_state:
    st.session_state.chapter_data = None

# Subject and class input
with st.sidebar:
    st.header("📋 Student Details")
    student_name = st.text_input("Student Name", value="Shaurya")
    student_class = st.selectbox("Class", ["6"])
    subject = st.selectbox("Subject", ["Science", "Maths", "English"])

    if st.button("Start Learning"):
        st.session_state.student = {"name": student_name, "class": student_class}
        st.session_state.subject = subject
        st.session_state.current_chapter = 1
        st.session_state.chapter_data = None
        st.experimental_rerun()

# OpenAI helper function
def get_openai_response(prompt):
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

# Generate chapter content
@st.cache_data(show_spinner=False)
def generate_chapter_content(subject, student_class, chapter_number):
    prompt = f"""
    Act like a kind, friendly CBSE tutor for a class {student_class} student. 
    Teach Chapter {chapter_number} of {subject} in a clear and engaging way, using simple language.

    1. Start with an emoji-rich title like '📖 Chapter 1: Food: Where Does It Come From'
    2. Explain the chapter content in a storytelling, friendly tone (400-500 words).
    3. Follow it up with a section titled '🧠 Quiz Time!' with 3 multiple-choice questions (3 options each).
    4. End the content with a friendly encouragement to proceed to the next chapter.

    Format the output with spacing for readability.
    """
    return get_openai_response(prompt)

# Display chapter content
if st.session_state.student:
    student = st.session_state.student
    st.subheader(f"👋 Welcome, {student['name']} (Class {student['class']})")
    st.markdown(f"### 📘 Subject: {st.session_state.subject}")

    chapter_number = st.session_state.current_chapter

    if st.session_state.chapter_data is None:
        with st.spinner("Fetching your personalized lesson..."):
            content = generate_chapter_content(st.session_state.subject, student["class"], chapter_number)
            st.session_state.chapter_data = content

    # Display the generated content
    st.markdown(st.session_state.chapter_data)

    # Buttons for navigation
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Mark Chapter as Complete"):
            st.success(f"Chapter {chapter_number} marked as complete! 🎉")

    with col2:
        if st.button("➡️ Go to Next Chapter"):
            st.session_state.current_chapter += 1
            st.session_state.chapter_data = None
            st.experimental_rerun()

else:
    st.info("Please fill in the student details and click 'Start Learning' to begin your AI tutoring journey.")
