# Market code with only food resources
import random
import numpy as np

class Market:
    def __init__(self, width=9, height=9):
        self.width = width
        self.height = height
        # Only track food, not gold
        self.grid = [[{"food": 0} for _ in range(width)] for _ in range(height)]
        self.agents = []
        self.trade_history = []
        self.distribute_resources()

    def distribute_resources(self):
    # Create a more sparse distribution of resources
        for y in range(self.height):
            for x in range(self.width):
                # Only 20% chance of food in each cell
                if random.random() < 0.05:
                    self.grid[y][x]["food"] = random.randint(1, 2)
                else:
                    self.grid[y][x]["food"] = 0

    def add_agent(self, agent, x=None, y=None):
        # Add agent to a random position or specific position
        if x is None:
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
        agent.position = (x, y)
        self.agents.append(agent)

    def move_agent(self, agent, direction):
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
        # Simple gather logic: take all food at current position
        x, y = agent.position
        food = self.grid[y][x]["food"]
        if food > 0:
            agent.food += food
            self.grid[y][x]["food"] = 0
            return food
        return 0

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
        # Find other agents within the specified distance
        nearby = []
        for other in self.agents:
            if other != agent:
                x1, y1 = agent.position
                x2, y2 = other.position
                if abs(x1 - x2) <= distance and abs(y1 - y2) <= distance:
                    nearby.append(other)
        return nearby

    def replenish_resources(self, amount=2):
        # Add a small amount of food to random cells
        for _ in range(amount):
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            self.grid[y][x]["food"] += random.randint(1, 3)