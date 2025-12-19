# AI-Powered Shopify Analytics App

An AI-powered analytics application that connects to Shopify stores and allows users to ask natural-language questions. The system translates questions into ShopifyQL queries, fetches data from Shopify, and returns answers in simple, business-friendly language.

## Architecture

The application consists of two services:

1. **Rails API (Backend Gateway)** - Handles HTTP requests, validates input, and forwards questions to Python service
2. **Python AI Service (LLM Agent)** - Uses LLM to understand questions, generate ShopifyQL queries, execute them, and format responses

```
Client → Rails API (Port 3000) → Python Service (Port 8000) → Shopify API
```

**Data Flow:**
```
Client Request → Rails API (Validation) → Python Service → AI Agent (Intent Understanding) 
→ ShopifyQL Generation → Shopify API (Data Retrieval) → Data Processing 
→ Explanation Generation → Response to Client
```

**Components:**
- **Rails API**: Ruby on Rails 7.1 (API-only), handles OAuth and request routing
- **Python Service**: FastAPI with OpenAI GPT-4, processes questions and generates insights
- **Services**: `PythonServiceClient`, `ShopifyOAuthService`, `AIAgent`, `ShopifyClient`

## Prerequisites

- Ruby 3.2.3+
- Python 3.12+
- OpenAI API key
- Shopify API credentials (API key, API secret)

## Setup Instructions

### Quick Setup

```bash
chmod +x setup.sh
./setup.sh
```

Edit `.env` files in both `rails_api/` and `python_service/` directories with your credentials.

### Manual Setup

#### Rails API

```bash
cd rails_api
bundle install

# Create .env file with:
# SHOPIFY_API_KEY=your_key
# SHOPIFY_API_SECRET=your_secret
# PYTHON_SERVICE_URL=http://localhost:8000

rails server  # Runs on http://localhost:3000
```

#### Python Service

```bash
cd python_service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env file with:
# OPENAI_API_KEY=your_key
# OPENAI_MODEL=gpt-4

uvicorn main:app --reload --port 8000
```

## API Endpoints

### POST /api/v1/questions

Ask a natural language question about your Shopify store.

**Request:**
```json
{
  "store_id": "example-store.myshopify.com",
  "question": "How much inventory should I reorder for next week?"
}
```

**Response:**
```json
{
  "answer": "Based on the last 30 days, you sell around 10 units per day. You should reorder at least 70 units to avoid stockouts next week.",
  "confidence": "medium",
  "query_used": "SHOW inventory_levels FROM products WHERE quantity < 20",
  "data": { "inventory_levels": [...] }
}
```

### GET /api/v1/auth/shopify

Initiate Shopify OAuth flow. Query parameter: `shop` (e.g., `example-store.myshopify.com`)

### GET /api/v1/auth/shopify/callback

OAuth callback endpoint (handled automatically by Shopify).

## Sample API Requests & Responses

### Example 1: Top Products

**Request:**
```bash
curl -X POST http://localhost:3000/api/v1/questions \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": "example-store.myshopify.com",
    "question": "What were my top 5 selling products last week?"
  }'
```

**Response:**
```json
{
  "answer": "Your top 5 selling products last week were: Product X (150 sales), Product Y (120 sales), Product Z (100 sales), Product A (85 sales), and Product B (70 sales).",
  "confidence": "high",
  "query_used": "SHOW top_selling_products FROM orders SINCE -7d LIMIT 5",
  "data": {
    "products": [
      { "id": 1, "title": "Product X", "price": "29.99", "sales_count": 150 }
    ]
  }
}
```

### Example 2: Inventory Reorder

**Request:**
```bash
curl -X POST http://localhost:3000/api/v1/questions \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": "example-store.myshopify.com",
    "question": "How much inventory should I reorder based on last 30 days sales?"
  }'
```

**Response:**
```json
{
  "answer": "Based on the last 30 days, your total sales were $12,500.50 across 45 orders, averaging $277.79 per order. You should reorder inventory to cover at least 1.5x your average daily sales.",
  "confidence": "medium",
  "query_used": "SHOW total_sales FROM orders SINCE -30d",
  "data": {
    "total_sales": 12500.50,
    "order_count": 45,
    "average_order_value": 277.79
  }
}
```

