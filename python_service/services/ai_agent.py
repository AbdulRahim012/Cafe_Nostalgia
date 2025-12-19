"""
AI Agent that interprets natural language questions, generates ShopifyQL queries,
and converts results into business-friendly explanations.
"""
import os
import json
from typing import Dict, Any, Optional
from openai import OpenAI
from services.shopify_client import ShopifyClient


class AIAgent:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
        self.shopify_client = ShopifyClient()
        self.model = os.getenv("OPENAI_MODEL", "gpt-4")
        
    async def process_question(self, question: str, store_id: str) -> Dict[str, Any]:
        """
        Main processing pipeline:
        1. Understand intent
        2. Generate ShopifyQL query
        3. Execute query
        4. Convert results to business language
        """
        try:
            # Step 1: Understand intent and generate query
            query_result = await self._generate_shopifyql_query(question, store_id)
            
            if query_result.get("error"):
                return query_result
            
            shopifyql_query = query_result.get("query")
            intent = query_result.get("intent")
            
            # Step 2: Execute query against Shopify
            data_result = await self.shopify_client.execute_query(
                store_id=store_id,
                query=shopifyql_query,
                query_type=intent
            )
            
            if data_result.get("error"):
                return {
                    "error": f"Failed to execute query: {data_result['error']}",
                    "query_used": shopifyql_query
                }
            
            # Step 3: Convert results to business-friendly explanation
            explanation = await self._generate_explanation(
                question=question,
                data=data_result.get("data", {}),
                query_type=intent
            )
            
            return {
                "answer": explanation.get("answer", "Unable to generate answer"),
                "confidence": explanation.get("confidence", "medium"),
                "query_used": shopifyql_query,
                "data": data_result.get("data")
            }
            
        except Exception as e:
            return {"error": f"Agent processing error: {str(e)}"}
    
    async def _generate_shopifyql_query(self, question: str, store_id: str) -> Dict[str, Any]:
        """
        Use LLM to understand intent and generate appropriate ShopifyQL query.
        """
        system_prompt = """You are an expert at analyzing Shopify store data and generating ShopifyQL queries.

ShopifyQL is a query language for Shopify Analytics. Common query patterns:

1. Sales queries:
   - SHOW sales FROM orders SINCE -30d UNTIL today
   - SHOW total_sales FROM orders WHERE created_at >= '2024-01-01'
   - SHOW top_products FROM orders SINCE -7d

2. Inventory queries:
   - SHOW inventory_levels FROM products
   - SHOW low_stock_items FROM inventory WHERE quantity < 10

3. Customer queries:
   - SHOW repeat_customers FROM orders SINCE -90d
   - SHOW customer_count FROM customers

4. Product queries:
   - SHOW top_selling_products FROM orders SINCE -7d LIMIT 5
   - SHOW product_performance FROM orders WHERE created_at >= '2024-01-01'

Based on the user's question, determine:
1. The intent (sales, inventory, customers, products)
2. The appropriate ShopifyQL query
3. Any time periods mentioned

Return a JSON object with:
- intent: one of "sales", "inventory", "customers", "products"
- query: the ShopifyQL query string
- reasoning: brief explanation of why this query fits the question
"""

        user_prompt = f"""User question: "{question}"

Generate the appropriate ShopifyQL query. If the question is ambiguous or cannot be answered with Shopify data, return an error message."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            if result.get("error"):
                return {"error": result["error"]}
            
            return {
                "intent": result.get("intent", "sales"),
                "query": result.get("query", ""),
                "reasoning": result.get("reasoning", "")
            }
            
        except Exception as e:
            # Fallback to simple pattern matching if LLM fails
            return self._fallback_query_generation(question)
    
    def _fallback_query_generation(self, question: str) -> Dict[str, Any]:
        """
        Fallback query generation using pattern matching when LLM is unavailable.
        """
        question_lower = question.lower()
        
        if "inventory" in question_lower or "stock" in question_lower:
            if "out of stock" in question_lower or "low" in question_lower:
                return {
                    "intent": "inventory",
                    "query": "SHOW inventory_levels FROM products WHERE quantity < 20"
                }
            return {
                "intent": "inventory",
                "query": "SHOW inventory_levels FROM products"
            }
        
        elif "top" in question_lower and "product" in question_lower:
            limit = 5
            if "5" in question or "five" in question_lower:
                limit = 5
            return {
                "intent": "products",
                "query": f"SHOW top_selling_products FROM orders SINCE -7d LIMIT {limit}"
            }
        
        elif "customer" in question_lower or "repeat" in question_lower:
            return {
                "intent": "customers",
                "query": "SHOW repeat_customers FROM orders SINCE -90d"
            }
        
        elif "sales" in question_lower or "revenue" in question_lower:
            return {
                "intent": "sales",
                "query": "SHOW total_sales FROM orders SINCE -30d"
            }
        
        else:
            return {
                "intent": "sales",
                "query": "SHOW total_sales FROM orders SINCE -30d"
            }
    
    async def _generate_explanation(self, question: str, data: Dict[str, Any], query_type: str) -> Dict[str, Any]:
        """
        Convert raw Shopify data into business-friendly explanations.
        """
        system_prompt = """You are a business analyst who explains Shopify store data in simple, actionable language.

Convert technical data into clear insights that a store owner can understand and act upon.
Be specific with numbers, timeframes, and recommendations.
Keep explanations concise (2-3 sentences max).
"""

        user_prompt = f"""Original question: "{question}"

Query type: {query_type}

Data retrieved: {json.dumps(data, indent=2)}

Generate a clear, business-friendly answer. Include:
- Key numbers/metrics
- Time period if relevant
- Actionable recommendations if applicable
- Confidence level (high/medium/low) based on data completeness

Return JSON with:
- answer: the explanation
- confidence: high/medium/low
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return {
                "answer": result.get("answer", "Unable to generate explanation"),
                "confidence": result.get("confidence", "medium")
            }
            
        except Exception as e:
            # Fallback explanation
            return self._fallback_explanation(question, data, query_type)
    
    def _fallback_explanation(self, question: str, data: Dict[str, Any], query_type: str) -> Dict[str, Any]:
        """
        Generate simple explanation when LLM is unavailable.
        """
        if not data:
            return {
                "answer": "I couldn't retrieve the requested data. Please check your store connection and try again.",
                "confidence": "low"
            }
        
        if query_type == "inventory":
            if isinstance(data, list) and len(data) > 0:
                low_stock = [item for item in data if item.get("quantity", 0) < 20]
                return {
                    "answer": f"Found {len(low_stock)} products with low inventory (less than 20 units). Consider reordering soon.",
                    "confidence": "medium"
                }
            return {
                "answer": "Inventory data retrieved. Review the details to make reordering decisions.",
                "confidence": "medium"
            }
        
        elif query_type == "products":
            if isinstance(data, list):
                return {
                    "answer": f"Found {len(data)} top-selling products. Review the list to identify your best performers.",
                    "confidence": "medium"
                }
        
        elif query_type == "sales":
            total = data.get("total_sales", data.get("sales", 0))
            return {
                "answer": f"Total sales: ${total:.2f} for the requested period.",
                "confidence": "medium"
            }
        
        return {
            "answer": f"Retrieved {query_type} data. Review the details for insights.",
            "confidence": "medium"
        }

