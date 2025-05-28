# llm_model.py
import os
import random
from dotenv import load_dotenv

# Load API key from .env file (still load in case we switch to real API later)
load_dotenv()

# Flag to use mock responses instead of real API
USE_MOCK = True

def call_gemini(prompt):
    """Mock wrapper for Gemini API to avoid quota issues"""
    if USE_MOCK:
        # Simple decision-making logic based on prompt content
        
        # Parse agent position
        position_match = None
        if "position:" in prompt:
            lines = prompt.split("\n")
            for line in lines:
                if "position:" in line:
                    position_match = line
                    break
        
        # Generate a reasonable action
        actions = ["MOVE UP", "MOVE DOWN", "MOVE LEFT", "MOVE RIGHT", "GATHER"]
        
        # If the prompt mentions food in the current position, prefer GATHER
        if "food: 0" not in prompt and "Gather if resources are present" in prompt:
            action = "GATHER" if random.random() < 0.7 else random.choice(actions)
        else:
            # Otherwise move randomly
            action = random.choice(actions)
            
        # Format as proper XML response
        return f"<ACTION>\n{action}\n</ACTION>"
    
    # Actual API call (not used due to quota)
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        response = model.generate_content(prompt)
        
        if not response.text:
            print("⚠️ Empty response from Gemini")
            return "<ACTION>\nMOVE UP\n</ACTION>"
            
        return response.text.strip()
    except Exception as e:
        print(f"⚠️ Error calling Gemini API: {e}")
        return f"<ACTION>\nMOVE {random.choice(['UP', 'DOWN', 'LEFT', 'RIGHT'])}\n</ACTION>"