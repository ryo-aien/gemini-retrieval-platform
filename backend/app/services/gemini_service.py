"""Gemini AI service for chat and report generation"""
import os
from typing import List, Dict, Any, AsyncGenerator
import httpx
import json

from app.models.schemas import ChatMessage, Citation


class GeminiService:
    """Service for interacting with Gemini AI"""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")

        self.model_name = "gemini-2.5-flash"

    def _extract_citations(self, response_data: Dict[str, Any], document_names: List[str] = None) -> List[Citation]:
        """Extract citations from grounding metadata"""
        citations = []

        # Check if response has candidates
        candidates = response_data.get('candidates', [])
        if not candidates:
            return citations

        candidate = candidates[0]

        # Look for grounding metadata in the candidate
        grounding = candidate.get('groundingMetadata', {})

        # Extract file search results
        file_search_results = grounding.get('fileSearchResults', [])
        for result in file_search_results:
            doc_name = result.get('documentName', '')

            # Filter by selected documents if specified
            if document_names and doc_name:
                if doc_name not in document_names:
                    continue

            citations.append(Citation(
                document_name=doc_name,
                chunk_id=result.get('chunkId', ''),
                score=result.get('score', 0.0),
                text=result.get('text', '')
            ))

        return citations

    async def chat_with_file_search(
        self,
        message: str,
        store_name: str,
        history: List[ChatMessage] = None,
        document_names: List[str] = None
    ) -> Dict[str, Any]:
        """Send a chat message with File Search context"""
        try:
            # Prepare conversation history
            contents = []

            # Add system instruction first (if no history)
            if not history or len(history) == 0:
                system_instruction = """あなたはドキュメントベースのアシスタントです。以下のルールを厳守してください：

1. **必ずアップロードされたドキュメントの情報のみを使用**してください
2. ドキュメントに記載されていない情報については、一般知識や外部情報を使用しないでください
3. ドキュメントに情報が見つからない場合は、「アップロードされたドキュメントには、この質問に関する情報が見つかりませんでした。」と明確に伝えてください
4. 回答する際は、必ずドキュメントからの引用を含めてください
5. 推測や想像で答えないでください

これらのルールを守り、ドキュメントに基づいた正確な情報のみを提供してください。"""

                contents.append({
                    "role": "user",
                    "parts": [{"text": system_instruction}]
                })
                contents.append({
                    "role": "model",
                    "parts": [{"text": "承知しました。アップロードされたドキュメントの情報のみを使用して回答します。ドキュメントに情報がない場合は、その旨を明確にお伝えします。"}]
                })

            if history:
                for msg in history:
                    contents.append({
                        "role": msg.role,
                        "parts": [{"text": msg.content}]
                    })

            # Add current user message
            contents.append({
                "role": "user",
                "parts": [{"text": message}]
            })

            # Prepare request body with File Search Tool
            # See: https://ai.google.dev/gemini-api/docs/file-search
            request_body = {
                "contents": contents,
                "tools": [{
                    "file_search": {
                        "file_search_store_names": [store_name]
                    }
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 2048,
                }
            }

            print(f"Gemini API request: {json.dumps(request_body, indent=2)}")

            # Send request to Gemini API
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.BASE_URL}/models/{self.model_name}:generateContent",
                    headers={
                        "Content-Type": "application/json",
                        "x-goog-api-key": self.api_key
                    },
                    json=request_body
                )

                if response.status_code >= 400:
                    print(f"Gemini API error: {response.status_code}")
                    print(f"Response body: {response.text}")

                response.raise_for_status()
                response_data = response.json()

            print(f"Gemini API response: {json.dumps(response_data, indent=2)}")

            # Extract text response
            response_text = ""
            candidates = response_data.get('candidates', [])
            if candidates:
                content = candidates[0].get('content', {})
                parts = content.get('parts', [])
                if parts:
                    response_text = parts[0].get('text', '')

            # Extract citations (filtered by selected documents)
            citations = self._extract_citations(response_data, document_names)

            # Check if citations exist
            # If no citations are found, it means the information is not in the documents
            if not citations:
                # Check if the response already mentions document unavailability
                if "アップロードされたドキュメントには" not in response_text and \
                   "ドキュメントに" not in response_text and \
                   "情報が見つかりませんでした" not in response_text:
                    # Override the response to be more explicit
                    response_text = """申し訳ございません。アップロードされたドキュメントには、ご質問に関する情報が見つかりませんでした。

以下をご確認ください：
- ドキュメントが正常にアップロードされているか
- 質問内容がドキュメントの内容に関連しているか

別の質問をお試しいただくか、関連するドキュメントをアップロードしてください。"""

            return {
                "message": response_text,
                "citations": citations
            }

        except Exception as e:
            import traceback
            print(f"Error in chat_with_file_search: {str(e)}")
            print(traceback.format_exc())
            raise Exception(f"Error in chat with file search: {str(e)}")

    async def chat_stream_with_file_search(
        self,
        message: str,
        store_name: str,
        history: List[ChatMessage] = None,
        document_names: List[str] = None
    ) -> AsyncGenerator[str, None]:
        """Stream chat responses with File Search context"""
        try:
            # Prepare conversation history
            contents = []

            # Add system instruction first (if no history)
            if not history or len(history) == 0:
                system_instruction = """あなたはドキュメントベースのアシスタントです。以下のルールを厳守してください：

1. **必ずアップロードされたドキュメントの情報のみを使用**してください
2. ドキュメントに記載されていない情報については、一般知識や外部情報を使用しないでください
3. ドキュメントに情報が見つからない場合は、「アップロードされたドキュメントには、この質問に関する情報が見つかりませんでした。」と明確に伝えてください
4. 回答する際は、必ずドキュメントからの引用を含めてください
5. 推測や想像で答えないでください

これらのルールを守り、ドキュメントに基づいた正確な情報のみを提供してください。"""

                contents.append({
                    "role": "user",
                    "parts": [{"text": system_instruction}]
                })
                contents.append({
                    "role": "model",
                    "parts": [{"text": "承知しました。アップロードされたドキュメントの情報のみを使用して回答します。ドキュメントに情報がない場合は、その旨を明確にお伝えします。"}]
                })

            if history:
                for msg in history:
                    contents.append({
                        "role": msg.role,
                        "parts": [{"text": msg.content}]
                    })

            # Add current user message
            contents.append({
                "role": "user",
                "parts": [{"text": message}]
            })

            # Prepare request body with File Search Tool
            request_body = {
                "contents": contents,
                "tools": [{
                    "file_search": {
                        "file_search_store_names": [store_name]
                    }
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 2048,
                }
            }

            print(f"Gemini API stream request: {json.dumps(request_body, indent=2)}")

            # Send streaming request to Gemini API
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.BASE_URL}/models/{self.model_name}:streamGenerateContent",
                    headers={
                        "Content-Type": "application/json",
                        "x-goog-api-key": self.api_key
                    },
                    json=request_body
                ) as response:
                    if response.status_code >= 400:
                        error_text = await response.aread()
                        print(f"Gemini API stream error: {response.status_code}")
                        print(f"Response body: {error_text.decode()}")
                        yield f"Error: {response.status_code}"
                        return

                    async for line in response.aiter_lines():
                        if line:
                            try:
                                # Parse JSON from stream
                                data = json.loads(line)
                                candidates = data.get('candidates', [])
                                if candidates:
                                    content = candidates[0].get('content', {})
                                    parts = content.get('parts', [])
                                    if parts:
                                        text = parts[0].get('text', '')
                                        if text:
                                            yield text
                            except json.JSONDecodeError:
                                continue

        except Exception as e:
            import traceback
            print(f"Error in chat_stream_with_file_search: {str(e)}")
            print(traceback.format_exc())
            yield f"Error: {str(e)}"

    async def generate_report(
        self,
        store_name: str,
        chat_history: List[ChatMessage],
        report_type: str = "comprehensive"
    ) -> str:
        """Generate a structured report based on chat history and sources"""
        try:
            # Prepare report generation prompt
            chat_summary = "\n".join([
                f"{msg.role}: {msg.content}"
                for msg in chat_history[-10:]  # Last 10 messages
            ])

            report_prompts = {
                "comprehensive": f"""Based on the following conversation and the available sources, generate a comprehensive report with the following structure:

# Executive Summary
[Provide a high-level overview of the main topics discussed]

# Key Topics and Analysis
[Analyze the main topics covered in the conversation and sources]

# Source-by-Source Insights
[For each source document, provide detailed insights and key findings]

# Conclusions and Recommendations
[Summarize findings and provide actionable recommendations]

Conversation context:
{chat_summary}

Please generate a well-structured report in Markdown format.""",

                "summary": f"""Create a concise summary of the key points from the conversation and sources.

Conversation context:
{chat_summary}

Provide a brief, bullet-point summary.""",

                "faq": f"""Based on the conversation and sources, generate a FAQ document with common questions and comprehensive answers.

Conversation context:
{chat_summary}

Format as a Q&A list.""",

                "briefing": f"""Create a briefing document suitable for quick review, highlighting the most important information.

Conversation context:
{chat_summary}

Keep it concise and action-oriented."""
            }

            prompt = report_prompts.get(report_type, report_prompts["comprehensive"])

            # Prepare request body with File Search Tool
            request_body = {
                "contents": [{
                    "role": "user",
                    "parts": [{"text": prompt}]
                }],
                "tools": [{
                    "file_search": {
                        "file_search_store_names": [store_name]
                    }
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 4096,
                }
            }

            print(f"Gemini API report request for type: {report_type}")

            # Send request to Gemini API
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.BASE_URL}/models/{self.model_name}:generateContent",
                    headers={
                        "Content-Type": "application/json",
                        "x-goog-api-key": self.api_key
                    },
                    json=request_body
                )

                if response.status_code >= 400:
                    print(f"Gemini API error: {response.status_code}")
                    print(f"Response body: {response.text}")

                response.raise_for_status()
                response_data = response.json()

            # Extract text response
            response_text = ""
            candidates = response_data.get('candidates', [])
            if candidates:
                content = candidates[0].get('content', {})
                parts = content.get('parts', [])
                if parts:
                    response_text = parts[0].get('text', '')

            return response_text

        except Exception as e:
            import traceback
            print(f"Error generating report: {str(e)}")
            print(traceback.format_exc())
            raise Exception(f"Error generating report: {str(e)}")
