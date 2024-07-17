from langchain_community.document_loaders import UnstructuredExcelLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings.bedrock import BedrockEmbeddings
from langchain.schema.document import Document
from langchain_community.vectorstores.utils import filter_complex_metadata
import boto3


class ProcessExcelDocument:
    def __init__(self, doc_path: str, vector_db_path: str) -> None:
        self.doc_path = doc_path
        self.vector_db_path = vector_db_path
    
    def embed_doc(self) -> bool:
        try:
            # Load the Excel document
            pages = self._load_excel_document()
            # Split the document into chunks
            chunks = self._split_documents(pages)
            # Add the vector to the ChromaDB
            status = self._add_vector_to_chromadb(chunks)
            return status
        except Exception as e:
            print(f"Error embedding document: {e}")
            return False

    def _load_excel_document(self):
        try:
            loader = UnstructuredExcelLoader(
                file_path=self.doc_path,
                mode="elements"
            )
            pages = loader.load()
            return pages
        except Exception as e:
            print(f"Error loading Excel document: {e}")
            return []
    
    def _split_documents(self, pages):
        try:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=800,
                chunk_overlap=80,
                length_function=len,
                is_separator_regex=False
            )
            docs = text_splitter.split_documents(pages)
            return docs
        except Exception as e:
            print(f"Error splitting document: {e}")
            return []

    def _calculate_chunk_ids(self, chunks):
        try:
            last_page_id = None
            current_chunk_index = 0

            for chunk in chunks:
                source = chunk.metadata["source"]
                page = chunk.metadata["page_number"]
                current_page_id = f"{source}:{page}"

                # If the page ID is the same as the last page ID, increment the chunk index
                if last_page_id == current_page_id:
                    current_chunk_index += 1
                else:
                    current_chunk_index = 0
            
                # Calculate the chunk ID
                chunk_id = f"{current_page_id}:{current_chunk_index}"
                last_page_id = current_page_id

                # Add the chunk ID to the chunk metadata
                chunk.metadata['id'] = chunk_id
            return chunks
        except Exception as e:
            print(f"Error calculating chunk IDs: {e}")
            return []
    
    def _add_vector_to_chromadb(self, chunks) -> bool:
        try:
            # Initialize ChromaDB
            db = Chroma(
                embedding_function=self._aws_bedrock_embeddings(),
                persist_directory=self.vector_db_path
            )
            db.persist()
            # Calculate chunk IDs
            chunks = self._calculate_chunk_ids(chunks)
        
            # Add or update the documents
            existing_items = db.get(include=[])
            existing_ids = set(existing_items['ids'])
            
            # Only add documents that don't already exist
            new_chunks = [chunk for chunk in chunks if chunk.metadata["id"] not in existing_ids]
            
            if new_chunks:
                new_chunk_ids = [chunk.metadata["id"] for chunk in new_chunks]
                db.add_documents(filter_complex_metadata(new_chunks), ids=new_chunk_ids)
                db.persist()
            return True
        except Exception as e:
            print(f"Error adding vector to ChromaDB: {e}")
            return False

    def _aws_bedrock_embeddings(self):
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
