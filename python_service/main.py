from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv

from services.ai_agent import AIAgent
from services.shopify_client import ShopifyClient

load_dotenv()

app = FastAPI(title="Shopify AI Analytics Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QuestionRequest(BaseModel):
    store_id: str
    question: str


class QuestionResponse(BaseModel):
    answer: str
    confidence: str
    query_used: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


@app.get("/")
def root():
    return {"message": "Shopify AI Analytics Service", "status": "running"}


@app.post("/api/v1/analyze", response_model=QuestionResponse)
async def analyze_question(request: QuestionRequest):
    """
    Main endpoint that receives questions from Rails API and processes them
    using the AI agent to generate ShopifyQL queries and return insights.
    """
    try:
        agent = AIAgent()
        shopify_client = ShopifyClient()
        
        # Process the question through the AI agent
        result = await agent.process_question(
            question=request.question,
            store_id=request.store_id
        )
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        
        return QuestionResponse(
            answer=result.get("answer", "Unable to generate answer"),
            confidence=result.get("confidence", "low"),
            query_used=result.get("query_used"),
            data=result.get("data")
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

