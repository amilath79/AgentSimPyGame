# llm_model.py - Energy-aware mock responses
import os
import random
from dotenv import load_dotenv

# Load API key from .env file (still load in case we switch to real API later)
load_dotenv()

# Flag to use mock responses instead of real API
USE_MOCK = True

def call_gemini(prompt):
    """Mock wrapper for Gemini API with energy-aware decision making"""
    if USE_MOCK:
        # Parse agent's current energy from prompt
        current_energy = 50  # default
        if "energy:" in prompt:
            lines = prompt.split("\n")
            for line in lines:
                if "energy:" in line:
                    try:
                        current_energy = int(line.split("energy:")[1].strip())
                    except:
                        pass
                    break
        
        # Parse nearby food information
        has_red_food_nearby = "red_food:" in prompt and not "red_food: 0" in prompt
        has_green_food_nearby = "green_food:" in prompt and not "green_food: 0" in prompt
        has_food_here = False
        
        # Check if there's food at current position
        if "position:" in prompt:
            position_match = None
            for line in prompt.split("\n"):
                if "position:" in line:
                    position_match = line
                    break
            
            if position_match:
                # Look for food at the same position in the market context
                for line in prompt.split("\n"):
                    if position_match.split("position:")[1].strip() in line:
                        if ("red_food:" in line and not "red_food: 0" in line) or \
                           ("green_food:" in line and not "green_food: 0" in line):
                            has_food_here = True
                            break
        
        # Energy-based decision making
        is_low_energy = current_energy <= 15
        is_critical_energy = current_energy <= 8
        
        # Decision logic
        if has_food_here:
            # Always gather if there's food at current position
            action = "GATHER"
        elif is_critical_energy and (has_red_food_nearby or has_green_food_nearby):
            # Critical energy: move toward any food
            if has_red_food_nearby:
                # Prefer red food (50 energy) over green food (5 energy)
                actions = ["MOVE UP", "MOVE DOWN", "MOVE LEFT", "MOVE RIGHT"]
                action = random.choice(actions)
            else:
                actions = ["MOVE UP", "MOVE DOWN", "MOVE LEFT", "MOVE RIGHT"] 
                action = random.choice(actions)
        elif is_low_energy:
            # Low energy: prioritize movement toward food
            if has_red_food_nearby or has_green_food_nearby:
                actions = ["MOVE UP", "MOVE DOWN", "MOVE LEFT", "MOVE RIGHT"]
                action = random.choice(actions)
            else:
                # Explore to find food
                actions = ["MOVE UP", "MOVE DOWN", "MOVE LEFT", "MOVE RIGHT"]
                action = random.choice(actions)
        else:
            # Normal energy: balanced behavior
            
            # Check for trade opportunities (if multiple agents nearby and not low energy)
            if "Nearby Agents:" in prompt and current_energy > 20:
                # Sometimes try to trade
                if random.random() < 0.3:  # 30% chance to trade
                    # Look for agent names in nearby agents section
                    agents_section = prompt.split("Nearby Agents:")[1] if "Nearby Agents:" in prompt else ""
                    if "Agent_" in agents_section and "None" not in agents_section:
                        # Extract first agent name (simple parsing)
                        for line in agents_section.split("\n"):
                            if "Agent_" in line:
                                agent_name = line.split(":")[0].strip()
                                trade_amount = random.randint(3, 8)
                                return f"<TRADE_OFFER>\noffer: {trade_amount} energy\nto: {agent_name}\n</TRADE_OFFER>"
            
            # Normal movement/gathering behavior
            if has_red_food_nearby:
                # Move toward high-value red food
                actions = ["MOVE UP", "MOVE DOWN", "MOVE LEFT", "MOVE RIGHT"]
                action = random.choice(actions)
            elif has_green_food_nearby:
                # Move toward green food if no red food available
                actions = ["MOVE UP", "MOVE DOWN", "MOVE LEFT", "MOVE RIGHT"]
                action = random.choice(actions)
            else:
                # Explore
                actions = ["MOVE UP", "MOVE DOWN", "MOVE LEFT", "MOVE RIGHT", "WAIT"]
                # Reduce waiting when no food is visible
                action_weights = [1, 1, 1, 1, 0.2]  # Less likely to wait
                action = random.choices(actions, weights=action_weights)[0]
        
        # Handle trade evaluation prompts
        if "ACCEPT or REJECT this offer" in prompt:
            # Parse the trade amount
            trade_amount = 0
            if "giving you:" in prompt:
                for line in prompt.split("\n"):
                    if "giving you:" in line and "energy" in line:
                        try:
                            trade_amount = int(line.split("giving you:")[1].replace("energy", "").strip())
                        except:
                            pass
                        break
            
            # Decision based on current energy level
            if current_energy <= 10:
                # Desperately need energy
                decision = "ACCEPT"
                reason = "I desperately need energy to survive"
            elif current_energy <= 20:
                # Low energy, likely accept
                decision = "ACCEPT" if random.random() < 0.8 else "REJECT"
                reason = "I need energy" if decision == "ACCEPT" else "Not enough benefit"
            elif current_energy >= 40:
                # High energy, might not need it
                decision = "REJECT" if random.random() < 0.6 else "ACCEPT"
                reason = "I have enough energy" if decision == "REJECT" else "Could be useful later"
            else:
                # Medium energy, balanced decision
                decision = "ACCEPT" if random.random() < 0.5 else "REJECT"
                reason = "Fair trade" if decision == "ACCEPT" else "Not the right time"
            
            return f"<DECISION>\n{decision}\n</DECISION>\n\n<REASON>\n{reason}\n</REASON>"
        
        # Format as proper XML response for actions
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