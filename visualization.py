# PyGame visualization for the economic simulation
import pygame
import time
import numpy as np

# Define colors
BACKGROUND = (240, 240, 240)
GRID_LINE = (200, 200, 200)
FOOD_COLOR = (0, 150, 0)
AGENT_COLORS = {
    "Risk-seeker": (255, 100, 100),    # Red
    "Risk-averse": (100, 100, 255),    # Blue
    "Cooperative": (100, 200, 100),    # Green
    "Competitive": (200, 100, 200),    # Purple
    "Opportunist": (200, 200, 0)       # Yellow
}
TEXT_COLOR = (10, 10, 10)

class Visualization:
    def __init__(self, width=9, height=9, cell_size=60):
        pygame.init()
        
        self.width = width
        self.height = height
        self.cell_size = cell_size
        
        # Calculate window size with extra space for trade dialog
        screen_width = width * cell_size + 1
        screen_height = height * cell_size + 201  # Extra 200px for trade dialog
        
        # Create the display
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Economic Agent Simulation")
        
        # Set up fonts
        self.font = pygame.font.SysFont('Arial', 12)
        self.title_font = pygame.font.SysFont('Arial', 16, bold=True)
        
        # Trade dialog area
        self.dialog_rect = pygame.Rect(0, height * cell_size + 1, screen_width, 200)
        
        # Dictionary to track trade dialogs
        self.trade_dialogs = {}
    
    def draw_grid(self, market):
        self.screen.fill(BACKGROUND)
        
        # Draw grid lines
        for x in range(self.width + 1):
            pygame.draw.line(
                self.screen, 
                GRID_LINE, 
                (x * self.cell_size, 0), 
                (x * self.cell_size, self.height * self.cell_size)
            )
        
        for y in range(self.height + 1):
            pygame.draw.line(
                self.screen, 
                GRID_LINE, 
                (0, y * self.cell_size), 
                (self.width * self.cell_size, y * self.cell_size)
            )
        
        # Draw food - make it proportional but with a maximum size
        for y in range(self.height):
            for x in range(self.width):
                food = market.grid[y][x]["food"]
                if food > 0:
                    # Smaller food circles
                    radius = min(5 * food, self.cell_size // 4)
                    center_x = x * self.cell_size + self.cell_size // 2
                    center_y = y * self.cell_size + self.cell_size // 2
                    pygame.draw.circle(self.screen, FOOD_COLOR, (center_x, center_y), radius)
    
    def draw_agents(self, agents):
        for agent in agents:
            x, y = agent.position
            
            # Calculate center of cell
            center_x = x * self.cell_size + self.cell_size // 2
            center_y = y * self.cell_size + self.cell_size // 2
            
            # Draw agent as colored circle
            color = AGENT_COLORS.get(agent.persona, (150, 150, 150))
            pygame.draw.circle(self.screen, color, (center_x, center_y), self.cell_size // 3)
            
            # Draw agent name
            text = self.font.render(agent.name.split('_')[1], True, TEXT_COLOR)
            text_rect = text.get_rect(center=(center_x, center_y - self.cell_size // 4))
            self.screen.blit(text, text_rect)
            
            # Draw food amount
            food_text = self.font.render(f"F:{agent.food}", True, TEXT_COLOR)
            food_rect = food_text.get_rect(center=(center_x, center_y + self.cell_size // 6))
            self.screen.blit(food_text, food_rect)
    
    def draw_trade_dialog(self, agents):
        # Clear dialog area
        pygame.draw.rect(self.screen, (220, 220, 220), self.dialog_rect)
        pygame.draw.line(self.screen, GRID_LINE, 
                          (0, self.height * self.cell_size), 
                          (self.width * self.cell_size, self.height * self.cell_size))
        
        # Draw title
        title = self.title_font.render("Recent Trade Activity", True, TEXT_COLOR)
        self.screen.blit(title, (10, self.height * self.cell_size + 5))
        
        # Track recent trades
        y_pos = self.height * self.cell_size + 30
        trades_shown = 0
        
        for agent in agents:
            if agent.latest_trade and trades_shown < 4:  # Show up to 4 recent trades
                trade = agent.latest_trade
                # Format: Agent A -> Agent B: 2 food (ACCEPTED/REJECTED: reason)
                status = "ACCEPTED" if trade["accepted"] else "REJECTED"
                color = (0, 130, 0) if trade["accepted"] else (180, 0, 0)
                
                trade_text = f"{trade['from']} offered {trade['amount']} food to {agent.name}: {status}"
                reason_text = f"Reason: {trade['reason'][:50]}..." if len(trade['reason']) > 50 else f"Reason: {trade['reason']}"
                
                text1 = self.font.render(trade_text, True, color)
                text2 = self.font.render(reason_text, True, TEXT_COLOR)
                
                self.screen.blit(text1, (10, y_pos))
                self.screen.blit(text2, (20, y_pos + 15))
                
                y_pos += 40
                trades_shown += 1
        
        # Draw recent actions
        y_pos = self.height * self.cell_size + 30
        x_pos = (self.width * self.cell_size) // 2 + 10
        
        self.screen.blit(self.title_font.render("Recent Actions", True, TEXT_COLOR), (x_pos, self.height * self.cell_size + 5))
        
        actions_shown = 0
        for agent in agents:
            if agent.latest_action and actions_shown < 4:
                action_type = agent.latest_action.get("type", "")
                if action_type == "ACTION":
                    action_text = f"{agent.name}: {agent.latest_action.get('action', 'UNKNOWN')}"
                elif action_type == "TRADE_OFFER":
                    to_agent = agent.latest_action.get("to", "someone")
                    amount = agent.latest_action.get("amount", 0)
                    action_text = f"{agent.name}: Offered {amount} food to {to_agent}"
                
                text = self.font.render(action_text, True, TEXT_COLOR)
                self.screen.blit(text, (x_pos, y_pos))
                
                y_pos += 20
                actions_shown += 1
    
    def update(self, market):
        self.draw_grid(market)
        self.draw_agents(market.agents)
        self.draw_trade_dialog(market.agents)
        pygame.display.flip()
    
    def check_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False, None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False, None
                if event.key == pygame.K_SPACE:
                    return True, "PAUSE"
                if event.key == pygame.K_RIGHT:
                    return True, "STEP"
                if event.key == pygame.K_UP:
                    return True, "SPEED_UP"
                if event.key == pygame.K_DOWN:
                    return True, "SPEED_DOWN"
        return True, None
        
    def close(self):
        pygame.quit()