"""
Answer Generator - Generates answers from retrieved context

Week 3: Simple context-to-prompt builder (no LLM yet)
Week 4+: Add LLM integration for full answer generation
"""

from typing import List, Dict, Optional
import json


class AnswerGenerator:
    """Generates answers from RAG retrieved context."""
    
    def __init__(self, llm_model: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize the answer generator.
        
        Args:
            llm_model: LLM model name (e.g., "gpt-3.5-turbo")
            api_key: API key for LLM service (e.g., OpenAI API key)
        """
        self.llm_model = llm_model
        self.api_key = api_key
        self.llm_client = None
        
        if llm_model and api_key:
            self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize LLM client (Week 5 - updated for newer OpenAI API)."""
        try:
            from openai import OpenAI
            self.llm_client = OpenAI(api_key=self.api_key)
            print(f" Initialized LLM: {self.llm_model}")
        except ImportError:
            print("Note: openai not installed. LLM functionality disabled.")
            self.llm_client = None
        except Exception as e:
            print(f"Note: Failed to initialize LLM: {e}")
            self.llm_client = None
    
    def build_rag_prompt(
        self,
        question: str,
        retrieved_chunks: List[Dict],
        include_sources: bool = True
    ) -> str:
        """
        Build a prompt for the LLM using retrieved context.
        
        Args:
            question: User question
            retrieved_chunks: List of retrieved chunks with metadata
            include_sources: Whether to include source references
        
        Returns:
            Formatted prompt string
        """
        # Extract and format context
        context_parts = []
        sources_used = set()
        
        for i, chunk in enumerate(retrieved_chunks, 1):
            chunk_text = chunk.get("chunk_text", chunk.get("text", ""))
            chunk_id = chunk.get("chunk_id", "unknown")
            page_number = chunk.get("page_number")
            file_name = chunk.get("metadata", {}).get("source", chunk.get("file_name", "unknown"))
            similarity = chunk.get("score", 0)
            
            # Format chunk with source
            if include_sources:
                source_info = f"[Source {i}: {file_name}"
                if page_number:
                    source_info += f", page {page_number}"
                source_info += f", similarity: {similarity:.2f}]"
                context_parts.append(f"{source_info}\n{chunk_text}")
                
                sources_used.add((file_name, page_number, chunk_id))
            else:
                context_parts.append(chunk_text)
        
        # Build the prompt
        context = "\n\n".join(context_parts)
        
        if not context:
            context = "No relevant context provided."
        
        prompt = f"""Answer the question using ONLY the provided context.

If the answer is not present in the context, respond with:
"I do not know based on the provided documents."

Do not make up information or use outside knowledge.

Context:
{context}

Question:
{question}

Answer:"""
        
        return prompt
    
    def generate_answer(
        self,
        question: str,
        retrieved_chunks: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> Dict:
        """
        Generate an answer using LLM (Week 4+).
        
        Args:
            question: User question
            retrieved_chunks: Retrieved context chunks
            temperature: LLM creativity (0.0-1.0)
            max_tokens: Max response length
        
        Returns:
            Dictionary with answer and confidence
        """
        if not self.llm_client:
            # Fallback: return prompt-only version
            prompt = self.build_rag_prompt(question, retrieved_chunks)
            return {
                "answer": None,
                "prompt": prompt,
                "confidence": 0.0,
                "status": "no_llm",
                "model": None
            }
        
        try:
            # Call LLM (Week 5 - updated for newer OpenAI API)
            prompt = self.build_rag_prompt(question, retrieved_chunks)
            
            response = self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions using only the provided context."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            answer = response.choices[0].message.content.strip()
            
            # Estimate confidence based on factors
            confidence = self._estimate_confidence(
                question=question,
                answer=answer,
                retrieved_chunks=retrieved_chunks
            )
            
            return {
                "answer": answer,
                "confidence": confidence,
                "status": "answered",
                "model": self.llm_model,
                "tokens_used": response.usage.total_tokens
            }
            
        except Exception as e:
            return {
                "answer": None,
                "error": str(e),
                "status": "error",
                "model": self.llm_model
            }
    
    def _estimate_confidence(
        self,
        question: str,
        answer: str,
        retrieved_chunks: List[Dict]
    ) -> float:
        """
        Estimate answer confidence based on context quality.

        Args:
            question: User question
            answer: Generated answer
            retrieved_chunks: Retrieved context chunks

        Returns:
            Confidence score (0.0-1.0)
        """
        if not retrieved_chunks:
            return 0.0

        scores = [
            c.get("similarity_score", c.get("score", 0.0))
            for c in retrieved_chunks
        ]
        avg_similarity = sum(scores) / len(scores) if scores else 0.0
        top_similarity = max(scores, default=0.0)
        
        # Check if answer contains "I do not know"
        has_no_answer_phrase = "i do not know" in answer.lower() or "not provided" in answer.lower()
        
        # Combine factors
        base_confidence = avg_similarity
        
        # Reduce confidence if no relevant context was found
        if top_similarity < 0.5:
            base_confidence *= 0.5
        
        # Reduce confidence if LLM indicated it doesn't know
        if has_no_answer_phrase:
            base_confidence *= 0.3
        
        return min(1.0, max(0.0, base_confidence))
    
    def format_response(
        self,
        question: str,
        answer: Optional[str],
        retrieved_chunks: List[Dict],
        status: str = "answered"
    ) -> Dict:
        """
        Format a complete RAG response (Week 5 fix).

        Always returns a non-empty answer field. Citations include optional
        document_external_id / document_db_id for downstream consumers.

        Args:
            question: User question
            answer: Generated answer (or None)
            retrieved_chunks: Retrieved context
            status: Response status

        Returns:
            Formatted response dict matching RAG response contract
        """
        citations = []
        seen_sources = set()

        for chunk in retrieved_chunks:
            chunk_id = chunk.get("chunk_id", chunk.get("id", ""))
            metadata = chunk.get("metadata", {}) or {}
            file_name = (
                chunk.get("file_name")
                or metadata.get("file_name")
                or metadata.get("source")
                or "Unknown"
            )
            page_number = (
                chunk.get("page_number")
                or metadata.get("page_number")
            )
            document_external_id = (
                chunk.get("document_external_id")
                or metadata.get("document_external_id")
            )
            document_db_id = chunk.get("document_db_id") or chunk.get("document_id_fk")

            key = (file_name, page_number, chunk_id)
            if key not in seen_sources and chunk_id:
                seen_sources.add(key)
                citation = {
                    "file_name": file_name,
                    "page_number": page_number,
                    "chunk_id": chunk_id,
                }
                if document_external_id is not None:
                    citation["document_external_id"] = document_external_id
                if document_db_id is not None:
                    citation["document_db_id"] = document_db_id
                citations.append(citation)

        if not answer:
            if not retrieved_chunks:
                answer = "I do not know based on the provided documents."
            else:
                top_text = (
                    retrieved_chunks[0].get("chunk_text")
                    or retrieved_chunks[0].get("text")
                    or ""
                ).strip()
                first_sentence = top_text.split(". ")[0].strip()
                if first_sentence:
                    if not first_sentence.endswith("."):
                        first_sentence += "."
                    answer = first_sentence
                else:
                    answer = "I do not know based on the provided documents."

        response = {
            "question": question,
            "answer": answer,
            "retrieved_context": retrieved_chunks,
            "citations": citations,
            "status": status,
            "model": "all-MiniLM-L6-v2",
            "metadata": {
                "num_chunks_retrieved": len(retrieved_chunks),
                "llm_model": self.llm_model,
            },
        }

        if retrieved_chunks:
            first = retrieved_chunks[0]
            first_meta = first.get("metadata", {}) or {}
            doc_ext_id = (
                first.get("document_external_id")
                or first_meta.get("document_external_id")
            )
            doc_db_id = first.get("document_db_id") or first.get("document_id_fk")
            fname = (
                first.get("file_name")
                or first_meta.get("file_name")
                or first_meta.get("source")
            )
            if doc_ext_id is not None:
                response["document_external_id"] = doc_ext_id
            if doc_db_id is not None:
                response["document_db_id"] = doc_db_id
            if fname is not None:
                response["file_name"] = fname

        return response


def build_rag_prompt(
    question: str,
    retrieved_chunks: List[Dict]
) -> str:
    """
    Functional interface to build a prompt from context.
    
    Args:
        question: User question
        retrieved_chunks: Retrieved context chunks
    
    Returns:
        Formatted prompt string
    """
    generator = AnswerGenerator()
    return generator.build_rag_prompt(question, retrieved_chunks)


def generate_simple_answer(
    question: str,
    retrieved_chunks: List[Dict]
) -> str:
    """
    Generate a simple answer from context without LLM.
    
    Args:
        question: User question
        retrieved_chunks: Retrieved context chunks
    
    Returns:
        Simple answer based on first chunk
    """
    if not retrieved_chunks:
        return "I do not know based on the provided documents."
    
    # Extract answer-like summary from top chunk
    top_chunk = retrieved_chunks[0]
    chunk_text = top_chunk.get("chunk_text", top_chunk.get("text", ""))
    
    # Try to extract first sentence as answer
    sentences = chunk_text.split(". ")
    if sentences:
        return sentences[0] + "."
    
    return chunk_text[:200] + "..."


if __name__ == "__main__":
    print("=== Testing AnswerGenerator ===\n")
    
    # Test prompt building
    print("Building RAG prompt...")
    
    sample_chunks = [
        {
            "chunk_id": "doc_001_page_1_chunk_000",
            "chunk_text": "Machine learning is a field of artificial intelligence that uses statistical techniques.",
            "file_name": "guide.pdf",
            "page_number": 1,
            "score": 0.87,
            "metadata": {"source": "guide.pdf"}
        },
        {
            "chunk_id": "doc_001_page_1_chunk_001",
            "chunk_text": "Deep learning uses neural networks with multiple layers.",
            "file_name": "guide.pdf",
            "page_number": 1,
            "score": 0.82,
            "metadata": {"source": "guide.pdf"}
        }
    ]
    
    generator = AnswerGenerator()
    
    prompt = generator.build_rag_prompt("What is machine learning?", sample_chunks)
    print(f"Generated prompt:\n{prompt}\n")
    
    # Test simple answer generation
    print("Generating simple answer...")
    simple_answer = generate_simple_answer("What is machine learning?", sample_chunks)
    print(f"Simple answer: {simple_answer}\n")
    
    # Test response formatting
    print("Formatting response...")
    response = generator.format_response(
        question="What is machine learning?",
        answer=simple_answer,
        retrieved_chunks=sample_chunks,
        status="answered"
    )
    print(f"Response structure:")
    print(f"  Question: {response['question']}")
    print(f"  Answer: {response['answer']}")
    print(f"  Citations: {len(response['citations'])} sources")
    print(f"  Status: {response['status']}")
