"""
RAG Agent
Main RAG agent with chat memory, prompt assembly, and generation.
Uses DeepSeek-R1 with streaming, falls back to Gemini Flash.
"""

import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
import httpx
import google.generativeai as genai
import uuid

from ..common import logger, config, storage
from .retriever_agent import RetrieverAgent, RetrievalResult
from .reranker_agent import RerankerAgent
from .decomposition_agent import DecompositionAgent
from .metadata_filter_agent import MetadataFilterAgent


class RAGAgent:
    """
    Main RAG agent orchestrating retrieval, reranking, and generation.
    """
    
    def __init__(self):
        self.ollama_host = config.ollama_host
        self.primary_model = self._parse_model_name(config.llm_primary)
        self.fallback_model = config.llm_fallback
        
        # Initialize sub-agents
        self.retriever = RetrieverAgent()
        self.reranker = RerankerAgent()
        self.decomposer = DecompositionAgent()
        self.filter_agent = MetadataFilterAgent()
        
        # Configure Gemini
        keys = config.get_gemini_keys()
        if keys:
            genai.configure(api_key=keys[0])
        
        self.system_prompt = """You are a helpful AI assistant with access to a multilingual document database. Your task is to answer questions based on the provided context from retrieved documents.

Instructions:
1. Answer based ONLY on the provided context
2. If the context doesn't contain enough information, say so
3. Cite the document/page when referencing information
4. Be concise but comprehensive
5. Maintain the language of the question in your response when appropriate
6. If multiple documents are relevant, synthesize information from all of them"""
    
    def _parse_model_name(self, model_str: str) -> str:
        """Parse model string."""
        if ":" in model_str:
            parts = model_str.split(":", 1)
            if len(parts) == 2:
                return parts[1]
        return model_str
    
    async def retrieve_context(
        self,
        query: str,
        top_k: int = 5,
        use_decomposition: bool = True
    ) -> List[RetrievalResult]:
        """
        Retrieve relevant context for a query.
        
        Args:
            query: User query
            top_k: Number of results to retrieve
            use_decomposition: Whether to use query decomposition
            
        Returns:
            List of RetrievalResult objects
        """
        # Extract metadata filters
        filters = self.filter_agent.extract_filters(query)
        cleaned_query = self.filter_agent.clean_query(query, filters) if filters else query
        
        # Decompose query if enabled
        if use_decomposition and config.enable_decomposition:
            queries = await self.decomposer.decompose_query(cleaned_query)
        else:
            queries = [cleaned_query]
        
        logger.info(f"Retrieving context for {len(queries)} queries")
        
        # Retrieve for each query
        all_results = []
        for q in queries:
            results = self.retriever.retrieve(
                query=q,
                top_k=top_k,
                metadata_filter=filters if filters else None
            )
            all_results.extend(results)
        
        # Deduplicate by chunk_id
        seen = set()
        unique_results = []
        for result in all_results:
            if result.chunk_id not in seen:
                seen.add(result.chunk_id)
                unique_results.append(result)
        
        # Rerank combined results
        if config.enable_rerank and len(unique_results) > top_k:
            reranked_results = self.reranker.rerank(cleaned_query, unique_results, top_k=top_k)
        else:
            reranked_results = unique_results[:top_k]
        
        logger.info(f"Retrieved {len(reranked_results)} context chunks")
        
        return reranked_results
    
    def build_prompt(
        self,
        query: str,
        context: List[RetrievalResult],
        chat_history: List[Dict[str, str]] = None
    ) -> str:
        """
        Build prompt with context and chat history.
        
        Args:
            query: User query
            context: Retrieved context chunks
            chat_history: Previous chat messages
            
        Returns:
            Formatted prompt
        """
        # Format context
        context_text = "\n\n".join([
            f"[Document: {r.doc_id}, Page: {r.page_num}, Language: {r.language}]\n{r.text}"
            for r in context
        ])
        
        # Format chat history
        history_text = ""
        if chat_history:
            history_lines = []
            for msg in chat_history[-5:]:  # Last 5 messages
                role = msg.get("role", "user")
                content = msg.get("content", "")
                history_lines.append(f"{role.upper()}: {content}")
            history_text = "\n".join(history_lines)
        
        # Build full prompt
        if history_text:
            prompt = f"""{self.system_prompt}

Previous conversation:
{history_text}

Context from documents:
{context_text}

Current question: {query}

Answer:"""
        else:
            prompt = f"""{self.system_prompt}

Context from documents:
{context_text}

Question: {query}

Answer:"""
        
        return prompt
    
    async def generate_with_ollama_stream(
        self,
        prompt: str
    ) -> AsyncGenerator[str, None]:
        """
        Generate response using Ollama with streaming.
        
        Args:
            prompt: Full prompt
            
        Yields:
            Response chunks
        """
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.ollama_host}/api/generate",
                    json={
                        "model": self.primary_model,
                        "prompt": prompt,
                        "stream": True,
                        "options": {
                            "temperature": 0.7,
                            "top_p": 0.9,
                            "num_predict": 2048,
                        }
                    }
                ) as response:
                    if response.status_code != 200:
                        logger.error(f"Ollama request failed with status {response.status_code}")
                        return
                    
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                import json
                                data = json.loads(line)
                                if "response" in data:
                                    yield data["response"]
                            except json.JSONDecodeError:
                                continue
                                
        except Exception as e:
            logger.error(f"Ollama streaming failed: {e}")
    
    def generate_with_gemini(self, prompt: str) -> str:
        """
        Generate response using Gemini Flash (fallback).
        
        Args:
            prompt: Full prompt
            
        Returns:
            Generated response
        """
        try:
            model = genai.GenerativeModel(self.fallback_model)
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_output_tokens": 2048,
                }
            )
            
            if response.text:
                return response.text
            else:
                logger.warning("Gemini returned empty response")
                return "I apologize, but I couldn't generate a response. Please try again."
                
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            return "I apologize, but I encountered an error. Please try again."
    
    async def chat(
        self,
        query: str,
        session_id: Optional[str] = None,
        stream: bool = True
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Main chat method with streaming.
        
        Args:
            query: User query
            session_id: Chat session ID
            stream: Whether to stream response
            
        Yields:
            Response chunks with metadata
        """
        # Create or get session
        if not session_id:
            session_id = str(uuid.uuid4())
            await storage.create_session(session_id)
        
        logger.info(f"Processing query in session {session_id}: '{query[:50]}...'")
        
        # Save user message
        await storage.add_message(session_id, "user", query)
        
        try:
            # Retrieve context
            yield {"type": "status", "message": "Retrieving relevant documents..."}
            context = await self.retrieve_context(query)
            
            if not context:
                yield {"type": "status", "message": "No relevant documents found"}
                response_text = "I couldn't find any relevant information in the document database to answer your question."
                yield {"type": "response", "content": response_text}
                await storage.add_message(session_id, "assistant", response_text)
                return
            
            yield {
                "type": "context",
                "chunks": [r.to_dict() for r in context]
            }
            
            # Get chat history
            history = await storage.get_session_messages(session_id, limit=10)
            chat_history = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in history[:-1]  # Exclude current message
            ]
            
            # Build prompt
            prompt = self.build_prompt(query, context, chat_history)
            
            # Generate response
            yield {"type": "status", "message": "Generating response..."}
            
            if stream:
                # Ollama streaming
                response_chunks = []
                
                async for chunk in self.generate_with_ollama_stream(prompt):
                    response_chunks.append(chunk)
                    yield {"type": "response", "content": chunk}
                
                if response_chunks:
                    full_response = "".join(response_chunks)
                    await storage.add_message(session_id, "assistant", full_response)
                    logger.success(f"Response generated with Ollama ({len(full_response)} chars)")
                else:
                    error_msg = "Ollama returned empty response"
                    logger.error(error_msg)
                    yield {"type": "error", "message": error_msg}
                    await storage.add_message(session_id, "assistant", error_msg)
            else:
                # Non-streaming Ollama
                response_text = ""
                async for chunk in self.generate_with_ollama_stream(prompt):
                    response_text += chunk
                
                if response_text:
                    await storage.add_message(session_id, "assistant", response_text)
                    logger.success(f"Response generated with Ollama ({len(response_text)} chars)")
                else:
                    error_msg = "Ollama returned empty response"
                    logger.error(error_msg)
                    response_text = error_msg
                
                yield {"type": "response", "content": response_text}
                await storage.add_message(session_id, "assistant", response_text)
            
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            error_msg = f"An error occurred: {str(e)}"
            yield {"type": "error", "message": error_msg}
            await storage.add_message(session_id, "assistant", error_msg)
    
    async def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get chat history for a session."""
        messages = await storage.get_session_messages(session_id)
        return [
            {
                "role": msg["role"],
                "content": msg["content"],
                "timestamp": msg["created_at"]
            }
            for msg in messages
        ]
    
    async def clear_session(self, session_id: str):
        """Clear chat history for a session."""
        await storage.clear_session(session_id)
        logger.info(f"Cleared session {session_id}")