### Example 3: Low Stock Alert

**Request:**
```bash
curl -X POST http://localhost:3000/api/v1/questions \
  -H "Content-Type: application/json" \
  -d '{
    "store_id": "example-store.myshopify.com",
    "question": "Which products are likely to go out of stock in 7 days?"
  }'
```

**Response:**
```json
{
  "answer": "Found 2 products with low inventory (less than 20 units): Product A (15 units) and Product B (5 units). Consider reordering soon.",
  "confidence": "medium",
  "query_used": "SHOW inventory_levels FROM products WHERE quantity < 20",
  "data": {
    "inventory_levels": [
      { "product_id": 1, "product_name": "Product A", "quantity": 15 }
    ]
  }
}
```

## Agent Flow Description

The AI Agent follows a 5-step workflow:

### Step 1: Intent Understanding
- Classifies question type (inventory, sales, customers, products)
- Extracts parameters (time periods, product names, metrics)

**Example**: "What were my top 5 selling products last week?"
- Intent: `products`
- Parameters: `top 5`, `last week`

### Step 2: Query Generation
- Determines required Shopify data sources
- Generates syntactically correct ShopifyQL query

**Example Queries:**
- Sales: `SHOW total_sales FROM orders SINCE -30d`
- Inventory: `SHOW inventory_levels FROM products WHERE quantity < 20`
- Products: `SHOW top_selling_products FROM orders SINCE -7d LIMIT 5`

### Step 3: Query Execution
- Authenticates with Shopify using stored access tokens
- Executes query via Shopify REST API
- Falls back to mock data if API unavailable (for testing)

### Step 4: Result Processing
- Analyzes retrieved data
- Calculates metrics and identifies patterns
- Handles empty/partial data gracefully

### Step 5: Explanation Generation
- Converts technical data to business-friendly language
- Provides actionable insights and recommendations
- Assigns confidence level (high/medium/low)

**Complete Example Flow:**

Question: "How much inventory should I reorder for next week?"

1. **Intent**: `inventory`, timeframe: `next week`
2. **Query**: `SHOW inventory_levels FROM products WHERE quantity < 20` + sales data
3. **Execution**: Fetches inventory and sales data
4. **Processing**: Calculates daily sales rate (10 units/day), projects weekly need (70 units)
5. **Explanation**: "Based on the last 30 days, you sell around 10 units per day. You should reorder at least 70 units to avoid stockouts next week."

**Error Handling:**
- LLM unavailable → Pattern matching fallback
- Shopify API fails → Mock data for testing
- Query generation fails → Predefined templates
- Data processing errors → Partial results with lower confidence

## Project Structure

```
CafeNostalgia/
├── rails_api/
│   ├── app/
│   │   ├── controllers/api/v1/
│   │   │   ├── questions_controller.rb
│   │   │   └── auth_controller.rb
│   │   └── services/
│   │       ├── python_service_client.rb
│   │       └── shopify_oauth_service.rb
│   └── config/
│
├── python_service/
│   ├── services/
│   │   ├── ai_agent.py
│   │   └── shopify_client.py
│   └── main.py
│
└── README.md
```

## Testing

```bash
# Test Rails API
curl -X POST http://localhost:3000/api/v1/questions \
  -H "Content-Type: application/json" \
  -d '{"store_id": "example-store.myshopify.com", "question": "What were my top 5 selling products last week?"}'

# Test Python Service directly
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"store_id": "example-store.myshopify.com", "question": "How much inventory should I reorder?"}'
```

## Error Handling

- **Rails API**: Input validation (400), service errors (502), internal errors (500)
- **Python Service**: LLM fallback to pattern matching, Shopify API fallback to mock data
- **Error Response Format**: `{"error": "message", "details": "..."}`

## Security

- Shopify OAuth 2.0 authentication
- Access tokens stored in environment variables (use database in production)
- Input validation on all endpoints
- CORS configured (restrict in production)
- No sensitive data in logs

## Limitations

- Uses mock data when Shopify credentials not configured
- ShopifyQL queries executed via REST API (full ShopifyQL requires GraphQL Admin API)
- No conversation context (each question is independent)
