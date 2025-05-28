# Market code with red and green food energy system
import random
import numpy as np

class Market:
    def __init__(self, width=9, height=9):
        self.width = width
        self.height = height
        # Track both red food (50 energy) and green food (5 energy)
        self.grid = [[{"red_food": 0, "green_food": 0} for _ in range(width)] for _ in range(height)]
        self.agents = []
        self.trade_history = []
        self.total_energy_added_per_turn = 100  # Fixed energy input to system
        self.distribute_resources()

    def distribute_resources(self):
        """Create initial distribution of red and green food"""
        # Calculate how much energy to distribute initially
        total_energy_to_distribute = self.total_energy_added_per_turn * 5  # Start with 5 turns worth
        energy_distributed = 0
        
        for y in range(self.height):
            for x in range(self.width):
                if energy_distributed >= total_energy_to_distribute:
                    break
                    
                # 15% chance of food in each cell
                if random.random() < 0.15:
                    # Decide between red and green food (70% red, 30% green for balance)
                    if random.random() < 0.7:
                        # Red food (50 energy each)
                        amount = random.randint(1, 2)
                        self.grid[y][x]["red_food"] = amount
                        energy_distributed += amount * 50
                    else:
                        # Green food (5 energy each)
                        amount = random.randint(1, 5)
                        self.grid[y][x]["green_food"] = amount
                        energy_distributed += amount * 5

    def add_agent(self, agent, x=None, y=None):
        # Add agent to a random position or specific position
        if x is None:
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
        agent.position = (x, y)
        self.agents.append(agent)

    def move_agent(self, agent, direction):
        # Only move if agent is alive
        if not agent.is_alive:
            return
            
        # Basic movement logic
        x, y = agent.position
        if direction == "UP":
            y = max(0, y - 1)
        elif direction == "DOWN":
            y = min(self.height - 1, y + 1)
        elif direction == "LEFT":
            x = max(0, x - 1)
        elif direction == "RIGHT":
            x = min(self.width - 1, x + 1)
        agent.position = (x, y)

    def gather_resources(self, agent):
        """Gather red and green food, convert to energy"""
        if not agent.is_alive:
            return 0
            
        x, y = agent.position
        total_energy_gained = 0
        
        # Gather red food (50 energy each)
        red_food = self.grid[y][x]["red_food"]
        if red_food > 0:
            energy_from_red = red_food * 50
            agent.energy += energy_from_red
            total_energy_gained += energy_from_red
            self.grid[y][x]["red_food"] = 0
            print(f"🔴 {agent.name} gathered {red_food} red food (+{energy_from_red} energy)")
        
        # Gather green food (5 energy each)
        green_food = self.grid[y][x]["green_food"]
        if green_food > 0:
            energy_from_green = green_food * 5
            agent.energy += energy_from_green
            total_energy_gained += energy_from_green
            self.grid[y][x]["green_food"] = 0
            print(f"🟢 {agent.name} gathered {green_food} green food (+{energy_from_green} energy)")
        
        return total_energy_gained

    def nearby_market_context(self, agent):
        # Get information about nearby cells
        x, y = agent.position
        context = {}
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    context[(nx, ny)] = self.grid[ny][nx]
        return context

    def nearby_agents(self, agent, distance=2):
        # Find other living agents within the specified distance
        nearby = []
        for other in self.agents:
            if other != agent and other.is_alive:
                x1, y1 = agent.position
                x2, y2 = other.position
                if abs(x1 - x2) <= distance and abs(y1 - y2) <= distance:
                    nearby.append(other)
        return nearby

    def replenish_resources(self, total_energy=None):
        """Add food to maintain fixed energy input per turn"""
        if total_energy is None:
            total_energy = self.total_energy_added_per_turn
            
        energy_added = 0
        attempts = 0
        max_attempts = 50  # Prevent infinite loop
        
        while energy_added < total_energy and attempts < max_attempts:
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            
            # Choose between red and green food (70% red, 30% green)
            if random.random() < 0.7:
                # Add red food (50 energy each)
                if energy_added + 50 <= total_energy:
                    self.grid[y][x]["red_food"] += 1
                    energy_added += 50
            else:
                # Add green food (5 energy each)
                if energy_added + 5 <= total_energy:
                    self.grid[y][x]["green_food"] += 1
                    energy_added += 5
            
            attempts += 1
        
        print(f"🌱 Market replenished with {energy_added} total energy")
        
    def remove_dead_agents(self):
        """Remove dead agents from the simulation"""
        alive_agents = [agent for agent in self.agents if agent.is_alive]
        dead_count = len(self.agents) - len(alive_agents)
        self.agents = alive_agents
        return dead_count
        
    def get_total_system_energy(self):
        """Calculate total energy in the system (agents + food)"""
        agent_energy = sum(agent.energy for agent in self.agents if agent.is_alive)
        
        food_energy = 0
        for y in range(self.height):
            for x in range(self.width):
                food_energy += self.grid[y][x]["red_food"] * 50
                food_energy += self.grid[y][x]["green_food"] * 5
                
        return agent_energy, food_energy, agent_energy + food_energy