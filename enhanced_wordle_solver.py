import streamlit as st
from collections import Counter, defaultdict
import time

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

# Compute positional frequencies
def compute_positional_frequencies(word_list):
    position_freq = [Counter() for _ in range(5)]
    for word in word_list:
        for i, char in enumerate(word):
            position_freq[i][char] += 1
    return position_freq

# Score words based on positional frequency
def score_words(word_list, position_freq):
    scores = {}
    for word in word_list:
        scores[word] = sum(position_freq[i][char] for i, char in enumerate(word))
    return scores

# Suggest the best word based on scores
def suggest_word(word_list, position_freq):
    scores = score_words(word_list, position_freq)
    return max(scores, key=scores.get) if scores else None

# Streamlit UI
def main():
    st.title("Enhanced Wordle Solver Bot")
    st.write("A smarter and more engaging Wordle solver!")

    # Load words
    words = load_words()
    if "word_list" not in st.session_state:
        st.session_state.word_list = words

    # Inputs
    guess = st.text_input("Enter your guess (5 letters):").lower()
    feedback = st.text_input(
        "Enter feedback (g=green, y=yellow, b=black):"
    ).lower()

    # Progress animation
    if st.button("Filter Words"):
        if len(guess) == 5 and len(feedback) == 5 and all(c in "gyb" for c in feedback):
            with st.spinner("Filtering words..."):
                time.sleep(1)  # Simulate processing delay
                st.session_state.word_list = filter_words(st.session_state.word_list, guess, feedback)
                st.success("Word list filtered based on feedback!")
        else:
            st.error("Invalid input. Ensure both guess and feedback are 5 characters long.")

    # Suggestions with scoring
    if st.session_state.word_list:
        st.subheader("Best Word Suggestion")
        position_freq = compute_positional_frequencies(st.session_state.word_list)
        suggestion = suggest_word(st.session_state.word_list, position_freq)
        if suggestion:
            st.write(f"🎯 **Suggested Word**: {suggestion}")
        else:
            st.write("No suggestions available.")

        # Animation for feedback
        if st.button("Simulate Feedback Animation"):
            st.write("🎨 Simulating feedback...")
            for i, char in enumerate(guess):
                if feedback[i] == "g":
                    st.success(f"Letter '{char}' is Green!")
                elif feedback[i] == "y":
                    st.warning(f"Letter '{char}' is Yellow!")
                elif feedback[i] == "b":
                    st.error(f"Letter '{char}' is Black!")
                time.sleep(0.5)

        # Display remaining words
        st.subheader("Remaining Words")
        st.write(", ".join(st.session_state.word_list[:50]))  # Display first 50 words

        # Positional frequency chart
        st.subheader("Positional Letter Frequencies")
        position_freq_data = {f"Position {i+1}": dict(freq) for i, freq in enumerate(position_freq)}
        for pos, freq in position_freq_data.items():
            st.bar_chart(freq)
    else:
        st.error("No words remaining! Please reset or check your inputs.")

    # Reset Button
    if st.button("Reset Word List"):
        st.session_state.word_list = words
        st.success("Word list reset!")

if __name__ == "__main__":
    main()
