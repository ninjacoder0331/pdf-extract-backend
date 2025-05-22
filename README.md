# PDF Parser with OpenAI

A simple Python backend for parsing PDF files using OpenAI's API.

## Setup

1. Create a virtual environment:
```
python -m venv venv
```

2. Activate the virtual environment:
- Windows: `venv\Scripts\activate`
- Unix/MacOS: `source venv/bin/activate`

3. Install dependencies:
```
pip install -r requirements.txt
```

4. Create a `.env` file with your OpenAI API key:
```
OPENAI_API_KEY=your_openai_api_key_here
```

## Running the Application

Run the Flask application:
```
python app.py
```

The server will start on http://localhost:5000.

## API Endpoints

- `POST /upload` - Upload and process a PDF file
- `GET /health` - Health check endpoint

## Example Usage

```python
import requests

url = 'http://localhost:5000/upload'
files = {'file': open('sample.pdf', 'rb')}

response = requests.post(url, files=files)
print(response.json())
``` 