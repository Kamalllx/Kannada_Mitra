import sys
from time import sleep
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
import json
import re

# Initialize Google's Generative AI for translation
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    google_api_key="AIzaSyDIG-JhAjoTJPZV_M5CGzjhIX8klNbXm3I"

)

@tool
def detect_language(text: str) -> dict:
    """Detect if the input text is primarily Kannada or English"""
    # Regex patterns for Kannada and English
    kannada_pattern = r'[\u0C80-\u0CFF]'
    english_pattern = r'[a-zA-Z]'
    
    kannada_chars = len(re.findall(kannada_pattern, text))
    english_chars = len(re.findall(english_pattern, text))
    
    if kannada_chars > english_chars:
        return {"detected_language": "kannada"}
    return {"detected_language": "english"}

@tool
def translate_to_english(text: str) -> dict:
    """Translate Kannada text to English"""
    prompt = f"""
    Translate the following Kannada text to English:
    {text}
    
    Provide the translation in a natural, conversational style while maintaining accuracy.
    Also provide:
    1. Literal translation
    2. Contextual meaning
    3. Any cultural notes if relevant
    
    Return as JSON with keys: translation, literal, context, cultural_notes
    """
    response = llm.invoke(prompt)
    try:
        return json.loads(response.content)
    except json.JSONDecodeError:
        return {
            "translation": response.content,
            "literal": "",
            "context": "",
            "cultural_notes": ""
        }

@tool
def translate_to_kannada(text: str) -> dict:
    """Translate English text to Kannada"""
    prompt = f"""
    Translate the following English text to Kannada:
    {text}
    
    Provide the translation in both Kannada script and transliteration.
    Also provide:
    1. Word-by-word breakdown
    2. Usage examples
    3. Any relevant grammatical notes
    
    Return as JSON with keys: translation, transliteration, breakdown, examples, grammar_notes
    """
    response = llm.invoke(prompt)
    try:
        return json.loads(response.content)
    except json.JSONDecodeError:
        return {
            "translation": response.content,
            "transliteration": "",
            "breakdown": "",
            "examples": "",
            "grammar_notes": ""
        }

def extract_translation_info(content):
    """Extract translation information for summary generation"""
    prompt = f"""
    Extract the translation information from the following conversation:
    {content}
    
    Return the information in JSON format with the following keys:
    - original_text: The original text being translated
    - translated_text: The translation provided
    - source_language: The language of the original text
    - target_language: The language of the translation
    - cultural_notes: Any cultural context provided
    - grammar_notes: Any grammatical notes provided
    - examples: Any usage examples provided
    """
    
    response = llm.invoke(prompt)
    try:
        return json.loads(response.content)
    except json.JSONDecodeError:
        return {}

def generate_pdf_summary(conversation_summary):
    """Generate PDF summary of the translation session"""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "Translation Session Summary")
    
    c.setFont("Helvetica", 12)
    y = height - 80
    
    # Add each section to the PDF
    sections = [
        ("Original Text", conversation_summary.get("original_text", "")),
        ("Translated Text", conversation_summary.get("translated_text", "")),
        ("Source Language", conversation_summary.get("source_language", "")),
        ("Target Language", conversation_summary.get("target_language", "")),
        ("Cultural Notes", conversation_summary.get("cultural_notes", "")),
        ("Grammar Notes", conversation_summary.get("grammar_notes", "")),
        ("Examples", conversation_summary.get("examples", ""))
    ]
    
    for title, content in sections:
        if content:
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y, title)
            y -= 20
            c.setFont("Helvetica", 12)
            # Handle multi-line content
            for line in content.split('\n'):
                c.drawString(50, y, line)
                y -= 20
            y -= 10
    
    c.save()
    buffer.seek(0)
    return buffer

tools = [detect_language, translate_to_english, translate_to_kannada]

def ChatModel(id, msg):
    config = {"configurable": {"thread_id": id}}
    inputs = {"messages": [("user", msg)]}
    
    try:
        res = print_stream(graph, inputs, config)
        extraction = extract_translation_info(res["msg"])
        return {"res": res, "info": extraction}
    except Exception as e:
        print("Error in ChatModel:", str(e))
        return {
            "res": {
                "msg": "ಕ್ಷಮಿಸಿ, ದೋಷ ಸಂಭವಿಸಿದೆ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ. / Sorry, an error occurred. Please try again.",
                "toolCall": {}
            },
            "info": {}
        }

def print_stream(graph, inputs, config):
    msg = ""
    toolCall = {}
    for s in graph.stream(inputs, config, stream_mode="values"):
        message = s["messages"][-1]
        if message.type == "ai":
            msg = msg + message.content
        elif message.type == "tool":
            toolCall = json.loads(message.content)
        
        if isinstance(message, tuple):
            print(message)
        else:
            message.pretty_print()
    return {"msg": msg, "toolCall": toolCall}

graph = create_react_agent(llm, tools, checkpointer=MemorySaver(), state_modifier='''You are KannadaGuru, an AI-powered Kannada-English translation assistant. Your primary role is to provide accurate translations between Kannada and English while helping users understand the cultural and linguistic nuances of both languages.

Key Features:
1. Bidirectional Translation: You can translate from Kannada to English and vice versa.
2. Language Detection: You automatically detect whether the input is in Kannada or English.
3. Cultural Context: You provide cultural notes and explanations when relevant.
4. Grammar Assistance: You explain grammatical structures and patterns.
5. Learning Support: You offer word-by-word breakdowns and usage examples.

Formatting Guidelines:
1. **Separate the translation and the pronunciation**: 
   - Use the heading *Translation:* followed by the translation text.
   - Include the pronunciation in parentheses after the translated word or phrase, using **bold** for the translated text.
2. **Use bullet points** for breakdowns:
   - Begin each key explanation with a bullet point and bold the terms or phrases that are being explained.
   - Each point should be on a new line for clarity.
3. **Maintain clarity and spacing**:
   - Use extra line spacing between sections to improve readability.
   - Ensure the response is structured and easy to follow.
**Guidelines:**
1. Always maintain accuracy while ensuring natural-sounding translations.
2. Provide both literal and contextual translations when appropriate.
3. Include transliteration for Kannada text to help with pronunciation.
4. Explain idioms, cultural references, and context-specific usage.
5. Offer grammatical explanations when helpful.
6. Be patient and supportive, especially with beginners.

Start each conversation by greeting in both languages and asking how you can help with translation today.
Example greeting:
ನಮಸ್ಕಾರ! Hello! I'm KannadaGuru, your Kannada-English translation assistant.
How can I help you with translation today?

Example output:
*Translation:* 
ನಮಸ್ಕಾರ! Hello! You're asking about the spelling of "banana" in Kannada. 
Here's how you spell it:
**ಬಾಳೆಹಣ್ಣು** (bāḷehaṇṇu) 

Let's break it down: 
* **ಬಾಳೆ** (bāḷe) means "banana tree" 
* **ಹಣ್ಣು** (haṇṇu) means "fruit" 

So, **ಬಾಳೆಹಣ್ಣು** literally translates to "banana fruit". 
It's a common word used in everyday conversations.

NOTE: Always remember to write the prnounciation of the kannada word using english letters in brackets whenever a kannada word is there in the output
''')

