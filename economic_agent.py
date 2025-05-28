# Simplified economic agent with basic decision-making
import yaml
from llm_model import call_gemini
import re

class EconomicAgent:
    def __init__(self, name, persona):
        self.name = name
        self.persona = persona
        self.position = (0, 0)
        self.food = 50
        self.latest_action = None
        self.latest_trade = None
        self.energy = 50  # Changed from food to energy, starting with 50 energy
        self.energy_loss_per_turn = 1  # Fixed energy consumption per turn
        self.is_alive = True  # Track if agent is alive


    def lose_energy_per_turn(self):
        """Called each turn to deduct energy. Agent dies if energy <= 0"""
        if self.is_alive:
            self.energy -= self.energy_loss_per_turn
            if self.energy <= 0:
                self.is_alive = False
                print(f"💀 {self.name} has died from lack of energy!")
    
    def decide_action(self, market):
        # Skip decision if agent is dead
        if not self.is_alive:
            return {"type": "ACTION", "action": "DEAD"}, "Agent is dead"
        
        # Get context about nearby resources and agents
        market_context = market.nearby_market_context(self)
        nearby_agents = market.nearby_agents(self)
        
        # Format YAML for agent state and context
        agent_yaml = yaml.dump({
            "name": self.name,
            "position": self.position,
            "energy": self.energy,  # Changed from food
            "energy_loss_per_turn": self.energy_loss_per_turn,
            "persona": self.persona
        }, sort_keys=False)
        
        
        # Update market context to show red and green food
        market_yaml = yaml.dump({
            str(pos): {
                "red_food": resources["red_food"], 
                "green_food": resources["green_food"]
            } for pos, resources in market_context.items() 
            if resources["red_food"] > 0 or resources["green_food"] > 0
        }, sort_keys=False)
        

        nearby_agents_yaml = yaml.dump({
            a.name: {
                "position": a.position,
                "energy": a.energy,  # Changed from food
                "persona": a.persona
            } for a in nearby_agents if a.is_alive
        }, sort_keys=False) if nearby_agents else "None"
        
        # Build the prompt for Gemini
        prompt = f"""
            You are an economic agent in a 9x9 grid simulation with an ENERGY SYSTEM.

            Your Profile:
            {agent_yaml}

            ENERGY RULES:
            - You lose {self.energy_loss_per_turn} energy every turn
            - You DIE if your energy reaches 0 or below
            - Red food gives 50 energy when gathered
            - Green food gives 5 energy when gathered

            Nearby Market Cells With Food:
            {market_yaml}

            Nearby Agents:
            {nearby_agents_yaml}

            CRITICAL: You must maintain your energy above 0 to survive! Prioritize gathering food if your energy is low.

            Available Actions:
            - MOVE UP / MOVE DOWN / MOVE LEFT / MOVE RIGHT (Choose a direction toward food)
            - GATHER (Use this when you are on a cell with red_food or green_food)
            - WAIT (Only use if no other action makes sense)

            If there's a nearby agent and you want to trade energy, respond with:
            <TRADE_OFFER>
            offer: [amount] energy
            to: [agent_name]
            </TRADE_OFFER>

            Otherwise, respond with:
            <ACTION>
            [YOUR_ACTION_HERE]
            </ACTION>

            STRATEGY HINTS:
            - If you see red food (50 energy), prioritize it over green food (5 energy)
            - If your energy is below 10, focus entirely on survival - find food immediately
            - If you don't see any food nearby, MOVE in a direction to explore
            - Consider your energy loss rate when making decisions
            """
        
        # Call Gemini and parse the response
        response = call_gemini(prompt)
        decision = self.parse_action(response)
        self.latest_action = decision
        return decision, response
        
        # Call Gemini and parse the response
        response = call_gemini(prompt)
        decision = self.parse_action(response)
        self.latest_action = decision
        return decision, response
    
    def parse_action(self, response_text):
        """
        Extract <ACTION> or <TRADE_OFFER> from Gemini response.
        Returns a dictionary with the parsed action.
        """
        try:
            if "<TRADE_OFFER>" in response_text:
                trade_match = re.search(r"<TRADE_OFFER>(.*?)</TRADE_OFFER>", response_text, re.DOTALL)
                if trade_match:
                    trade_text = trade_match.group(1).strip()
                    offer_match = re.search(r"offer:\s*(\d+)\s*energy", trade_text)
                    to_match = re.search(r"to:\s*(\w+)", trade_text)
                    
                    if offer_match and to_match:
                        return {
                            "type": "TRADE_OFFER",
                            "amount": int(offer_match.group(1)),
                            "to": to_match.group(1)
                        }
            
            # Parse simple action
            action_match = re.search(r"<ACTION>\s*(.*?)\s*</ACTION>", response_text, re.DOTALL)
            if action_match:
                action = action_match.group(1).strip().upper()
                if action in ["MOVE UP", "MOVE DOWN", "MOVE LEFT", "MOVE RIGHT", "GATHER", "WAIT"]:
                    return {"type": "ACTION", "action": action}
            
            # If we get here, something went wrong with parsing
            print(f"Warning: Could not parse response: {response_text}")
            # Default to a random move
            return {"type": "ACTION", "action": f"MOVE {random.choice(['UP', 'DOWN', 'LEFT', 'RIGHT'])}"}
            
        except Exception as e:
            print(f"⚠️ Error parsing response: {e}")
            return {"type": "ACTION", "action": "WAIT"}
    
    def evaluate_trade(self, offer, from_agent):
        # Only evaluate trades if alive
        if not self.is_alive:
            return False, "Agent is dead"
            
        # Make a decision about a trade offer
        prompt = f"""
        You are {self.name}, an economic agent with the persona: {self.persona}.

        ENERGY SYSTEM:
        - You currently have {self.energy} energy
        - You lose {self.energy_loss_per_turn} energy per turn
        - You DIE if energy reaches 0

        {from_agent.name} (persona: {from_agent.persona}) is offering you a trade:
        - They want to give you: {offer['amount']} energy

        Decide whether to ACCEPT or REJECT this offer based on your energy needs and survival.
        Reply with either:

        <DECISION>
        ACCEPT
        </DECISION>

        OR

        <DECISION>
        REJECT
        </DECISION>

        <REASON>
        Brief explanation for your decision
        </REASON>
        """
        
        response = call_gemini(prompt)
        
        # Parse decision
        decision_match = re.search(r"<DECISION>\s*(.*?)\s*</DECISION>", response, re.DOTALL)
        reason_match = re.search(r"<REASON>\s*(.*?)\s*</REASON>", response, re.DOTALL)
        
        accepted = decision_match and decision_match.group(1).strip().upper() == "ACCEPT"
        reason = reason_match.group(1).strip() if reason_match else "(No explanation provided)"
        
        # Save the trade outcome for visualization
        self.latest_trade = {
            "from": from_agent.name,
            "amount": offer['amount'],
            "accepted": accepted,
            "reason": reason
        }
        
        return accepted, reason