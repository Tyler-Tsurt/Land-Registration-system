"""
generate_training_data.py

Generate realistic land registration training data for Ndola, Zambia.
Creates 2000+ samples with realistic names, locations, and conflicts.
"""
import random
import csv
from datetime import datetime, timedelta
from typing import List, Dict

# Zambian names database
FIRST_NAMES_MALE = [
    'Moses', 'Joseph', 'Brian', 'Patrick', 'Simon', 'Michael', 'Peter', 'Victor', 'David', 'George',
    'Samuel', 'James', 'Nelson', 'Chileshe', 'Mukuka', 'Chibwe', 'Nchimunya', 'Chanda', 'Mulenga'
]

FIRST_NAMES_FEMALE = [
    'Grace', 'Memory', 'Patricia', 'Alice', 'Esther', 'Mercy', 'Linda', 'Angela', 'Ruth', 'Rose',
    'Faith', 'Beatrice', 'Mary', 'Chipo', 'Thandiwe', 'Mutale', 'Mwansa'
]

LAST_NAMES = [
    'Mwanza', 'Phiri', 'Banda', 'Lungu', 'Tembo', 'Zulu', 'Chola', 'Mulenga', 'Sichone', 'Ndalama',
    'Kapasa', 'Chanda', 'Mumba', 'Kaluba', 'Mulilo', 'Mwape', 'Sitali', 'Kaunda'
]

# Company suffixes
COMPANY_TYPES = ['Ltd', 'Co', 'PLC', 'Enterprises', 'Group', 'Holdings', 'Resources', 'Industrial']

COMPANY_PREFIXES = [
    'Ndola Estate', 'Kansenshi Traders', 'Lubuto Cooperative', 'UrbanDevelopers', 'ZamBuild',
    'Copperbelt Logistics', 'Central Agro', 'PanAfrican Cement', 'GreenFields', 'Ndola Minerals'
]

# Ndola locations
LOCATIONS = [
    'Northrise', 'Kansenshi', 'Chipulukusu', 'Kabushi', 'Masala', 'Twapia', 'Chifubu', 'Lubuto',
    'Mushili', 'Itawa', 'Mapalo', 'Industrial Area', 'Town Centre', 'Ndeke', 'Garden',
    'Railway Line', 'Kitwe Road', 'Chililabombwe Road'
]

# Land uses
LAND_USES = ['Residential', 'Commercial', 'Industrial', 'Agricultural', 'Mixed Use']

# Title deed statuses
TENURES = ['Freehold', 'Leasehold (99 yrs)', 'Leasehold (65 yrs)', 'Leasehold (50 yrs)', 'State Land']

# Encumbrances
ENCUMBRANCES = [
    'None', 'Mortgaged', 'Caveat', 'Auctioned', 'Boundary_Dispute', 'Double_Allocation'
]

# Ground rent status
RENT_STATUS = ['Paid', 'Arrears']

def generate_nrc() -> str:
    """Generate realistic Zambian NRC number."""
    number = random.randint(100000, 999999)
    district = random.randint(10, 50)
    check = random.randint(1, 9)
    return f"{number}/{district:02d}/{check}"

def generate_tpin() -> str:
    """Generate realistic TPIN (10 digits)."""
    return f"{random.randint(100000000, 999999999):010d}"

def generate_phone() -> str:
    """Generate realistic Zambian phone number."""
    prefixes = ['095', '096', '097', '076', '077']
    prefix = random.choice(prefixes)
    number = random.randint(1000000, 9999999)
    return f"0{prefix[1:]}{number:07d}"

def generate_email(name: str) -> str:
    """Generate email address based on name."""
    name_clean = name.lower().replace(' ', '.')
    domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'company.co.zm']
    return f"{name_clean}{random.randint(1, 99)}@{random.choice(domains)}"

def generate_coordinates() -> str:
    """Generate GPS coordinates within Ndola bounds."""
    # Ndola: Lat -12.96 to -13.00, Lon 28.62 to 28.67
    lat = random.uniform(-12.998, -12.960)
    lon = random.uniform(28.620, 28.675)
    return f"{lat:.6f},{lon:.6f}"

def generate_plot_number(index: int) -> str:
    """Generate plot number."""
    return f"NDL-{index:04d}"

def generate_title_deed(year: int, index: int) -> str:
    """Generate title deed reference."""
    return f"TDR-{year}-{index:04d}"

def generate_person_name() -> str:
    """Generate a person's full name."""
    if random.random() < 0.7:  # 70% male, 30% female
        first = random.choice(FIRST_NAMES_MALE)
    else:
        first = random.choice(FIRST_NAMES_FEMALE)
    last = random.choice(LAST_NAMES)
    return f"{first} {last}"

def generate_company_name() -> str:
    """Generate a company name."""
    prefix = random.choice(COMPANY_PREFIXES)
    suffix = random.choice(COMPANY_TYPES)
    return f"{prefix} {suffix}"

def generate_owner_name(index: int) -> str:
    """Generate owner name (person or company)."""
    # 20% companies, 80% individuals
    if random.random() < 0.2:
        return generate_company_name()
    else:
        return generate_person_name()

def generate_land_size(land_use: str) -> int:
    """Generate appropriate land size based on use."""
    if land_use == 'Residential':
        return random.choice([200, 250, 300, 350, 400, 450, 500, 600, 700, 800, 1000])
    elif land_use == 'Commercial':
        return random.choice([250, 300, 400, 500, 800, 1000, 1200, 1500])
    elif land_use == 'Industrial':
        return random.choice([2000, 3000, 5000, 8000, 10000, 20000])
    elif land_use == 'Agricultural':
        return random.choice([1500, 2000, 3000, 5000, 8000, 10000, 20000])
    else:  # Mixed Use
        return random.randint(300, 2000)

