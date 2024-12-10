import streamlit as st
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import spacy
from collections import Counter
import pandas as pd
import altair as alt
import json
import gettext

# Define Streamlit layout
st.set_page_config(
    layout="wide", 
    page_title="FAO Text Insighter", 
    page_icon="assets/favicon.ico"
)

# Set up localization
langs = {
    "en": "EN",
    "es": "ES"
}

spacy_models = {
    "en": {"model": "en_core_web_md", "label": "English"},
    "es": {"model": "es_core_news_md", "label": "Spanish"}
}

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

lang = st.sidebar.radio(
    "",
    list(langs.keys()),
    format_func=langs.get,
    horizontal=True
)
locale_dir = "locales"
gettext.bindtextdomain('messages', locale_dir)
gettext.textdomain('messages')
_ = gettext.translation('messages', locale_dir, languages=[lang]).gettext

st.title("FAO Text Insighter")
st.sidebar.header(_("Settings"))

# Sidebar settings

model_option = st.sidebar.selectbox(
    _("Select spaCy model:"),
    options=list(spacy_models.keys()),
    format_func=lambda lang: _(spacy_models[lang]["label"])
)

# Load the selected spaCy model
nlp = spacy.load(spacy_models[model_option]["model"])

top_n = st.sidebar.slider(_("Top N elements to display"), min_value=1, max_value=30, value=15)

# Full POS list with descriptions
# POS inclusion and exclusion filters in a collapsible section
with st.sidebar.expander(_("Part of Speech (POS)")):
    # POS inclusion filter
    pos_filter = st.multiselect(
        _("Include POS:"),
        options=list(pos_options.keys()),
        format_func=lambda pos: _(pos_options[pos]),
        default=[]
    )

    # POS exclusion filter
    exclude_pos_filter = st.multiselect(
        _("Exclude POS:"),
        options=list(pos_options.keys()),
        format_func=lambda pos: _(pos_options[pos]),
        default=[]
    )

# Load default values from JSON file
defaults_file = f"defaults.{model_option}.json"
try:
    with open(defaults_file, "r") as f:
        defaults = json.load(f)
except FileNotFoundError:
    st.error(_("Defaults file for {label} not found. Using empty defaults.").format(label=spacy_models[model_option]['label']))
    defaults = {}

# Exclude unigrams input
with st.sidebar.expander(_("Exclude Unigrams")):
    exclude_unigrams = st.data_editor(
        pd.DataFrame(defaults.get("exclude_unigrams", []), columns=["Unigram"]),
        num_rows="dynamic",
        key="exclude_unigrams"
    )
exclude_unigrams_set = set(exclude_unigrams["Unigram"].str.lower())

# Exclude bigrams input
with st.sidebar.expander(_("Exclude Bigrams")):
    exclude_bigrams = st.data_editor(
        pd.DataFrame(defaults.get("exclude_bigrams", []), columns=["Bigram"]),
        num_rows="dynamic",
        key="exclude_bigrams"
    )
exclude_bigrams_set = set(exclude_bigrams["Bigram"].str.lower())

# Exclude trigrams input
with st.sidebar.expander(_("Exclude Trigrams")):
    exclude_trigrams = st.data_editor(
        pd.DataFrame(defaults.get("exclude_trigrams", []), columns=["Trigram"]),
        num_rows="dynamic",
        key="exclude_trigrams"
    )
exclude_trigrams_set = set(exclude_trigrams["Trigram"].str.lower())

# Unigram replacements
with st.sidebar.expander(_("Unigram Replacements")):
    unigram_replacements = st.data_editor(
        pd.DataFrame(columns=["Word", "Replacement"]),
        num_rows="dynamic",
        key="unigram_replacements"
    )

# Bigram replacements
with st.sidebar.expander(_("Bigram Replacements")):
    bigram_replacements = st.data_editor(
        pd.DataFrame(list(defaults.get("replace_bigrams", {}).items()), columns=["Bigram", "Replacement"]),
        num_rows="dynamic",
        key="bigram_replacements"
    )

# Trigram replacements
with st.sidebar.expander(_("Trigram Replacements")):
    trigram_replacements = st.data_editor(
        pd.DataFrame(list(defaults.get("replace_trigrams", {}).items()), columns=["Trigram", "Replacement"]),
        num_rows="dynamic",
        key="trigram_replacements"
    )

# Token property checkboxes in a collapsible section
with st.sidebar.expander(_("Token Filters")):
    filter_stop_words = st.checkbox(_("Exclude stop words"), value=True)
    filter_punct = st.checkbox(_("Exclude punctuation"), value=True)
    filter_digits = st.checkbox(_("Exclude digits"), value=True)
    filter_currency = st.checkbox(_("Exclude currency symbols"), value=True)
    filter_quotes = st.checkbox(_("Exclude quotes"), value=True)
    lemmatize = st.checkbox(_("Lemmatize"), value=False)

