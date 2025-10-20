import google.generativeai as genai

# Configure Gemini API with your key
genai.configure(api_key="AIzaSyC2vCvUu3PL6KtVwWA4ZSaFYf283VMSFUs")

try:
    # List available models
    print("=== AVAILABLE GEMINI MODELS ===")
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"Model: {model.name}")
            print(f"Display Name: {model.display_name}")
            print(f"Description: {model.description}")
            print("---")
            
except Exception as e:
    print(f"Error listing models: {e}")
    
    # Try with different API version
    try:
        print("\n=== TRYING WITH DIFFERENT CONFIGURATION ===")
        genai.configure(api_key="AIzaSyC2vCvUu3PL6KtVwWA4ZSaFYf283VMSFUs", transport='rest')
        
        for model in genai.list_models():
            if 'generateContent' in model.supported_generation_methods:
                print(f"Model: {model.name}")
                print(f"Display Name: {model.display_name}")
                print("---")
                
    except Exception as e2:
        print(f"Error with rest transport: {e2}")
