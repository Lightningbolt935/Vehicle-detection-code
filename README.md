# RoundAbout traffic light controller based on the 
This code detects the number of vehicles in all the directions and according to it turn lights colour to red yellow and green

import random
import time

# Simulated traffic data for four directions
def simulate_traffic_flow():
    return (
        random.randint(0, 100),  # North
        random.randint(0, 100),  # South
        random.randint(0, 100),  # East
        random.randint(0, 100)   # West
    )

# Simple Roundabout Traffic Controller
class RoundaboutTrafficController:
    def __init__(self):
        self.base_duration = 10  # Base duration in seconds

    def adjust_light_duration(self, traffic_densities):
        # Adjust green light duration based on traffic densities
        return [max(5, min(30, self.base_duration + density // 5)) for density in traffic_densities]

    def run_cycle(self):
        traffic_densities = simulate_traffic_flow()
        directions = ["North", "South", "East", "West"]
        
        print(f"Current traffic densities: {dict(zip(directions, traffic_densities))}")

        durations = self.adjust_light_duration(traffic_densities)
        print(f"Adjusted green light durations: {dict(zip(directions, durations))}")
        
        # Simulate green light phase for each direction
        for direction, duration in zip(directions, durations):
            print(f"{direction} Green light ON for {duration} seconds")
            time.sleep(duration)
            print(f"{direction} Green light OFF")

        print()  # New line for clarity

# Main simulation loop
def main():
    controller = RoundaboutTrafficController()
    cycles = 3  # Number of cycles to simulate

    for _ in range(cycles):
        controller.run_cycle()

if __name__ == "__main__":
    main()