# WordCloud inclusion checkboxes
with st.sidebar.expander(_("WordCloud Filters")):
    include_unigrams_wc = st.checkbox(_("Include Unigrams in WordCloud"), value=True)
    include_bigrams_wc = st.checkbox(_("Include Bigrams in WordCloud"), value=True)
    include_trigrams_wc = st.checkbox(_("Include Trigrams in WordCloud"), value=True)

# Responsive layout
col1, col2 = st.columns([2, 1])  # Left (text input + WordCloud) and right (bar charts)

# Actual text input
with col1:
    st.subheader(_("Input Text"))
    text_input = st.text_area(_("Enter text:"), height=300)

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
    unigram_replacement_dict = dict(zip(
        unigram_replacements["Word"].str.lower().apply(lambda x: nlp(x)[0].lemma_ if lemmatize else x),
        unigram_replacements["Replacement"].str.lower()
    ))
    tokens = [unigram_replacement_dict.get(token, token) for token in tokens]

    unigram_counts = Counter(tokens)
    bigram_counts = Counter([" ".join(bigram) for bigram in zip(tokens, tokens[1:])])
    trigram_counts = Counter([" ".join(trigram) for trigram in zip(tokens, tokens[1:], tokens[2:])])

    # Apply bigram replacements
    bigram_replacement_dict = dict(zip(
        bigram_replacements["Bigram"].str.lower().apply(lambda x: " ".join([token.lemma_ if lemmatize else token.text for token in nlp(x)])),
        bigram_replacements["Replacement"].str.lower()
    ))
    bigram_counts = Counter({bigram_replacement_dict.get(bigram, bigram): count for bigram, count in bigram_counts.items()})
    
    # Apply trigram replacements
    trigram_replacement_dict = dict(zip(
        trigram_replacements["Trigram"].str.lower().apply(lambda x: " ".join([token.lemma_ if lemmatize else token.text for token in nlp(x)])),
        trigram_replacements["Replacement"].str.lower()
    ))
    trigram_counts = Counter({trigram_replacement_dict.get(trigram, trigram): count for trigram, count in trigram_counts.items()})

    # Apply unigram exclusion filter
    exclude_unigrams_set = set(exclude_unigrams["Unigram"].str.lower().apply(lambda x: nlp(x)[0].lemma_ if lemmatize else x))
    filtered_unigram_counts = Counter({
        k: v for k, v in unigram_counts.items()
        if k not in exclude_unigrams_set
    })

    # Apply bigram exclusion filter
    exclude_bigrams_set = set(exclude_bigrams["Bigram"].str.lower().apply(lambda x: " ".join([token.lemma_ if lemmatize else token.text for token in nlp(x)])))
    filtered_bigram_counts = Counter({
        k: v for k, v in bigram_counts.items()
        if k not in exclude_bigrams_set
    })

    # Apply trigram exclusion filter
    exclude_trigrams_set = set(exclude_trigrams["Trigram"].str.lower().apply(lambda x: " ".join([token.lemma_ if lemmatize else token.text for token in nlp(x)])))
    filtered_trigram_counts = Counter({
        k: v for k, v in trigram_counts.items()
        if k not in exclude_trigrams_set
    })

    # Merge unigram, bigram, and trigram counts
    combined_counts = Counter()
    if include_unigrams_wc:
        combined_counts += filtered_unigram_counts
    if include_bigrams_wc:
        combined_counts += filtered_bigram_counts
    if include_trigrams_wc:
        combined_counts += filtered_trigram_counts

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
        st.subheader(_("Word Cloud"))
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
        st.subheader(_("Unigram Frequency Plot"))
        top_unigrams = filtered_unigram_counts.most_common(top_n)
        unigram_df = pd.DataFrame(top_unigrams, columns=["Unigram", "Frequency"])
        unigram_chart = create_bar_chart(
            unigram_df, x_label="Unigram", y_label="Frequency", title=_("Top Unigrams")
        ).configure_axisX(labelAngle=-45, labelOverlap=False)
        st.altair_chart(unigram_chart, use_container_width=True)

        st.subheader(_("Bigram Frequency Plot"))
        top_bigrams = filtered_bigram_counts.most_common(top_n)
        bigram_df = pd.DataFrame(top_bigrams, columns=["Bigram", "Frequency"])
        bigram_chart = create_bar_chart(
            bigram_df, x_label="Bigram", y_label="Frequency", title=_("Top Bigrams")
        ).configure_axisX(labelAngle=-45, labelOverlap=False)
        st.altair_chart(bigram_chart, use_container_width=True)

        st.subheader(_("Trigram Frequency Plot"))
        top_trigrams = filtered_trigram_counts.most_common(top_n)
        trigram_df = pd.DataFrame(top_trigrams, columns=["Trigram", "Frequency"])
        trigram_chart = create_bar_chart(
            trigram_df, x_label="Trigram", y_label="Frequency", title=_("Top Trigrams")
        ).configure_axisX(labelAngle=-45, labelOverlap=False)
        st.altair_chart(trigram_chart, use_container_width=True)
