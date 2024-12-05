import streamlit as st
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import spacy
from collections import Counter
import pandas as pd

# Load the spaCy model
nlp = spacy.load("en_core_web_trf")

# Define Streamlit layout
st.title("Text Analysis App")
st.sidebar.header("Settings")

# Input text
text_input = st.text_area("Enter text:", height=200)

# User inputs
top_n = st.sidebar.slider("Top N elements to display", min_value=1, max_value=50, value=10)
pos_filter = st.sidebar.multiselect("Filter by POS", ["VERB", "NOUN", "ADJ", "ADV", "PROPN"], default=[])
exclude_words = st.sidebar.text_input("Words to exclude (comma-separated):")
exclude_words_set = set([word.strip().lower() for word in exclude_words.split(",") if word.strip()])

# Process text with spaCy
if text_input.strip():
    doc = nlp(text_input)
    tokens = [
        token.text.lower() for token in doc 
        if (not token.is_stop and not token.is_punct and token.is_alpha)
    ]
    filtered_tokens = [
        token for token in tokens 
        if token not in exclude_words_set and 
           (not pos_filter or any(token_obj.pos_ in pos_filter for token_obj in doc if token_obj.text.lower() == token))
    ]

    # Generate WordCloud
    wordcloud = WordCloud(width=800, height=400, background_color="white").generate(" ".join(filtered_tokens))
    
    # Frequency counts for unigrams and bigrams
    unigram_counts = Counter(filtered_tokens)
    bigram_counts = Counter([" ".join(bigram) for bigram in zip(filtered_tokens, filtered_tokens[1:])])
    
    # Display WordCloud
    st.subheader("Word Cloud")
    fig, ax = plt.subplots()
    ax.imshow(wordcloud, interpolation="bilinear")
    ax.axis("off")
    st.pyplot(fig)
    
    # Display unigram frequency plot
    st.subheader("Unigram Frequency Plot")
    top_unigrams = unigram_counts.most_common(top_n)
    unigram_df = pd.DataFrame(top_unigrams, columns=["Unigram", "Frequency"])
    st.bar_chart(unigram_df.set_index("Unigram"))
    
    # Display bigram frequency plot
    st.subheader("Bigram Frequency Plot")
    top_bigrams = bigram_counts.most_common(top_n)
    bigram_df = pd.DataFrame(top_bigrams, columns=["Bigram", "Frequency"])
    st.bar_chart(bigram_df.set_index("Bigram"))
    
    # Export data
    st.sidebar.header("Export")
    if st.sidebar.button("Download WordCloud as Image"):
        wordcloud.to_file("wordcloud.png")
        st.sidebar.success("WordCloud saved as wordcloud.png")
    if st.sidebar.button("Download Frequency Data"):
        unigram_df.to_csv("unigram_frequency.csv", index=False)
        bigram_df.to_csv("bigram_frequency.csv", index=False)
        st.sidebar.success("Frequency data saved as unigram_frequency.csv and bigram_frequency.csv")