import streamlit as st
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import spacy
from collections import Counter
import pandas as pd
import altair as alt

# Load the spaCy model
nlp = spacy.load("en_core_web_md")

# Define Streamlit layout
st.set_page_config(layout="wide", page_title="Text Insighter")
st.title("Text Insighter")
st.sidebar.header("Settings")

# Sidebar settings
top_n = st.sidebar.slider("Top N elements to display", min_value=1, max_value=30, value=15)

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
    format_func=pos_options.get,
    default=[]
)

# POS exclusion filter
exclude_pos_filter = st.sidebar.multiselect(
    "Exclude POS (Part of Speech):",
    options=list(pos_options.keys()),
    format_func=pos_options.get,
    default=[]
)

# Exclude words input
exclude_words = st.sidebar.text_input("Words to exclude (comma-separated):")
exclude_words_set = set([word.strip().lower() for word in exclude_words.split(",") if word.strip()])

# Token property checkboxes
filter_stop_words = st.sidebar.checkbox("Exclude stop words", value=True)
filter_punct = st.sidebar.checkbox("Exclude punctuation", value=True)
filter_digits = st.sidebar.checkbox("Exclude digits", value=True)
filter_currency = st.sidebar.checkbox("Exclude currency symbols", value=True)
filter_quotes = st.sidebar.checkbox("Exclude quotes", value=True)
lemmatize = st.sidebar.checkbox("Lemmatize", value=False)

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
        (token.lemma_ if lemmatize else token.text).lower() for token in doc
        if (token.is_alpha and
            (not filter_stop_words or not token.is_stop) and
            (not filter_punct or not token.is_punct) and
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

    unigram_counts = Counter(filtered_tokens)
    bigram_counts = Counter([" ".join(bigram) for bigram in zip(filtered_tokens, filtered_tokens[1:])])
    
    # Merge unigram and bigram counts
    combined_counts = unigram_counts + bigram_counts
    
    wordcloud = WordCloud(
        width=1600, 
        height=800, 
        background_color="white",
        colormap="viridis",  # Improved color palette
        max_words=200,  # Adjust maximum words
        prefer_horizontal=0.9,  # Prefer horizontal words
        contour_width=1,  # Add contour for better visual quality
        contour_color="black"  # Contour color
    ).generate_from_frequencies(combined_counts)

    

    # WordCloud below the text input
    with col1:
        st.subheader("Word Cloud")
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.imshow(wordcloud, interpolation="bilinear")
        ax.axis("off")
        st.pyplot(fig)

    # Create bar charts using Altair
    def create_bar_chart(data, x_label, y_label, title):
        chart = (
            alt.Chart(data)
            .mark_bar()
            .encode(
                x=alt.X(x_label, sort="-y", title=x_label.capitalize()),
                y=alt.Y(y_label, title="Frequency"),
                tooltip=[x_label, y_label]
            )
            .properties(title=title)
            .configure_title(fontSize=16)
        )
        return chart

    # Both bar charts on the right
    with col2:
        st.subheader("Unigram Frequency Plot")
        top_unigrams = unigram_counts.most_common(top_n)
        unigram_df = pd.DataFrame(top_unigrams, columns=["Unigram", "Frequency"])
        unigram_chart = create_bar_chart(
            unigram_df, x_label="Unigram", y_label="Frequency", title="Top Unigrams"
        ).configure_axisX(labelAngle=-45, labelOverlap=False)
        st.altair_chart(unigram_chart, use_container_width=True)

        st.subheader("Bigram Frequency Plot")
        top_bigrams = bigram_counts.most_common(top_n)
        bigram_df = pd.DataFrame(top_bigrams, columns=["Bigram", "Frequency"])
        bigram_chart = create_bar_chart(
            bigram_df, x_label="Bigram", y_label="Frequency", title="Top Bigrams"
        ).configure_axisX(labelAngle=-45, labelOverlap=False)
        st.altair_chart(bigram_chart, use_container_width=True)
