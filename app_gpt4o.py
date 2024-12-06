import streamlit as st
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import spacy
from collections import Counter
import pandas as pd

# Load the spaCy model
nlp = spacy.load("en_core_web_trf")

# Define Streamlit layout
st.set_page_config(layout="wide")
st.title("Text Analysis App")
st.sidebar.header("Settings")

# Sidebar settings
top_n = st.sidebar.slider("Top N elements to display", min_value=1, max_value=50, value=10)

# Full POS list with descriptions
pos_options = {
    "ADJ": "Adjective",
    "ADP": "Adposition",
    "ADV": "Adverb",
    "AUX": "Auxiliary",
    "CCONJ": "Coordinating Conjunction",
    "DET": "Determiner",
    "INTJ": "Interjection",
    "NOUN": "Noun",
    "NUM": "Numeral",
    "PART": "Particle",
    "PRON": "Pronoun",
    "PROPN": "Proper Noun",
    "PUNCT": "Punctuation",
    "SCONJ": "Subordinating Conjunction",
    "SYM": "Symbol",
    "VERB": "Verb",
    "X": "Other"
}

# POS inclusion filter
pos_filter = st.sidebar.multiselect(
    "Include POS (Part of Speech):",
    options=list(pos_options.keys()),
    format_func=lambda x: f"{x}: {pos_options[x]}",
    default=[]
)

# POS exclusion filter
exclude_pos_filter = st.sidebar.multiselect(
    "Exclude POS (Part of Speech):",
    options=list(pos_options.keys()),
    format_func=lambda x: f"{x}: {pos_options[x]}",
    default=[]
)

# Token property checkboxes
filter_stop_words = st.sidebar.checkbox("Exclude stop words", value=True)
filter_punct = st.sidebar.checkbox("Exclude punctuation", value=True)
filter_alpha = st.sidebar.checkbox("Include only alphabetic tokens", value=True)
filter_digits = st.sidebar.checkbox("Exclude digits", value=False)
filter_currency = st.sidebar.checkbox("Exclude currency symbols", value=False)
filter_quotes = st.sidebar.checkbox("Exclude quotes", value=False)

# Exclude words input
exclude_words = st.sidebar.text_input("Words to exclude (comma-separated):")
exclude_words_set = set([word.strip().lower() for word in exclude_words.split(",") if word.strip()])

# Responsive layout
col1, col2 = st.columns([2, 1])  # Left (text input + WordCloud) and right (bar charts)

# Actual text input
with col1:
    st.subheader("Input Text")
    text_input = st.text_area("Enter text:", height=300)

if text_input.strip():
    doc = nlp(text_input)

    # Token filters
    tokens = [
        token.text.lower() for token in doc
        if ((not filter_stop_words or not token.is_stop) and
            (not filter_punct or not token.is_punct) and
            (not filter_alpha or token.is_alpha) and
            (not filter_digits or not token.is_digit) and
            (not filter_currency or not token.is_currency) and
            (not filter_quotes or not token.is_quote) and
            (not pos_filter or token.pos_ in pos_filter) and
            (not exclude_pos_filter or token.pos_ not in exclude_pos_filter))
    ]

    filtered_tokens = [
        token for token in tokens
        if token not in exclude_words_set
    ]

    # Generate WordCloud
    wordcloud = WordCloud(width=800, height=400, background_color="white").generate(" ".join(filtered_tokens))
    
    # Frequency counts for unigrams and bigrams
    unigram_counts = Counter(filtered_tokens)
    bigram_counts = Counter([" ".join(bigram) for bigram in zip(filtered_tokens, filtered_tokens[1:])])

    # WordCloud below the text input
    with col1:
        st.subheader("Word Cloud")
        fig, ax = plt.subplots()
        ax.imshow(wordcloud, interpolation="bilinear")
        ax.axis("off")
        st.pyplot(fig)

    # Both bar charts on the right
    with col2:
        st.subheader("Unigram Frequency Plot")
        top_unigrams = unigram_counts.most_common(top_n)
        unigram_df = pd.DataFrame(top_unigrams, columns=["Unigram", "Frequency"])
        st.bar_chart(unigram_df.set_index("Unigram"))

        st.subheader("Bigram Frequency Plot")
        top_bigrams = bigram_counts.most_common(top_n)
        bigram_df = pd.DataFrame(top_bigrams, columns=["Bigram", "Frequency"])
        st.bar_chart(bigram_df.set_index("Bigram"))