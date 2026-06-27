import streamlit as st
import time
import google.generativeai as genai
from pypdf import PdfReader
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr
from pydub import AudioSegment
import pandas as pd
from fpdf import FPDF

def clean_text(text):
    replacements = {
        "–": "-",
        "—": "-",
        "•": "*",
        "✓": "[OK]",
        "✗": "[X]",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "…": "...",
        "→": "->"
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text.encode("latin-1", "replace").decode("latin-1")


def create_pdf_report():

    pdf = FPDF()

    pdf.add_page()

    pdf.set_font("Arial", "B", 16)

    pdf.cell(
        200,
        10,
        txt="AI Interview Report",
        ln=True,
        align="C"
    )

    pdf.ln(10)

    pdf.set_font("Arial", size=12)

    for i in range(
        min(
            len(st.session_state.answers),
            len(st.session_state.feedbacks)
        )
    ):

        pdf.multi_cell(
            0,
            10,
            clean_text(
                f"Question {i+1}: "
        f"      {st.session_state.questions[i]}"
            )
        )

        pdf.multi_cell(
            0,
            10,
            clean_text(
                f"Answer: "
                f"{st.session_state.answers[i]}"
            )
        )

        pdf.multi_cell(
            0,
            10,
            clean_text(
                f"Evaluation: "
                f"{st.session_state.feedbacks[i]}"
            )
        )

        pdf.ln(5)

    pdf.multi_cell(
        0,
        10,
        clean_text(
            f"Final Result:\n"
            f"{st.session_state.final_result}"
        )
    )

    pdf.output("Interview_Report.pdf")
# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(page_title="AI Interview Coach")

st.title("🎤 AI Interview Coach")
st.caption("Upload your resume and start a mock interview")

# -----------------------------
# Session State
# -----------------------------
if "questions" not in st.session_state:
    st.session_state.questions = []

if "current_question" not in st.session_state:
    st.session_state.current_question = 0

if "answers" not in st.session_state:
    st.session_state.answers = []

if "feedbacks" not in st.session_state:
    st.session_state.feedbacks = []
if "scores" not in st.session_state:
    st.session_state.scores = []
if "final_result" not in st.session_state:
    st.session_state.final_result = ""
if "voice_text" not in st.session_state:
    st.session_state.voice_text = ""

# -----------------------------
# API Key
# -----------------------------
api_key = st.sidebar.text_input(
    "Enter Gemini API Key",
    type="password"
)

# -----------------------------
# Upload Resume
# -----------------------------
uploaded_file = st.file_uploader(
    "Upload Resume PDF",
    type="pdf"
)

if uploaded_file:

    pdf_reader = PdfReader(uploaded_file)

    resume_text = ""

    for page in pdf_reader.pages:

        page_text = page.extract_text()

        if page_text:
            resume_text += page_text

    st.success("✅ Resume uploaded successfully")

    # Resume Stats
    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Characters",
            len(resume_text)
        )

    with col2:
        st.metric(
            "Words",
            len(resume_text.split())
        )

    # Preview
    st.subheader("📄 Resume Preview")

    st.text_area(
        "Extracted Text",
        resume_text[:2000],
        height=300
    )

    # -----------------------------
    # Generate Questions
    # -----------------------------
    if api_key:

        genai.configure(api_key=api_key)

        if st.button("🎤 Start Interview"):
            st.session_state.scores =[]
            st.session_state.answers =[]
            st.session_state.feedbacks=[]

            prompt = f"""
            You are an experienced HR and Technical Interviewer.

            Analyze the resume.

            Generate exactly 5 interview questions.

            Rules:
            - Mix HR and Technical questions.
            - Questions should be based on skills.
            - Questions should be based on projects.
            - Return only questions.
            - One question per line.

            Resume:
            {resume_text}
            """

            model = genai.GenerativeModel(
                "gemini-2.5-flash"
            )

            with st.spinner(
                "Generating Interview Questions..."
            ):
                time.sleep(15)
                response = model.generate_content(
                    prompt
                )

            questions = [
                q.strip()
                for q in response.text.split("\n")
                if q.strip()
            ]

            st.session_state.questions = questions
            st.session_state.current_question = 0
            st.session_state.answers = []
            st.session_state.feedbacks=[]
            st.session_state.voice_text = ""
            st.rerun()

    # -----------------------------
    # Interview Section
    # -----------------------------
    if len(st.session_state.questions) > 0:

        current_index = st.session_state.current_question
        progress = current_index/len(st.session_state.questions)
        st.progress(progress)
        st.write(
            f"Question{current_index + 1} of"
            f"{len(st.session_state.questions)}"
        )
        if len(st.session_state.feedbacks) > 0:
            st.subheader("📊 Previous Answer Evaluation")
            st.write(st.session_state.feedbacks[-1])

        # Questions Remaining
        if current_index < len(
            st.session_state.questions
        ):

            st.subheader(
                f"Question {current_index + 1}"
            )

            st.write(
                st.session_state.questions[
                    current_index
                ]
            )

            voice_text = ""
            audio = mic_recorder(
                start_prompt = "🎤 Start Recording",
                stop_prompt="⏹️ Stop Recording",
                key=f"recorder_{current_index}"
            )
            if audio:
                st.success("Voice Recoreded Successfully")
                with open("temp.webm", "wb") as f:
                    f.write(audio["bytes"])
                audio_segment = AudioSegment.from_file("temp.webm")
                audio_segment.export("answer.wav", format = "wav")
                st.audio("answer.wav")
                recognizer = sr.Recognizer()
                
                try:
                    with sr.AudioFile("answer.wav") as source:
                        audio_data = recognizer.record(source)
                        speech_text = recognizer.recognize_google(
                        audio_data)
                        st.session_state.voice_text = speech_text
                        text_key= f"answer_{current_index}"
                        st.session_state[text_key]= speech_text
                        
                    st.success(
                        "✅ Speech Converted Successfully"
                    )
                    st.write("### Transcribed Answer")
                    st.write(speech_text)
                except Exception as e:
                    st.error(
                         f"Error: {e}"
                    )
            text_key = f"answer_{current_index}" 
            if text_key not in st.session_state:
                st.session_state[text_key] = ""
            user_answer = st.text_area(
                "your answer",
                key = text_key
            )

            if st.button(
                "Submit Answer"
            ):
                
                question = st.session_state.questions[
                    current_index
                ]
                evaluation_prompt = f"""
                you are an expert insterviewr.

                Question:
                {question}

                Candidate Answer:
                {user_answer}

                Evaluate the answer.
                Give:
                Score = X/10
                Feedback:
                Brief explanation of strengths and improvements. 
                """
                model = genai.GenerativeModel("gemini-2.5-flash")

                with st.spinner("Evaluating answer..."):
                     time.sleep(15)
                     evalution = model.generate_content(
                        evaluation_prompt
                     )

                st.session_state.answers.append(
                    user_answer
                )

                st.session_state.feedbacks.append(
                    evalution.text
                )
                import re 
                score_match = re.search(
                    r'(\d+)/10',
                    evalution.text
                )
                if score_match:
                    score = int(score_match.group(1))
                else:
                    score =0 
                st.session_state.scores.append(score)
                

                st.session_state.current_question += 1
                st.session_state.voice_text = ""

                st.rerun()

        # Interview Complete
        else:

            st.success(
                "🎉 Interview Completed!"
            )
            st.subheader("📊 Performance Dashboard")
            total_score = sum(st.session_state.scores)

            if len(st.session_state.scores)>0:
                average_score = total_score/len(st.session_state.scores)
            else:
                average_score=0

            col1, col2 = st.columns(2)

            with col1:
                st.metric("Total Score",
                          f"{total_score}/50")
            with col2:
                st.metric("Average Score", f"{average_score: .1f}/10")

            chart_data = pd.DataFrame(
                {
                    "Question": [
                        f"Q{i+1}"
                        for i in range(len(st.session_state.scores))
                    ],
                    "Score":
                    st.session_state.scores
                }
            )
            st.line_chart(
                chart_data.set_index("Question")
            )
            high_scores = [
                i+1
                for i,s in enumerate(st.session_state.scores)
                if s >=8
            ]
            low_scores = [
                i+1
                for i, s in enumerate(st.session_state.scores)
                if s<6
            ]
            st.subheader("🟢 Strengths")
            if high_scores:
                st.write(
                    f"Strong performance in questions{high_scores}"
                )
            else:
                st.write("No strong areas identified")
            st.subheader("🔴 Areas To Improve")

            if low_scores:
                st.write(f"Needs imporemnt in question{low_scores}")
            else:
                st.write("No major weaknesses.")

            st.subheader(
                "📋 Interview Report"
            )
            if st.session_state.final_result == "":
                report_prompt = f"""
                You are a hiring manager.

                Interview Questions:
                {st.session_state.questions}

                Candidate answers:
                {st.session_state.answers}

                Evaluate the overall interview.
                Provide 
                Total score out of 50

                Selection Decision:

                Improvement suggestions.
                """
                model = genai.GenerativeModel("gemini-2.5-flash")

                with st.spinner(
                    "Generating final result"
                ):
                    time.sleep(15)
                    result = model.generate_content(
                        report_prompt
                    )
                    st.session_state.final_result=(
                        result.text
                    )
                st.subheader("🏆 Final Hiring Decision")
                st.write( st.session_state.final_result)
                create_pdf_report()
                with open(
                    "Interview_Report.pdf",
                    "rb"
                    ) as pdf_file:

                    st.download_button(
                    label="📄 Download Report",
                    data=pdf_file,
                    file_name="Interview_Report.pdf",
                    mime="application/pdf"
                        )


            for i in range(
                min(
                len(st.session_state.answers),
                len(st.session_state.feedbacks)
                    )
                    ):

                        st.write(
                            f"### Question {i+1}"
                        )

                        st.write(
                            st.session_state.questions[i]
                        )

                        st.write("**Your Answer:**")
                        st.write(
                            st.session_state.answers[i]
                        )

                        st.write("**Evaluation:**")
                        st.write(
                            st.session_state.feedbacks[i]
                        )

                        st.markdown("---")

else:

    st.info(
        "Please upload a resume PDF."
    )