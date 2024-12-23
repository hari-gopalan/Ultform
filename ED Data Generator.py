import pandas as pd
import random
from faker import Faker
from datetime import datetime, timedelta

fake = Faker()

# Generate synthetic data
def generate_synthetic_data(num_days=1):
    data = []
    doctors = [fake.name() + " MD" for _ in range(20)]
    high_order_doctors = random.sample(doctors, 5)
    low_order_doctors = random.sample([doc for doc in doctors if doc not in high_order_doctors], 5)
    
    # Define doctor schedules
    doctor_schedules = {doc: [] for doc in doctors}
    for doc in doctors:
        num_shifts = random.randint(2, 5)
        shifts = random.sample(range(7), num_shifts)
        doctor_schedules[doc] = shifts

    # Keep one doctor's schedule the same (2 shifts per week)
    fixed_doc = doctors[0]
    doctor_schedules[fixed_doc] = [0, 3]

    ultrasound_types = [
        'US Scrotal', 
        'US Abdomen', 
        'US Thyroid', 
        'US Pelvic', 
        'US Abdomen Pelvis',
        'US Upper Extremity Doppler',
        'US Lower Extremity Doppler'
    ]

    chief_complaints = {
        'US Scrotal': [
            'Sudden onset of pain in left testicle',
            'Swelling in right testicle',
            'Testicular torsion',
            'Trauma to scrotum',
            'Persistent testicular pain',
            'Lump in scrotum',
            'Redness and swelling in scrotum',
            'Painful urination with testicular pain'
        ],
        'US Abdomen': [
            'Abdominal pain',
            'Vomiting',
            'Suspected appendicitis',
            'Bloating and discomfort',
            'Persistent nausea',
            'Unexplained weight loss',
            'Jaundice',
            'Abdominal trauma',
            'Blood in stool',
            'Severe constipation'
        ],
        'US Thyroid': [
            'Fast growing lump on the neck with a fever',
            'Swelling in neck',
            'Difficulty swallowing',
            'Hoarseness of voice',
            'Pain in neck',
            'Enlarged thyroid gland',
            'Unexplained weight changes',
            'Persistent cough'
        ],
        'US Pelvic': [
            'Pelvic pain',
            'Ovarian torsion',
            'Irregular menstrual cycles',
            'Heavy menstrual bleeding',
            'Lower abdominal pain',
            'Suspected ovarian cyst',
            'Pain during intercourse',
            'Unexplained pelvic mass'
        ],
        'US Abdomen Pelvis': [
            'Abdominal and pelvic pain',
            'Lower abdominal pain with fever',
            'Suspected kidney stones',
            'Persistent lower back pain',
            'Blood in urine',
            'Unexplained pelvic mass',
            'Painful urination with abdominal pain'
        ],
        'US Upper Extremity Doppler': [
            'Swelling in arm with pain',
            'Suspected DVT in upper extremity',
            'Redness and warmth in arm',
            'Pain in arm after trauma'
        ],
        'US Lower Extremity Doppler': [
            'Swelling in leg with pain',
            'Suspected DVT in lower extremity',
            'Redness and warmth in leg',
            'Pain in leg after trauma'
        ]
    }
    start_date = datetime.now() - timedelta(days=num_days)
    end_date = datetime.now()

    current_date = start_date
    annual_growth_rate = random.uniform(0.01, 0.05)
    initial_ultrasound_rate = random.uniform(4, 15)
    initial_patient_rate = random.randint(60, 120)

    while current_date <= end_date:
        # Calculate the patient rate for the current year
        years_passed = (current_date - start_date).days // 365
        current_patient_rate = initial_patient_rate * ((1 + annual_growth_rate) ** years_passed)

        # Determine the number of patients based on season
        if current_date.month in [9, 10, 11, 12, 1, 2, 3]:
            num_patients = int(current_patient_rate * random.uniform(0.8, 1.3))  # Higher volumes during viral season
        else:
            num_patients = int(current_patient_rate * random.uniform(0.6, 1.0))  # Lower volumes during summer

        # Adjust volumes based on day of the week
        if current_date.weekday() in [5, 6]:  # Weekends
            num_patients = int(num_patients * 0.8)
        elif current_date.weekday() == 0:  # Mondays
            num_patients = int(num_patients * 1.2)

        # Select doctors for the day
        day_of_week = current_date.weekday()
        working_doctors = [doc for doc in doctors if day_of_week in doctor_schedules[doc]]
        
        if len(working_doctors) < 4:
            additional_docs_needed = 4 - len(working_doctors)
            additional_docs = random.sample([doc for doc in doctors if doc not in working_doctors], additional_docs_needed)
            working_doctors.extend(additional_docs)

        morning_shift_docs = working_doctors[:2]
        evening_shift_docs = working_doctors[2:]

        for _ in range(num_patients):
            mrn = fake.unique.random_number(digits=8)
            name = fake.name()
            age_years = random.randint(0, 17)
            if age_years < 1:
                age_months = random.randint(0, 11)
                if age_months < 1:
                    age_weeks = random.randint(0, 11)
                    if age_weeks < 1:
                        age_days = random.randint(0, 6)
                        age = f"{age_days} days"
                    else:
                        age = f"{age_weeks} weeks"
                else:
                    age = f"{age_months} months"
            else:
                age = f"{age_years} years"

            # Generate arrival time with dual peak curve around 10 am and 4 pm
            if random.random() < 0.5:
                arrival_time = (datetime.combine(current_date, datetime.min.time()) + timedelta(hours=10) + timedelta(minutes=random.randint(-60, 60))).time()
            else:
                arrival_time = (datetime.combine(current_date, datetime.min.time()) + timedelta(hours=16) + timedelta(minutes=random.randint(-60, 60))).time()
            
            # Ensure less patients arrive after 19:00h (1-2 per hour)
            if arrival_time.hour >= 19:
                arrival_time = (datetime.combine(current_date, datetime.min.time()) + timedelta(hours=random.randint(19, 23)) + timedelta(minutes=random.randint(0, 59))).time()

            arrival_date = current_date.strftime('%Y-%m-%d')
            initial_assessment_time = (datetime.combine(current_date, arrival_time) + timedelta(hours=random.randint(1, 10))).time()
            
            # Calculate the ultrasound rate for the current year
            current_ultrasound_rate = initial_ultrasound_rate * ((1 + annual_growth_rate) ** years_passed)
            
            ordered_ultrasound = random.choices(['Y', 'N'], weights=[current_ultrasound_rate, 100 - current_ultrasound_rate])[0]
            ultrasound_type = random.choice(ultrasound_types) if ordered_ultrasound == 'Y' else ''
            chief_complaint = random.choice(chief_complaints[ultrasound_type]) if ordered_ultrasound == 'Y' else random.choice(['Fever', 'Injury', 'Headache'])
            
            # Make 90% of the ultrasounds P1 or P2
            priority_code_weights = [45, 45, 5, 5] if ordered_ultrasound == 'Y' else [0, 0, 0, 100]
            priority_code = random.choices(['P1', 'P2', 'P3', 'P4'], weights=priority_code_weights)[0]
            
            # Change the definition of P2 to within 12 hours, P3 to within 24 hours, P4 to within 7 days, and P4+ to within 30 days
            if priority_code == 'P1':
                ultrasound_order_time = (datetime.combine(current_date, initial_assessment_time) + timedelta(hours=random.randint(1, 2))).time()
            elif priority_code == 'P2':
                ultrasound_order_time = (datetime.combine(current_date, initial_assessment_time) + timedelta(hours=random.randint(3, 12))).time()
            elif priority_code == 'P3':
                ultrasound_order_time = (datetime.combine(current_date, initial_assessment_time) + timedelta(hours=random.randint(13, 24))).time()
            elif priority_code == 'P4':
                ultrasound_order_time = (datetime.combine(current_date, initial_assessment_time) + timedelta(days=random.randint(1, 7))).time()
            
            ultrasound_order_date = arrival_date if ordered_ultrasound == 'Y' else ''
            ordering_physician = random.choices(doctors, weights=[2 if doc in high_order_doctors else 1 for doc in doctors])[0]

            data.append([mrn, name, age, arrival_time.strftime('%H:%M:%S'), arrival_date, initial_assessment_time.strftime('%H:%M:%S'), chief_complaint,
                         ordered_ultrasound, ultrasound_type, priority_code, ultrasound_order_time.strftime('%H:%M:%S') if ordered_ultrasound == 'Y' else '',
                         ultrasound_order_date, ordering_physician])

        current_date += timedelta(days=1)

    columns = ['MRN', 'Patient Name', 'Age', 'ED Arrival Time', 'ED Arrival Date', 'ED Patient Initial Assessment Time',
               'Chief Complaint', 'Ordered Ultrasound (Y/N)', 'Ultrasound Type', 'Priority Code',
               'Time Ultrasound Ordered', 'Date Ultrasound Ordered', 'Ordering Physician']
    
    df = pd.DataFrame(data, columns=columns)
    return df

# Generate data for seven years and save to CSV
df_synthetic_data_1_day = generate_synthetic_data(num_days=1)
df_synthetic_data_1_day.to_csv('synthetic_ed_data_1_day.csv', index=False)
print("Synthetic ED data for 1 day has been generated and saved to synthetic_ed_data_1_day.csv")
