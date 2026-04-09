import pandas as pd
from datetime import datetime, timedelta
import altair as alt

def build_dataframe(data):
    rows = []
    for cluster in data["clusters"]:
        for event in cluster["events"]:
            dt = datetime.strptime(event["date"], "%Y-%m-%d")
            rows.append({"date": dt, "value": event["duration"]})

    df = pd.DataFrame(rows)
    df = df.groupby("date").sum().reset_index()

    date_max = df["date"].max()
    date_min = min(df["date"].min(), date_max - timedelta(weeks=12))

    full_range = pd.date_range(date_min, date_max)
    df = df.set_index("date").reindex(full_range).fillna(0).rename_axis("date").reset_index()

    origin = df["date"].min()
    df["week"] = ((df["date"] - origin).dt.days // 7)
    df["day"] = df["date"].dt.weekday  # 0=lundi

    return df

def build_chart(df):
    # 1 label par mois, sur la 1ère semaine où le mois apparaît
    month_df = df.copy()
    month_df["month_label"] = month_df["date"].dt.strftime("%b")
    month_df["month"] = month_df["date"].dt.month

    # Première semaine de chaque mois
    first_week_per_month = (
        month_df.groupby("month")["week"].min().reset_index()
    )
    first_week_per_month["month_label"] = first_week_per_month["month"].apply(
        lambda m: datetime(2000, m, 1).strftime("%b")
    )
    # Supprimer les doublons de semaine
    first_week_per_month = first_week_per_month.drop_duplicates("week")

    mapping = "{" + ",".join(
        f"{int(row.week)}: '{row.month_label}'"
        for _, row in first_week_per_month.iterrows()
    ) + "}"
    label_expr = f"({mapping})[datum.value] || ''"

    chart = alt.Chart(df).mark_rect(
        cornerRadius=2
    ).encode(
        x=alt.X(
            "week:O",
            title=None,
            axis=alt.Axis(
                values=first_week_per_month["week"].tolist(),
                labelExpr=label_expr,
                labelAngle=0,
                tickSize=0,
                domain=False,
                labelColor="#8b949e",
                labelFontSize=11,
            )
        ),
        y=alt.Y(
            "day:O",
            sort=list(range(7)),
            title=None,
            axis=alt.Axis(
                values=[0, 2, 4],
                labelExpr="['Mon','','Wed','','Fri','',''][datum.value]",
                tickSize=0,
                domain=False,
                labelColor="#8b949e",
                labelFontSize=11,
            )
        ),
        color=alt.Color(
            "value:Q",
            scale=alt.Scale(
                domain=[0, 0.5, 1.5, 3],
                range=["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
            ),
            legend=None  # on fera la légende manuellement si besoin
        ),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%d %b %Y"),
            alt.Tooltip("value:Q", title="Durée (h)", format=".2f"),
        ]
    ).properties(
        width=alt.Step(16),
        height=alt.Step(16),
    ).configure_view(
        stroke=None,
        fill="#0d1117",       # fond sombre comme GitHub
        continuousWidth=400,
        continuousHeight=120,
    ).configure_axis(
        grid=False,
        labelColor="#8b949e",
    )

    return chart