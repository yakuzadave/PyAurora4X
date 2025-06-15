import streamlit as st
from pyaurora4x.engine.simulation import GameSimulation
from pyaurora4x.core.models import Ship

@st.cache_resource
def get_simulation():
    sim = GameSimulation()
    sim.initialize_new_game(num_systems=3, num_empires=2)
    # Create a few sample ships for the player's first fleet
    player = sim.get_player_empire()
    ships = {}
    if player and player.fleets:
        fleet = sim.get_fleet(player.fleets[0])
        if fleet:
            for i in range(3):
                ship = Ship(
                    name=f"Ship {i+1}",
                    design_id="basic",
                    empire_id=player.id,
                    fleet_id=fleet.id,
                )
                fleet.ships.append(ship.id)
                ships[ship.id] = ship
    return sim, ships

sim, ships = get_simulation()

st.title("PyAurora 4X Dashboard")

view = st.sidebar.selectbox("View", ["Worlds", "Ships", "Empires"])

if view == "Worlds":
    systems = list(sim.star_systems.values())
    if not systems:
        st.write("No star systems available.")
    else:
        idx = st.selectbox(
            "Star System",
            range(len(systems)),
            format_func=lambda i: systems[i].name,
        )
        system = systems[idx]
        st.subheader(system.name)
        st.write(f"Star Type: {system.star_type}")
        st.write(f"Planets: {len(system.planets)}")
        for planet in system.planets:
            st.markdown(f"**{planet.name}** - {planet.planet_type}")
            st.write(f"Orbit: {planet.orbital_distance:.2f} AU")
        if system.asteroid_belts:
            st.write("Asteroid Belts:")
            for belt in system.asteroid_belts:
                st.write(f"- {belt.distance:.2f} AU width {belt.width:.2f} AU")
elif view == "Ships":
    if not ships:
        st.write("No ships available.")
    else:
        ids = list(ships.keys())
        ship_id = st.selectbox(
            "Ship",
            ids,
            format_func=lambda sid: ships[sid].name,
        )
        ship = ships[ship_id]
        st.subheader(ship.name)
        st.write(f"Design: {ship.design_id}")
        st.write(f"Fleet ID: {ship.fleet_id}")
        st.write(f"Empire: {sim.empires[ship.empire_id].name}")
        st.write(f"Fuel: {ship.fuel}")
        st.write(f"Condition: {ship.condition}")
elif view == "Empires":
    ids = list(sim.empires.keys())
    if not ids:
        st.write("No empires found.")
    else:
        empire_id = st.selectbox(
            "Empire",
            ids,
            format_func=lambda eid: sim.empires[eid].name,
        )
        empire = sim.empires[empire_id]
        st.subheader(empire.name)
        st.write(f"Home System: {sim.star_systems[empire.home_system_id].name}")
        st.write(f"Colonies: {len(empire.colonies)}")
        st.write(f"Fleets: {len(empire.fleets)}")
        st.write(f"Resources: {empire.resources}")

