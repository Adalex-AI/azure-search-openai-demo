# This file likely contains the retrieve-then-read approach

from typing import Any, Optional, Union
import re

from azure.search.documents.aio import SearchClient
from azure.search.documents.models import VectorQuery
from azure.search.documents.agent.aio import KnowledgeAgentRetrievalClient
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

from approaches.approach import Approach, Document, ExtraInfo, DataPoints, ThoughtStep
from core.authentication import AuthenticationHelper


class RetrieveThenReadApproach(Approach):
    """
    Simple retrieve-then-read implementation, using the AI Search and OpenAI APIs directly.
    """

    def __init__(
        self,
        *,
        search_client: SearchClient,
        openai_client: AsyncOpenAI,
        auth_helper: AuthenticationHelper,
        chatgpt_model: str,
        chatgpt_deployment: Optional[str],
        embedding_deployment: Optional[str],
        embedding_model: str,
        embedding_dimensions: int,
        embedding_field: str,
        sourcepage_field: str,
        content_field: str,
        query_language: Optional[str],
        query_speller: Optional[str],
        openai_host: str = "azure",
        vision_endpoint: str = "",
        vision_token_provider = None,
        prompt_manager,
        reasoning_effort: Optional[str] = None,
        # Additional parameters from app.py
        search_index_name: Optional[str] = None,
        agent_model: Optional[str] = None,
        agent_deployment: Optional[str] = None,
        agent_client: Optional[KnowledgeAgentRetrievalClient] = None,
    ):
        super().__init__(
            search_client=search_client,
            openai_client=openai_client,
            auth_helper=auth_helper,
            query_language=query_language,
            query_speller=query_speller,
            embedding_deployment=embedding_deployment,
            embedding_model=embedding_model,
            embedding_dimensions=embedding_dimensions,
            embedding_field=embedding_field,
            openai_host=openai_host,
            vision_endpoint=vision_endpoint,
            vision_token_provider=vision_token_provider,
            prompt_manager=prompt_manager,
            reasoning_effort=reasoning_effort,
        )
        self.chatgpt_model = chatgpt_model
        self.chatgpt_deployment = chatgpt_deployment
        self.sourcepage_field = sourcepage_field
        self.content_field = content_field
        # Store additional parameters
        self.search_index_name = search_index_name
        self.agent_model = agent_model
        self.agent_deployment = agent_deployment
        self.agent_client = agent_client
        # Add missing answer_prompt initialization
        self.answer_prompt = self.try_load_prompt("ask_answer_question.prompty")

    def build_filter(self, overrides: dict[str, Any], auth_claims: dict[str, Any]) -> Optional[str]:
        """Build search filter with multi-category support - no automatic court detection"""
        filters: list[str] = []

        if ex := overrides.get("exclude_category"):
            ex_escaped = str(ex).replace("'", "''")
            filters.append(f"category ne '{ex_escaped}'")

        # Only apply category filter if user explicitly selected categories
        inc = overrides.get("include_category")
        if inc and inc not in ("All", ""):
            parts = [p.strip() for p in inc.split(",")]
            cat_filters = ["category eq '{}'".format(p.replace("'", "''")) for p in parts if p]
            if cat_filters:
                filters.append("(" + " or ".join(cat_filters) + ")")
        # No automatic fallback - if "All" or nothing selected, show everything

        if overrides.get("use_oid_security_filter"):
            oid = auth_claims.get("oid")
            if oid:
                oid_escaped = str(oid).replace("'", "''")
                filters.append(f"oids/any(g:g eq '{oid_escaped}')")

        if overrides.get("use_groups_security_filter"):
            groups = auth_claims.get("groups", []) or []
            if groups:
                group_conditions = []
                for g in groups:
                    g_escaped = str(g).replace("'", "''")
                    group_conditions.append(f"g eq '{g_escaped}'")
                if group_conditions:
                    filters.append(f"groups/any(g:{' or '.join(group_conditions)})")

        return " and ".join(filters) if filters else None

    def get_sources_content(self, results: list[Document], use_semantic_captions: bool, use_image_citation: bool) -> list[dict[str, Any]]:
        """Return structured data with full content preserved"""
        return self.get_sources_content_structured(results, use_semantic_captions, use_image_citation)

    def get_sources_content_structured(self, results: list[Document], use_semantic_captions: bool, use_image_citation: bool) -> list[dict[str, Any]]:
        """Return structured data with all fields preserved including full content and updated field"""
        structured_results = []
        for doc in results:
            # Create structured object with all available fields, ensuring no None values
            result_obj = {
                "id": str(doc.id) if doc.id is not None else "",
                "content": str(doc.content) if doc.content is not None else "",  # Full content preserved, no truncation
                "sourcepage": str(doc.sourcepage) if doc.sourcepage is not None else "",
                "sourcefile": str(doc.sourcefile) if doc.sourcefile is not None else "",
                "category": str(doc.category) if doc.category is not None else "",
                "storageUrl": str(doc.storage_url) if doc.storage_url is not None else "",
                "oids": doc.oids if doc.oids is not None else [],
                "groups": doc.groups if doc.groups is not None else [],
                "score": float(doc.score) if doc.score is not None else 0.0,
                "reranker_score": float(doc.reranker_score) if doc.reranker_score is not None else 0.0,
                "updated": str(doc.updated) if doc.updated is not None else "",  # Include updated field
                # Add citation information for frontend compatibility
                "citation": self.get_citation_from_document(doc),
                "filepath": str(doc.sourcepage) if doc.sourcepage is not None else "",
                "url": str(doc.storage_url) if doc.storage_url is not None else "",
            }

            # Add captions as supplementary information if using semantic captions
            if use_semantic_captions and doc.captions:
                result_obj["captions"] = [
                    {
                        "text": str(caption.text) if caption.text is not None else "",
                        "highlights": str(caption.highlights) if caption.highlights is not None else "",
                        "additional_properties": caption.additional_properties if caption.additional_properties is not None else {},
                    }
                    for caption in doc.captions
                ]
                # Store caption summary separately - don't replace content
                caption_texts = [str(c.text) for c in doc.captions if c.text is not None]
                if caption_texts:
                    result_obj["caption_summary"] = " . ".join(caption_texts)

            structured_results.append(result_obj)

        return structured_results

    def get_citation_from_document(self, doc: Document) -> str:
        """Get citation string from document object"""
        if doc.storage_url:
            return doc.storage_url
            
        sourcepage = doc.sourcepage or ""
        sourcefile = doc.sourcefile or ""
        
        if sourcepage and sourcefile:
            return f"{sourcepage}, {sourcefile}"
        elif sourcepage:
            return sourcepage
        elif sourcefile:
            return sourcefile
        else:
            return "Unknown source"

    async def run(self, messages: list[ChatCompletionMessageParam], session_state: Any = None, context: dict[str, Any] = {}) -> dict[str, Any]:
        """Implementation for retrieve-then-read"""
        auth_claims = context.get("auth_claims", {})
        overrides = context.get("overrides", {})
        
        # Perform search
        top = overrides.get("top", 3)
        query_text = str(messages[-1]["content"]) if messages else ""
        
        # Build filter with user selection only (no automatic detection)
        filter = self.build_filter(overrides, auth_claims)
        
        use_text_search = overrides.get("retrieval_mode") in ["text", "hybrid", None]
        use_vector_search = overrides.get("retrieval_mode") in ["vectors", "hybrid", None]
        use_semantic_ranker = overrides.get("semantic_ranker", False)
        use_semantic_captions = overrides.get("semantic_captions", False)
        
        vectors = []
        if use_vector_search and query_text:
            vectors.append(await self.compute_text_embedding(query_text))
        
        # Log the search parameters for debugging
        import logging
        logging.info(f"Ask Question - Searching with query: {query_text}, top: {top}, filter: {filter}")
        
        results = await self.search(
            top=top,
            query_text=query_text,
            filter=filter,
            vectors=vectors,
            use_text_search=use_text_search,
            use_vector_search=use_vector_search,
            use_semantic_ranker=use_semantic_ranker,
            use_semantic_captions=use_semantic_captions,
            minimum_search_score=overrides.get("minimum_search_score", 0.0),
            minimum_reranker_score=overrides.get("minimum_reranker_score", 0.0),
        )
        
        # Log the search results for debugging
        logging.info(f"Ask Question - Search returned {len(results)} results")
        for i, result in enumerate(results[:3]):  # Log first 3 results
            content_preview = result.content[:200] if result.content else "No content"
            logging.info(f"Ask Question - Result {i}: id={result.id}, content_length={len(result.content or '')}, preview={content_preview}")
        
        # Get structured sources with all fields including updated and storageUrl
        sources = self.get_sources_content_structured(results, use_semantic_captions, use_image_citation=False)
        
        # Ensure all required fields are properly set
        for source in sources:
            if isinstance(source, dict):
                # Map fields from search result to ensure completeness
                result_idx = sources.index(source)
                if result_idx < len(results):
                    search_result = results[result_idx]
                    source["sourcepage"] = getattr(search_result, "sourcepage", source.get("sourcepage", ""))
                    source["sourcefile"] = getattr(search_result, "sourcefile", source.get("sourcefile", ""))
                    source["category"] = getattr(search_result, "category", source.get("category", ""))
                    source["updated"] = getattr(search_result, "updated", source.get("updated", ""))
                    source["storageUrl"] = getattr(search_result, "storage_url", source.get("storageUrl", ""))
                    source["url"] = source.get("storageUrl", "")
        
        # Format sources for prompt with citation format similar to chat approach
        sources_for_prompt = []
        for source in sources:
            sourcepage = source.get("sourcepage", "")
            sourcefile = source.get("sourcefile", "")
            content = source.get("content", "")
            
            # Format source with clear citation format for the prompt
            formatted_source = f"[{sourcepage}, {sourcefile}]: {content}"
            sources_for_prompt.append(formatted_source)
        
        extra_info = ExtraInfo(
            DataPoints(text=sources),  # Pass structured data to frontend for proper citation handling
            thoughts=[
                ThoughtStep(
                    "Search using user query",
                    query_text,
                    {
                        "use_semantic_captions": use_semantic_captions,
                        "use_semantic_ranker": use_semantic_ranker,
                        "top": top,
                        "filter": filter,
                        "use_vector_search": use_vector_search,
                        "use_text_search": use_text_search,
                        # removed leftover automatic court detection reference
                        # "detected_court": self.detect_court_in_query(query_text),
                    },
                ),
                ThoughtStep(
                    "Search results",
                    [result.serialize_for_results() for result in results],
                ),
            ],
        )

        q = query_text
        seed = overrides.get("seed", None)

        messages = self.render_prompt(
             self.answer_prompt,
             self.get_system_prompt_variables(overrides.get("prompt_template"))
             | {"user_query": q, "text_sources": sources_for_prompt},  # Use formatted sources for prompt
         )

        # Append the properly formatted “Prompt to generate answer” ThoughtStep using the rendered prompt
        try:
            readable = self.prompt_manager.messages_to_readable(messages)
            # Prefer array of lines for UI; split by blank lines between messages
            description = [seg for seg in readable.split("\n\n") if seg.strip()]
        except Exception:
            # Fallback to minimal per-message rendering
            description = []
            for m in messages:
                role = (m.get("role") if isinstance(m, dict) else getattr(m, "role", "unknown")) or "unknown"
                content = (m.get("content") if isinstance(m, dict) else getattr(m, "content", "")) or ""
                if isinstance(content, list):
                    content = f"[content parts: {len(content)}]"
                description.append(f"{role.upper()}:\n{str(content).strip()[:2000]}{' …' if len(str(content))>2000 else ''}")

        extra_info.thoughts.append(
            ThoughtStep(
                "Prompt to generate answer",
                description,
                {
                    "model": self.chatgpt_model,
                    "deployment": self.chatgpt_deployment,
                    "temperature": overrides.get("temperature", 0.3),
                    "max_tokens": 8192,
                    "raw_messages": messages,  # keep for debugging
                },
            )
        )

        chat_completion = await self.openai_client.chat.completions.create(
            model=self.chatgpt_deployment if self.chatgpt_deployment else self.chatgpt_model,
            messages=messages,
            temperature=overrides.get("temperature", 0.3),
            max_tokens=8192,  # Increased from 1024 to accommodate full content
            n=1,
            seed=seed,
        )

        return {
            "message": {
                "content": chat_completion.choices[0].message.content,
                "role": chat_completion.choices[0].message.role,
            },
            "context": extra_info,
            "session_state": session_state,
        }

    async def run_agentic_retrieval_approach(
        self,
        messages: list[ChatCompletionMessageParam],
        overrides: dict[str, Any],
        auth_claims: dict[str, Any],
    ):
        minimum_reranker_score = overrides.get("minimum_reranker_score", 0)
        search_index_filter = self.build_filter(overrides, auth_claims)
        top = overrides.get("top", 3)
        max_subqueries = overrides.get("max_subqueries", 10)
        results_merge_strategy = overrides.get("results_merge_strategy", "interleaved")
        # 50 is the amount of documents that the reranker can process per query
        max_docs_for_reranker = max_subqueries * 50

        response, results = await self.run_agentic_retrieval(
            messages,
            self.agent_client,
            search_index_name=self.search_index_name,
            top=top,
            filter_add_on=search_index_filter,
            minimum_reranker_score=minimum_reranker_score,
            max_docs_for_reranker=max_docs_for_reranker,
            results_merge_strategy=results_merge_strategy,
        )

        text_sources = self.get_sources_content(results, use_semantic_captions=False, use_image_citation=False)

        extra_info = ExtraInfo(
            DataPoints(text=text_sources),
            thoughts=[
                ThoughtStep(
                    "Use agentic retrieval",
                    # Convert messages to readable format
                    self.prompt_manager.messages_to_readable(messages) if hasattr(self.prompt_manager, 'messages_to_readable') else str(messages),
                    {
                        "reranker_threshold": minimum_reranker_score,
                        "max_docs_for_reranker": max_docs_for_reranker,
                        "results_merge_strategy": results_merge_strategy,
                        "filter": search_index_filter,
                    },
                ),
                ThoughtStep(
                    f"Agentic retrieval results (top {top})",
                    [result.serialize_for_results() for result in results],
                    {
                        "query_plan": (
                            [activity.as_dict() for activity in response.activity] if response.activity else None
                        ),
                        "model": self.agent_model,
                        "deployment": self.agent_deployment,
                    },
                ),
            ],
        )
        return extra_info

    def get_citation_from_document_dict(self, doc_dict: dict[str, Any]) -> str:
        """Get citation string from document dict"""
        if doc_dict.get("storageUrl"):
            return doc_dict["storageUrl"]
            
        sourcepage = doc_dict.get("sourcepage", "")
        sourcefile = doc_dict.get("sourcefile", "")
        
        if sourcepage and sourcefile:
            return f"{sourcepage}, {sourcefile}"
        elif sourcepage:
            return sourcepage
        elif sourcefile:
            return sourcefile
        else:
            return "Unknown source"

    def get_sources_content(self, results: list[Document], use_semantic_captions: bool, use_image_citation: bool) -> list[dict[str, Any]]:
        """Return structured data for consistent processing with full content preserved"""
        structured_results = []
        for doc in results:
            # Create structured object with all available fields, ensuring no None values
            result_obj = {
                "id": str(doc.id) if doc.id is not None else "",
                "content": str(doc.content) if doc.content is not None else "",  # Full content, no truncation
                "sourcepage": str(doc.sourcepage) if doc.sourcepage is not None else "",
                "sourcefile": str(doc.sourcefile) if doc.sourcefile is not None else "",
                "category": str(doc.category) if doc.category is not None else "",
                "storageUrl": str(doc.storage_url) if doc.storage_url is not None else "",
                "oids": doc.oids if doc.oids is not None else [],
                "groups": doc.groups if doc.groups is not None else [],
                "score": doc.score if doc.score is not None else 0.0,
                "reranker_score": doc.reranker_score if doc.reranker_score is not None else 0.0,
                "updated": str(doc.updated) if doc.updated is not None else "",
                # Add citation information for frontend compatibility
                "citation": self.get_citation_from_document(doc),
                "filepath": str(doc.sourcepage) if doc.sourcepage is not None else "",
                "url": str(doc.storage_url) if doc.storage_url is not None else "",
            }

            # Add captions as supplementary information if using semantic captions
            if use_semantic_captions and doc.captions:
                result_obj["captions"] = [
                    {
                        "text": str(caption.text) if caption.text is not None else "",
                        "highlights": caption.highlights if caption.highlights is not None else "",
                        "additional_properties": caption.additional_properties if caption.additional_properties is not None else {},
                    }
                    for caption in doc.captions
                ]
                # Store caption summary separately - don't replace content
                caption_texts = [str(c.text) for c in doc.captions if c.text is not None]
                if caption_texts:
                    result_obj["caption_summary"] = " . ".join(caption_texts)

            structured_results.append(result_obj)

        return structured_results


    def nonewlines(self, text: str) -> str:
        """Utility function to remove newlines from text"""
        return text.replace("\n", " ").replace("\r", " ")