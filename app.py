import streamlit as st
from pypdf import PdfReader
import google.generativeai as genai
import requests

# Configure the Gemini and YouTube API keys using Streamlit's secrets
api_key = st.secrets["GOOGLE_API_KEY"]
youtube_api_key =  st.secrets["YOUTUBE_API"]

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-pro')

# Function to extract text from a PDF file
def extract_pdf_text(pdf_file_path):
    pdf_reader = PdfReader(pdf_file_path)
    pdf_text = ""
    for page in pdf_reader.pages:
        pdf_text += page.extract_text() + "\n"
    return pdf_text

# Function to save the uploaded PDF to the local file system
def save_uploaded_file(uploaded_file, file_path):
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

# Function to fetch YouTube video suggestions
def fetch_youtube_videos(query, max_results=5):
    youtube_api_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "key": youtube_api_key,
        "maxResults": max_results,
        "type": "video"
    }
    response = requests.get(youtube_api_url, params=params)
    if response.status_code == 200:
        return response.json().get("items", [])
    else:
        return []

# Streamlit app interface
st.title('Lessstudy: Upload Question Papers')

# Placeholder to store the paths of saved PDFs
pdf_file_paths = []

# Create 5 upload areas for the PDFs
for i in range(1, 6):
    pdf_file = st.file_uploader(f"Upload PDF {i}", type="pdf", key=f"pdf{i}")
    if pdf_file is not None:
        st.success(f'PDF {i} uploaded successfully.')
        # Save the uploaded file to the local file system
        file_path = f"./QuesPap{i}.pdf"
        save_uploaded_file(pdf_file, file_path)
        pdf_file_paths.append(file_path)

# Ensure all 5 PDFs are uploaded before proceeding
if len(pdf_file_paths) == 5:
    st.write("All 5 PDFs uploaded successfully! Extracting text...")

    # Extract text from the uploaded PDFs
    extracted_texts = []
    for idx, pdf_path in enumerate(pdf_file_paths, 1):
        pdf_content = extract_pdf_text(pdf_path)
        extracted_texts.append(f"PDF {idx} Content:\n{pdf_content}")

    # Combine the content from all PDFs
    combined_content = "\n\n".join(extracted_texts)

    # Create the query for Gemini API
    query = f"""
    Please analyze the following content extracted from five PDFs and categorize the questions module-wise.

    Instructions:
    - Identify and mark the questions based on the number of repetitions across the five PDFs.
    - Categorize questions as 'Most repeated' (appears 3 or more times), 'Repeated' (appears 2 times), and 'Unique' (appears only once).
    - Organize the questions by modules.
    - Consider that the questions may not have the exact same wording but might be similar in meaning.

    Content:
    {combined_content}
    """

    # Call the Gemini API to generate the content
    response = model.generate_content(query)
    
    # Display the result
    st.write(response.text)

    # Fetch YouTube video suggestions for "Most Repeated" questions
    most_repeated_section = "Most repeated"  # Extract this section from response.text
    st.subheader("YouTube Suggestions for 'Most Repeated' Questions")
    
    for question in response.text.split("\n"):
        if "Most repeated" in question:
            # Fetch YouTube videos for this question
            youtube_videos = fetch_youtube_videos(question.strip())
            
            if youtube_videos:
                st.write(f"Suggestions for: **{question.strip()}**")
                for video in youtube_videos:
                    video_title = video["snippet"]["title"]
                    video_url = f"https://www.youtube.com/watch?v={video['id']['videoId']}"
                    st.write(f"- [{video_title}]({video_url})")
            else:
                st.write(f"No suggestions found for: **{question.strip()}**")

else:
    st.warning("Please upload all 5 PDFs.")

# Add credits at the bottom of the page
st.markdown("""
    <p style='text-align: center;'>
    Made by <a href="https://www.linkedin.com/in/rohith-borana-b10778266" target="_blank">Rohith Borana</a>
    </p>
    """, unsafe_allow_html=True)
