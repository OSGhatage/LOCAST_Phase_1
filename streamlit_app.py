import streamlit as st
from datetime import datetime
import plotly.graph_objects as go

# Configure page
st.set_page_config(
    page_title="LOCAST",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'show_locust_info' not in st.session_state:
    st.session_state.show_locust_info = False
if 'show_stage_info' not in st.session_state:
    st.session_state.show_stage_info = False
if 'show_recent_events' not in st.session_state:
    st.session_state.show_recent_events = False
if 'show_organizations' not in st.session_state:
    st.session_state.show_organizations = False

# Custom CSS with Montserrat and Glacial Indifference fonts, and new color palette
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@700&family=Glacial+Indifference:wght@700&display=swap');
    body, .main-header {
        background: #ffdb99 !important;
    }
    .main-header {
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .main-header h1 {
        color: #ffffff;
        text-align: center;
        margin: 0;
        font-size: 3rem;
        font-family: 'Montserrat', sans-serif;
        font-weight: 400;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .tagline {
        color: #ffffff;
        text-align: center;
        font-size: 1.4rem;
        margin: 0.5rem 0;
        font-family: 'Glacial Indifference', sans-serif;
        font-weight: 700;
    }
    .region-info {
        color: #ffffff;
        text-align: center;
        font-size: 1.1rem;
        margin: 0;
        font-family: 'Glacial Indifference', sans-serif;
    }
    .parameter-container {
        background: #fff8e1;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 4px solid #ffbd59;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .result-container {
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
        text-align: center;
        font-size: 1.4rem;
        font-weight: bold;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .danger-high {
        background: #ffcdd2;
        color: #c62828;
        border: 3px solid #e57373;
    }
    .danger-moderate {
        background: #ffcc02;
        color: #ef6c00;
        border: 3px solid #ffb74d;
    }
    .safe {
        background: #c8e6c9;
        color: #2e7d32;
        border: 3px solid #81c784;
    }
    .info-button {
        background: #ffdb99;
        color: #ffffff;
        border: none;
        padding: 0.8rem 1.5rem;
        border-radius: 25px;
        font-size: 1rem;
        font-weight: bold;
        cursor: pointer;
        margin: 0.5rem;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        font-family: 'Glacial Indifference', sans-serif;
    }
    .info-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }
    .logo-container {
        text-align: center;
        margin-bottom: 1rem;
    }
    .logo-image {
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        margin: 1rem 0;
        max-width: 200px;
        height: auto;
    }
    .alert-banner {
        background: #ffdb99;
        color: #ffffff;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        text-align: center;
        font-weight: bold;
        font-family: 'Glacial Indifference', sans-serif;
    }
    .reference-note {
        font-style: italic;
        color: #666;
        font-size: 0.9rem;
        margin-top: 1rem;
        text-align: center;
    }
    @media (max-width: 600px) {
        .main-header h1 { font-size: 2rem; }
        .parameter-container { padding: 1rem; }
        .result-container { font-size: 1.2rem; }
        .info-button { padding: 0.6rem 1rem; font-size: 0.9rem; }
        .logo-image { max-width: 150px; }
    }
</style>
""", unsafe_allow_html=True)

# Environmental Suitability Thresholds (OPTIMAL CONDITIONS for locusts)
thresholds = {
    "Egg Laying": {
        "Rainfall": (20, 28),
        "Soil Moisture": (20, 40),
        "Soil Temperature": (15, 35),
        "Air Temperature": (18, 35),
    },
    "Hopper": {
        "Rainfall": (20, 28),
        "Surface Wind Speed": (0, 2),
        "Air Temperature": (22, 34),
    },
    "Adult": {
        "Rainfall": (20, 28),
        "Surface Wind Speed": (6, 8),
        "Soil Temperature": (15, 24),
        "Air Temperature": (20, 22),
    },
    "Swarm": {
        "Rainfall": (20, 28),
        "Wind Speed 850hPa": (6, float('inf')),  # >6 m/s
        "Air Temperature": (23, 26),
        "Vegetation (NDVI)": (0.5, 1.0),
    }
}

# Parameter ranges for visualization
param_ranges = {
    "Rainfall": (0, 50),
    "Soil Moisture": (0, 50),
    "Soil Temperature": (15, 50),
    "Air Temperature": (15, 50),
    "Surface Wind Speed": (0, 10),
    "Wind Speed 850hPa": (0, 10),
    "Vegetation (NDVI)": (0, 1),
}

# Parameter units
param_units = {
    "Rainfall": "mm",
    "Soil Moisture": "%",
    "Soil Temperature": "°C",
    "Air Temperature": "°C",
    "Surface Wind Speed": "m/s",
    "Wind Speed 850hPa": "m/s",
    "Vegetation (NDVI)": ""
}

@st.cache_data
def create_parameter_bar(param_name, value, stage):
    """Create a visual bar showing safe and optimal (locust-suitable) zones"""
    min_val, max_val = param_ranges[param_name]
    optimal_min, optimal_max = thresholds[stage][param_name]

    # Normalize values for HTML positioning
    def normalize(v): 
        return max(0, min(1, (v - min_val) / (max_val - min_val)))

    normalized_value = normalize(value)
    normalized_optimal_min = normalize(optimal_min)
    normalized_optimal_max = min(normalize(optimal_max), 1.0)  # Cap at 1 for infinite max

    is_optimal = optimal_min <= value <= optimal_max
    marker_color = '#1a1a1a' if is_optimal else '#ffffff'
    badge_bg = '#ffcdd2' if is_optimal else '#c8e6c9'
    badge_text = '#c62828' if is_optimal else '#2e7d32'

    # Modularized HTML components
    bar_background = """
    <div style="position: relative; height: 40px; background: linear-gradient(to right, #c8e6c9, #a5d6a7); border-radius: 20px; overflow: hidden; border: 2px solid #ddd;">
    """
    optimal_zone = f"""
    <div style="position: absolute; left: {normalized_optimal_min * 100}%; width: {(normalized_optimal_max - normalized_optimal_min) * 100}%; height: 100%;
                background: linear-gradient(135deg, #d32f2f 0%, #f44336 100%); opacity: 0.9;">
    </div>
    """
    value_marker = f"""
    <div style="position: absolute; left: {normalized_value * 100}%; width: 6px; height: 100%; background: {marker_color}; border-radius: 3px;
                transform: translateX(-50%); box-shadow: 0 0 10px rgba(0,0,0,0.5);">
    </div>
    """
    value_labels = f"""
    <div style="position: absolute; left: 8px; top: 50%; transform: translateY(-50%);
                font-size: 13px; color: #000; font-weight: bold;">
        {min_val}{param_units[param_name]}
    </div>
    <div style="position: absolute; right: 8px; top: 50%; transform: translateY(-50%);
                font-size: 13px; color: #000; font-weight: bold;">
        {max_val}{param_units[param_name]}
    </div>
    </div>
    """
    current_value = f"""
    <div style="text-align: center; margin-top: 8px;">
        <span style="background: {badge_bg}; padding: 4px 12px; border-radius: 15px;
                     font-size: 14px; font-weight: bold; color: {badge_text};">
            Current: {value:.1f}{param_units[param_name]}
        </span>
    </div>
    """
    range_info = f"""
    <div style="display: flex; justify-content: space-between; margin-top: 8px; font-size: 12px;">
        <span style="color: #2e7d32;">🟢 Safe Zone</span>
        <span style="color: #666;">Optimal Zone: {optimal_min}-{optimal_max if optimal_max != float('inf') else '∞'}{param_units[param_name]}</span>
        <span style="color: #d32f2f;">🔴 Locust Optimal</span>
    </div>
    """

    return f"""
    <div style="margin: 15px 0;">
        {bar_background}
        {optimal_zone}
        {value_marker}
        {value_labels}
        {current_value}
        {range_info}
    </div>
    """

def calculate_suitability(inputs, stage):
    """Calculate danger level based on input parameters and stage thresholds"""
    optimal_count = 0
    total_params = len(inputs)
    
    for param, value in inputs.items():
        min_threshold, max_threshold = thresholds[stage][param]
        if min_threshold <= value <= max_threshold:
            optimal_count += 1
    
    danger_percentage = (optimal_count / total_params) * 100
    
    if danger_percentage >= 80:
        return "HIGH DANGER", "🔴", "danger-high"
    elif danger_percentage >= 50:
        return "MODERATE DANGER", "🟡", "danger-moderate"
    else:
        return "SAFE CONDITIONS", "🟢", "safe"

def render_chart(inputs, stage):
    """Render Plotly bar chart for parameter suitability"""
    suitability = [
        min(100, max(0, (inputs[param] - thresholds[stage][param][0]) / 
                     (thresholds[stage][param][1] - thresholds[stage][param][0]) * 100 
                     if thresholds[stage][param][1] != float('inf') else (100 if inputs[param] >= thresholds[stage][param][0] else 0)))
        for param in inputs
    ]
    
    fig = go.Figure(data=[
        go.Bar(
            x=list(inputs.keys()),
            y=suitability,
            marker_color=["#ffbd59", "#ffdb99", "#ffcc80", "#ffa726", "#ff9800"],
            marker_line_color=["#ff8c00", "#e65100", "#ff6f00", "#ef6c00", "#f57c00"],
            marker_line_width=1
        )
    ])
    
    fig.update_layout(
        title=f"Parameter Suitability for {stage} Stage",
        xaxis_title="Parameters",
        yaxis_title="Suitability (%)",
        yaxis=dict(range=[0, 100]),
        showlegend=False,
        height=400,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    st.plotly_chart(fig, use_container_width=True)

def display_locust_info():
    """Display comprehensive information about desert locusts"""
    st.markdown("### 🦗 Desert Locust Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Scientific Name:** *Schistocerca gregaria*
        
        **Key Characteristics:**
        - Length: 4-6 cm
        - Color: Yellow-brown (solitary), bright yellow/pink (gregarious)
        - Lifecycle: Egg → Hopper → Adult (45-65 days)
        - Swarm capacity: Up to 80 million locusts per km²
        
        **Threat Level:**
        - Can travel 130 km per day
        - Consume their own body weight daily
        - 1 km² swarm eats same as 35,000 people
        """)
    
    with col2:
        st.markdown("""
        **Behavioral Phases:**
        - **Solitary:** Harmless, avoid each other
        - **Transient:** Begin grouping, color changes
        - **Gregarious:** Form swarms, highly destructive
        
        **Preferred Conditions:**
        - Breeding: 25-35°C, 10-30% soil moisture
        - Swarming: 30-40°C, seasonal rains
        - Migration: Wind speeds 15-30 km/h
        """)

def display_stage_info():
    """Display information about different locust stages"""
    st.markdown("### 🔄 Locust Life Stages")
    
    stages_info = {
        "🥚 Egg Stage (2-4 weeks)": {
            "description": "Eggs laid in moist soil, 2-4 inches deep",
            "conditions": "Requires 15-35°C soil temperature, 20-40% soil moisture",
            "danger": "Foundation of population explosion"
        },
        "🦗 Hopper Stage (5-6 weeks)": {
            "description": "Wingless juveniles, 5 molting stages",
            "conditions": "Needs 22-34°C air temperature, vegetation for food",
            "danger": "Form bands, march together"
        },
        "🦗 Adult Stage (3-5 months)": {
            "description": "Fully winged, capable of long flights",
            "conditions": "Survives 20-22°C air temperature, low soil moisture",
            "danger": "Long-distance migration capability"
        },
        "🌪️ Swarm Stage": {
            "description": "Massive gregarious adult formations",
            "conditions": "Requires specific wind patterns, NDVI >0.5",
            "danger": "Most destructive phase"
        }
    }
    
    for stage, info in stages_info.items():
        with st.expander(stage):
            st.write(f"**Description:** {info['description']}")
            st.write(f"**Conditions:** {info['conditions']}")
            st.error(f"**Danger Level:** {info['danger']}")

def display_recent_events():
    """Display recent locust events and alerts"""
    st.markdown("### 📰 Recent Desert Locust Events")
    
    st.info("**Latest Updates from FAO Locust Watch:**")
    
    events = [
        {
            "date": "July 2025",
            "location": "Rajasthan, India",
            "event": "Moderate locust activity reported in Jaisalmer district",
            "status": "Monitoring"
        },
        {
            "date": "June 2025",
            "location": "Thar Desert",
            "event": "Favorable breeding conditions detected",
            "status": "Alert"
        },
        {
            "date": "May 2025",
            "location": "Pakistan Border",
            "event": "Small swarm movement towards Indian border",
            "status": "Watch"
        }
    ]
    
    for event in events:
        status_color = {"Alert": "🔴", "Watch": "🟡", "Monitoring": "🔵"}[event["status"]]
        st.write(f"{status_color} **{event['date']}** - {event['location']}")
        st.write(f"   {event['event']}")
        st.write(f"   Status: **{event['status']}**")
        st.write("---")

def display_organizations():
    """Display information about locust monitoring organizations"""
    st.markdown("### 🏛️ Locust Monitoring Organizations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **🌍 FAO Locust Watch**
        - Global desert locust monitoring
        - Real-time situation updates
        - Early warning system
        - Website: fao.org/ag/locusts
        
        **🇮🇳 Locust Warning Organization (India)**
        - Ministry of Agriculture, Government of India
        - Headquartered in Jodhpur, Rajasthan
        - Regional monitoring stations
        - Direct field operations
        """)
    
    with col2:
        st.markdown("""
        **🚁 Control Operations:**
        - Aerial spraying programs
        - Ground survey teams
        - Pesticide application
        - Farmer coordination
        
        **📊 Research & Development:**
        - Breeding ground monitoring
        - Weather pattern analysis
        - Population dynamics study
        - Bio-control research
        """)

def get_stage_parameters(stage):
    """Get the parameters for a specific stage"""
    return list(thresholds[stage].keys())

def get_parameter_defaults(param):
    """Get default values for parameters"""
    defaults = {
        "Rainfall": 25.0,
        "Soil Moisture": 30.0,
        "Soil Temperature": 25.0,
        "Air Temperature": 25.0,
        "Surface Wind Speed": 5.0,
        "Wind Speed 850hPa": 5.0,
        "Vegetation (NDVI)": 0.5,
    }
    return defaults.get(param, 0.0)

def main():
    # Header with logo
    try:
        st.image(
            "logo/LOCAST_2.png",
            width=200
        )
    except:
        # Fallback if logo not found
        st.markdown("### Logo: LOCAST")
    
    st.markdown("""
    <div class="main-header">
        <h1>LOCAST</h1>
        <p class="tagline">LOCust Activity Suitability Tracker</p>
        <p class="tagline">Predicting the Threat, Protecting the Crops</p>
        <p class="region-info">Desert Locust Status Warning System</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Alert banner
    st.markdown("""
    <div class="alert-banner">
        🚨 ACTIVE MONITORING: Desert Locust Activity in Thar Desert Region 🚨
    </div>
    """, unsafe_allow_html=True)
    
    # Information buttons
    st.markdown("### 📚 Information Center")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("About Desert Locusts", key="locust_info"):
            st.session_state.show_locust_info = True
            st.session_state.show_stage_info = False
            st.session_state.show_recent_events = False
            st.session_state.show_organizations = False
    
    with col2:
        if st.button("Locust Stages", key="stage_info"):
            st.session_state.show_locust_info = False
            st.session_state.show_stage_info = True
            st.session_state.show_recent_events = False
            st.session_state.show_organizations = False
    
    with col3:
        if st.button("Recent Events", key="recent_events"):
            st.session_state.show_locust_info = False
            st.session_state.show_stage_info = False
            st.session_state.show_recent_events = True
            st.session_state.show_organizations = False
    
    with col4:
        if st.button("Organizations", key="organizations"):
            st.session_state.show_locust_info = False
            st.session_state.show_stage_info = False
            st.session_state.show_recent_events = False
            st.session_state.show_organizations = True
    
    # Display selected information
    if st.session_state.show_locust_info:
        display_locust_info()
        if st.button("❌ Close", key="close_locust"):
            st.session_state.show_locust_info = False
    
    if st.session_state.show_stage_info:
        display_stage_info()
        if st.button("❌ Close", key="close_stage"):
            st.session_state.show_stage_info = False
    
    if st.session_state.show_recent_events:
        display_recent_events()
        if st.button("❌ Close", key="close_events"):
            st.session_state.show_recent_events = False
    
    if st.session_state.show_organizations:
        display_organizations()
        if st.button("❌ Close", key="close_orgs"):
            st.session_state.show_organizations = False
    
    st.markdown("---")
    
    # Sidebar for inputs
    st.sidebar.header("🔧 Environmental Assessment")
    
    # Stage selection
    stage = st.sidebar.selectbox(
        "Select Locust Stage:",
        ["Egg Laying", "Hopper", "Adult", "Swarm"],
        help="Choose the locust life stage for danger assessment"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Current Field Conditions")
    
    # Get stage-specific parameters
    stage_params = get_stage_parameters(stage)
    
    # Input parameters with validation - only show relevant parameters for selected stage
    inputs = {}
    
    for param in stage_params:
        if param == "Rainfall":
            inputs[param] = st.sidebar.number_input(
                f"💧 {param} (mm)",
                min_value=0.0,
                max_value=50.0,
                value=get_parameter_defaults(param),
                step=1.0,
                help="Recent rainfall measurement in millimeters"
            )
        elif param == "Soil Moisture":
            inputs[param] = st.sidebar.number_input(
                f"🌱 {param} (%)",
                min_value=0.0,
                max_value=50.0,
                value=get_parameter_defaults(param),
                step=1.0,
                help="Current soil moisture percentage"
            )
        elif param == "Soil Temperature":
            inputs[param] = st.sidebar.number_input(
                f"🌡️ {param} (°C)",
                min_value=15.0,
                max_value=50.0,
                value=get_parameter_defaults(param),
                step=0.5,
                help="Current soil temperature in Celsius"
            )
        elif param == "Air Temperature":
            inputs[param] = st.sidebar.number_input(
                f"🌡️ {param} (°C)",
                min_value=15.0,
                max_value=50.0,
                value=get_parameter_defaults(param),
                step=0.5,
                help="Current air temperature in Celsius"
            )
        elif param in ["Surface Wind Speed", "Wind Speed 850hPa"]:
            inputs[param] = st.sidebar.number_input(
                f"💨 {param} (m/s)",
                min_value=0.0,
                max_value=10.0,
                value=get_parameter_defaults(param),
                step=0.1,
                help="Current wind speed in meters per second"
            )
        elif param == "Vegetation (NDVI)":
            inputs[param] = st.sidebar.number_input(
                f"🌿 {param}",
                min_value=0.0,
                max_value=1.0,
                value=get_parameter_defaults(param),
                step=0.1,
                help="Normalized Difference Vegetation Index (0-1)"
            )
    
    # Add reference note in sidebar
    st.sidebar.markdown("""
    <div class="reference-note">
        <strong>Note:</strong> Optimal conditions as per Cressman & Stefanski. (2016). Weather and Desert Locusts. Rome: FAO, UN
    </div>
    """, unsafe_allow_html=True)
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader(f"📈 Environmental Analysis for {stage} Stage")
        
        # Display parameter bars (prioritized at the top)
        for param, value in inputs.items():
            with st.container():
                st.markdown(f"**{param}** - Current Reading")
                bar_html = create_parameter_bar(param, value, stage)
                st.markdown(bar_html, unsafe_allow_html=True)
                st.markdown("---")
        
        # Render Plotly chart (below bars)
        st.markdown("**Parameter Suitability Overview**")
        render_chart(inputs, stage)
    
    with col2:
        st.subheader("🎯 Threat Assessment")
        
        # Calculate danger level
        danger_level, emoji, css_class = calculate_suitability(inputs, stage)
        
        # Display result
        st.markdown(f"""
        <div class="result-container {css_class}">
            {emoji} {danger_level}<br>
            <span style="font-size: 1.0rem;">for {stage} Stage</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Show detailed breakdown
        st.subheader("📊 Parameter Analysis")
        
        optimal_params = []
        safe_params = []
        
        for param, value in inputs.items():
            min_thresh, max_thresh = thresholds[stage][param]
            if min_thresh <= value <= max_thresh:
                optimal_params.append(param)
            else:
                safe_params.append(param)
        
        if optimal_params:
            st.error(f"🔴 **Optimal Parameters ({len(optimal_params)}):**")
            for param in optimal_params:
                st.write(f"• {param}")
        
        if safe_params:
            st.success(f"🟢 **Safe Parameters ({len(safe_params)}):**")
            for param in safe_params:
                value = inputs[param]
                min_thresh, max_thresh = thresholds[stage][param]
                st.write(f"• {param}: {value:.1f} {param_units[param]} (outside {min_thresh}-{max_thresh if max_thresh != float('inf') else '∞'})")
        
        # Overall threat score
        threat_score = len(optimal_params) / len(inputs) * 100
        st.metric("Threat Level", f"{threat_score:.0f}%")
        
        # Recommendation
        if threat_score >= 80:
            st.error("🚨 **HIGH ALERT:** Immediate monitoring required!")
        elif threat_score >= 50:
            st.warning("⚠️ **MODERATE RISK:** Increased surveillance needed")
        else:
            st.success("✅ **LOW RISK:** Continue routine monitoring")
    
    # Footer with stage information
    st.markdown("---")
    st.subheader("📚 Stage-Specific Information")
    
    stage_info = {
        "Egg Laying": "🥚 Egg Laying stage creates foundation for population explosion. Moist soil and moderate temperatures are ideal breeding conditions.",
        "Hopper": "🦗 Hopper stage forms marching bands. Adequate vegetation and warm temperatures support rapid development.",
        "Adult": "🦗 Adult locusts are highly mobile. Specific wind and temperature conditions favor long-distance migration.",
        "Swarm": "🌪️ Swarm formation is most destructive. High NDVI and specific wind patterns trigger mass movement."
    }
    
    st.warning(f"**{stage} Stage Alert:** {stage_info[stage]}")
    
    # Technical notes
    with st.expander("ℹ️ Technical Information"):
        st.markdown("""
        **Monitoring Parameters:**
        - **Rainfall**: Critical for egg survival and vegetation growth
        - **Soil Moisture**: Essential for egg development and hatching
        - **Soil Temperature**: Affects egg and hopper development
        - **Air Temperature**: Influences development speed and survival rates
        - **Surface Wind Speed/Wind Speed 850hPa**: Influences migration and swarm movement
        - **Vegetation (NDVI)**: Indicates food availability for swarms
        
        **Threat Assessment:**
        - **HIGH DANGER**: 80%+ parameters in locust-favorable range
        - **MODERATE DANGER**: 50-79% parameters in locust-favorable range
        - **SAFE CONDITIONS**: <50% parameters in locust-favorable range
        
        **Color Coding:**
        - 🔴 Red Zone: Conditions suitable for locust development (DANGEROUS)
        - 🟢 Green Zone: Conditions unsuitable for locusts (SAFE)
        
        **Source:** Cressman & Stefanski (2016). Weather and Desert Locusts. Rome: FAO, UN
        """)

if __name__ == "__main__":
    main()