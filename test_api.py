import requests
import sys

def test_upload_pdf(file_path):
    """
    Test uploading a PDF file to the API.
    
    Args:
        file_path (str): Path to the PDF file to upload
    """
    url = 'http://localhost:5000/upload'
    
    try:
        with open(file_path, 'rb') as file:
            files = {'file': file}
            response = requests.post(url, files=files)
        
        if response.status_code == 200:
            print("PDF processed successfully.")
            result = response.json()
            print("\nExtracted text sample:")
            print("-" * 40)
            print(result['extracted_text_sample'])
            print("-" * 40)
            print("\nAnalysis from OpenAI:")
            print("-" * 40)
            print(result['analysis'])
            print("-" * 40)
        else:
            print(f"Error: {response.status_code}")
            print(response.json())
    except Exception as e:
        print(f"Error occurred: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_api.py <path_to_pdf_file>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    test_upload_pdf(pdf_path) 