def generate_date(start_year: int = 2005, end_year: int = 2024) -> str:
    """Generate random date."""
    start_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31)
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    date = start_date + timedelta(days=random_days)
    return date.strftime('%Y-%m-%d')

def introduce_duplicates(records: List[Dict], duplicate_rate: float = 0.05) -> List[Dict]:
    """
    Introduce intentional duplicates for training the AI.
    About 5% of records will have duplicates.
    """
    num_duplicates = int(len(records) * duplicate_rate)
    
    for _ in range(num_duplicates):
        # Pick a random record to duplicate
        original_idx = random.randint(0, len(records) - 1)
        original = records[original_idx]
        
        # Create a duplicate with slight variations
        duplicate = original.copy()
        duplicate['Plot_Number'] = f"NDL-{len(records):04d}"
        
        # Decide what type of duplicate
        dup_type = random.choice(['same_person', 'same_location', 'typo'])
        
        if dup_type == 'same_person':
            # Same NRC/TPIN, different location
            duplicate['Location'] = random.choice(LOCATIONS)
            duplicate['GPS_Coordinates'] = generate_coordinates()
        
        elif dup_type == 'same_location':
            # Different person, same location (boundary conflict)
            duplicate['Owner_Name'] = generate_owner_name(len(records))
            duplicate['NRC_Number'] = generate_nrc()
            duplicate['Encumbrances'] = 'Double_Allocation'
        
        else:  # typo
            # Same person with typo in name
            name_parts = original['Owner_Name'].split()
            if len(name_parts) >= 2:
                # Introduce typo
                name_parts[0] = name_parts[0][:-1] + random.choice('abcdefgh')
                duplicate['Owner_Name'] = ' '.join(name_parts)
        
        records.append(duplicate)
    
    return records

def generate_land_records(num_records: int = 2000) -> List[Dict]:
    """Generate realistic land registration records."""
    records = []
    
    print(f"Generating {num_records} land records...")
    
    for i in range(1, num_records + 1):
        if i % 100 == 0:
            print(f"  Generated {i}/{num_records} records...")
        
        land_use = random.choice(LAND_USES)
        owner_name = generate_owner_name(i)
        
        record = {
            'Plot_Number': generate_plot_number(i),
            'Owner_Name': owner_name,
            'NRC_Number': generate_nrc(),
            'Location': random.choice(LOCATIONS),
            'Plot_Size_sq_m': generate_land_size(land_use),
            'Land_Use': land_use,
            'Title_Deed': generate_title_deed(random.randint(2005, 2024), random.randint(1000, 9999)),
            'Tenure': random.choice(TENURES),
            'Registration_Date': generate_date(),
            'Encumbrances': random.choice(ENCUMBRANCES) if random.random() < 0.15 else 'None',
            'GPS_Coordinates': generate_coordinates(),
            'Ground_Rent_Status': random.choice(RENT_STATUS) if random.random() < 0.2 else 'Paid'
        }
        
        records.append(record)
    
    print("Introducing intentional duplicates for AI training...")
    records = introduce_duplicates(records, duplicate_rate=0.05)
    
    print(f"Total records including duplicates: {len(records)}")
    return records

def save_to_csv(records: List[Dict], filename: str):
    """Save records to CSV file."""
    if not records:
        print("No records to save!")
        return
    
    fieldnames = records[0].keys()
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    
    print(f"✅ Saved {len(records)} records to {filename}")

def generate_applicant_data(num_applicants: int = 500) -> List[Dict]:
    """Generate applicant/citizen data for testing."""
    applicants = []
    
    print(f"Generating {num_applicants} applicant records...")
    
    for i in range(1, num_applicants + 1):
        if i % 50 == 0:
            print(f"  Generated {i}/{num_applicants} applicants...")
        
        first_name = random.choice(FIRST_NAMES_MALE + FIRST_NAMES_FEMALE)
        last_name = random.choice(LAST_NAMES)
        full_name = f"{first_name} {last_name}"
        
        applicant = {
            'Applicant_ID': f"APP-{i:04d}",
            'Full_Name': full_name,
            'NRC_Number': generate_nrc(),
            'TPIN_Number': generate_tpin(),
            'Phone_Number': generate_phone(),
            'Email': generate_email(full_name),
            'Address': f"{random.randint(1, 999)} {random.choice(LOCATIONS)} Street, Ndola",
            'Registration_Date': generate_date(2020, 2024)
        }
        
        applicants.append(applicant)
    
    return applicants

if __name__ == '__main__':
    # Generate main land records dataset
    land_records = generate_land_records(2000)
    save_to_csv(land_records, 'collected data/ndola_land_extended.csv')
    
    # Generate applicant data
    applicant_records = generate_applicant_data(500)
    save_to_csv(applicant_records, 'collected data/applicants_data.csv')
    
    print("\n" + "="*60)
    print("✅ TRAINING DATA GENERATION COMPLETE!")
    print("="*60)
    print(f"📊 Land Records: {len(land_records)} entries")
    print(f"👥 Applicant Records: {len(applicant_records)} entries")
    print(f"📁 Files saved in 'collected data/' directory")
    print("\n🔍 Dataset includes:")
    print("  • Realistic Zambian names and locations")
    print("  • Valid NRC, TPIN, phone formats")
    print("  • Intentional duplicates (~5%) for AI training")
    print("  • Various land uses and tenures")
    print("  • Conflict scenarios (double allocation, disputes)")
