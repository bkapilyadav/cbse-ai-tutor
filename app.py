import streamlit as st
import json
import os
import openai

# --- Page setup ---
st.set_page_config(page_title="CBSE AI Tutor", layout="wide")
st.title("📚 CBSE AI Teaching Agent")
st.markdown("Welcome! Let's start your learning journey.")

# --- File handling ---
data_file = "student_data.json"
if not os.path.exists(data_file):
    with open(data_file, "w") as f:
        json.dump({}, f)

def load_data():
    with open(data_file, "r") as f:
        return json.load(f)

def save_data(data):
    with open(data_file, "w") as f:
        json.dump(data, f, indent=4)

students = load_data()

# --- Student input ---
st.sidebar.header("Enter Student Information")
name = st.sidebar.text_input("Name")
student_id = st.sidebar.text_input("Student ID")
student_class = st.sidebar.selectbox("Class", ["6th", "7th", "8th", "9th", "10th"])
subject = st.sidebar.selectbox("Subject", ["Mathematics", "Science", "English"])

# --- Start Learning ---
if st.sidebar.button("Start Learning"):
    if student_id not in students:
        students[student_id] = {
            "name": name,
            "class": student_class,
            "subject": subject,
            "progress": {"chapter": 1, "topic": 1, "last_position": "start"},
            "quiz_scores": []
        }
        save_data(students)
        st.success(f"Welcome, {name}! Let's begin your {subject} lessons.")
    else:
        st.success(f"Welcome back, {students[student_id]['name']}! Resuming from where you left off.")
        student_class = students[student_id]["class"]
        subject = students[student_id]["subject"]

    # --- Lesson section ---
    st.subheader(f"Class {student_class} - {subject}")
    chapter = students[student_id]["progress"]["chapter"]
    topic = students[student_id]["progress"]["topic"]
    st.markdown(f"**Chapter {chapter} - Topic {topic}**")

    # --- Visual Explanations ---
    image_links = {
        "Mathematics": {"6th": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/70/Basic_maths_formula_chart.png/640px-Basic_maths_formula_chart.png"},
        "Science": {"6th": "https://upload.wikimedia.org/wikipedia/commons/6/6b/Water_cycle.png"}
    }
    img_url = image_links.get(subject, {}).get(student_class)
    if img_url:
        st.image(img_url, caption="📸 Visual Explanation")

    # --- AI Explanation (Optional) ---
    openai.api_key = os.getenv("OPENAI_API_KEY")

    def generate_teaching_prompt(grade, subject, chapter, topic):
        return f"You are an AI teacher for class {grade} students in India following CBSE curriculum. Teach Chapter {chapter}, Topic {topic} of {subject} in a simple and interactive way."

    def get_ai_lesson(prompt):
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "You are a helpful AI teacher."},
                      {"role": "user", "content": prompt}]
        )
        return response['choices'][0]['message']['content']

    prompt = generate_teaching_prompt(student_class, subject, chapter, topic)
    ai_content = get_ai_lesson(prompt)
    st.markdown(ai_content)

    # --- Mark topic complete ---
    if st.button("Complete Topic"):
        students[student_id]["progress"]["topic"] += 1
        students[student_id]["progress"]["last_position"] = "next_topic"
        save_data(students)
        st.success("Progress saved. Next topic ready!")

    # --- Quiz Time ---
    st.subheader("🧪 Quiz Time!")

    quiz_bank = {
        "6th": {
            "Mathematics": [
                {"question": "What is 5 + 7?", "options": ["10", "12", "14"], "answer": "12"},
                {"question": "What is the value of 9 x 3?", "options": ["27", "18", "36"], "answer": "27"}
            ],
            "Science": [
                {"question": "Which of these is a living thing?", "options": ["Rock", "Cat", "Car"], "answer": "Cat"},
                {"question": "Water boils at?", "options": ["90°C", "100°C", "80°C"], "answer": "100°C"}
            ]
        }
    }

    quiz_set = quiz_bank.get(student_class, {}).get(subject, [])
    if quiz_set:
        score = 0
        for i, q in enumerate(quiz_set):
            st.markdown(f"**Q{i+1}: {q['question']}**")
            user_ans = st.radio("Choose your answer:", q["options"], key=f"quiz_{i}")
            if user_ans == q["answer"]:
                score += 1

        if st.button("Submit Quiz"):
            st.success(f"🎉 You scored {score} out of {len(quiz_set)}")
            students[student_id]["quiz_scores"].append({"subject": subject, "score": score})
            save_data(students)
    else:
        st.info("No quiz available for this subject yet.")
