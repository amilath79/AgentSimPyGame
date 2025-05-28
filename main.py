# main.py - Energy-based economic simulation
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
    
    print("=== Energy-Based Economic Agent Simulation Started ===")
    print("Energy Rules:")
    print("- Red food: 50 energy each")
    print("- Green food: 5 energy each") 
    print("- Agents lose 2 energy per turn")
    print("- Agents die when energy ≤ 0")
    print("Controls: ESC to exit, SPACE to pause/resume, RIGHT ARROW to step when paused")
    
    clock = pygame.time.Clock()
    
    while running and step <= 1000:  # Run for 1000 steps max
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
        
        # ENERGY LOSS: All agents lose energy per turn
        print("⚡ Agents lose energy...")
        for agent in market.agents:
            if agent.is_alive:
                old_energy = agent.energy
                agent.lose_energy_per_turn()
                if agent.is_alive:
                    print(f"  {agent.name}: {old_energy} → {agent.energy} energy")
        
        # Remove dead agents
        dead_count = market.remove_dead_agents()
        if dead_count > 0:
            print(f"💀 {dead_count} agent(s) died this turn")
        
        # Check if all agents are dead
        if not market.agents:
            print("💀 All agents have died! Simulation ending.")
            break
        
        # Process each living agent
        for agent in market.agents:
            if not agent.is_alive:
                continue
            
            # DEBUG: Show what agent sees at their current position
            x, y = agent.position
            current_cell = market.grid[y][x]
            print(f"🔍 {agent.name} at {agent.position}: Red food: {current_cell['red_food']}, Green food: {current_cell['green_food']}, Energy: {agent.energy}")
                
            # Get decision from the agent
            decision, raw_response = agent.decide_action(market)
            
            # Skip dead agents
            if decision["type"] == "ACTION" and decision.get("action") == "DEAD":
                continue
            
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
                    if agent.position != old_pos:
                        print(f"🚶 {agent.name} moved {direction} from {old_pos} to {agent.position}")
                    else:
                        print(f"🚫 {agent.name} tried to move {direction} but hit boundary at {old_pos}")
                
                elif action == "GATHER":
                    energy_gained = market.gather_resources(agent)
                    if energy_gained > 0:
                        print(f"⚡ {agent.name} gained {energy_gained} energy (total: {agent.energy})")
                    else:
                        print(f"❌ {agent.name} found no food to gather")
                
                elif action == "WAIT":
                    print(f"⏳ {agent.name} waits")
            
            elif decision["type"] == "TRADE_OFFER":
                target_name = decision["to"]
                amount = decision["amount"]
                
                # Find the target agent
                target = next((a for a in market.agents if a.name == target_name and a.is_alive), None)
                
                if target and target in market.nearby_agents(agent):
                    print(f"💬 {agent.name} offers {amount} energy to {target_name}")
                    
                    # Check if agent has enough energy (and won't die from giving it away)
                    if agent.energy > amount and (agent.energy - amount) > agent.energy_loss_per_turn:
                        # Let target evaluate the offer
                        accepted, reason = target.evaluate_trade(decision, agent)
                        
                        if accepted:
                            # Execute the trade
                            agent.energy -= amount
                            target.energy += amount
                            
                            print(f"✅ {target_name} accepted: {reason}")
                            print(f"  {agent.name}: {agent.energy + amount} → {agent.energy} energy")
                            print(f"  {target_name}: {target.energy - amount} → {target.energy} energy")
                            
                            # Record the trade
                            market.trade_history.append({
                                "step": step,
                                "from": agent.name,
                                "to": target_name,
                                "energy": amount
                            })
                        else:
                            print(f"❌ {target_name} rejected: {reason}")
                    else:
                        if agent.energy <= amount:
                            print(f"❌ Trade failed: {agent.name} doesn't have enough energy")
                        else:
                            print(f"❌ Trade failed: {agent.name} would die from giving away energy")
                else:
                    print(f"❌ Trade failed: {target_name} not found or too far away")
        
        # Replenish resources every 10 steps
        if step % 10 == 0:
            market.replenish_resources()  # Uses default energy input per turn
        
        # Print system energy status every 5 steps
        if step % 5 == 0:
            agent_energy, food_energy, total_energy = market.get_total_system_energy()
            alive_count = len([a for a in market.agents if a.is_alive])
            print(f"📊 System Status: {alive_count} agents, {agent_energy} agent energy, {food_energy} food energy, {total_energy} total")
        
        # Update visualization
        vis.update(market)
        
        step += 1
        
        # Control simulation speed
        if not paused:
            clock.tick(2)  # 2 frames per second when running
            time.sleep(simulation_speed)
    
    print("\n=== Simulation Ended ===")
    print(f"Total steps: {step}")
    print("\nFinal Agent States:")
    
    for agent in market.agents:
        status = f"Energy: {agent.energy}" if agent.is_alive else "DEAD"
        print(f"{agent.name} ({agent.persona}) - {status}")
    
    # Energy system statistics
    if market.agents:
        alive_agents = [a for a in market.agents if a.is_alive]
        if alive_agents:
            avg_energy = sum(a.energy for a in alive_agents) / len(alive_agents)
            print(f"\nSurviving agents: {len(alive_agents)}")
            print(f"Average energy: {avg_energy:.1f}")
    
    # Trade statistics
    if market.trade_history:
        print("\nTrade Statistics:")
        print(f"Total trades: {len(market.trade_history)}")
        
        # Count trades by agent
        agent_trades = {}
        for trade in market.trade_history:
            agent_trades[trade["from"]] = agent_trades.get(trade["from"], 0) + 1
        
        for agent_name, count in agent_trades.items():
            print(f"{agent_name} initiated {count} trades")
    
    # Final system energy
    agent_energy, food_energy, total_energy = market.get_total_system_energy()
    print(f"\nFinal System Energy: {total_energy} (Agents: {agent_energy}, Food: {food_energy})")
    
    # Wait for a moment before closing
    time.sleep(3)
    
    # Clean up
    vis.close()

if __name__ == "__main__":
    main()