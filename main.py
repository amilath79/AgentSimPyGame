# main.py
import time
import random
import pygame
from market import Market
from economic_agent import EconomicAgent
from visualization import Visualization

def main():
    # Create market
    market = Market(width=9, height=9)

    simulation_speed = 1.0  # seconds per step
    
    # Initialize visualization
    vis = Visualization(width=9, height=9)
    
    # Create agents with different personas
    personas = ["Risk-averse", "Risk-averse", "Risk-averse", "Risk-averse"]
    agents = [EconomicAgent(f"Agent_{i+1}", personas[i]) for i in range(4)]
    
    # Add agents to different positions to avoid starting in the same place
    positions = [(2, 2), (6, 2), (2, 6), (6, 6)]
    for i, agent in enumerate(agents):
        market.add_agent(agent, positions[i][0], positions[i][1])
    
    # Main simulation loop
    step = 0
    running = True
    paused = False
    
    print("=== Economic Agent Simulation Started ===")
    print("Controls: ESC to exit, SPACE to pause/resume, RIGHT ARROW to step when paused")
    
    clock = pygame.time.Clock()
    
    while running and step <= 1000:  # Run for 500 steps max
        # Check for events (including pause/step controls)
        running, action = vis.check_events()
        if not running:
            break

        if action == "SPEED_UP":
            simulation_speed = max(0.2, simulation_speed - 0.2)
            print(f"Speed increased: {1/simulation_speed:.1f} steps/second")
        elif action == "SPEED_DOWN":
            simulation_speed = min(5.0, simulation_speed + 0.2)
            print(f"Speed decreased: {1/simulation_speed:.1f} steps/second")
            
        if action == "PAUSE":
            paused = not paused
            print(f"Simulation {'paused' if paused else 'resumed'}")
        
        if paused and action != "STEP":
            # If paused and not stepping, just update the display and continue
            vis.update(market)
            clock.tick(30)  # Limit frame rate while paused
            continue
            
        print(f"\n=== Step {step + 1} ===")
        
        # Process each agent
        for agent in market.agents:
            # Get decision from the agent
            decision, raw_response = agent.decide_action(market)
            
            # Debug output - limited to first 100 chars for readability
            debug_response = raw_response[:100] + "..." if len(raw_response) > 100 else raw_response
            print(f"\n{agent.name} ({agent.persona}) raw response (truncated):\n{debug_response}")
            
            # Execute the decision
            if decision["type"] == "ACTION":
                action = decision["action"]
                print(f"{agent.name} ({agent.persona}) decided: {action}")
                
                if action.startswith("MOVE"):
                    direction = action.split()[-1]
                    old_pos = agent.position
                    market.move_agent(agent, direction)
                    print(f"🚶 {agent.name} moved {direction} from {old_pos} to {agent.position}")
                
                elif action == "GATHER":
                    food = market.gather_resources(agent)
                    print(f"🍔 {agent.name} gathered {food} food")
                
                elif action == "WAIT":
                    print(f"⏳ {agent.name} waits")
            
            elif decision["type"] == "TRADE_OFFER":
                target_name = decision["to"]
                amount = decision["amount"]
                
                # Find the target agent
                target = next((a for a in market.agents if a.name == target_name), None)
                
                if target and target in market.nearby_agents(agent):
                    print(f"💬 {agent.name} offers {amount} food to {target_name}")
                    
                    # Check if agent has enough food
                    if agent.food >= amount:
                        # Let target evaluate the offer
                        accepted, reason = target.evaluate_trade(decision, agent)
                        
                        if accepted:
                            # Execute the trade
                            agent.food -= amount
                            target.food += amount
                            
                            print(f"✅ {target_name} accepted: {reason}")
                            
                            # Record the trade
                            market.trade_history.append({
                                "step": step,
                                "from": agent.name,
                                "to": target_name,
                                "food": amount
                            })
                        else:
                            print(f"❌ {target_name} rejected: {reason}")
                    else:
                        print(f"❌ Trade failed: {agent.name} doesn't have enough food")
                else:
                    print(f"❌ Trade failed: {target_name} not found or too far away")
        
        # Replenish resources every 5 steps
        if step % 20 == 0:
            market.replenish_resources(2)  # Only add 5 food units to make resources more valuable
            print("🌱 Market replenished with new food")
        
        # Update visualization
        vis.update(market)
        
        step += 1
        
        # Slow down simulation for visibility, but not too much
        if not paused:
            clock.tick(1)  # 2 frames per second when running

        if not paused:
            time.sleep(simulation_speed)
    
    print("\n=== Simulation Ended ===")
    print(f"Total steps: {step}")
    print("\nFinal Agent States:")
    
    for agent in market.agents:
        print(f"{agent.name} ({agent.persona}) - Food: {agent.food}")
    
    # Trade statistics
    if market.trade_history:
        print("\nTrade Statistics:")
        print(f"Total trades: {len(market.trade_history)}")
        
        # Count trades by agent
        agent_trades = {}
        for trade in market.trade_history:
            agent_trades[trade["from"]] = agent_trades.get(trade["from"], 0) + 1
        
        for agent, count in agent_trades.items():
            print(f"{agent} initiated {count} trades")
    
    # Wait for a moment before closing
    time.sleep(3)
    
    # Clean up
    vis.close()

if __name__ == "__main__":
    main()