import pandas as pd
import random
import joblib
import streamlit as st
from faker import Faker
import plotly.express as px
import xgboost as xgb
from datetime import datetime, timedelta
import math

# Initialize Faker
fake = Faker()

# Load the compressed model
try:
    compressed_model_path = 'xgboost_model_compressed.pkl'
    model = joblib.load(compressed_model_path)
    st.sidebar.success("Model loaded successfully.")
except Exception as e:
    model = None
    st.sidebar.error(f"Model could not be loaded: {e}")

# Function to generate synthetic patient data
def generate_patient_data(num_patients, day):
    data = {
        "Ordered Ultrasound (Y/N)": [random.choice([0, 1]) for _ in range(num_patients)],  # 0 for Not Ordered, 1 for Ordered
        "Priority Code": [random.choice(["High", "Medium", "Low"]) for _ in range(num_patients)],
        "Ultrasound Type": [random.choice(["Type1", "Type2", "Not Ordered"]) for _ in range(num_patients)],
        "Attending Physician": [fake.name() for _ in range(num_patients)],
        "Age": [random.randint(0, 18) for _ in range(num_patients)],  # Age binned to 0-18 years
        "Is_AM": [random.choice([0, 1]) for _ in range(num_patients)],
        "Is_PM": [random.choice([0, 1]) for _ in range(num_patients)],
        "Is_Business_Hour": [random.choice([0, 1]) for _ in range(num_patients)],
        "Is_AM_Business_Hours": [random.choice([0, 1]) for _ in range(num_patients)],
        "Is_PM_Business_Hours": [random.choice([0, 1]) for _ in range(num_patients)],
        "Day_of_Week": [random.choice(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]) for _ in range(num_patients)],
        "Is_Weekend": [random.choice([0, 1]) for _ in range(num_patients)],
        "Time_Between_Arrivals": [random.randint(1, 24) for _ in range(num_patients)],  # Random hours between arrivals
    }
    df = pd.DataFrame(data)
    df['Day'] = day  # Add a 'Day' column to track the day of data generation
    return df

# Preprocess the input data to match the model's expected format
def preprocess_user_input(df):
    # Apply binning technique for age groups (patients aged 0-18 only)
    bins = [0, 1, 5, 12, 18]  # Adjusted to your new bins for 0-18 years only
    labels = ['Infant', 'Toddler', 'Child', 'Teen']
    df['Age Group'] = pd.cut(df['Age'], bins=bins, labels=labels, right=False)

    # Convert 'Day_of_Week' to a categorical column (numeric codes)
    df['Day_of_Week'] = df['Day_of_Week'].astype('category').cat.codes

    # Dummify 'Priority Code', 'Ultrasound Type', 'Attending Physician', 'Age Group' columns
    df = pd.get_dummies(df, columns=['Priority Code', 'Ultrasound Type', 'Attending Physician', 'Age Group'], dummy_na=True)

    # Ensure the order of columns matches the model's feature set
    missing_columns = [col for col in model.feature_names_in_ if col not in df.columns]
    for col in missing_columns:
        df[col] = 0  # Add missing columns with 0 values

    # Ensure the order of columns matches the model
    df = df[model.feature_names_in_]

    return df

# Streamlit app interface with centered text and button
st.markdown("""
    <div style="text-align: center;">
        <h1>Ultrasound Forecasting Model 🔮 (ULTFORM 🔮)</h1>
        <p>ULTFORM is a predictive tool designed to estimate the percentage of Emergency Department (ED) patients who will require ultrasounds. It also helps identify when the number of patients in the ED will approach the Ultrasound Department’s maximum capacity, ensuring optimal service planning.</p>
    </div>
""", unsafe_allow_html=True)

# Center the button using columns
left_col, center_col, right_col = st.columns([1, 2, 1])

with center_col:
    pull_data = st.button(
        "Pull Data From Electronic Medical Record",
        key="pull_data_btn",
        help="Generate synthetic patient data for a random month in 2025"
    )

# Button action
if pull_data:
    # Generate a random start month in 2025
    random_month = random.randint(1, 12)  # Random month from 1 to 12
    start_date = datetime(2025, random_month, 1)
    
    # Get the number of days in the selected month
    next_month = start_date.replace(day=28) + timedelta(days=4) 
    num_days = (next_month - timedelta(days=next_month.day)).day

    conversion_rates = []  # Store the conversion rates for each day
    projected_patients = []  # store the projected number of patients for each day
    max_capacity_patients = []  # Sotre the number of patients approaching or exceeding max capacity
    for day in range(1, num_days + 1):  # Loop for the random month
        num_patients = random.randint(40, 200)  # Random number of patients per day
        patient_data = generate_patient_data(num_patients, day)
        
        # Preprocess the patient data
        patient_data_preprocessed = preprocess_user_input(patient_data)

        # Use the pre-trained pipeline to predict based on patient data
        predictions = model.predict(patient_data_preprocessed)

        # Calculate conversion rate (percentage of patients who ordered ultrasound)
        conversion_rate = (predictions.mean())  
        conversion_rates.append(round(conversion_rate, 2))  

        # Calculate the projected number of patients for the ED
        projected_patients.append(num_patients)

        # Calculate the number of patients approaching or exceeding ultrasound capacity
        max_capacity_patients.append(math.ceil(num_patients * conversion_rate / 100))

    # Generate fake dates in the selected month
    dates = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(num_days)]

    # Create DataFrame with conversion rates, projected patients, and max capacity patients
    conversion_df = pd.DataFrame({
        'Date': dates,
        'Ultrasound Conversion Rate (%)': conversion_rates,
        'Projected Number of Patients to Visit ED': projected_patients,
        'Threshold for Max US Capacity': max_capacity_patients 
    })

    # Plot the max capacity patients first
    fig = px.line(conversion_df, x='Date', y='Threshold for Max US Capacity', title=f"Number of ED Patients Signaling Ultrasound Max Capacity for the Next {num_days} Days in {start_date.strftime('%B')}")

    # Update hover info to reflect the new focus
    fig.update_traces(
        hovertemplate=(
            'Projected Number of Patients: %{customdata[0]}<br>' +
            'When the ED reaches %{customdata[1]} patients, ultrasound capacity will be at or near maximum.' +
            '<extra></extra>'
        ),
        customdata=[[
            row['Projected Number of Patients to Visit ED'],  # Total projected patients
            math.ceil(row['Projected Number of Patients to Visit ED'] * row['Ultrasound Conversion Rate (%)'] / 100)  # Patients approaching max capacity
        ] for _, row in conversion_df.iterrows()]
    )

    # Update axis label
    fig.update_layout(
        yaxis_title="# of ED Patients Approaching Ultrasound Capacity"
    )

    # Show the plot
    st.plotly_chart(fig)

    # Center the display of the table
    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    st.write(f"Estimated Ultrasound Conversion Rates and Projected Number of Patients to Visit ED for the Next {num_days} Days in {start_date.strftime('%B')}:")
    st.write(conversion_df[['Date', 'Ultrasound Conversion Rate (%)', 'Projected Number of Patients to Visit ED', 'Threshold for Max US Capacity']])
    st.markdown("</div>", unsafe_allow_html=True)