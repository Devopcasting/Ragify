from flask import Blueprint, render_template, flash, request
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings.bedrock import BedrockEmbeddings
from langchain.prompts import ChatPromptTemplate
from langchain_community.llms.ollama import Ollama
from app import app
from app.query.forms import AskQueryForm
import boto3
import os

# Create a Blueprint instance for the 'query' module
query_route = Blueprint('query', __name__, template_folder='templates')

# Vector database path
VECTOR_DB_PATH = os.path.join(app.root_path, 'static', 'vectordb')
os.makedirs(VECTOR_DB_PATH, exist_ok=True)

# Route for handling the query form
@query_route.route('/query', methods=['GET', 'POST'])
def query():
    form = AskQueryForm()
    PROMPT_TEMPLATE = """
Answer based on the following search results: {context}

Here is the user's question: {question}
"""
    formated_response = ""
    source_list = []

    if form.validate_on_submit():  
        try:
            # Initialize Bedrock embeddings
            bedrock_embeddings = _aws_bedrock_embeddings()

            # Query the document
            db = Chroma(
                embedding_function=bedrock_embeddings,
                persist_directory=VECTOR_DB_PATH
            )

            # Similarity search
            result = db.similarity_search_with_score(form.query.data, k=5)

            # Context text
            context_text = "\n\n---\n\n".join([doc.page_content for doc, _ in result])

            # Prompt template
            prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
            prompt = prompt_template.format_messages(context=context_text, question=form.query.data)

            # LLM Model
            model = Ollama(model="mistral")

            # Get Response
            response_text = model.invoke(prompt)
            source = [doc.metadata.get("id", None) for doc, _ in result]

            # Format sources for display
            if source:
                for i in source:
                    source_dict = {}
                    doc_name = i.split(':')[0].split("/")[-1]
                    page_num = i.split(":")[1]
                    source_dict["doc"] = doc_name
                    source_dict["page"] = page_num
                    source_list.append(source_dict)

            formated_response = response_text
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'danger')

    return render_template('query/query.html', title='Query', form=form, response=formated_response, source=source_list)

def _aws_bedrock_embeddings():
    # Initialize BedrockEmbeddings
    bedrock_client = boto3.client(
        service_name='bedrock-runtime',
        region_name='us-east-1'
    )
    aws_bedrock_embeddings = BedrockEmbeddings(
        credentials_profile_name="default",
        region_name="us-east-1",
        model_id="amazon.titan-embed-text-v1",
        client=bedrock_client
    )
    return aws_bedrock_embeddings
