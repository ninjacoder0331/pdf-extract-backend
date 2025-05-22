import os
import tempfile
import base64
import requests
import fitz  # PyMuPDF
import io
from PIL import Image
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from flask_cors import CORS


# Load environment variables
load_dotenv()

# Get OpenAI API key
api_key = os.getenv('OPENAI_API_KEY')
print("OpenAI API Key available:", bool(api_key))

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

def convert_pdf_page_to_image(page):
    """Convert a single PDF page to an image and return base64 encoding."""
    # Create a high-resolution image of the page
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    
    # Convert to PIL Image
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    
    # Convert image to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    # Convert to base64 string
    return base64.b64encode(img_bytes.getvalue()).decode('utf-8')

def analyze_pdf_with_openai(pdf_path):
    """Process PDF by converting pages to images and analyzing with OpenAI."""
    try:
        # Step 1: Open the PDF and convert pages to images
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        
        # Convert pages to images (limit to first 5 pages to avoid token limits)
        pages_to_analyze = min(5, total_pages)
        page_images = []
        
        for page_num in range(pages_to_analyze):
            page = doc.load_page(page_num)
            base64_image = convert_pdf_page_to_image(page)
            page_images.append(base64_image)
        
        doc.close()
        
        # Step 2: Prepare the OpenAI API request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # Start with text instruction
        message_content = [
            {"type": "text", "text": "Analyze these PDF pages and extract all important information. Provide a comprehensive summary."}
        ]
        
        # Add each page image to the message
        for base64_image in page_images:
            message_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{base64_image}",
                    "detail": "high"
                }
            })
        
        # Create the complete request payload
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system", 
                    "content": """You are an AI specialized in extracting structured information from invoice PDFs.
Extract ONLY the requested fields and return them in a JSON format with EXACTLY these keys:

{
  "kunde_navn": "Customer full name",
  "installationsadresse": "Installation address (full address with street, number, zip code, city)",
  "forbrug_kwh": "Energy consumption in kWh (number only)",
  "el_abonnement": "Electricity subscription cost (number only)",
  "el_afgift": "Electricity tax (number only)",
  "transport": "Transport cost (number only)",
  "samlet_pris": "Total price (number only)",
  "faktura_dato": "Invoice date in YYYY-MM-DD format",
  "udbyder": "Provider/company name"
}

Important rules:
1. Return ONLY the JSON object, nothing else.
2. If you cannot find a specific field, use null for its value.
3. For numerical values, return only the number without currency symbols or thousand separators.
4. Dates must be in YYYY-MM-DD format.
5. Do not include any explanations, analysis, or additional text - ONLY the JSON.
6. Do not make up information - if not present, use null."""
                },
                {
                    "role": "user",
                    "content": message_content
                }
            ],
            "max_tokens": 1500,
            "response_format": { "type": "json_object" }
        }
        
        # Step 3: Call the OpenAI API and process the response
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            # Extract the analysis text from the response
            analysis_text = response.json()["choices"][0]["message"]["content"]
            
            # Parse the JSON response
            try:
                # Return the extracted data along with page info
                return {
                    "extracted_data": analysis_text,
                    "total_pages": total_pages,
                    "pages_analyzed": pages_to_analyze
                }
            except Exception as e:
                return {
                    "error": f"Failed to parse response as JSON: {str(e)}",
                    "raw_response": analysis_text
                }
        else:
            return f"Error from OpenAI API: {response.status_code} - {response.text}"
            
    except Exception as e:
        return f"Error processing PDF: {str(e)}"

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy"})

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload and process a PDF file."""
    # Check if a file was included in the request
    if 'files' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['files']
    
    # Check if a file was selected
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    # Check if the file is a PDF
    if file and file.filename.endswith('.pdf'):
        # Save the uploaded file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp:
            file.save(temp.name)
            temp_path = temp.name
        
        try:
            # Process the PDF with OpenAI
            analysis_result = analyze_pdf_with_openai(temp_path)
            
            # For debugging
            print("Analysis: ==================", analysis_result)
            
            # Clean up: remove the temporary file
            os.unlink(temp_path)
            
            # Return the results
            return jsonify({
                "success": True,
                "result": analysis_result
            })
        except Exception as e:
            # Clean up in case of error
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "File must be a PDF"}), 400

if __name__ == '__main__':
    app.run(debug=True) 