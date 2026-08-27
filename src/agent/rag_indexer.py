import os
import logging
from langchain_text_splitters import MarkdownTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
class KnowledgeIndexer:
    def __init__(self,persist_directory="data/chroma_db"):
        self.persist_directory=persist_directory
        self.embeddings=HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vector_store=Chroma(collection_name="textile_knowledge",embedding_function=self.embeddings,persist_directory=self.persist_directory)
    def _parse_frontmatter(self,text):
        metadata={}
        content=text
        if text.startswith("---"):
            parts=text.split("---",2)
            if len(parts)>=3:
                frontmatter=parts[1]
                content=parts[2]
                for line in frontmatter.strip().split("\n"):
                    if ":" in line:
                        k,v=line.split(":",1)
                        metadata[k.strip()]=v.strip()
        return metadata,content.strip()
    def index_directory(self,docs_dir):
        if not os.path.exists(docs_dir):
            return
        documents=[]
        for filename in os.listdir(docs_dir):
            if filename.endswith(".md"):
                filepath=os.path.join(docs_dir,filename)
                with open(filepath,"r",encoding="utf-8") as f:
                    text=f.read()
                metadata,content=self._parse_frontmatter(text)
                metadata["filename"]=filename
                splitter=MarkdownTextSplitter(chunk_size=500,chunk_overlap=50)
                chunks=splitter.split_text(content)
                for chunk in chunks:
                    documents.append(Document(page_content=chunk,metadata=metadata))
        if documents:
            self.vector_store.add_documents(documents)
if __name__=="__main__":
    KnowledgeIndexer().index_directory("data/knowledge/raw")
