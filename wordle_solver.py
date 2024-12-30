import streamlit as st
from collections import Counter
import random

# Load word list
@st.cache
def load_words(file_path='words_alpha.txt'):
    with open(file_path, 'r') as file:
        return [word.strip().lower() for word in file if len(word.strip()) == 5]

# Filter words based on feedback
def filter_words(word_list, guess, feedback):
    filtered = []
    for word in word_list:
        valid = True
        for i, (g, f) in enumerate(zip(guess, feedback)):
            if f == 'g' and word[i] != g:  # Green
                valid = False
            elif f == 'y' and (g not in word or word[i] == g):  # Yellow
                valid = False
            elif f == 'b' and g in word:  # Black/Gray
                valid = False
        if valid:
            filtered.append(word)
    return filtered

# Compute letter frequencies
def compute_letter_frequencies(word_list):
    counter = Counter()
    for word in word_list:
        counter.update(set(word))  # Count unique letters only
    return counter

# Suggest the best word based on letter frequency
def suggest_word(word_list):
    letter_frequencies = compute_letter_frequencies(word_list)
    scored_words = {
        word: sum(letter_frequencies[char] for char in set(word))
        for word in word_list
    }
    return max(scored_words, key=scored_words.get) if scored_words else None

# Streamlit UI
def main():
    st.title("Wordle Solver Bot")
    st.write("A helper to solve Wordle puzzles with probability-based suggestions.")

    # Load words
    words = load_words()
    if "word_list" not in st.session_state:
        st.session_state.word_list = words

    # Inputs
    guess = st.text_input("Enter your guess (5 letters):").lower()
    feedback = st.text_input(
        "Enter feedback (g=green, y=yellow, b=black):"
    ).lower()
    
    if st.button("Filter Words"):
        if len(guess) == 5 and len(feedback) == 5 and all(c in "gyb" for c in feedback):
            st.session_state.word_list = filter_words(st.session_state.word_list, guess, feedback)
            st.success("Word list filtered based on feedback!")
        else:
            st.error("Invalid input. Ensure both guess and feedback are 5 characters long.")

    # Suggestions
    if st.session_state.word_list:
        suggestion = suggest_word(st.session_state.word_list)
        st.subheader("Suggested Word")
        st.write(suggestion if suggestion else "No suggestions available.")

        st.subheader("Remaining Words")
        st.write(", ".join(st.session_state.word_list[:50]))  # Display first 50 words

        st.subheader("Letter Frequencies")
        letter_frequencies = compute_letter_frequencies(st.session_state.word_list)
        st.bar_chart(letter_frequencies)
    else:
        st.error("No words remaining! Please reset or check your inputs.")

    # Reset Button
    if st.button("Reset Word List"):
        st.session_state.word_list = words
        st.success("Word list reset!")

if __name__ == "__main__":
    main()
