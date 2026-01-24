"""Tennis Win Probability Engine page."""

import streamlit as st
from datetime import datetime
import pandas as pd
import time
from src.tennis_schema import MatchSnapshot, PlayerStats
from src.data_sources.url_scraper import fetch_match_stats_from_url, get_available_match_pages
from src.data_sources.paste_parser import parse_pasted_stats
from src.models.probabilities import (
    next_point_probability,
    next_game_probability,
    next_three_games_forecast,
    set_win_probability,
    match_win_probability,
    get_all_game_outcomes,
    forecast_next_game_outcomes,
)


def render():
    """Render the Tennis Win Probability Engine."""
    st.title("🎾 LIVE TENNIS WIN PROBABILITY ENGINE")

    st.markdown(
        """
        Ingest live match stats and compute win probabilities for the next point,
        game, and match. Gracefully handles URL scraping, pasted data, or manual entry.
        """
    )

    # Initialize session state for snapshots
    if "snapshots" not in st.session_state:
        st.session_state.snapshots = []
    if "prediction_history" not in st.session_state:
        st.session_state.prediction_history = []

    st.divider()

    # DATA INGESTION PANEL
    st.header("📊 DATA INGESTION")

    col1, col2 = st.columns(2)
    with col1:
        data_mode = st.radio(
            "Data source:",
            ["Manual Entry", "Paste Snapshot", "From URL"],
            help="How to provide match stats",
        )

    with col2:
        refresh_mode = st.radio(
            "Refresh mode:",
            ["Manual", "Auto (5s)"],
        )

    # Auto-refresh logic for URL mode
    auto_refresh = refresh_mode == "Auto (5s)" and data_mode == "From URL"
    if auto_refresh:
        if "last_refresh" not in st.session_state:
            st.session_state.last_refresh = time.time()
        
        time_since_refresh = time.time() - st.session_state.last_refresh
        if time_since_refresh < 5:
            st.info(f"⏳ Next refresh in {5 - int(time_since_refresh)} seconds...")
            time.sleep(0.5)
            st.rerun()

    snapshot = None

    if data_mode == "From URL":
        st.subheader("FETCH FROM MATCH URL")
        st.markdown("""
        **Supported sites:** Australian Open, Wimbledon, US Open, Roland Garros, ATP Tour, WTA Tour, and more
        
        Paste a match URL to automatically extract player info and statistics:
        """)
        
        match_url = st.text_input(
            "Match stats URL:",
            placeholder="https://ausopen.com/match/2026-elise-mertens-vs-nikola-bartunkova-ws314#!",
            help="Public match URL (e.g., Australian Open, Wimbledon, ATP/WTA Tours)",
        )

        if match_url:
            # Create columns for fetch button and refresh toggle
            col_btn, col_info = st.columns([1, 3])
            with col_btn:
                fetch_clicked = st.button("🔍 Fetch & Parse", use_container_width=True)
            
            if fetch_clicked or auto_refresh:
                with st.spinner("🔄 Fetching and parsing match data..."):
                    stats_dict = fetch_match_stats_from_url(match_url)
                    
                    # Also try to get available match pages
                    available_pages = get_available_match_pages(match_url)
                
                if stats_dict:
                    # Store in session
                    if "url_snapshot" not in st.session_state:
                        st.session_state.url_snapshot = {}
                    st.session_state.url_snapshot.update(stats_dict)
                    st.session_state.last_refresh = time.time()
                    
                    # Show extracted data
                    st.success(f"✅ Successfully extracted {len(stats_dict)} data fields!")
                    
                    # Display extracted player names if available
                    extracted_cols = st.columns(2)
                    with extracted_cols[0]:
                        if "player_a_name" in stats_dict:
                            st.info(f"👤 Player A: **{stats_dict['player_a_name']}**")
                    with extracted_cols[1]:
                        if "player_b_name" in stats_dict:
                            st.info(f"👤 Player B: **{stats_dict['player_b_name']}**")
                    
                    # Show available match pages if detected
                    if available_pages:
                        with st.expander("📑 Available Match Pages"):
                            page_cols = st.columns(len(available_pages) if len(available_pages) <= 4 else 4)
                            for idx, page in enumerate(available_pages):
                                with page_cols[idx % 4]:
                                    st.write(f"• **{page.get('label', page.get('type'))}**")
                    
                    # Show extracted stats
                    with st.expander("📊 Extracted Statistics"):
                        stat_cols = st.columns(3)
                        stat_items = list(stats_dict.items())
                        for idx, (key, value) in enumerate(stat_items):
                            with stat_cols[idx % 3]:
                                # Format the display
                                display_key = key.replace('_', ' ').title()
                                if isinstance(value, float):
                                    st.metric(display_key, f"{value:.1%}" if value <= 1 else f"{value:.2f}")
                                else:
                                    st.write(f"**{display_key}:** {value}")
                    
                    st.info("✏️ Pre-filled values from URL will appear in the fields below. Edit as needed!")
                else:
                    st.warning("⚠️ Could not extract stats from this URL. The site may not be supported or data not available yet.")
                    st.info("💡 Try these example URLs:\n"
                           "- https://ausopen.com/match/2026-elise-mertens-vs-nikola-bartunkova-ws314#!\n"
                           "- https://ausopen.com/match/2026-ben-shelton-vs-valentin-vacherot-ms313#!")
        else:
            st.info("👆 Paste a tennis match URL above to extract player info and statistics")

    elif data_mode == "Paste Snapshot":
        st.subheader("PASTE MATCH STATS")
        pasted_text = st.text_area(
            "Paste JSON, CSV, or key:value stats:",
            height=150,
            placeholder='{"first_serve_in_pct": 0.65, "first_serve_points_won_pct": 0.82}',
        )
        if pasted_text:
            stats_dict = parse_pasted_stats(pasted_text)
            if stats_dict:
                st.success(f"✅ Parsed {len(stats_dict)} fields")
            else:
                st.warning("⚠️ Could not parse pasted data. Check format.")

    st.divider()

    # MANUAL MATCH CONTEXT
    st.header("⚙️ MATCH CONTEXT")

    col1, col2, col3 = st.columns(3)
    with col1:
        # Get default from URL extraction if available
        default_pa = st.session_state.get("url_snapshot", {}).get("player_a_name", "Player A")
        player_a_name = st.text_input("Player A:", value=default_pa, key="pa_name")
    with col2:
        # Get default from URL extraction if available
        default_pb = st.session_state.get("url_snapshot", {}).get("player_b_name", "Player B")
        player_b_name = st.text_input("Player B:", value=default_pb, key="pb_name")
    with col3:
        best_of_sets = st.selectbox("Best of:", [3, 5], index=1)

    st.markdown("### Current Match State")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        sets_won_a = st.number_input("Sets won (A):", min_value=0, max_value=5, value=0)
    with col2:
        sets_won_b = st.number_input("Sets won (B):", min_value=0, max_value=5, value=0)
    with col3:
        games_in_set_a = st.number_input("Games in set (A):", min_value=0, max_value=12, value=0)
    with col4:
        games_in_set_b = st.number_input("Games in set (B):", min_value=0, max_value=12, value=0)

    st.markdown("### Current Point")

    col1, col2, col3 = st.columns(3)
    with col1:
        server = st.selectbox("Server:", ["A", "B"], key="server_select")
    with col2:
        point_score_a = st.selectbox("Points (A):", ["0", "15", "30", "40", "AD"], index=0)
    with col3:
        point_score_b = st.selectbox("Points (B):", ["0", "15", "30", "40", "AD"], index=0)

    is_tiebreak = st.checkbox("Tiebreak", value=False)
    if is_tiebreak:
        col1, col2 = st.columns(2)
        with col1:
            tiebreak_points_a = st.number_input("TB Points (A):", min_value=0, value=0)
        with col2:
            tiebreak_points_b = st.number_input("TB Points (B):", min_value=0, value=0)
    else:
        tiebreak_points_a = None
        tiebreak_points_b = None

    st.divider()

    # PLAYER SERVE STATS
    st.header("🎾 SERVE PERFORMANCE STATS")

    st.markdown(
        """
        **Minimum required for win probability:**
        - First Serve In % (0–1)
        - First Serve Points Won % (0–1)
        - Second Serve Points Won % (0–1)
        """
    )

    col_a, col_b = st.columns(2)
    
    # Get defaults from URL extraction if available
    url_snapshot = st.session_state.get("url_snapshot", {})
    default_fsi_a = url_snapshot.get("first_serve_in_pct", 0.65) if isinstance(url_snapshot.get("first_serve_in_pct"), float) else 0.65
    default_fspw_a = url_snapshot.get("first_serve_points_won_pct", 0.82) if isinstance(url_snapshot.get("first_serve_points_won_pct"), float) else 0.82
    default_sspw_a = url_snapshot.get("second_serve_points_won_pct", 0.60) if isinstance(url_snapshot.get("second_serve_points_won_pct"), float) else 0.60

    with col_a:
        st.subheader(f"📍 {player_a_name}")
        fsi_a = st.number_input(
            "1st Serve In % (A):",
            min_value=0.0,
            max_value=1.0,
            value=default_fsi_a,
            step=0.01,
            key="fsi_a",
        )
        fspw_a = st.number_input(
            "1st Serve Points Won % (A):",
            min_value=0.0,
            max_value=1.0,
            value=default_fspw_a,
            step=0.01,
            key="fspw_a",
        )
        sspw_a = st.number_input(
            "2nd Serve Points Won % (A):",
            min_value=0.0,
            max_value=1.0,
            value=default_sspw_a,
            step=0.01,
            key="sspw_a",
        )

    with col_b:
        st.subheader(f"📍 {player_b_name}")
        fsi_b = st.number_input(
            "1st Serve In % (B):",
            min_value=0.0,
            max_value=1.0,
            value=0.68,
            step=0.01,
            key="fsi_b",
        )
        fspw_b = st.number_input(
            "1st Serve Points Won % (B):",
            min_value=0.0,
            max_value=1.0,
            value=0.80,
            step=0.01,
            key="fspw_b",
        )
        sspw_b = st.number_input(
            "2nd Serve Points Won % (B):",
            min_value=0.0,
            max_value=1.0,
            value=0.58,
            step=0.01,
            key="sspw_b",
        )

    st.divider()

    # PRIORS & BLENDING
    st.header("🔧 PRIORS & BLENDING")

    col1, col2 = st.columns(2)
    with col1:
        blending_weight = st.slider(
            "Blending weight (live data):",
            min_value=0.0,
            max_value=1.0,
            value=0.70,
            step=0.05,
            help="Higher = trust live data more, lower = trust prior more",
        )

    with col2:
        generic_prior = st.slider(
            "Generic prior (serve point win):",
            min_value=0.50,
            max_value=0.70,
            value=0.62,
            step=0.01,
            help="Baseline serve-point-win rate (e.g., 0.62 = men's average)",
        )

    st.divider()

    # BUILD SNAPSHOT & COMPUTE
    st.header("⚡ COMPUTE PROBABILITIES")

    if st.button("🚀 Calculate Win Probabilities", type="primary"):
        # Create snapshot
        snapshot = MatchSnapshot(
            timestamp=datetime.now(),
            match_url=None,
            data_source="manual",
            best_of_sets=best_of_sets,
            player_a_name=player_a_name,
            player_b_name=player_b_name,
            sets_won_a=sets_won_a,
            sets_won_b=sets_won_b,
            games_in_set_a=games_in_set_a,
            games_in_set_b=games_in_set_b,
            point_score_a=point_score_a,
            point_score_b=point_score_b,
            server=server,
            is_tiebreak=is_tiebreak,
            tiebreak_points_a=tiebreak_points_a,
            tiebreak_points_b=tiebreak_points_b,
            player_a=PlayerStats(
                player_name=player_a_name,
                first_serve_in_pct=fsi_a,
                first_serve_points_won_pct=fspw_a,
                second_serve_points_won_pct=sspw_a,
            ),
            player_b=PlayerStats(
                player_name=player_b_name,
                first_serve_in_pct=fsi_b,
                first_serve_points_won_pct=fspw_b,
                second_serve_points_won_pct=sspw_b,
            ),
            blending_weight_live=blending_weight,
            generic_prior_serve_point_win=generic_prior,
        )

        # Add to snapshots history
        st.session_state.snapshots.append(snapshot)

        # DISPLAY RESULTS
        st.success("✅ Snapshot recorded!")

        st.subheader("📈 WIN PROBABILITIES")

        # Create a container for prediction history toggle
        show_history = st.checkbox("📋 Show prediction history", value=False)

        # Next point
        p_server_point, p_receiver_point, note = next_point_probability(snapshot)
        if p_server_point is not None:
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    f"P({player_a_name} wins next point)",
                    f"{p_server_point:.1%}" if server == "A" else f"{p_receiver_point:.1%}",
                )
            with col2:
                st.metric(
                    f"P({player_b_name} wins next point)",
                    f"{p_receiver_point:.1%}" if server == "A" else f"{p_server_point:.1%}",
                )
        else:
            st.warning(note)

        st.markdown("---")

        # DETAILED GAME OUTCOMES - NEW SECTION
        st.subheader("🎯 DETAILED CURRENT GAME ANALYSIS")

        game_outcomes, p_deuce, note_outcomes = get_all_game_outcomes(snapshot)
        if game_outcomes is not None:
            st.markdown(f"**Possible outcomes from {point_score_a}–{point_score_b}:**")
            
            # Sort outcomes by probability (descending)
            sorted_outcomes = sorted(game_outcomes.items(), key=lambda x: x[1], reverse=True)
            
            # Find highest probability for bolding
            max_prob = max(game_outcomes.values()) if game_outcomes else 0
            
            # Display in columns for better layout
            outcomes_col = st.columns([2, 1])
            with outcomes_col[0]:
                for outcome, prob in sorted_outcomes[:10]:  # Show top 10
                    if prob >= max_prob * 0.95:  # Bold the highest probability outcomes (within 5%)
                        st.markdown(f"**{outcome}: {prob:.1%}**")
                    else:
                        st.write(f"  {outcome}: {prob:.1%}")
            
            with outcomes_col[1]:
                st.metric("P(Deuce)", f"{p_deuce:.1%}")

            # Store prediction
            st.session_state.prediction_history.append({
                "timestamp": datetime.now(),
                "score": f"{point_score_a}–{point_score_b}",
                "server": server,
                "game_outcomes": game_outcomes,
                "p_deuce": p_deuce,
                "match_state": f"{sets_won_a}-{sets_won_b} {games_in_set_a}-{games_in_set_b}"
            })
        else:
            st.info(note_outcomes)

        st.markdown("---")

        # Next game prediction
        st.subheader("🎾 NEXT GAME PREDICTION")
        next_game_outcomes, next_game_note = forecast_next_game_outcomes(snapshot)
        if next_game_outcomes is not None:
            for outcome, prob in next_game_outcomes.items():
                st.write(f"  • {outcome}")
        else:
            st.info(next_game_note)

        st.markdown("---")

        # Next game
        p_hold, p_break, score_dist, note = next_game_probability(snapshot)
        if p_hold is not None:
            col1, col2 = st.columns(2)
            with col1:
                if server == "A":
                    st.metric(f"P({player_a_name} holds)", f"{p_hold:.1%}")
                else:
                    st.metric(f"P({player_a_name} breaks)", f"{p_break:.1%}")
            with col2:
                if server == "A":
                    st.metric(f"P({player_b_name} breaks)", f"{p_break:.1%}")
                else:
                    st.metric(f"P({player_b_name} holds)", f"{p_hold:.1%}")

            if score_dist:
                st.markdown("**Likely game endings:**")
                sorted_dist = sorted(score_dist.items(), key=lambda x: x[1], reverse=True)
                max_dist_prob = max(score_dist.values())
                for outcome, prob in sorted_dist:
                    if prob >= max_dist_prob * 0.90:  # Bold top outcomes
                        st.markdown(f"**{outcome}: {prob:.1%}**")
                    else:
                        st.write(f"  {outcome}: {prob:.1%}")
        else:
            st.warning(note)

        st.markdown("---")

        # Next 3 games
        forecast, note = next_three_games_forecast(snapshot)
        if forecast:
            st.markdown("**Next 3 games forecast:**")
            cols = st.columns(3)
            for i, col in enumerate(cols):
                with col:
                    game_num = i + 1
                    p_a = forecast.get(f"p_a_game{game_num}", 0)
                    p_b = forecast.get(f"p_b_game{game_num}", 0)
                    st.metric(f"Game {game_num}", f"A: {p_a:.0%} / B: {p_b:.0%}")

            if "set_score_dist" in forecast:
                st.markdown("**Set scores after 3 games:**")
                sorted_set = sorted(forecast["set_score_dist"].items(), key=lambda x: x[1], reverse=True)
                max_set_prob = max(forecast["set_score_dist"].values())
                for score, prob in sorted_set:
                    if prob >= max_set_prob * 0.85:
                        st.markdown(f"**{score}: {prob:.1%}**")
                    else:
                        st.write(f"  {score}: {prob:.1%}")
        else:
            st.info(note)

        st.markdown("---")

        # Set & match win
        p_a_set, note_set = set_win_probability(snapshot)
        p_a_match, note_match = match_win_probability(snapshot)

        if p_a_set is not None:
            col1, col2 = st.columns(2)
            with col1:
                st.metric(f"P({player_a_name} wins set)", f"{p_a_set:.1%}")
            with col2:
                st.metric(f"P({player_a_name} wins match)", f"{p_a_match:.1%}")
        else:
            st.warning("Cannot compute set/match probability: " + note_set)

        # PREDICTION HISTORY
        if show_history and st.session_state.prediction_history:
            st.divider()
            st.subheader("📊 PREDICTION HISTORY")
            st.markdown("Previous predictions for reference:")
            
            for idx, pred in enumerate(reversed(st.session_state.prediction_history)):
                with st.expander(f"Prediction #{len(st.session_state.prediction_history) - idx} - {pred['timestamp'].strftime('%H:%M:%S')} | {pred['match_state']} | {pred['score']}"):
                    st.write(f"**Match State:** {pred['match_state']}")
                    st.write(f"**Score:** {pred['score']} ({pred['server']} serving)")
                    st.write(f"**P(Deuce):** {pred['p_deuce']:.1%}")
                    st.markdown("**Game outcomes:**")
                    sorted_hist = sorted(pred['game_outcomes'].items(), key=lambda x: x[1], reverse=True)
                    for outcome, prob in sorted_hist[:5]:
                        st.write(f"  • {outcome}: {prob:.1%}")

        st.divider()

        # SHOW MATH
        if st.checkbox("📐 Show formulas & assumptions"):
            st.markdown(
                f"""
                ### Formulas Used

                **Serve-Point-Win Probability:**
                ```
                p_serve = p(1st in) × p(1st win) + (1 - p(1st in)) × p(2nd win)
                ```

                **Blending with Prior:**
                ```
                p_blended = {blending_weight:.2f} × p_live + {1-blending_weight:.2f} × p_prior
                ```

                **Game Probability:**
                Uses Markov chain recursion from current point score (0, 15, 30, 40, AD).

                **Set/Match Probability:**
                Uses Markov chain over game/set states.

                ### Assumptions
                - Both players maintain current serve stats across the match
                - No momentum or fatigue modeling
                - Break point conversion = 1 - (server hold %)
                - Tiebreak: first to 7 with 2+ lead
                """
            )

        st.divider()

        # EXPORT & SHARE
        st.subheader("📥 EXPORT & SHARE")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 Export to CSV"):
                if st.session_state.snapshots:
                    df = _snapshots_to_dataframe(st.session_state.snapshots)
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name="tennis_snapshots.csv",
                        mime="text/csv",
                    )

        with col2:
            if st.button("📋 Copy Summary"):
                summary = _create_summary(snapshot)
                st.text_area("Copy this summary:", value=summary, height=100)


