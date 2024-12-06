import streamlit as st
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import spacy
from collections import Counter
import pandas as pd
import altair as alt
import json

# Define Streamlit layout
st.set_page_config(layout="wide", page_title="Text Insighter")
st.title("Text Insighter")
st.sidebar.header("Settings")

# Sidebar settings
spacy_models = {
    "en_core_web_md": "🇺🇸 English",
    "es_core_news_md": "🇪🇸 Spanish"
}
model_option = st.sidebar.selectbox(
    "Select spaCy model:",
    options=list(spacy_models.keys()),
    format_func=spacy_models.get
)

# Load the selected spaCy model
nlp = spacy.load(model_option)

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

# Load default values from JSON file
with open("defaults.json", "r") as f:
    defaults = json.load(f)

# Exclude unigrams input
with st.sidebar.expander("Exclude Unigrams"):
    exclude_unigrams = st.data_editor(
        pd.DataFrame(defaults.get("exclude_unigrams", []), columns=["Unigram"]),
        num_rows="dynamic",
        key="exclude_unigrams"
    )
exclude_unigrams_set = set(exclude_unigrams["Unigram"].str.lower())

# Exclude bigrams input
with st.sidebar.expander("Exclude Bigrams"):
    exclude_bigrams = st.data_editor(
        pd.DataFrame(defaults.get("exclude_bigrams", []), columns=["Bigram"]),
        num_rows="dynamic",
        key="exclude_bigrams"
    )
exclude_bigrams_set = set(exclude_bigrams["Bigram"].str.lower())

# Unigram replacements
with st.sidebar.expander("Unigram Replacements"):
    unigram_replacements = st.data_editor(
        pd.DataFrame(columns=["Word", "Replacement"]),
        num_rows="dynamic",
        key="unigram_replacements"
    )

# Bigram replacements
with st.sidebar.expander("Bigram Replacements"):
    bigram_replacements = st.data_editor(
        pd.DataFrame(list(defaults.get("replace_bigrams", {}).items()), columns=["Bigram", "Replacement"]),
        num_rows="dynamic",
        key="bigram_replacements"
    )

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

    # Apply unigram replacements
    unigram_replacement_dict = dict(zip(unigram_replacements["Word"].str.lower(), unigram_replacements["Replacement"].str.lower()))
    tokens = [unigram_replacement_dict.get(token, token) for token in tokens]

    unigram_counts = Counter(tokens)
    bigram_counts = Counter([" ".join(bigram) for bigram in zip(tokens, tokens[1:])])

    # Apply bigram replacements
    bigram_replacement_dict = dict(zip(bigram_replacements["Bigram"].str.lower(), bigram_replacements["Replacement"].str.lower()))
    bigram_counts = Counter({bigram_replacement_dict.get(bigram, bigram): count for bigram, count in bigram_counts.items()})
    
    # Apply unigram exclusion filter
    filtered_unigram_counts = Counter({
        k: v for k, v in unigram_counts.items()
        if k not in exclude_unigrams_set
    })

    # Apply bigram exclusion filter
    filtered_bigram_counts = Counter({
        k: v for k, v in bigram_counts.items()
        if k not in exclude_bigrams_set
    })

    # Merge unigram and bigram counts
    combined_counts = filtered_unigram_counts + filtered_bigram_counts

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
        top_unigrams = filtered_unigram_counts.most_common(top_n)
        unigram_df = pd.DataFrame(top_unigrams, columns=["Unigram", "Frequency"])
        unigram_chart = create_bar_chart(
            unigram_df, x_label="Unigram", y_label="Frequency", title="Top Unigrams"
        ).configure_axisX(labelAngle=-45, labelOverlap=False)
        st.altair_chart(unigram_chart, use_container_width=True)

        st.subheader("Bigram Frequency Plot")
        top_bigrams = filtered_bigram_counts.most_common(top_n)
        bigram_df = pd.DataFrame(top_bigrams, columns=["Bigram", "Frequency"])
        bigram_chart = create_bar_chart(
            bigram_df, x_label="Bigram", y_label="Frequency", title="Top Bigrams"
        ).configure_axisX(labelAngle=-45, labelOverlap=False)
        st.altair_chart(bigram_chart, use_container_width=True)
