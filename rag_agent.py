from typing import Dict, List
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import BaseMessage
import numpy as np
from vector_store import VectorStore

class RAGAgent:
    def __init__(self, vector_store: VectorStore, llm: ChatOpenAI):
        self.vector_store = vector_store
        self.llm = llm
        
    def retrieve(self, query: str, k: int = 5) -> List[Dict]:
        """Retrieve relevant documents based on query."""
        # Convert query to embedding using the same model as data ingestion
        query_embedding = self.llm.get_embedding(query)
        
        # Search vector store
        results = self.vector_store.search(query_embedding, k=k)
        return results
        
    def generate_context(self, retrieved_docs: List[Dict]) -> str:
        """Generate a structured context from retrieved documents."""
        context = []
        for i, doc in enumerate(retrieved_docs, 1):
            motion_data = doc.get('document', {})
            context.append(
                f"Motion Pattern {i}:\n"
                f"- Position: Pitch={motion_data['pos']['pitch']:.2f}, "
                f"Roll={motion_data['pos']['roll']:.2f}, "
                f"Yaw={motion_data['pos']['yaw']:.2f}\n"
                f"- Movement: X={motion_data['gyro']['x']:.2f}, "
                f"Y={motion_data['gyro']['y']:.2f}, "
                f"Z={motion_data['gyro']['z']:.2f}\n"
            )
        return "\n".join(context)
        
    def analyze(self, query: str, context: str) -> Dict:
        """Analyze the context and generate insights."""
        template = """You are an AI expert in analyzing IMU motion data.
        Based on the following motion patterns:
        {context}
        
        Answer the following query: {query}
        
        Provide your analysis in the following format:
        1. Key Observations:
           - List key patterns and anomalies
        2. Insights:
           - Detailed interpretation of the motion data
        3. Recommendations:
           - Actionable suggestions based on the analysis"""
        
        prompt = ChatPromptTemplate.from_template(template)
        messages = prompt.format_messages(context=context, query=query)
        response = self.llm.invoke(messages)
        
        return {
            "analysis": response.content,
            "source_data": context
        }
        
    def execute_rag_workflow(self, query: str) -> Dict:
        """Execute the full RAG workflow."""
        # Step 1: Retrieve relevant documents
        retrieved_docs = self.retrieve(query)
        
        # Step 2: Generate context
        context = self.generate_context(retrieved_docs)
        
        # Step 3: Analyze and generate response
        result = self.analyze(query, context)
        
        return result

class QueryPlanner:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        
    def decompose_query(self, query: str) -> List[str]:
        """Decompose complex queries into simpler sub-queries."""
        template = """You are a Query Planner AI responsible for retrieving the most relevant information from a vector store. Based on the following user query:

{query}

1. Break down the query into specific sub-questions to retrieve focused results.
2. Ensure each sub-question is aligned with the context of the user's motion data and the task requirements.
3. Return a list of structured queries optimized for retrieving embeddings and documents from the vector store.

Respond in the following format:
- **Main Query**: [Restated Main Query]
- **Sub-Queries**:
  1. [Sub-Query 1]
  2. [Sub-Query 2]
  3. [Sub-Query 3]
- **Additional Notes**:"""
        
        prompt = ChatPromptTemplate.from_template(template)
        messages = prompt.format_messages(query=query)
        response = self.llm.invoke(messages)
        
        # Extract sub-queries from the response
        sub_queries = []
        lines = response.content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('  1.') or line.startswith('  2.') or line.startswith('  3.'):
                # Remove the number and brackets
                query = line.split('.', 1)[1].strip()
                query = query.strip('[]')
                sub_queries.append(query)
        
        return sub_queries
        
    def synthesize_results(self, sub_results: List[Dict]) -> Dict:
        """Synthesize results from multiple sub-queries."""
        template = """Synthesize the following analysis results into a coherent response:
        
        {results}
        
        Provide a unified analysis that combines all insights."""
        
        # Format sub-results
        formatted_results = "\n\n".join([
            f"Analysis {i+1}:\n{result['analysis']}"
            for i, result in enumerate(sub_results)
        ])
        
        prompt = ChatPromptTemplate.from_template(template)
        messages = prompt.format_messages(results=formatted_results)
        response = self.llm.invoke(messages)
        
        return {
            "synthesized_analysis": response.content,
            "sub_results": sub_results
        }
