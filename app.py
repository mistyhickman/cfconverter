# ColdFusion Code Converter Application
# Requirements: pip install flask openai python-dotenv

import os
import openai
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get OpenAI API key from environment variables
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Initialize OpenAI client
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
    logger.info("OpenAI API key loaded successfully")
else:
    logger.error("OPENAI_API_KEY not found in environment variables")
    print("ERROR: OPENAI_API_KEY not found in .env file!")

# Allowed file extensions
ALLOWED_EXTENSIONS = {'cfm', 'cfc', 'cfml', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class CodeConverter:
    def __init__(self):
        self.supported_languages = {
            'react': 'React with JavaScript/TypeScript',
            'ruby': 'Ruby on Rails',
            'python': 'Python with Flask/Django',
            'php': 'PHP',
            'java': 'Java with Spring',
            'csharp': 'C# with ASP.NET'
        }
    
    def convert_code(self, coldfusion_code, target_language, custom_prompt=""):
        """Convert ColdFusion code to target language using GPT"""
        try:
            # Base conversion prompt
            base_prompt = f"""
You are an expert developer skilled in ColdFusion and {self.supported_languages.get(target_language, target_language)}.

Please convert the following ColdFusion code to {target_language}. 

Requirements:
1. Maintain the same functionality and logic
2. Follow best practices for {target_language}
3. Include necessary imports/dependencies
4. Add comments explaining complex conversions
5. Ensure the code is production-ready
6. Handle any ColdFusion-specific features appropriately

{custom_prompt}

ColdFusion Code to Convert:
```coldfusion
{coldfusion_code}
```

Please provide:
1. The converted code
2. A brief explanation of key changes made
3. Any additional setup or dependencies needed
"""

            # Make API call to OpenAI
            response = openai.ChatCompletion.create(
                model="gpt-4",  # Use gpt-3.5-turbo if gpt-4 is not available
                messages=[
                    {"role": "system", "content": "You are an expert code converter specializing in migrating legacy ColdFusion applications to modern frameworks."},
                    {"role": "user", "content": base_prompt}
                ],
                max_tokens=4000,
                temperature=0.1
            )
            
            return {
                'success': True,
                'converted_code': response.choices[0].message.content,
                'usage': response.usage
            }
            
        except Exception as e:
            logger.error(f"Error converting code: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

# Initialize converter
converter = CodeConverter()

@app.route('/')
def index():
    return render_template('index.html', languages=converter.supported_languages)

@app.route('/convert', methods=['POST'])
def convert_code():
    try:
        # Get form data
        target_language = request.form.get('target_language')
        custom_prompt = request.form.get('custom_prompt', '')
        coldfusion_code = request.form.get('code_input', '')
        
        # Handle file upload if provided
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                # Read file content
                with open(filepath, 'r', encoding='utf-8') as f:
                    coldfusion_code = f.read()
                
                # Clean up uploaded file
                os.remove(filepath)
        
        if not coldfusion_code.strip():
            return jsonify({'success': False, 'error': 'No ColdFusion code provided'})
        
        if not target_language:
            return jsonify({'success': False, 'error': 'No target language specified'})
        
        # Convert the code
        result = converter.convert_code(coldfusion_code, target_language, custom_prompt)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in convert_code route: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'supported_languages': list(converter.supported_languages.keys())})

if __name__ == '__main__':
    # Check if OpenAI API key is set
    if not OPENAI_API_KEY:
        print("\n" + "="*50)
        print("❌ ERROR: OPENAI_API_KEY not found!")
        print("="*50)
        print("Please create a .env file in your project directory with:")
        print("OPENAI_API_KEY=your_actual_api_key_here")
        print("\nTo get an API key:")
        print("1. Go to https://platform.openai.com/api-keys")
        print("2. Create a new API key")
        print("3. Copy it to your .env file")
        print("="*50 + "\n")
        exit(1)
    
    print(f"🚀 Starting ColdFusion Converter...")
    print(f"📡 Server running at: http://localhost:5000")
    print(f"✅ OpenAI API key loaded successfully")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)