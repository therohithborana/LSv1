import streamlit as st
from pypdf import PdfReader
import google.generativeai as genai
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os

# Configure the Gemini API key using Streamlit's secrets
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Initialize the Gemini model
model = genai.GenerativeModel('gemini-pro')

# YouTube API setup
YOUTUBE_API_KEY = st.secrets["YOUTUBE_API_KEY"]  # Add this to your Streamlit secrets
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

def extract_pdf_text(pdf_file_path):
    try:
        pdf_reader = PdfReader(pdf_file_path)
        pdf_text = ""
        for page in pdf_reader.pages:
            pdf_text += page.extract_text() + "\n"
        return pdf_text
    except Exception as e:
        st.error(f"Error extracting text from PDF: {str(e)}")
        return None

def save_uploaded_file(uploaded_file, file_path):
    try:
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return file_path
    except Exception as e:
        st.error(f"Error saving file: {str(e)}")
        return None

def search_youtube_videos(query, max_results=3):
    try:
        search_response = youtube.search().list(
            q=query,
            part='snippet',
            maxResults=max_results,
            type='video',
            relevanceLanguage='en',
            order='relevance'
        ).execute()

        videos = []
        for item in search_response['items']:
            video = {
                'title': item['snippet']['title'],
                'videoId': item['id']['videoId'],
                'thumbnail': item['snippet']['thumbnails']['medium']['url'],
                'description': item['snippet']['description']
            }
            videos.append(video)
        return videos
    except HttpError as e:
        st.error(f"Error searching YouTube: {str(e)}")
        return []

def analyze_papers(texts):
    combined_content = "\n\n".join([f"PDF {idx + 1} Content:\n{text}" for idx, text in enumerate(texts)])

    query = f"""
    Analyze the following content from PDF question papers and provide:
    1. Module-wise categorization of questions
    2. Identification of repeated questions (mark frequency in brackets)
    3. Key topics that students should focus on
    4. Generate 3 specific YouTube search queries for the most important topics

    Content:
    {combined_content}

    Format the response in clear sections with headers.
    For YouTube queries, provide them in a separate section titled 'YOUTUBE_QUERIES:' with one query per line.
    """

    try:
        response = model.generate_content(query)
        return response.text
    except Exception as e:
        st.error(f"Error analyzing papers: {str(e)}")
        return None

# Streamlit UI
st.title('📚 LessStudy: Smart Question Paper Analyzer')

st.markdown("""
    ### How to use:
    1. Upload at least 2 question papers (up to 5)
    2. Get AI-powered analysis of question patterns
    3. Watch recommended YouTube videos for important topics
    """)

# Create a container for file uploaders
with st.container():
    st.subheader("Upload Question Papers")
    uploaded_files = []

    # Create 5 upload areas
    cols = st.columns(5)
    for i in range(5):
        with cols[i]:
            uploaded_file = st.file_uploader(f"PDF {i+1}", type="pdf", key=f"pdf{i}")
            if uploaded_file:
                uploaded_files.append(uploaded_file)

    if len(uploaded_files) < 2:
        st.warning("Please upload at least 2 PDF files to proceed.")
    else:
        st.success(f"{len(uploaded_files)} PDFs uploaded successfully!")

# Analysis button
if len(uploaded_files) >= 2:
    if st.button("Analyze Papers", type="primary"):
        with st.spinner("Processing PDFs and analyzing patterns..."):
            # Save and extract text from PDFs
            pdf_texts = []
            for idx, uploaded_file in enumerate(uploaded_files):
                file_path = f"./QuesPap{idx+1}.pdf"
                if save_uploaded_file(uploaded_file, file_path):
                    text = extract_pdf_text(file_path)
                    if text:
                        pdf_texts.append(text)
                    # Clean up the temporary file
                    os.remove(file_path)

            if pdf_texts:
                # Analyze the papers
                analysis_result = analyze_papers(pdf_texts)

                if analysis_result:
                    # Split the analysis to separate YouTube queries
                    parts = analysis_result.split("YOUTUBE_QUERIES:")

                    # Display the main analysis
                    st.markdown("### 📊 Analysis Results")
                    st.markdown(parts[0])

                    # Handle YouTube recommendations
                    if len(parts) > 1:
                        st.markdown("### 🎥 Recommended Videos")
                        queries = parts[1].strip().split('\n')

                        # Create tabs for different topics
                        topic_tabs = st.tabs([f"Topic {i+1}" for i in range(len(queries))])

                        for tab, query in zip(topic_tabs, queries):
                            with tab:
                                videos = search_youtube_videos(query.strip())
                                for video in videos:
                                    col1, col2 = st.columns([1, 2])
                                    with col1:
                                        st.image(video['thumbnail'])
                                    with col2:
                                        st.markdown(f"**{video['title']}**")
                                        st.markdown(f"Watch: https://youtube.com/watch?v={video['videoId']}")
                                        with st.expander("Description"):
                                            st.write(video['description'])

# Footer
st.markdown("""
    ---
    <p style='text-align: center;'>
    Made by <a href="https://www.linkedin.com/in/rohith-borana-b10778266" target="_blank">Rohith Borana</a>
    </p>
    """, unsafe_allow_html=True)
