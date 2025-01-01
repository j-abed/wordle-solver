"""
[WIP] Wordle Solver with Smart Color Preservation
Known issues:
- Green tile preservation not working correctly between guesses
- Need to fix comparison logic for letter positions
Status: Development version, not ready for production
"""

import streamlit as st
import numpy as np
import pandas as pd
from collections import Counter

# Load word list
@st.cache_data
def load_words(file_path="words_enable.txt"):
    with open(file_path, "r") as file:
        words = [word.strip().lower() for word in file if len(word.strip()) == 5]
    return words

# Statistical scoring based on letter frequency
def calculate_statistical_scores(word_list):
    letter_freq = Counter("".join(word_list))
    scores = {
        word: sum(letter_freq[char] for char in set(word))
        for word in word_list
    }
    return scores

# Entropy calculations for word scoring
def compute_entropy(word_list, possible_words):
    entropy_scores = {}
    for guess in word_list:
        pattern_counts = Counter(
            evaluate_guess(word, guess) for word in possible_words
        )
        total = sum(pattern_counts.values())
        entropy = -sum(
            (count / total) * np.log2(count / total)
            for count in pattern_counts.values()
            if count > 0
        )
        entropy_scores[guess] = entropy
    return entropy_scores

# Evaluate guess feedback
def evaluate_guess(solution, guess):
    feedback = ["b"] * 5  # Default to black
    solution_chars = list(solution)

    # Green matches
    for i, (s, g) in enumerate(zip(solution, guess)):
        if s == g:
            feedback[i] = "g"
            solution_chars[i] = None

    # Yellow matches
    for i, g in enumerate(guess):
        if feedback[i] == "b" and g in solution_chars:
            feedback[i] = "y"
            solution_chars[solution_chars.index(g)] = None

    return "".join(feedback)

# Filter words based on feedback
def filter_words(word_list, guess, feedback):
    return [word for word in word_list if evaluate_guess(word, guess) == feedback]

# Suggest the best word
def suggest_word(scores):
    if not scores:
        return None
    return max(scores, key=scores.get)

# Display feedback as horizontal tiles
def display_feedback(guess, feedback, show_title=False):
    if show_title:
        st.write("Wordle Feedback:")
    tile_html = "<div style='display: flex; gap: 10px;'>"
    for char, fb in zip(guess, feedback):
        color = {"g": "green", "y": "#FFD700", "b": "gray"}[fb]
        tile_html += f"""
        <span style="
            display: inline-block;
            padding: 10px 15px;
            background-color: {color};
            color: white;
            font-weight: bold;
            border-radius: 5px;
            text-align: center;
            width: 30px;">
            {char.upper()}
        </span>
        """
    tile_html += "</div>"
    st.components.v1.html(tile_html, height=50)

# Normalize scores to percentages
def normalize_scores(scores):
    total_score = sum(scores.values())
    if total_score == 0:
        return {word: 0 for word in scores}
    return {word: (score / total_score) * 100 for word, score in scores.items()}

# User input for color feedback using clickable tiles
def get_green_positions(guess, feedback):
    """Return indices and letters of green matches"""
    return [(i, guess[i]) for i, fb in enumerate(feedback) if fb == "g"]

def get_color_feedback(guess):
    # Initialize states and history
    if 'feedback_states' not in st.session_state:
        st.session_state.feedback_states = [0] * 5
    if 'guess_history' not in st.session_state:
        st.session_state.guess_history = []
    if 'green_positions' not in st.session_state:
        st.session_state.green_positions = []
    
    if not guess:
        return ["b"] * 5

    # Define color mappings
    COLORS = {
        0: "⚫",  # Black/Gray
        1: "🟡",  # Yellow
        2: "🟢",  # Green
    }
    
    st.write("Click the circles to change colors: ⚫ → 🟡 → 🟢")
    
    # Create container for feedback display
    feedback_display = st.container()
    button_container = st.container()

    with button_container:
        # Create columns for buttons
        cols = st.columns(6)

        # Create buttons for each letter
        for i, (col, char) in enumerate(zip(cols[:5], guess)):
            state = st.session_state.feedback_states[i]
            with col:
                st.write(f"### {char.upper()}")
                if st.button(
                    COLORS[state],
                    key=f"btn_{i}_{guess}",
                    use_container_width=True
                ):
                    st.session_state.feedback_states[i] = (state + 1) % 3
                    st.rerun()

        # Add submit button in the last column
        with cols[5]:
            st.write("###")  # Empty header to align with letters
            submit_clicked = st.button("Submit", use_container_width=True, type="primary")

    # Convert current state to feedback
    state_to_feedback = {0: "b", 1: "y", 2: "g"}
    current_feedback = [state_to_feedback[state] for state in st.session_state.feedback_states]
    
    # Process and display feedback if submit was clicked
    if submit_clicked:
        feedback_str = ''.join(current_feedback)
        
        if len(guess) == 5 and len(feedback_str) == 5:
            # Add to history and process feedback
            st.session_state.guess_history.append((guess, current_feedback))
            st.session_state.word_list = filter_words(st.session_state.word_list, guess, feedback_str)

            # Update probability calculations
            if len(st.session_state.word_list) < 1000:
                st.session_state.scores = compute_entropy(st.session_state.word_list, st.session_state.word_list)
                st.session_state.probability_type = "Entropy-Based Calculation"
            else:
                st.session_state.scores = calculate_statistical_scores(st.session_state.word_list)
                st.session_state.probability_type = "Statistical Likelihood"

            st.success(f"Filtered words: {len(st.session_state.word_list)} remaining.")
            
            # Smart reset: preserve only matching greens from current word
            new_states = [0] * 5  # Start with all black
            
            # If we have a previous guess, compare letters at green positions
            if st.session_state.last_guess and st.session_state.last_green_letters:
                prev_guess = st.session_state.last_guess
                # Only preserve greens if same letter in same position
                for pos, letter in st.session_state.last_green_letters.items():
                    if pos < len(guess) and guess[pos] == prev_guess[pos] == letter:
                        new_states[pos] = 2

            # Get current green positions
            current_green_positions = get_green_positions(guess, current_feedback)
            
            # Update with new greens
            for pos, letter in current_green_positions:
                new_states[pos] = 2

            # Store current guess and its green letters for next comparison
            st.session_state.last_guess = guess
            st.session_state.last_green_letters = {
                pos: letter for pos, letter in current_green_positions
            }
            
            # Update the feedback states
            st.session_state.feedback_states = new_states
            
            st.rerun()

    return current_feedback

