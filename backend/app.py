from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from chat_model import *
import json
import os
import google.generativeai as genai
from PIL import Image

# Configure Gemini
os.environ["GOOGLE_API_KEY"] = "AIzaSyDvHS-6L1iDiTgu5zBUWs4GeCb0bIOveyk"
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")
s=[]
@app.route('/voice/response', methods=['POST'])
def handle_voice_response():
    """Handle voice input for translation"""
    data = request.json
    print("Voice input received:", data)
    emit("voice_response", data)
    return jsonify({"status": "Voice input processed"})

@app.route('/generate_summary', methods=['POST'])
def generate_summary_route():
    """Generate summary of conversation."""
    conversation_history = s # Adjust as needed

    try:
        # Use the generative model to create a summary
        summary_response = model.generate_content(
            ["Provide a concise summary of the following conversation:", "\n".join(conversation_history)]
        )

        summary_text = summary_response.text
        print("\n\n\nsummary =", summary_text)
        return jsonify({"summary": summary_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/send_message', methods=['POST'])
def handle_send_message_http():
    """Handle translation requests via HTTP POST"""
    msg = request.json
    print("Translation request received:", msg)
    res = ChatModel(msg["id"], msg["msg"])
    s.append(res)
    print("Translation response:", res)
    return jsonify(res)

@socketio.on('send_message')
def handle_send_message_socket(msg):
    """Handle translation requests via WebSocket"""
    print("Translation request received:", msg)
    res = ChatModel(msg["id"], msg["msg"])
    print("Translation response:", res)
    socketio.emit("response", res)

@app.route('/feedback', methods=['POST'])
def handle_feedback():
    """Handle user feedback on translations"""
    feedback = request.json
    print("Feedback received:", feedback)
    return jsonify({"status": "Feedback received", "message": "Thank you for your feedback!"})

@app.route('/save_translation', methods=['POST'])
def save_translation():
    """Save translation history for users"""
    translation_data = request.json
    print("Translation saved:", translation_data)
    return jsonify({"status": "Translation saved"})

@app.route('/image/translate', methods=['POST'])
def handle_image_upload():
    """Handle image upload and send it to the model for translation."""
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        # Open the uploaded image using PIL
        image = Image.open(file)
        
        # Call the translate_image function to get the description
        response = translate_image(image)
        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def translate_image(image):
    """Send the image to the generative AI model and return the response."""
    try:
        # Generate content from the image using the generative model
        response = model.generate_content(['''Describe this image in short and in points. Describe it in maximum 2 short sentences.
                                           Formatting Guidelines:
1. **Separate the translation and the pronunciation**: 
   - Use the heading *Translation:* followed by the translation text.
   - Include the pronunciation in parentheses after the translated word or phrase, using **bold** for the translated text.
2. **Use bullet points** for breakdowns:
   - Begin each key explanation with a bullet point and bold the terms or phrases that are being explained.
   - Each point should be on a new line for clarity.
3. **Maintain clarity and spacing**:
   - Use extra line spacing between sections to improve readability.
   - Ensure the response is structured and easy to follow. ''', image])

        # Parse the response text into multiple descriptions
        description_en = response.text  # Assume the response is in English
        description_kn = translate_to_kannada(description_en)  # Custom translation logic
        transliteration = transliterate(description_kn)  # Optional transliteration logic
        s.append((description_en,description_kn,transliteration))
       
        return {
            "description_en": description_en,
            "description_kn": description_kn,
            "description_transliteration": transliteration,
        }

    except Exception as e:
        raise RuntimeError(f"Image translation failed: {e}")

def translate_to_kannada(text):
    """Translate English text to Kannada using the Gemini model."""
    response = model.generate_content(['''Translate this text to Kannada and after each sentence in the next line write the pronunciation of the sentence using English letters. Enter a new line for each sentence. 
    Formatting Guidelines:
1. **Separate the translation and the pronunciation**: 
   - Use the heading *Translation:* followed by the translation text.
   - Include the pronunciation in parentheses after the translated word or phrase, using **bold** for the translated text.
2. **Use bullet points** for breakdowns:
   - Begin each key explanation with a bullet point and bold the terms or phrases that are being explained.
   - Each point should be on a new line for clarity.
3. **Maintain clarity and spacing**:
   - Use extra line spacing between sections to improve readability.
   - Ensure the response is structured and easy to follow.''', text])

    description_kn = response.text
    return description_kn

def transliterate(text):
    """Transliterate Kannada text using the Gemini model."""
    response = model.generate_content(["Write the Kannada text using English letters so that beginners can understand it. Also, process each word and break down the pronunciation of each word using English letters.", text])    
    transliteration = response.text
    return transliteration

@app.route('/analyze_audio', methods=['POST'])
def analyze_audio():
    try:
        data = request.json
        kannada_transcript = data.get('transcript')

        if not kannada_transcript:
            return jsonify({'error': 'No transcript provided'}), 400

        # Generate English transliteration
        transliteration = transliterate(kannada_transcript)

        # Analyze pronunciation using custom rules
        def analyze_pronunciation(text, transliteration):
            common_mistakes = {
                'ಳ': {'roman': 'La', 'common_error': 'la', 'explanation': 'Should be pronounced with retroflex L'},
                'ಠ': {'roman': 'Tha', 'common_error': 'ta', 'explanation': 'Should be pronounced with more aspiration'},
            }
            
            corrections = []
            score = 100
            for char in text:
                if char in common_mistakes:
                    score -= 5
                    corrections.append({
                        'word': char,
                        'suggestion': common_mistakes[char]['roman'],
                        'reason': common_mistakes[char]['explanation']
                    })
            
            return {
                'isCorrect': score > 90,
                'score': score,
                'corrections': corrections
            }

        pronunciation_analysis = analyze_pronunciation(kannada_transcript, transliteration)

        # Get Gemini analysis
        prompt = f"""
        Analyze the following Kannada text and its transliteration:
        
        Kannada: {kannada_transcript}
        Transliteration: {transliteration}
        
        Please provide:
        1. Whether the pronunciation and grammar follows standard Kannada pronunciation rules
        2. Any specific areas where pronunciation might be challenging
        3. Tips for improving pronunciation
        4. Common mistakes to avoid
        
        NOTE: the Analysis should be very strict, the score allotment should be very particular should ensure accuracy and grammar as the most important fields of marking scheme.
        Format the response in a clear, structured way.
        """

        gemini_response = model.generate_content(prompt)
        gemini_analysis = gemini_response.text
        
    
        response = {
            'transcript': kannada_transcript,
            'transliteration': transliteration,
            'pronunciationAnalysis': pronunciation_analysis,
            'geminiAnalysis': gemini_analysis
        }
        s.append(response)
        return jsonify(response)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    socketio.run(app, debug=True, host='127.0.0.1', port=5000)
