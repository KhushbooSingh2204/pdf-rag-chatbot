import streamlit as st
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_classic.chains.question_answering import load_qa_chain
from langchain_google_genai import ChatGoogleGenerativeAI

st.set_page_config(page_title="PDF Q&A Bot")

st.title("📄 Intelligent PDF Assistant")
st.caption(
    "RAG-powered document question answering using Gemini, LangChain and FAISS"
)

google_api_key = st.sidebar.text_input(
    "Enter Gemini API Key",
    type="password"
)
st.sidebar.header("About")

st.sidebar.info(
    """
    Upload a PDF and ask questions about its contents.

    Technologies:
    - Gemini 2.5 Flash
    - LangChain
    - FAISS
    - HuggingFace Embeddings
    - Streamlit
    """
)

uploaded_file = st.file_uploader(
    "Upload PDF",
    type="pdf"
)

if uploaded_file and google_api_key:

    # Read PDF
    pdf_reader = PdfReader(uploaded_file)

    text = ""

    for page in pdf_reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text

    with st.expander("Preview Document Text"):
        st.write(text[:1500])


    # Split Text
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    chunks = splitter.split_text(text)

    st.write(f"Number of chunks: {len(chunks)}")

    with st.expander("Preview First Chunk"):
        st.write(chunks[0])
  
    st.metric("Chunks Created", len(chunks))
    st.metric("Characters", len(text))

    # Create Embeddings
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    # Create Vector Store
    with st.spinner("Creating vector database..."):
        vector_store = FAISS.from_texts(
            texts=chunks,
            embedding=embeddings
        )

    st.success("✅ Vector database created")

    # Question Input
  
    question = st.text_input(
    "Ask a question from the PDF"
    )

    ask_button = st.button("🔍 Get Answer")

    if ask_button and question:

        docs = vector_store.similarity_search(
            question,
            k=3
        )

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=google_api_key,
            temperature=0.3
        )

        chain = load_qa_chain(
            llm,
            chain_type="stuff"
        )
        with st.spinner("Gemini is analyzing the document..."):
            response = chain.run(
                input_documents=docs,
                question=question
            )

        st.subheader("🤖 Answer")
        st.write(response)

st.markdown("---")
st.caption(
    "Built with Gemini, LangChain, FAISS, HuggingFace Embeddings and Streamlit"
)