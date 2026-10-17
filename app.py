'''
RUN THIS IN TERMINAL:
python -m streamlit run app.py
'''

import streamlit as st
import networkx as nx
import pickle

# =====================================
# PAGE CONFIG
# =====================================

st.set_page_config(
    page_title="6 Degrees of MLB",
    page_icon="⚾",
    layout="wide"
)

# =====================================
# LOAD GRAPH
# =====================================

@st.cache_resource
def load_data():

    with open("graph.pkl", "rb") as f:
        return pickle.load(f)

data = load_data()

G = data["graph"]
display_lookup = data["display_lookup"]

# =====================================
# PLAYER LIST
# =====================================

@st.cache_data
def get_player_list():
    return sorted(
        G.nodes(),
        key=lambda p: display_lookup[p]
    )

player_list = get_player_list()

# =====================================
# SHORTEST PATH CACHE
# =====================================

@st.cache_data
def get_shortest_path(
    start_player,
    end_player
):
    return nx.shortest_path(
        G,
        start_player,
        end_player
    )

@st.cache_data
def get_all_shortest_paths(
    start_player,
    end_player
):
    return list(
        nx.all_shortest_paths(
            G,
            start_player,
            end_player
        )
    )

# =====================================
# FORMAT TEAM/YEAR CONNECTIONS
# =====================================

def format_team_years(connections):

    teams = {}

    for team, year in connections:

        if team not in teams:
            teams[team] = []

        teams[team].append(year)

    results = []

    for team in sorted(teams):

        years = sorted(set(teams[team]))

        ranges = []

        start = years[0]
        end = years[0]

        for year in years[1:]:

            if year == end + 1:
                end = year

            else:

                if start == end:
                    ranges.append(str(start))
                else:
                    ranges.append(f"{start}-{end}")

                start = year
                end = year

        if start == end:
            ranges.append(str(start))
        else:
            ranges.append(f"{start}-{end}")

        results.append(
            f"{team} ({', '.join(ranges)})"
        )

    return "; ".join(results)

# =====================================
# SESSION STATE
# =====================================

if "start_player" not in st.session_state:
    st.session_state["start_player"] = None

if "end_player" not in st.session_state:
    st.session_state["end_player"] = None

if "num_bridges" not in st.session_state:
    st.session_state["num_bridges"] = 1

# =====================================
# CALLBACKS
# =====================================

def clear_all():

    st.session_state["start_player"] = None
    st.session_state["end_player"] = None

    for key in list(st.session_state.keys()):

        if key.startswith("bridge_"):
            del st.session_state[key]

    st.session_state["num_bridges"] = 1


def clear_start():
    st.session_state["start_player"] = None


def clear_end():
    st.session_state["end_player"] = None


def clear_bridge(idx):
    st.session_state[f"bridge_{idx}"] = None


# =====================================
# PAGE TITLE
# =====================================

st.title("⚾ 6 Degrees of MLB")

st.write(
    "Choose a starting player and ending player, then build a teammate chain."
)

# =====================================
# START PLAYER
# =====================================

col1, col2 = st.columns([20, 1])

with col1:

    start_player = st.selectbox(
        "Starting Player",
        player_list,
        key="start_player",
        index=None,
        placeholder="Type a player name...",
        format_func=lambda p: display_lookup[p]
    )

with col2:

    st.write("")
    st.write("")

    st.button(
        "❌",
        key="clear_start_btn",
        on_click=clear_start
    )

# =====================================
# END PLAYER
# =====================================

col1, col2 = st.columns([20, 1])

with col1:

    end_player = st.selectbox(
        "Ending Player",
        player_list,
        key="end_player",
        index=None,
        placeholder="Type a player name...",
        format_func=lambda p: display_lookup[p]
    )

with col2:

    st.write("")
    st.write("")

    st.button(
        "❌",
        key="clear_end_btn",
        on_click=clear_end
    )

# =====================================
# BRIDGE CONTROLS
# =====================================

st.subheader("Build Your Bridge")

control1, control2 = st.columns(2)

with control1:

    if st.button("➕ Add Bridge Player"):

        st.session_state["num_bridges"] += 1
        st.rerun()

with control2:

    if (
        st.button("➖ Remove Last Bridge Player")
        and st.session_state["num_bridges"] > 1
    ):

        last_key = (
            f"bridge_{st.session_state['num_bridges'] - 1}"
        )

        if last_key in st.session_state:
            del st.session_state[last_key]

        st.session_state["num_bridges"] -= 1
        st.rerun()

# =====================================
# BRIDGE SELECTORS
# =====================================

bridges = []

