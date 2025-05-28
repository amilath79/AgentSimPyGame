# PyGame visualization for the energy-based economic simulation
import pygame
import time
import numpy as np

# Define colors
BACKGROUND = (240, 240, 240)
GRID_LINE = (200, 200, 200)
RED_FOOD_COLOR = (220, 50, 50)     # Red food (50 energy)
GREEN_FOOD_COLOR = (50, 180, 50)   # Green food (5 energy)
AGENT_COLORS = {
    "Risk-seeker": (255, 100, 100),    # Red
    "Risk-averse": (100, 100, 255),    # Blue
    "Cooperative": (100, 200, 100),    # Green
    "Competitive": (200, 100, 200),    # Purple
    "Opportunist": (200, 200, 0)       # Yellow
}
DEAD_AGENT_COLOR = (80, 80, 80)    # Gray for dead agents
TEXT_COLOR = (10, 10, 10)

class Visualization:
    def __init__(self, width=9, height=9, cell_size=60):
        pygame.init()
        
        self.width = width
        self.height = height
        self.cell_size = cell_size
        
        # Calculate window size with extra space for energy info and trade dialog
        screen_width = width * cell_size + 1
        screen_height = height * cell_size + 251  # Extra 250px for info panels
        
        # Create the display
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Energy-Based Economic Agent Simulation")
        
        # Set up fonts
        self.font = pygame.font.SysFont('Arial', 12)
        self.title_font = pygame.font.SysFont('Arial', 16, bold=True)
        
        # Info panels
        self.trade_dialog_rect = pygame.Rect(0, height * cell_size + 1, screen_width // 2, 125)
        self.energy_info_rect = pygame.Rect(screen_width // 2, height * cell_size + 1, screen_width // 2, 125)
        self.system_info_rect = pygame.Rect(0, height * cell_size + 126, screen_width, 125)
        
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
        
        # Draw red and green food
        for y in range(self.height):
            for x in range(self.width):
                center_x = x * self.cell_size + self.cell_size // 2
                center_y = y * self.cell_size + self.cell_size // 2
                
                # Draw red food (50 energy each)
                red_food = market.grid[y][x]["red_food"]
                if red_food > 0:
                    # Larger circles for red food (higher energy)
                    radius = min(8 + (red_food * 3), self.cell_size // 3)
                    pygame.draw.circle(self.screen, RED_FOOD_COLOR, 
                                     (center_x - 8, center_y - 8), radius)
                    # Show count if multiple
                    if red_food > 1:
                        count_text = self.font.render(str(red_food), True, (255, 255, 255))
                        self.screen.blit(count_text, (center_x - 15, center_y - 15))
                
                # Draw green food (5 energy each)
                green_food = market.grid[y][x]["green_food"]
                if green_food > 0:
                    # Smaller circles for green food (lower energy)
                    radius = min(4 + (green_food * 2), self.cell_size // 4)
                    pygame.draw.circle(self.screen, GREEN_FOOD_COLOR, 
                                     (center_x + 8, center_y + 8), radius)
                    # Show count if multiple
                    if green_food > 1:
                        count_text = self.font.render(str(green_food), True, (255, 255, 255))
                        self.screen.blit(count_text, (center_x + 5, center_y + 5))
    
    def draw_agents(self, agents):
        for agent in agents:
            x, y = agent.position
            
            # Calculate center of cell
            center_x = x * self.cell_size + self.cell_size // 2
            center_y = y * self.cell_size + self.cell_size // 2
            
            # Choose color based on alive status
            if agent.is_alive:
                color = AGENT_COLORS.get(agent.persona, (150, 150, 150))
            else:
                color = DEAD_AGENT_COLOR
            
            # Draw agent as colored circle
            pygame.draw.circle(self.screen, color, (center_x, center_y), self.cell_size // 3)
            
            # Draw agent name
            text = self.font.render(agent.name.split('_')[1], True, TEXT_COLOR)
            text_rect = text.get_rect(center=(center_x, center_y - self.cell_size // 4))
            self.screen.blit(text, text_rect)
            
            # Draw energy amount (or DEAD)
            if agent.is_alive:
                energy_text = self.font.render(f"E:{agent.energy}", True, TEXT_COLOR)
                # Color code energy level
                if agent.energy <= 10:
                    energy_color = (255, 0, 0)  # Red for low energy
                elif agent.energy <= 25:
                    energy_color = (255, 165, 0)  # Orange for medium energy
                else:
                    energy_color = (0, 150, 0)  # Green for high energy
                energy_text = self.font.render(f"E:{agent.energy}", True, energy_color)
            else:
                energy_text = self.font.render("DEAD", True, (255, 0, 0))
            
            energy_rect = energy_text.get_rect(center=(center_x, center_y + self.cell_size // 6))
            self.screen.blit(energy_text, energy_rect)
    
    def draw_trade_dialog(self, agents):
        # Clear trade dialog area
        pygame.draw.rect(self.screen, (220, 220, 220), self.trade_dialog_rect)
        pygame.draw.line(self.screen, GRID_LINE, 
                          (0, self.height * self.cell_size), 
                          (self.width * self.cell_size, self.height * self.cell_size))
        
        # Draw title
        title = self.title_font.render("Recent Trades", True, TEXT_COLOR)
        self.screen.blit(title, (10, self.height * self.cell_size + 5))
        
        # Track recent trades
        y_pos = self.height * self.cell_size + 25
        trades_shown = 0
        
        for agent in agents:
            if agent.latest_trade and trades_shown < 3:  # Show up to 3 recent trades
                trade = agent.latest_trade
                status = "ACCEPTED" if trade["accepted"] else "REJECTED"
                color = (0, 130, 0) if trade["accepted"] else (180, 0, 0)
                
                trade_text = f"{trade['from']} → {agent.name}: {trade['amount']}E"
                reason_text = f"{status}: {trade['reason'][:20]}..." if len(trade['reason']) > 20 else f"{status}: {trade['reason']}"
                
                text1 = self.font.render(trade_text, True, TEXT_COLOR)
                text2 = self.font.render(reason_text, True, color)
                
                self.screen.blit(text1, (10, y_pos))
                self.screen.blit(text2, (10, y_pos + 12))
                
                y_pos += 30
                trades_shown += 1
    
    def draw_energy_info(self, market):
        # Clear energy info area
        pygame.draw.rect(self.screen, (240, 240, 255), self.energy_info_rect)
        
        # Draw title
        title = self.title_font.render("Energy Status", True, TEXT_COLOR)
        x_pos = self.width * self.cell_size // 2 + 10
        self.screen.blit(title, (x_pos, self.height * self.cell_size + 5))
        
        # Show living agents and their energy
        y_pos = self.height * self.cell_size + 25
        alive_agents = [a for a in market.agents if a.is_alive]
        
        for i, agent in enumerate(alive_agents[:4]):  # Show up to 4 agents
            energy_color = (0, 150, 0) if agent.energy > 25 else (255, 165, 0) if agent.energy > 10 else (255, 0, 0)
            agent_text = f"{agent.name}: {agent.energy}E"
            text = self.font.render(agent_text, True, energy_color)
            self.screen.blit(text, (x_pos, y_pos + i * 15))
        
        # Population count
        pop_text = f"Population: {len(alive_agents)}"
        pop_surface = self.font.render(pop_text, True, TEXT_COLOR)
        self.screen.blit(pop_surface, (x_pos, y_pos + 75))
    
    def draw_system_info(self, market):
        # Clear system info area
        pygame.draw.rect(self.screen, (255, 240, 240), self.system_info_rect)
        
        # Draw title
        title = self.title_font.render("System Energy", True, TEXT_COLOR)
        self.screen.blit(title, (10, self.height * self.cell_size + 131))
        
        # Calculate energy distribution
        agent_energy, food_energy, total_energy = market.get_total_system_energy()
        
        y_pos = self.height * self.cell_size + 151
        
        # Energy breakdown
        agent_text = f"Agent Energy: {agent_energy}"
        food_text = f"Food Energy: {food_energy} (🔴×50 + 🟢×5)"
        total_text = f"Total System Energy: {total_energy}"
        input_text = f"Energy Input/Turn: {market.total_energy_added_per_turn}"
        
        self.screen.blit(self.font.render(agent_text, True, TEXT_COLOR), (10, y_pos))
        self.screen.blit(self.font.render(food_text, True, TEXT_COLOR), (10, y_pos + 15))
        self.screen.blit(self.font.render(total_text, True, TEXT_COLOR), (10, y_pos + 30))
        self.screen.blit(self.font.render(input_text, True, TEXT_COLOR), (10, y_pos + 45))
        
        # Energy loss calculation
        alive_agents = len([a for a in market.agents if a.is_alive])
        total_loss = alive_agents * 2  # Assuming 2 energy loss per agent per turn
        net_energy = market.total_energy_added_per_turn - total_loss
        
        loss_text = f"Energy Loss/Turn: -{total_loss} ({alive_agents} agents × 2)"
        net_text = f"Net Energy/Turn: {net_energy:+d}"
        net_color = (0, 150, 0) if net_energy >= 0 else (255, 0, 0)
        
        x_pos2 = self.width * self.cell_size // 2 + 10
        self.screen.blit(self.font.render(loss_text, True, TEXT_COLOR), (x_pos2, y_pos))
        self.screen.blit(self.font.render(net_text, True, net_color), (x_pos2, y_pos + 15))
    
    def update(self, market):
        self.draw_grid(market)
        self.draw_agents(market.agents)
        self.draw_trade_dialog(market.agents)
        self.draw_energy_info(market)
        self.draw_system_info(market)
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