# User input for guess and color feedback in a single action
def get_guess_and_feedback():
    guess = st.text_input("Enter your guess (5 letters):", max_chars=5).lower()
    if guess and len(guess) == 5:
        return guess, get_color_feedback(guess)
    return guess, ["b"] * 5

# Streamlit App
def main():
    st.title("Wordle Solver")
    st.write("An entropy based Wordle helper!")

    # Initialize guess history if not exists
    if 'guess_history' not in st.session_state:
        st.session_state.guess_history = []

    # Load words
    words = load_words()
    if "word_list" not in st.session_state:
        st.session_state.word_list = words
        st.session_state.scores = calculate_statistical_scores(words)
        st.session_state.probability_type = "Statistical Likelihood"

    # Initialize new session state variables
    if "last_green_positions" not in st.session_state:
        st.session_state.last_green_positions = []
    if "last_guess" not in st.session_state:
        st.session_state.last_guess = None

    # Initialize green letter tracking
    if "last_green_letters" not in st.session_state:
        st.session_state.last_green_letters = {}

    # Get guess and process feedback in one step
    guess, feedback = get_guess_and_feedback()
    
    # Display guess history
    if st.session_state.guess_history:
        st.write("### Previous Guesses:")
        for hist_guess, hist_feedback in st.session_state.guess_history:
            display_feedback(hist_guess, hist_feedback, show_title=False)
    
    # Rest of the display logic
    if st.session_state.word_list:
        # Show probability type
        st.write(f"**Current Probability Calculation Type:** {st.session_state.probability_type}")
        
        # Suggestion
        if st.session_state.word_list:
            suggestion = suggest_word(st.session_state.scores)
            if suggestion:
                normalized_scores = normalize_scores(st.session_state.scores)
                st.write(f"🎯 **Suggested Word**: {suggestion} (Likelihood: {normalized_scores[suggestion]:.2f}%)")

                # Top 10 suggested words
                scores_df = pd.DataFrame.from_dict(normalized_scores, orient="index", columns=["Likelihood (%)"])
                scores_df = scores_df.sort_values("Likelihood (%)", ascending=False).head(10)
                st.write("**Top Suggested Words:**")
                st.table(scores_df)

                # Bar chart of top words using Streamlit
                st.bar_chart(scores_df)
            else:
                st.write("No suggestions available.")

    # Reset
    if st.button("Reset Word List"):
        st.session_state.word_list = words
        st.session_state.scores = calculate_statistical_scores(words)
        st.session_state.probability_type = "Statistical Likelihood"
        st.session_state.feedback_states = [0] * 5
        st.session_state.submitted_feedback = None
        st.session_state.guess_history = []  # Clear history
        st.session_state.last_green_positions = []  # Clear green position history
        st.session_state.last_guess = None  # Clear last guess
        st.session_state.last_green_letters = {}  # Clear green letter positions
        st.success("Word list reset!")

    # Detailed explanation of entropy at the bottom
    with st.expander("What is Entropy?"):
        st.write("""
        Entropy is a concept from information theory that quantifies uncertainty. 
        In the context of this Wordle solver, entropy measures the amount of information 
        gained by making a particular guess. A guess with high entropy provides more 
        insight into the solution, helping narrow down the possibilities.
        
        This method is particularly useful in later stages of the game, when the remaining 
        possible solutions are fewer. By calculating the expected feedback for each guess, 
        the solver identifies the most "informative" guess to make next.
        """)

if __name__ == "__main__":
    main()
