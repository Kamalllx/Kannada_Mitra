# Example usage scenarios for the Kannada-English Translation Chatbot

from chat_model import ChatModel, generate_pdf_summary

def test_translation_examples():
    # Example 1: English to Kannada translation
    english_query = {
        "id": "session_001",
        "msg": "Translate to Kannada: How are you? I would like to learn Kannada."
    }
    print("\nTest Case 1: English to Kannada")
    print("Input:", english_query["msg"])
    result = ChatModel(english_query["id"], english_query["msg"])
    print("Translation Result:", result["res"]["msg"])
    print("Extracted Info:", result["info"])

    # Example 2: Kannada to English translation
    kannada_query = {
        "id": "session_002",
        "msg": "ಇಂಗ್ಲಿಷ್‌ಗೆ ಅನುವಾದಿಸಿ: ನನ್ನ ಹೆಸರು ರಾಮ. ನಾನು ಬೆಂಗಳೂರಿನಿಂದ."
    }
    print("\nTest Case 2: Kannada to English")
    print("Input:", kannada_query["msg"])
    result = ChatModel(kannada_query["id"], kannada_query["msg"])
    print("Translation Result:", result["res"]["msg"])
    print("Extracted Info:", result["info"])

    # Example 3: Mixed language input with questions
    mixed_query = {
        "id": "session_003",
        "msg": "What is ಮನೆ in English? And how do you say 'school' in Kannada?"
    }
    print("\nTest Case 3: Mixed Language Query")
    print("Input:", mixed_query["msg"])
    result = ChatModel(mixed_query["id"], mixed_query["msg"])
    print("Translation Result:", result["res"]["msg"])
    print("Extracted Info:", result["info"])

def test_conversation_flow():
    # Simulating a conversation flow
    conversation = [
        {
            "sender": "user",
            "content": "Hello! I want to learn how to introduce myself in Kannada."
        },
        {
            "sender": "assistant",
            "content": "Here's how you can introduce yourself in Kannada:\nನನ್ನ ಹೆಸರು [your name]. (nanna hesaru [your name])"
        },
        {
            "sender": "user",
            "content": "Can you break down the grammar of that sentence?"
        }
    ]
    
    # Generate PDF summary of the conversation
    pdf_buffer = generate_pdf_summary(conversation)
    with open("translation_summary.pdf", "wb") as f:
        f.write(pdf_buffer.getvalue())
    print("\nPDF summary generated: translation_summary.pdf")

def interactive_translation_session():
    print("\nInteractive Translation Session")
    print("Type 'exit' to end the session")
    session_id = "interactive_001"
    
    while True:
        user_input = input("\nEnter text to translate: ")
        if user_input.lower() == 'exit':
            break
            
        query = {
            "id": session_id,
            "msg": user_input
        }
        
        result = ChatModel(query["id"], query["msg"])
        print("\nTranslation:")
        print(result["res"]["msg"])
        print("\nAdditional Information:")
        for key, value in result["info"].items():
            if value:
                print(f"{key}: {value}")

def main():
    print("=== Kannada-English Translation Chatbot Testing ===")
    
    # Run example translation tests
    test_translation_examples()
    
    # Test conversation flow and PDF generation
    test_conversation_flow()
    
    # Run interactive session
    choice = input("\nWould you like to start an interactive translation session? (y/n): ")
    if choice.lower() == 'y':
        interactive_translation_session()

if __name__ == "__main__":
    main()

# Example output format for translations:
"""
=== Example Translation Output ===

Input: "How are you? I would like to learn Kannada."
Translation Result: {
    "translation": "ನೀವು ಹೇಗಿದ್ದೀರಿ? ನಾನು ಕನ್ನಡ ಕಲಿಯಲು ಬಯಸುತ್ತೇನೆ.",
    "transliteration": "nīvu hēgiddīri? nānu kannaḍa kaliyalu bayasuttēne.",
    "breakdown": {
        "ನೀವು": "you (formal)",
        "ಹೇಗಿದ್ದೀರಿ": "how are (formal)",
        "ನಾನು": "I",
        "ಕನ್ನಡ": "Kannada",
        "ಕಲಿಯಲು": "to learn",
        "ಬಯಸುತ್ತೇನೆ": "want/wish"
    },
    "grammar_notes": "The verb 'bayasuttēne' is in the first person present tense...",
    "cultural_notes": "In Kannada, it's common to use the formal form (ನೀವು) when speaking to strangers..."
}
"""