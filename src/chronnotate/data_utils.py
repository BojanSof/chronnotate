import pandas as pd


def find_subsegments(df, label_column):
    if label_column not in df.columns:
        raise ValueError(
            f"Column '{label_column}' does not exist in the DataFrame"
        )

    labels = df[label_column]
    changes = (labels != labels.shift()) | labels.isna()

    segment_starts = df.index[changes]
    segment_ends = list(segment_starts[1:]) + [df.index[-1] + 1]

    subsegments = [
        {"start": start, "end": end, "label": df.at[start, label_column]}
        for start, end in zip(segment_starts, segment_ends)
        if not pd.isna(df.at[start, label_column])  # Exclude NaN segments
    ]

    return subsegments
