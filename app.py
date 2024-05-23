import os
import streamlit as st
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from io import BytesIO
import numpy as np
from PIL import Image, ImageDraw
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

def word_cloud(word_list):
    wordcloud = WordCloud(width=1200, height=800, background_color='white', colormap='viridis', random_state=42).generate(word_list)
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
        image_buf = word_cloud(summary)
        st.image(image_buf, use_column_width=True)
        st.write(summary)

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
    border-radius: 10px;
    background-color: #f1f1f1;
    transition: background-color 1s ease, color 1s ease;
    overflow-y: auto;
    height: 400px;
    border: 0px solid #ccc;
}
.chat-box:hover {
    background-color: #A7F5A4; /* Darker Green */
    color: black;
}
.message {
    padding: 10px;
    margin: 10px 0;
    border-radius: 10px;
    
}
.user-message {
    background-color: #dcf8c6;
    text-align: right;
}
.bot-message {
    background-color: #fff;
    text-align: left;
}
.button {
    background-color: #4CAF50; /* Green */
    border: none;
    color: white;
    padding: 15px 32px;
    text-align: center;
    text-decoration: none;
    display: inline-block;
    font-size: 16px;
    margin: 4px 2px;
    transition-duration: 0.4s;
    cursor: pointer;
    border-radius: 8px;
}
.button:hover {
    background-color: #45a049; /* Darker Green */
    color: white;
}
</style>
"""

# Display chat interface
st.markdown(chat_css, unsafe_allow_html=True)
st.markdown("#### Ask Me")



# Display the chat history
chat_history_str = '<div class="chat-box">'
for message in st.session_state.chat_history:
    if message["role"] == "user":
        chat_history_str += f'<div class="message user-message"><b>You:</b> {message["text"]}</div>'
    else:
        chat_history_str += f'<div class="message bot-message"><b>Bot:</b> {message["text"]}</div>'
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
        st.session_state.chat_history.append({"role": "bot", "text": chunk.text})
    st.session_state.input_key += 1

    st.rerun()
