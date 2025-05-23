import streamlit as st
import openai

# === Set your OpenAI API Key here or via environment variable ===
openai.api_key = "YOUR_OPENAI_API_KEY"

# --- Hardcoded syllabus example for Class 6 (can be expanded or fetched dynamically) ---
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
        ],
    },
    "maths": {
        "6": [
            {"chapter": 1, "title": "Knowing Our Numbers"},
            {"chapter": 2, "title": "Whole Numbers"},
            {"chapter": 3, "title": "Playing with Numbers"},
            {"chapter": 4, "title": "Basic Geometrical Ideas"},
            {"chapter": 5, "title": "Understanding Elementary Shapes"},
            # Add more chapters as needed...
        ]
    },
    "english": {
        "6": [
            {"chapter": 1, "title": "The Best Christmas Present in the World"},
            {"chapter": 2, "title": "The Ant and the Cricket"},
            {"chapter": 3, "title": "The Little Girl"},
            # Add more chapters as needed...
        ]
    }
}

# --- Helper function to generate lesson content using OpenAI ---
def generate_lesson(subject, class_num, chapter_title):
    prompt = (
        f"You are a friendly and knowledgeable tutor for CBSE Class {class_num} {subject.capitalize()}.\n"
        f"Provide a detailed, easy-to-understand lesson explanation for the chapter titled: '{chapter_title}'.\n"
        f"Use simple language suitable for Class {class_num} students.\n"
        "Make the content engaging and educational."
    )
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "You are a helpful CBSE tutor."},
                  {"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=800,
    )
    return response.choices[0].message.content.strip()

# --- Helper function to generate quiz questions using OpenAI ---
def generate_quiz(subject, class_num, chapter_title):
    prompt = (
        f"Create 3 multiple-choice quiz questions for CBSE Class {class_num} {subject.capitalize()} chapter titled '{chapter_title}'.\n"
        "Each question should have 3 options labeled A, B, and C.\n"
        "Also, specify the correct answer for each question.\n"
        "Format the output as a list of questions with options and correct answer keys."
    )
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "You are a helpful quiz creator for CBSE students."},
                  {"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=500,
    )
    return response.choices[0].message.content.strip()

# --- Streamlit App ---

st.set_page_config(page_title="CBSE AI Tutor", page_icon="📘", layout="centered")

st.title("📘 CBSE AI Tutor")

# Initialize session state variables
if "subject" not in st.session_state:
    st.session_state.subject = None
if "class_num" not in st.session_state:
    st.session_state.class_num = None
if "chapter_index" not in st.session_state:
    st.session_state.chapter_index = 0
if "completed_chapters" not in st.session_state:
    st.session_state.completed_chapters = []
if "quiz_answers" not in st.session_state:
    st.session_state.quiz_answers = {}

# Step 1: Get subject and class inputs
if st.session_state.subject is None or st.session_state.class_num is None:
    st.write("Enter the subject and class to start learning:")
    subject_input = st.text_input("Subject (e.g., science, maths, english)").lower().strip()
    class_input = st.text_input("Class (e.g., 6)").strip()

    if st.button("Start Learning"):
        if subject_input in SYLLABUS and class_input in SYLLABUS[subject_input]:
            st.session_state.subject = subject_input
            st.session_state.class_num = class_input
            st.session_state.chapter_index = 0
            st.experimental_rerun()
        else:
            st.error("Subject or class not found in syllabus. Please try again.")

else:
    subject = st.session_state.subject
    class_num = st.session_state.class_num
    chapters = SYLLABUS[subject][class_num]

    st.markdown(f"### Chapters for **{subject.capitalize()}** - Class {class_num}:")

    # List all chapters with completion status
    for idx, ch in enumerate(chapters):
        status = "✅ Completed" if idx in st.session_state.completed_chapters else ""
        st.write(f"Chapter {ch['chapter']}: {ch['title']} {status}")

    st.markdown("---")

    # Show current chapter details
    current_idx = st.session_state.chapter_index
    current_chapter = chapters[current_idx]

    st.subheader(f"📖 Chapter {current_chapter['chapter']}: {current_chapter['title']}")

    # Generate lesson content only once per chapter to save tokens (cache per session)
    if f"lesson_{current_idx}" not in st.session_state:
        with st.spinner("Generating lesson content..."):
            lesson_content = generate_lesson(subject, class_num, current_chapter["title"])
            st.session_state[f"lesson_{current_idx}"] = lesson_content
    else:
        lesson_content = st.session_state[f"lesson_{current_idx}"]

    st.markdown(lesson_content)

    st.markdown("### Quiz Time! 📝")

    # Generate quiz questions only once per chapter
    if f"quiz_{current_idx}" not in st.session_state:
        with st.spinner("Generating quiz questions..."):
            quiz_text = generate_quiz(subject, class_num, current_chapter["title"])
            # Parse quiz text into structured format (basic parsing)
            # Expecting output format like:
            # 1. Question text
            #    A. option1
            #    B. option2
            #    C. option3
            # Correct answer: B
            # We'll split and store questions in session_state for rendering
            questions = []
            lines = quiz_text.split("\n")
            q = {}
            option_keys = ['A', 'B', 'C']
            option_index = 0
            for line in lines:
                line = line.strip()
                if line == "":
                    continue
                if line[0].isdigit() and line[1] == '.':  # new question
                    if q:
                        questions.append(q)
                        q = {}
                    q["question"] = line[3:].strip()
                    q["options"] = {}
                    option_index = 0
                elif any(line.startswith(k + ".") for k in option_keys):
                    key = line[0]
                    option_text = line[2:].strip()
                    q["options"][key] = option_text
                elif line.lower().startswith("correct answer"):
                    q["answer"] = line.split(":")[-1].strip().upper()
            if q:
                questions.append(q)
            st.session_state[f"quiz_{current_idx}"] = questions
            st.session_state[f"quiz_answers_{current_idx}"] = [None] * len(questions)
    else:
        questions = st.session_state[f"quiz_{current_idx}"]

    # Show quiz questions with multiple choice options
    user_answers = []
    for i, q in enumerate(questions):
        st.write(f"**Q{i+1}: {q['question']}**")
        options = q["options"]
        # Radio buttons to select answer
        ans = st.radio(
            label=f"Select answer for question {i+1}",
            options=list(options.keys()),
            format_func=lambda x: f"{x}. {options[x]}",
            key=f"quiz_{current_idx}_q{i}"
        )
        user_answers.append(ans)

    # Save user answers
    st.session_state[f"quiz_answers_{current_idx}"] = user_answers

    # Buttons for next chapter and mark complete
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Mark Chapter as Completed"):
            # Check if all questions answered
            if None in user_answers:
                st.warning("Please answer all quiz questions before marking complete.")
            else:
                st.session_state.completed_chapters.append(current_idx)
                st.success(f"Chapter {current_chapter['chapter
