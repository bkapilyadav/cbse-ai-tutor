import os
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client with API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_chapters(subject, student_class):
    prompt = f"List the chapters for {subject} in Class {student_class} as per the CBSE curriculum."
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None

# Streamlit app interface
st.title("📘 CBSE AI Tutor")

# Input fields for subject and class
subject = st.text_input("Enter the subject (e.g., Mathematics):")
student_class = st.text_input("Enter the class (e.g., 10):")

# Generate chapters when button is clicked
if st.button("Generate Chapters"):
    if subject and student_class:
        chapters = generate_chapters(subject, student_class)
        if chapters:
            st.subheader(f"Chapters for {subject} - Class {student_class}:")
            st.markdown(chapters)
    else:
        st.warning("Please enter both subject and class.")
