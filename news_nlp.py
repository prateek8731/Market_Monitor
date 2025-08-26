import pandas as pd
def analyze_headlines(headlines_df):
    if headlines_df is None or headlines_df.empty:
        return pd.DataFrame()
    df = headlines_df.copy().rename(columns={"title":"text"})
    # simple sentiment via naive polarity (placeholder)
    df["sentiment"] = df["text"].str.len() % 3 * 0.1  # placeholder
    df["entities"] = df["text"].apply(lambda t: [])
    return df

def map_entities_to_ticker(nlp_df, api_client=None):
    rows = []
    if nlp_df is None or nlp_df.empty:
        return pd.DataFrame()
    for _, r in nlp_df.iterrows():
        for ent in r.get("entities", []):
            rows.append({"entity": ent, "ticker": None, "sentiment": r.get("sentiment",0), "title": r.get("text","")})
    return pd.DataFrame(rows)