import os
import numpy as np

# Try importing RAG-related libraries with fallbacks
try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.vectorstores import FAISS
    from langchain.embeddings import HuggingFaceEmbeddings
    from langchain.docstore.document import Document
    from langchain.chains import RetrievalQA
    from langchain.prompts import PromptTemplate
    from langchain.schema.runnable import RunnablePassthrough, RunnableLambda
    import faiss
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False

    # Define fallback classes if langchain is not available
    class Document:
        def __init__(self, page_content, metadata=None):
            self.page_content = page_content
            self.metadata = metadata or {}

    class PromptTemplate:
        @staticmethod
        def from_template(template):
            def format_prompt(variables):
                result = template
                for key, value in variables.items():
                    result = result.replace("{" + key + "}", str(value))
                return result
            return format_prompt

def create_embeddings():
    """Create embeddings model"""
    if HAS_LANGCHAIN:
        try:
            # Using a lighter model for embeddings to conserve resources
            return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        except Exception as e:
            print(f"Error creating embeddings: {str(e)}")

    # Return a simple mock embeddings class if real embeddings can't be created
    class MockEmbeddings:
        def embed_documents(self, texts):
            # Return mock embeddings (just for demo purposes)
            return [[0.1, 0.2, 0.3] for _ in texts]

        def embed_query(self, text):
            # Return a mock query embedding
            return [0.1, 0.2, 0.3]

    return MockEmbeddings()

def prepare_documents(documents):
    """
    Prepare documents for RAG by splitting and creating a vector store

    Args:
        documents: List of document dictionaries with 'content' field

    Returns:
        FAISS vector store or a simple retriever if FAISS is not available
    """
    if not HAS_LANGCHAIN or not documents:
        # Return a simple mock retriever if we don't have langchain or documents
        class MockRetriever:
            def get_relevant_documents(self, query):
                return []

            def as_retriever(self, search_kwargs=None):
                return self

        return MockRetriever()

    try:
        # Create text splitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

        # Process each document
        all_splits = []
        for doc in documents:
            # Create Document objects with metadata
            doc_content = doc['content']
            doc_name = doc['name']
            doc_type = doc['type']

            # Split text into chunks
            splits = text_splitter.split_text(doc_content)

            # Create Document objects
            for i, split in enumerate(splits):
                doc_obj = Document(
                    page_content=split,
                    metadata={
                        "source": doc_name,
                        "type": doc_type,
                        "chunk": i
                    }
                )
                all_splits.append(doc_obj)

        # Create embeddings
        embeddings = create_embeddings()

        # Create vector store
        vector_store = FAISS.from_documents(all_splits, embeddings)

        return vector_store

    except Exception as e:
        print(f"Error preparing documents: {str(e)}")
        # Return a simple mock retriever on error
        class MockRetriever:
            def get_relevant_documents(self, query):
                return []

            def as_retriever(self, search_kwargs=None):
                return self

        return MockRetriever()

def generate_prompt_from_image_analysis(image_analysis):
    """
    Generate a prompt for the LLM based on image analysis

    Args:
        image_analysis: Dictionary with image analysis results

    Returns:
        str: Prompt text
    """
    prompt = f"""
    Analyze this photography based on the following technical details:

    - Dimensions: {image_analysis['dimensions']}
    - Aspect Ratio: {image_analysis['aspect_ratio']}
    - Brightness: {image_analysis['brightness']}
    - Contrast: {image_analysis['contrast']}
    - Sharpness: {image_analysis['sharpness']}
    - Exposure: {image_analysis['exposure']}
    - Color Balance: {image_analysis['color_balance']}
    - Saturation: {image_analysis['saturation']}
    - Composition: {image_analysis['composition']}
    - Contains Faces: {'Yes' if image_analysis['has_faces'] else 'No'}
    - Number of Faces: {image_analysis['number_of_faces']}
    - Red Channel Average: {image_analysis['red_channel_avg']}
    - Green Channel Average: {image_analysis['green_channel_avg']}
    - Blue Channel Average: {image_analysis['blue_channel_avg']}

    As a photography expert, provide a comprehensive evaluation of this photograph, including:
    1. Overall rating on a scale of 1-5 stars
    2. Technical strengths and weaknesses
    3. Artistic assessment
    4. Specific improvement suggestions
    5. Tips for post-processing

    Format your response with clear sections and be constructive in your feedback.
    """
    return prompt

def format_docs(docs):
    """Format retrieved documents into a single string"""
    return "\n\n".join(doc.page_content for doc in docs)

def generate_rag_response(image_analysis, documents, model):
    """
    Generate RAG response based on image analysis and documents

    Args:
        image_analysis: Dictionary with image analysis results
        documents: List of document dictionaries
        model: LLM model

    Returns:
        str: Generated response
    """
    # Prepare documents for RAG if we have documents
    if documents:
        vector_store = prepare_documents(documents)
        retriever = vector_store.as_retriever(search_kwargs={"k": 3})
    else:
        # If no documents, we'll just use the LLM without retrieval
        retriever = None

    # Generate question from image analysis
    question = generate_prompt_from_image_analysis(image_analysis)

    # Create prompt template for the RAG chain
    template = """
    You are a photography expert and teacher. Use the following photography reference materials to help you
    provide an in-depth analysis and feedback on a student's photograph.

    Reference materials:
    {context}

    Photo analysis task:
    {question}

    Provide your analysis in English, focusing on actionable feedback and specific improvements.
    Be sure to include a clear rating out of 5 stars in your response.
    """

    if HAS_LANGCHAIN:
        prompt = PromptTemplate.from_template(template)
    else:
        # Simple template substitution when LangChain is not available
        def simple_prompt(variables):
            result = template
            for key, value in variables.items():
                result = result.replace("{" + key + "}", str(value))
            return result
        prompt = simple_prompt

    if retriever and HAS_LANGCHAIN:
        # Create RAG chain with retrieval
        rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | model
        )

        # Run the chain
        response = rag_chain.invoke(question)
    elif retriever:
        # Simple fallback when LangChain is not available
        docs = retriever.get_relevant_documents(question)
        context = format_docs(docs)
        formatted_prompt = prompt({"context": context, "question": question})
        response = model.invoke(formatted_prompt)
    else:
        # If no documents, just use the LLM with a simplified prompt
        simplified_prompt = """
        You are a photography expert and teacher. Provide an in-depth analysis 
        and feedback on a student's photograph.

        Photo analysis task:
        {question}

        Provide your analysis in English, focusing on actionable feedback and specific improvements.
        Be sure to include a clear rating out of 5 stars in your response.
        """

        # Format the prompt and invoke the model directly when not using LangChain
        formatted_prompt = simplified_prompt.replace("{question}", question)
        response = model.invoke(formatted_prompt)

    return response