for i in range(st.session_state["num_bridges"]):

    key = f"bridge_{i}"

    if key not in st.session_state:
        st.session_state[key] = None

    col1, col2 = st.columns([20, 1])

    with col1:

        bridge = st.selectbox(
            f"Bridge Player {i + 1}",
            player_list,
            key=key,
            index=None,
            placeholder="Type a player name...",
            format_func=lambda p: display_lookup[p]
        )

    with col2:

        st.write("")
        st.write("")

        st.button(
            "❌",
            key=f"clear_bridge_btn_{i}",
            on_click=clear_bridge,
            args=(i,)
        )

    bridges.append(bridge)

import random

if st.button("🎲 Random Challenge"):

    players = random.sample(
        player_list,
        2
    )

    st.session_state["start_player"] = players[0]
    st.session_state["end_player"] = players[1]

    st.rerun()

# =====================================
# ACTION BUTTONS
# =====================================

st.divider()

col1, col2 = st.columns(2)

with col1:

    check_clicked = st.button(
        "✅ Check Path",
        use_container_width=True
    )

with col2:

    st.button(
        "🔄 Clear All",
        use_container_width=True,
        on_click=clear_all
    )

# =====================================
# CHECK PATH
# =====================================

if check_clicked:

    if start_player is None or end_player is None:

        st.error(
            "Please select both a starting player and an ending player."
        )

    else:

        chain = [start_player]

        for bridge in bridges:

            if bridge is not None:
                chain.append(bridge)

        chain.append(end_player)

        # ==============================
        # DUPLICATE CHECK
        # ==============================

        if len(chain) != len(set(chain)):

            st.error(
                "❌ A player cannot appear more than once in the chain."
            )

        else:

            # ==============================
            # EDGE VALIDATION
            # ==============================

            valid = True

            for i in range(len(chain) - 1):

                if not G.has_edge(
                    chain[i],
                    chain[i + 1]
                ):
                    valid = False
                    break

            if not valid:

                st.error(
                    "❌ Invalid teammate path"
                )

            else:

                try:

                    all_shortest = get_all_shortest_paths(
                        start_player,
                        end_player
                    )

                except Exception:

                    st.error(
                        "Too many shortest paths to display."
                    )

                    st.stop()

                MAX_PATHS = 100
                display_paths = all_shortest[:MAX_PATHS]

                if len(all_shortest) > MAX_PATHS:
                    st.warning(
                        f"Showing the first {MAX_PATHS} shortest paths out of "
                        f"{len(all_shortest)} total."
                    )

                user_deg = len(chain) - 1
                optimal_deg = len(all_shortest[0]) - 1

                extra_degrees = max(
                    0,
                    user_deg - optimal_deg
                )

                score = max(
                    0,
                    100 - (extra_degrees * 15)
                )

                st.success(
                    "✅ Valid Chain"
                )

                m1, m2, m3, m4, m5 = st.columns(5)

                m1.metric(
                    "Your Degrees",
                    user_deg
                )

                m2.metric(
                    "Best Degrees",
                    optimal_deg
                )

                m3.metric(
                    "Extra Degrees",
                    extra_degrees
                )

                m4.metric(
                    "Score",
                    f"{score}/100"
                )

                m5.metric(
                    "Shortest Paths",
                    len(all_shortest)
                )

                # ==============================
                # YOUR PATH
                # ==============================

                st.subheader("Your Path")

                st.write(
                    " → ".join(
                        display_lookup[player]
                        for player in chain
                    )
                )

                # ==============================
                # CONNECTION DETAILS
                # ==============================

                st.subheader(
                    "Shared Teams & Years"
                )

                for i in range(len(chain) - 1):

                    p1 = chain[i]
                    p2 = chain[i + 1]

                    shared = sorted(
                        set(
                            G[p1][p2]["teams"]
                        )
                    )

                    st.markdown(
                        f"**{display_lookup[p1]}** ↔ **{display_lookup[p2]}**"
                    )

                    st.write(
                        format_team_years(shared)
                    )

                # ==============================
                # HIDDEN SHORTEST PATH
                # ==============================

                with st.expander(
                    f"👀 Viewing {len(display_paths)} of {len(all_shortest)} Shortest Paths"
                ):

                    for path_num, shortest in enumerate(
                        display_paths,
                        start=1
                    ):

                        st.markdown(
                            f"### Path {path_num}"
                        )

                        st.write(
                            " → ".join(
                                display_lookup[player]
                                for player in shortest
                            )
                        )

                        st.caption(
                            f"{len(shortest) - 1} degrees"
                        )

                        st.subheader(
                            "Shortest Path Connections"
                        )

                        for i in range(len(shortest) - 1):

                            p1 = shortest[i]
                            p2 = shortest[i + 1]

                            shared = sorted(
                                set(
                                    G[p1][p2]["teams"]
                                )
                            )

                            st.markdown(
                                f"**{display_lookup[p1]}** ↔ **{display_lookup[p2]}**"
                            )

                            st.write(
                                format_team_years(shared)
                            )

                        if path_num < len(display_paths):
                            st.divider()