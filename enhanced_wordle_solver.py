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
def display_feedback(guess, feedback):
    st.write("Wordle Feedback:")
    tile_html = "<div style='display: flex; gap: 10px;'>"
    for char, fb in zip(guess, feedback):
        color = {"g": "green", "y": "yellow", "b": "gray"}[fb]
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

# Streamlit App
def main():
    st.title("Interactive Wordle Solver")
    st.write("A smarter and more engaging Wordle bot!")

    # Load words
    words = load_words()
    if "word_list" not in st.session_state:
        st.session_state.word_list = words
        st.session_state.scores = calculate_statistical_scores(words)
        st.session_state.probability_type = "Statistical Likelihood"

    # Inputs
    guess = st.text_input("Enter the guess you made in wordle (5 letters):").lower()
    feedback = st.text_input("Enter the color feedback of each tile from wordle in order using g, y, or b with no spaces (g=green, y=yellow, b=black):").lower()

    # Process feedback
    if st.button("Submit Feedback"):
        if len(guess) == 5 and len(feedback) == 5 and all(c in "gyb" for c in feedback):
            st.session_state.word_list = filter_words(st.session_state.word_list, guess, feedback)

            # Display feedback as horizontal tiles
            display_feedback(guess, feedback)

            # Switch to entropy calculations if word list is small
            if len(st.session_state.word_list) < 1000:
                st.session_state.scores = compute_entropy(st.session_state.word_list, st.session_state.word_list)
                st.session_state.probability_type = "Entropy-Based Calculation"
            else:
                st.session_state.scores = calculate_statistical_scores(st.session_state.word_list)
                st.session_state.probability_type = "Statistical Likelihood"

            st.success(f"Filtered words: {len(st.session_state.word_list)} remaining.")
        else:
            st.error("Invalid input. Ensure both guess and feedback are 5 characters long.")

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
