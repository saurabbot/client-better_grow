# WhatsApp Order Processor

A FastAPI backend that processes WhatsApp messages, extracts order information using OpenAI GPT-4, and creates Sales Orders in Frappe.

## Features

- WhatsApp webhook endpoint for receiving messages
- OpenAI GPT-4 integration for extracting order details
- Frappe ERP integration for creating sales orders
- Comprehensive error handling and logging
- Environment-based configuration

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file with the following variables:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   FRAPPE_API_KEY=your_frappe_api_key_here
   FRAPPE_API_SECRET=your_frappe_api_secret_here
   FRAPPE_BASE_URL=https://your-frappe-instance.com
   PORT=8000
   HOST=0.0.0.0
   ```

## Running the Application

Start the server:
```bash
python main.py
```

The server will start on the configured host and port (default: http://0.0.0.0:8000).

## API Endpoints

### POST /webhook

Receives WhatsApp messages and processes them into sales orders.

Example webhook payload:
```json
{
    "message": {
        "text": "I need 5 units of Product X at $10 each from Supplier Y"
    }
}
```

## Error Handling

The application includes comprehensive error handling and logging:
- All errors are logged to `app.log`
- API errors return appropriate HTTP status codes
- Detailed error messages are provided in the response

## Security

- All sensitive credentials are loaded from environment variables
- API keys and secrets are never exposed in the code
- HTTPS is recommended for production deployment 