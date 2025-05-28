# Simplified economic agent with basic decision-making
import yaml
from llm_model import call_gemini
import re

class EconomicAgent:
    def __init__(self, name, persona):
        self.name = name
        self.persona = persona
        self.position = (0, 0)
        self.food = 0
        self.latest_action = None
        self.latest_trade = None
    
    def decide_action(self, market):
        # Get context about nearby resources and agents
        market_context = market.nearby_market_context(self)
        nearby_agents = market.nearby_agents(self)
        
        # Format YAML for agent state and context
        agent_yaml = yaml.dump({
            "name": self.name,
            "position": self.position,
            "food": self.food,
            "persona": self.persona
        }, sort_keys=False)
        
        market_yaml = yaml.dump({str(pos): resources for pos, resources in market_context.items() if resources["food"] > 0}, sort_keys=False)
        
        nearby_agents_yaml = yaml.dump({
            a.name: {
                "position": a.position,
                "food": a.food,
                "persona": a.persona
            } for a in nearby_agents
        }, sort_keys=False) if nearby_agents else "None"
        
        # Build the prompt for Gemini
        prompt = f"""
            You are an economic agent in a 9x9 grid simulation.

            Your Profile:
            {agent_yaml}

            Nearby Market Cells With Resources:
            {market_yaml}

            Nearby Agents:
            {nearby_agents_yaml}

            IMPORTANT: You should ALWAYS choose to move, gather, or trade if possible. WAIT should only be used as a last resort.

            Available Actions:
            - MOVE UP / MOVE DOWN / MOVE LEFT / MOVE RIGHT (Choose a direction toward food or unexplored areas)
            - GATHER (Use this when you are on a cell with food)
            - WAIT (Only use if no other action makes sense)

            If there's a nearby agent and you want to trade, respond with:
            <TRADE_OFFER>
            offer: [amount] food
            to: [agent_name]
            </TRADE_OFFER>

            Otherwise, respond with:
            <ACTION>
            [YOUR_ACTION_HERE]
            </ACTION>

            STRATEGY HINTS:
            - If you see food in an adjacent cell, MOVE toward it
            - If there's food in your current cell, GATHER it
            - If you don't see any resources nearby, MOVE in a random direction to explore
            - "{self.persona}" agents should be especially active in finding resources

            IMPORTANT TRADING INSTRUCTIONS:
            - If you are near another agent, strongly consider making a trade offer
            - Trading is always beneficial compared to waiting
            - If you have 2 or more food, you should try to trade 1 food with a nearby agent
            """
        
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
                    offer_match = re.search(r"offer:\s*(\d+)\s*food", trade_text)
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
        # Make a decision about a trade offer
        prompt = f"""
You are {self.name}, an economic agent with the persona: {self.persona}.

You have {self.food} food.

{from_agent.name} (persona: {from_agent.persona}) is offering you a trade:
- They want to give you: {offer['amount']} food

Decide whether to ACCEPT or REJECT this offer based on your needs and persona.
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