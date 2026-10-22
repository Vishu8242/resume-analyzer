"""
Charts Component
Provides interactive Plotly visualizations:
- Circular score gauge
- Radar / spider chart of component scores
- Component performance horizontal bars
- Skills distribution donut chart
"""

from typing import Dict, Any, Optional

try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


def create_gauge_chart(score: float, grade: str = "Compatibility") -> Any:
    """
    Creates an executive circular gauge chart for the ATS score.
    """
    if not PLOTLY_AVAILABLE:
        return None

    # Determine needle / bar color
    if score >= 85:
        bar_color = "#10B981"  # Emerald
    elif score >= 70:
        bar_color = "#3B82F6"  # Blue
    elif score >= 50:
        bar_color = "#F59E0B"  # Amber
    else:
        bar_color = "#EF4444"  # Red

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": f"<b>{grade}</b>", "font": {"size": 16, "color": "#1E293B"}},
        number={"suffix": "/100", "font": {"size": 36, "color": "#0F172A", "family": "Plus Jakarta Sans, sans-serif"}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#94A3B8", "dtick": 20},
            "bar": {"color": bar_color, "thickness": 0.28},
            "bgcolor": "#F1F5F9",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 50], "color": "#FEE2E2"},
                {"range": [50, 70], "color": "#FEF3C7"},
                {"range": [70, 85], "color": "#DBEAFE"},
                {"range": [85, 100], "color": "#D1FAE5"}
            ],
            "threshold": {
                "line": {"color": "#6366F1", "width": 3},
                "thickness": 0.75,
                "value": 75
            }
        }
    ))

    fig.update_layout(
        height=260,
        margin=dict(l=20, r=20, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "Plus Jakarta Sans, -apple-system, sans-serif"}
    )
    return fig


def create_radar_chart(component_scores: Optional[Dict[str, Optional[float]]]) -> Any:
    """
    Creates a radar chart showing candidate balance across the 5 ATS pillars.
    """
    if not PLOTLY_AVAILABLE:
        return None

    if not component_scores:
        component_scores = {}

    categories = [
        "Skills Match",
        "Experience",
        "Education",
        "Keyword Alignment",
        "Formatting & Layout"
    ]
    
    score_keys = ["skills", "experience", "education", "keywords", "formatting"]
    values = [component_scores.get(k, 0.0) or 0.0 for k in score_keys]
    
    # Close the radar polygon
    categories_closed = categories + [categories[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()

    # Target Benchmark polygon (75%)
    benchmark = [75, 75, 75, 75, 75, 75]
    fig.add_trace(go.Scatterpolar(
        r=benchmark,
        theta=categories_closed,
        fill=None,
        line=dict(color="#94A3B8", dash="dot", width=1.5),
        name="Target Benchmark (75%)"
    ))

    # Candidate polygon
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill="toself",
        fillcolor="rgba(99, 102, 241, 0.22)",
        line=dict(color="#4F46E5", width=2.5),
        name="Candidate Profile"
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(size=10, color="#64748B"),
                gridcolor="#E2E8F0"
            ),
            angularaxis=dict(
                tickfont=dict(size=11, color="#1E293B", family="Plus Jakarta Sans"),
                gridcolor="#E2E8F0"
            ),
            bgcolor="#FAFAFA"
        ),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        height=320,
        margin=dict(l=35, r=35, t=25, b=25),
        paper_bgcolor="rgba(0,0,0,0)"
    )
    return fig


def create_horizontal_bar_chart(component_scores: Optional[Dict[str, Optional[float]]]) -> Any:
    """
    Creates horizontal performance bars for each component score.
    """
    if not PLOTLY_AVAILABLE:
        return None

    if not component_scores:
        component_scores = {}

    labels = ["Formatting", "Keywords", "Education", "Experience", "Skills Match"]
    keys = ["formatting", "keywords", "education", "experience", "skills"]
    scores = [component_scores.get(k, 0.0) or 0.0 for k in keys]

    colors_list = []
    for s in scores:
        if s >= 80:
            colors_list.append("#10B981")
        elif s >= 60:
            colors_list.append("#3B82F6")
        elif s >= 40:
            colors_list.append("#F59E0B")
        else:
            colors_list.append("#EF4444")

    fig = go.Figure(go.Bar(
        x=scores,
        y=labels,
        orientation="h",
        marker=dict(color=colors_list, line=dict(color="rgba(0,0,0,0.1)", width=1)),
        text=[f"{s:.1f}%" for s in scores],
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(color="white", size=12, family="Plus Jakarta Sans")
    ))

    fig.update_layout(
        xaxis=dict(range=[0, 100], title="Score (%)", gridcolor="#E2E8F0"),
        yaxis=dict(gridcolor="#E2E8F0"),
        height=240,
        margin=dict(l=10, r=20, t=10, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig


def create_skills_donut_chart(stats: Optional[Dict[str, int]]) -> Any:
    """
    Creates a donut chart displaying the breakdown of matching vs missing skills.
    """
    if not PLOTLY_AVAILABLE:
        return None

    if not stats:
        stats = {}

    labels = ["Matching Skills", "Missing Required", "Missing Preferred"]
    values = [
        stats.get("total_matching", 0),
        stats.get("total_missing_required", 0),
        stats.get("total_missing_preferred", 0)
    ]

    # If no skills
    if sum(values) == 0:
        return None

    colors = ["#10B981", "#EF4444", "#F59E0B"]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.55,
        marker=dict(colors=colors),
        textinfo="value+percent",
        textfont=dict(size=12, family="Plus Jakarta Sans")
    )])

    fig.update_layout(
        height=260,
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
        paper_bgcolor="rgba(0,0,0,0)"
    )
    return fig
