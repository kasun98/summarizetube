import os
import streamlit as st
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
from io import BytesIO
import numpy as np
import PIL
from PIL import Image, ImageDraw
import base64
from dotenv import load_dotenv

load_dotenv()

import google.generativeai as genai
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

from youtube_transcript_api import YouTubeTranscriptApi



prompt="""I have a YouTube video transcript that I need summarized with the key points highlighted. Please provide a concise and informative summary that captures the main ideas and important details from the transcript within 250 words. Make sure to include the following:

Title and Subject: What is the video about?
Introduction: Briefly describe the introduction of the video.
Main Points: List the key points discussed in the video in a clear and structured manner.
Important Details: Mention any significant details, facts, or examples that are emphasized.
Conclusion: Summarize how the video wraps up its content.
Make the summary engaging and easy to understand, suitable for viewers who want a quick overview of the video's content. 
The transcript is: """


## getting the transcript data from youtube
def extract_transcript_details(youtube_video_url):
    try:
        video_id=youtube_video_url.split("=")[1]
        
        transcript_text=YouTubeTranscriptApi.get_transcript(video_id)

        transcript = ""
        for i in transcript_text:
            transcript += " " + i["text"]

        return transcript

    except Exception as e:
        raise e

model=genai.GenerativeModel("gemini-pro")

## getting the summary based on Prompt from Google Gemini Pro
def generate_gemini_content(transcript_text,prompt):
    response=model.generate_content(prompt+transcript_text)
    return response.text

wc_mask = np.array(PIL.Image.open('ytb.png'))


def word_cloud(word_list):
    wordcloud = WordCloud(stopwords=STOPWORDS, mask=wc_mask, width=1200, height=800, background_color='white', colormap='viridis', random_state=42).generate(word_list)
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)
    return buf


chat = model.start_chat(history=[])

def get_gemini_response(question):
    response=chat.send_message(question,stream=True)
    return response

title_html = """
<div style="display: flex; align-items: center; justify-content: center;">
    <h1>Summarize<span style="color: red;">Tube</span></h1>
</div>
"""

# Display the custom HTML title
st.markdown(title_html, unsafe_allow_html=True)

# Additional text above the input box
st.markdown("### Enter the YouTube video link below to get a summary")
youtube_link = st.text_input("Example input https://www.youtube.com/watch?v=VIDEOID")

if youtube_link:
    video_id = youtube_link.split("=")[1]
    st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", width=400)

if st.button("Summarize"):
    transcript_text=extract_transcript_details(youtube_link)

    if transcript_text:
        summary=generate_gemini_content(transcript_text,prompt)
        st.markdown("### Summary of the video:")
        image_buf = word_cloud(transcript_text)
        st.image(image_buf, use_column_width=True)
        st.write(summary)

st.markdown("<br><br>", unsafe_allow_html=True)

# Initialize session state for chat history if not already done
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'input_key' not in st.session_state:
    st.session_state.input_key = 0

# Define CSS for chat interface
chat_css = """
<style>
.chat-box {
    max-width: 700px;
    margin: auto;
    padding: 10px;
    border-radius: 15px;
    background-color: #ffffff;
    transition: background-color 1s ease, color 1s ease;
    overflow-y: auto;
    height: 300px;
    border: 0px solid #ccc;
}

.message {
    padding: 10px;
    margin: 10px 0;
    border-radius: 15px;
    
}

.user-message {
    background-color: #dcf8c6;
    transition: background-color 1s ease, color 1s ease;
    text-align: right;
    border-radius: 15px;
}
.user-message:hover {
    background-color: #ABEBC6; /* Darker Green */
    color: black;
}
.bot-message {
    background-color: #FDEDEC;
    transition: background-color 1s ease, color 1s ease;
    text-align: left;
}
.bot-message:hover {
    background-color: #F5B7B1 ; /* Darker Green */
    color: black;
}

</style>
"""

# Display chat interface
st.markdown(chat_css, unsafe_allow_html=True)
# Main content inside a transparent box with a border
st.markdown("""
<div class="transparent-box" style="
    border: 1px solid #ccc; 
    border-radius: 15px; 
    padding: 10px; 
    background-color: rgba(255, 255, 255, 0.5);
">
    <h4 style="text-align: center;">Ask from AI Bot</h4>
""", unsafe_allow_html=True)

# Display the chat history
chat_history_str = '<div class="chat-box" style="max-height: 300px; overflow-y: auto;">'
for message in st.session_state.chat_history:
    if message["role"] == "user":
        chat_history_str += f'<div class="message user-message" style="margin-bottom: 10px;"><b>You:</b> {message["text"]}</div>'
    else:
        chat_history_str += f'<div class="message bot-message" style="margin-bottom: 10px;"><b>Bot:</b> {message["text"]}</div>'
chat_history_str += '</div>'
st.markdown(chat_history_str, unsafe_allow_html=True)

# Text input for user query
inp = st.text_input("Message", key=f"input_{st.session_state.input_key}")
submit = st.button("Send")

if submit and inp:
    # Get response from the model
    response = get_gemini_response(inp)
    
    # Add user query and model response to the chat history
    st.session_state.chat_history.append({"role": "user", "text": inp})
    for chunk in response:
        chunk_text = chunk.text
    st.session_state.chat_history.append({"role": "bot", "text": chunk_text})
    
    st.session_state.input_key += 1
    st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

# Footer HTML and CSS
footer_html = """
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #f1f1f1;
        transition: background-color 2s ease, color 2s ease;
        color: #000;
        text-align: center;
        padding: 7px;
        font-size: 14px;
        border-top: 0px solid #e1e1e1;
    }
    .footer:hover {
        background-color: #000000 ; 
        color: white;
    }
    </style>
    <div class="footer">
        <p>© 2024 SummarizeTube | <a href="https://github.com/kasun98/summarizetube" target="_blank">GitHub</a></p>
    </div>
    """

# Inject the footer HTML and CSS into the Streamlit app
st.markdown(footer_html, unsafe_allow_html=True)