def _snapshots_to_dataframe(snapshots):
    """Convert snapshots to DataFrame for export."""
    rows = []
    for snap in snapshots:
        row = {
            "timestamp": snap.timestamp.isoformat(),
            "player_a": snap.player_a_name,
            "player_b": snap.player_b_name,
            "sets_a": snap.sets_won_a,
            "sets_b": snap.sets_won_b,
            "games_a": snap.games_in_set_a,
            "games_b": snap.games_in_set_b,
            "point_a": snap.point_score_a,
            "point_b": snap.point_score_b,
        }
        p_a_match, _ = match_win_probability(snap)
        row["p_match_a"] = p_a_match
        rows.append(row)
    return pd.DataFrame(rows)


def _create_summary(snapshot: MatchSnapshot) -> str:
    """Create shareable plain-text summary."""
    p_a_match, _ = match_win_probability(snapshot)
    summary = f"""
TENNIS MATCH SNAPSHOT
{snapshot.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}

Players: {snapshot.player_a_name} vs {snapshot.player_b_name}
Score: {snapshot.sets_won_a}–{snapshot.sets_won_b} sets, {snapshot.games_in_set_a}–{snapshot.games_in_set_b} games
Current point: {snapshot.point_score_a}–{snapshot.point_score_b}, {snapshot.server} serving

Serve stats (1st serve in % / 1st win % / 2nd win %):
  {snapshot.player_a_name}: {snapshot.player_a.first_serve_in_pct:.1%} / {snapshot.player_a.first_serve_points_won_pct:.1%} / {snapshot.player_a.second_serve_points_won_pct:.1%}
  {snapshot.player_b_name}: {snapshot.player_b.first_serve_in_pct:.1%} / {snapshot.player_b.first_serve_points_won_pct:.1%} / {snapshot.player_b.second_serve_points_won_pct:.1%}

Match win probability: {snapshot.player_a_name} {p_a_match:.1%}, {snapshot.player_b_name} {1-p_a_match:.1%}

Blending weight (live): {snapshot.blending_weight_live:.0%}
Prior (serve-point): {snapshot.generic_prior_serve_point_win:.1%}
    """
    return summary.strip()
