import plotly.express as px

dimensions = ["Java深度", "架构设计", "化工知识", "算法能力", "工程效率"]
fig = px.line_polar(
    df, r='current', theta=dimensions,
    line_close=True,
    template="plotly_dark",
    animation_frame="week_num"
)
fig.update_traces(fill='toself')