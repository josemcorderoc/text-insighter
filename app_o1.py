import streamlit as st
import spacy
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from itertools import tee
import io
import base64

# Load spaCy model
nlp = spacy.load("en_core_web_trf")

def generate_ngrams(tokens, n=1):
    if n == 1:
        return tokens
    else:
        t1, t2 = tee(tokens)
        for _ in range(n - 1):
            next(t2, None)
        return [" ".join(x) for x in zip(*[t1, t2])]

def filter_tokens(doc, pos_filter, exclude_words):
    tokens = [token.text for token in doc if token.is_alpha and (token.pos_ == pos_filter or pos_filter == "ALL")]
    # Exclude words
    tokens = [t for t in tokens if t.lower() not in exclude_words]
    return tokens

def plot_wordcloud(tokens):
    text = " ".join(tokens)
    wordcloud = WordCloud(background_color="white").generate(text)
    fig, ax = plt.subplots()
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis("off")
    return fig

def plot_frequency(tokens, top_n=10, ngram=1):
    ngrams = generate_ngrams(tokens, n=ngram)
    freq = Counter(ngrams).most_common(top_n)
    labels, values = zip(*freq) if freq else ([], [])
    fig, ax = plt.subplots()
    ax.barh(labels, values)
    ax.set_xlabel("Frequency")
    ax.set_ylabel("N-Grams" if ngram > 1 else "Tokens")
    plt.gca().invert_yaxis()
    plt.tight_layout()
    return fig

def export_fig_to_png(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=300, bbox_inches='tight')
    buf.seek(0)
    return buf

st.title("Text Analysis with spaCy")

# Text input
text = st.text_area("Insert your text here:")

# POS filter
pos_options = ["ALL", "NOUN", "VERB", "ADJ", "ADV", "PROPN", "PRON", "DET", "ADP", "AUX", "CCONJ", "INTJ", "NUM", "PART", "SCONJ", "SYM", "X"]
pos_filter = st.selectbox("Filter by POS", options=pos_options, index=0)

# Words to exclude
exclude_input = st.text_input("Words to exclude (comma separated):", value="")
exclude_words = {w.strip().lower() for w in exclude_input.split(",") if w.strip()}

# Top N slider
top_n = st.slider("Top N elements to display in frequency plots:", 5, 50, 10)

if text:
    doc = nlp(text)
    tokens_filtered = filter_tokens(doc, pos_filter, exclude_words)

    # Wordcloud
    wordcloud_fig = plot_wordcloud(tokens_filtered)

    # Unigram frequency plot
    unigram_fig = plot_frequency(tokens_filtered, top_n=top_n, ngram=1)

    # Bigram frequency plot
    bigram_fig = plot_frequency(tokens_filtered, top_n=top_n, ngram=2)

    st.header("Wordcloud")
    st.pyplot(wordcloud_fig)

    st.header("Unigram Frequency")
    st.pyplot(unigram_fig)

    st.header("Bigram Frequency")
    st.pyplot(bigram_fig)

    # Export buttons
    for name, fig in [("wordcloud.png", wordcloud_fig), ("unigram.png", unigram_fig), ("bigram.png", bigram_fig)]:
        buf = export_fig_to_png(fig)
        b64 = base64.b64encode(buf.read()).decode()
        href = f'<a href="data:file/png;base64,{b64}" download="{name}">Download {name}</a>'
        st.markdown(href, unsafe_allow_html=True)