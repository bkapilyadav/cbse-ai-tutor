import streamlit as st
import openai

# -------------- OpenAI API key setup --------------
openai.api_key = st.secrets.get("OPENAI_API_KEY") or "YOUR_OPENAI_API_KEY"

# -------------- Hardcoded syllabus for demo --------------
SYLLABUS = {
    "science": {
        "6": [
            {"chapter": 1, "title": "Food: Where Does It Come From?"},
            {"chapter": 2, "title": "Components of Food"},
            {"chapter": 3, "title": "Fibre to Fabric"},
            {"chapter": 4, "title": "Sorting Materials into Groups"},
            {"chapter": 5, "title": "Separation of Substances"},
            {"chapter": 6, "title": "Changes Around Us"},
            {"chapter": 7, "title": "Getting to Know Plants"},
            {"chapter": 8, "title": "Body Movements"},
            {"chapter": 9, "title": "The Living Organisms and Their Surroundings"},
            {"chapter": 10, "title": "Motion and Measurement of Distances"},
            {"chapter": 11, "title": "Light, Shadows and Reflections"},
            {"chapter": 12, "title": "Electricity and Circuits"},
            {"chapter": 13, "title": "Fun with Magnets"},
            {"chapter": 14, "title": "Water"},
            {"chapter": 15, "title": "Air Around Us"},
            {"chapter": 16, "title": "Garbage In, Garbage Out"}
        ]
    }
}

# -------------- Helper Functions --------------

def generate_lesson(subject, class_num, chapter_title):
    prompt = (
        f"You are a friendly and knowledgeable CBSE tutor for Class {class_num} {subject.capitalize()}.\n"
        f"Explain the chapter titled '{chapter_title}' in a simple and engaging way suitable for Class {class_num} students."
    )
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful CBSE tutor."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=800
    )
    return response.choices[0].message.content.strip()

def generate_quiz(subject, class_num, chapter_title):
    prompt = (
        f"Create 3 multiple-choice questions for Class {class_num} {subject.capitalize()} chapter '{chapter_title}'.\n"
        "Each question should have options A, B, and C, and specify the correct answer."
    )
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful quiz generator."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=500
    )
    return response.choices[0].message.content.strip()

def parse_quiz(raw_quiz_text):
    # Parse raw quiz text into structured format [{question, options, answer}, ...]
    questions = []
    lines = raw_quiz_text.split("\n")
    q = {}
    options_labels = ["A", "B", "C"]
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line[0].isdigit() and line[1] == '.':
            if q:
                questions.append(q)
            q = {"question": line[3:].strip(), "options": {}, "answer": None}
        elif any(line.startswith(label + ".") for label in options_labels):
            label = line[0]
            q["options"][label] = line[2:].strip()
        elif line.lower().startswith("correct answer"):
            q["answer"] = line.split(":")[-1].strip().upper()
    if q:
        questions.append(q)
    return questions

# -------------- Streamlit UI --------------

st.set_page_config(page_title="CBSE AI Tutor", page_icon="📘")

st.title("📘 CBSE AI Tutor")

# --- Student Data Form ---
with st.form("student_info"):
    st.subheader("Enter Student Details")
    student_id = st.text_input("Student ID (required)")
    student_name = st.text_input("Student Name")
    submitted = st.form_submit_button("Submit Student Info")

if submitted:
    if not student_id.strip():
        st.error("Student ID is required to continue.")
    else:
        st.session_state["student_id"] = student_id.strip()
        st.session_state["student_name"] = student_name.strip()
        st.success(f"Welcome, {student_name or 'Student'} (ID: {student_id})!")

# If student info not set, stop here
if "student_id" not in st.session_state:
    st.info("Please enter your student details to proceed.")
    st.stop()

# --- Subject and Class selection ---
with st.form("subject_class_form"):
    st.subheader("Select Subject and Class")
    subject_input = st.selectbox("Subject", options=list(SYLLABUS.keys()))
    class_input = st.selectbox("Class", options=sorted(SYLLABUS[subject_input].keys()))
    start_learning = st.form_submit_button("Start Learning")

if start_learning:
    st.session_state.subject = subject_input
    st.session_state.class_num = class_input
    st.session_state.chapter_index = 0
    st.session_state.completed_chapters = []
    st.session_state.quiz_answers = {}
    st.experimental_rerun()

# --- Learning Module ---
if "subject" in st.session_state and "class_num" in st.session_state:
    subject = st.session_state.subject
    class_num = st.session_state.class_num
    chapters = SYLLABUS[subject][class_num]

    st.markdown(f"### Syllabus: {subject.capitalize()} Class {class_num}")
    for ch in chapters:
        st.write(f"Chapter {ch['chapter']}: {ch['title']}")

    idx = st.session_state.get("chapter_index", 0)
    current_chapter = chapters[idx]

    st.markdown("---")
    st.header(f"Chapter {current_chapter['chapter']}: {current_chapter['title']}")

    # Generate and display lesson content (cache to avoid repeated calls)
    lesson_key = f"lesson_{idx}"
    if lesson_key not in st.session_state:
        with st.spinner("Generating lesson content..."):
            lesson = generate_lesson(subject, class_num, current_chapter["title"])
            st.session_state[lesson_key] = lesson
    else:
        lesson = st.session_state[lesson_key]
    st.markdown(lesson)

    # Generate and display quiz questions
    quiz_key = f"quiz_{idx}"
    if quiz_key not in st.session_state:
        with st.spinner("Generating quiz questions..."):
            raw_quiz = generate_quiz(subject, class_num, current_chapter["title"])
            questions = parse_quiz(raw_quiz)
            st.session_state[quiz_key] = questions
            st.session_state["quiz_answers"][idx] = [None] * len(questions)
    else:
        questions = st.session_state[quiz_key]

    st.subheader("Quiz Time! 📝")

    answers = st.session_state["quiz_answers"].get(idx, [None]*len(questions))

    for i, q in enumerate(questions):
        st.write(f"**Q{i+1}: {q['question']}**")
        selected = st.radio(
            label=f"Select answer for question {i+1}",
            options=list(q["options"].keys()),
            format_func=lambda x, opts=q["options"]: f"{x}. {opts[x]}",
            key=f"quiz_{idx}_q{i}"
        )
        answers[i] = selected

    st.session_state["quiz_answers"][idx] = answers

    # Buttons to navigate chapters and mark complete
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Mark Chapter Completed"):
            if None in answers:
                st.warning("Please answer all questions before marking chapter as completed.")
            else:
                completed = st.session_state.get("completed_chapters", [])
                if idx not in completed:
                    completed.append(idx)
                st.session_state.completed_chapters = completed
                st.success(f"Chapter {current_chapter['chapter']} marked as completed.")

    with col2:
        if st.button("Next Chapter"):
            if idx + 1 < len(chapters):
                st.session_state.chapter_index = idx + 1
                st.experimental_rerun()
            else:
                st.info("You have reached the last chapter!")

# --- Show Progress ---
if "completed_chapters" in st.session_state:
    st.markdown("---")
    st.write(f"Chapters Completed: {len(st.session_state.completed_chapters)}/{len(SYLLABUS.get(st.session_state.subject, {}).get(st.session_state.class_num, []))}")

