"""
Seed Users Script

Creates all 100+ employees from the provided employee data with correct role mappings.
Run this script to populate the database with initial user data.

Usage:
    python scripts/seed_users.py

Note: Sarjak Patel (Consultant) is given HEAD role to be at par with Khilav Joshi (Head of Strategy)
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add backend to sys.path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from app.core.database import db
from app.core.security import get_password_hash
from app.models.domain.user import User, UserRole


# Role mapping based on job title
def get_role_from_title(title: str, name: str = "") -> UserRole:
    """Map job title to UserRole enum."""
    title_lower = title.lower()
    name_lower = name.lower()
    
    # Special case: Sarjak Patel should be HEAD level (per user request)
    if "sarjak" in name_lower:
        return UserRole.HEAD
    
    # Director level
    if any(x in title_lower for x in ["founder", "ceo", "director", "partner"]):
        return UserRole.DIRECTOR
    
    # Head level
    if any(x in title_lower for x in ["head", "gm "]):
        return UserRole.HEAD
    
    # Lead level
    if any(x in title_lower for x in ["lead", "manager"]):
        return UserRole.LEAD
    
    # Analyst/Senior level
    if any(x in title_lower for x in ["sr ", "sr.", "senior", "consultant", "engineer", "specialist", "scientist", "analyst", "expert"]):
        return UserRole.ANALYST
    
    # Default to trainee
    return UserRole.TRAINEE


# All employee data from the provided list
EMPLOYEES = [
    {"employee_number": "1644", "name": "Aarchi Thakker", "job_title": "Sr Consultant - Digital Analytics", "department": "Customer Delivery - Data Analysis & Insights", "location": "Ahmedabad", "email": "aarchi@tatvic.com"},
    {"employee_number": "IN201", "name": "Aarya Samaiya", "job_title": "Technical Trainee", "department": "Customer Delivery - Data Collection", "location": "Ahmedabad", "email": "aarya@tatvic.com"},
    {"employee_number": "1603", "name": "Abhishek Shah", "job_title": "AI Project Lead", "department": "Strategy", "location": "Ahmedabad", "email": "abhishek.shah@tatvic.com"},
    {"employee_number": "1664", "name": "Abhishek Singh", "job_title": "Marketing Executive", "department": "Marketing", "location": "Ahmedabad", "email": "abhishek.s@tatvic.com"},
    {"employee_number": "1659", "name": "Adityavardhan Jain", "job_title": "Digital Analyst", "department": "Customer Delivery - Data Analysis & Insights", "location": "Ahmedabad", "email": "adityavardhan@tatvic.com"},
    {"employee_number": "1389", "name": "Akash Pandya", "job_title": "Digital Analyst", "department": "Customer Delivery - Data Analysis & Insights", "location": "Ahmedabad", "email": "akashpandya@tatvic.com"},
    {"employee_number": "1663", "name": "Anamika Gupta", "job_title": "Technical Analyst", "department": "Customer Delivery - Data Collection", "location": "Ahmedabad", "email": "anamika@tatvic.com"},
    {"employee_number": "IN210", "name": "Anjali Thacker", "job_title": "Technical Trainee", "department": "Customer Delivery - Data Engineering", "location": "Ahmedabad", "email": "anjali.t@tatvic.com"},
    {"employee_number": "1640", "name": "Ankita Singh", "job_title": "Marketing Manager", "department": "Marketing", "location": "Ahmedabad", "email": "ankita@tatvic.com"},
    {"employee_number": "IN207", "name": "Aryan Singh", "job_title": "Technical Trainee", "department": "Customer Delivery - Data Engineering", "location": "Ahmedabad", "email": "aryan@tatvic.com"},
    {"employee_number": "IN200", "name": "Ashwin Soni", "job_title": "Technical Trainee", "department": "Customer Delivery - Data Collection", "location": "Ahmedabad", "email": "ashwin@tatvic.com"},
    {"employee_number": "1652", "name": "Ayush Shukla", "job_title": "Marketing Lead", "department": "Marketing", "location": "Ahmedabad", "email": "ayush.shukla@tatvic.com"},
    {"employee_number": "1634", "name": "Bansal Kyada", "job_title": "Assistant Admin Manager", "department": "IT & Admin", "location": "Ahmedabad", "email": "bansal@tatvic.com"},
    {"employee_number": "1641", "name": "Bhavi Parikh", "job_title": "Marketing Manager", "department": "Marketing", "location": "Ahmedabad", "email": "bhavi.p@tatvic.com"},
    {"employee_number": "1167", "name": "Bhumita Sarabhai", "job_title": "Media Lead", "department": "Customer Delivery - Campaign Management", "location": "Ahmedabad", "email": "bhumita@tatvic.com"},
    {"employee_number": "1398", "name": "Chandni Sedani", "job_title": "Business Finance", "department": "Accounts & Finance", "location": "Ahmedabad", "email": "chandni@tatvic.com"},
    {"employee_number": "Vistior_63", "name": "Chilin Tang", "job_title": "Google Analytics Expert", "department": "APAC - Market", "location": "Singapore", "email": "chilin@tatvic.com"},
    {"employee_number": "1394", "name": "Devang Pathak", "job_title": "Admin Manager", "department": "IT & Admin", "location": "Ahmedabad", "email": "devang@tatvic.com"},
    {"employee_number": "IN208", "name": "Dhananjay Kanjariya", "job_title": "Technical Trainee", "department": "Customer Delivery - Data Engineering", "location": "Ahmedabad", "email": "dhananjay@tatvic.com"},
    {"employee_number": "1205", "name": "Dharmik Raval", "job_title": "Software Development Engineer - Level 2", "department": "Strategy", "location": "Ahmedabad", "email": "dharmik@tatvic.com"},
    {"employee_number": "1357", "name": "Dhrupad Pandya", "job_title": "CRO Specialist", "department": "Customer Delivery - CRO", "location": "Ahmedabad", "email": "dhrupad@tatvic.com"},
    {"employee_number": "1661", "name": "Dhruvesh Panchal", "job_title": "Technical Analyst", "department": "Customer Delivery - Data Collection", "location": "Ahmedabad", "email": "dhruvesh@tatvic.com"},
    {"employee_number": "1629", "name": "Dhruvi Parekh", "job_title": "Technical Analyst", "department": "Customer Delivery - Data Collection", "location": "Ahmedabad", "email": "dhruvi.p@tatvic.com"},
    {"employee_number": "1665", "name": "Dhruvin Shah", "job_title": "Digital Analyst", "department": "Customer Delivery - Data Analysis & Insights", "location": "Ahmedabad", "email": "dhruvin@tatvic.com"},
    {"employee_number": "1523", "name": "Dipak Patel", "job_title": "Admin Executive", "department": "IT & Admin", "location": "Ahmedabad", "email": "dp9394509@gmail.com"},
    {"employee_number": "1457", "name": "Disha Vachhani", "job_title": "Inside sales manager", "department": "Marketing", "location": "Ahmedabad", "email": "disha@tatvic.com"},
    {"employee_number": "IN187", "name": "Divya Gupta", "job_title": "Technical Trainee", "department": "Customer Delivery - Data Analysis & Insights", "location": "Ahmedabad", "email": "divya.gupta@tatvic.com"},
    {"employee_number": "1320", "name": "Ekta Joshi", "job_title": "Sr Technical Analyst QA", "department": "Customer Delivery - Data Collection", "location": "Ahmedabad", "email": "ekta@tatvic.com"},
    {"employee_number": "1260", "name": "Gaurav Shukla", "job_title": "Account Management Lead - North Region", "department": "Account Management", "location": "Ahmedabad", "email": "gaurav.shukla@tatvic.com"},
    {"employee_number": "1511", "name": "Harsh Panchal", "job_title": "Consultant Digital Analyst", "department": "Customer Delivery - Data Analysis & Insights", "location": "Ahmedabad", "email": "harsh.panchal@tatvic.com"},
    {"employee_number": "IN188", "name": "Het Patel", "job_title": "Technical Trainee", "department": "Customer Delivery - Data Analysis & Insights", "location": "Ahmedabad", "email": "het.patel@tatvic.com"},
    {"employee_number": "IN193", "name": "Jainil Patel", "job_title": "Technical Trainee", "department": "Strategy", "location": "Ahmedabad", "email": "jainil@tatvic.com"},
    {"employee_number": "IN185", "name": "Jash Sanghvi", "job_title": "Technical Trainee", "department": "Customer Delivery - Data Analysis & Insights", "location": "Ahmedabad", "email": "jash@tatvic.com"},
    {"employee_number": "1459", "name": "Jeet Shah", "job_title": "Lead - Data Engineering", "department": "Customer Delivery - Data Engineering", "location": "Ahmedabad", "email": "jeet.shah@tatvic.com"},
    {"employee_number": "1682", "name": "Jeet Shaileshkumar Pandya", "job_title": "GM Accounts & Finance", "department": "Accounts & Finance", "location": "Ahmedabad", "email": "jeet.pandya@tatvic.com"},
    {"employee_number": "IN204", "name": "Jimit Chavda", "job_title": "Technical Trainee", "department": "Customer Delivery - Data Collection", "location": "Ahmedabad", "email": "jimit@tatvic.com"},
    {"employee_number": "1666", "name": "Kaavya Vyas", "job_title": "Technical Analyst", "department": "Customer Delivery - Data Collection", "location": "Ahmedabad", "email": "kaavya@tatvic.com"},
    {"employee_number": "1314", "name": "Kalpesh Kanade", "job_title": "IT Manager", "department": "IT & Admin", "location": "Ahmedabad", "email": "kalpesh@tatvic.com"},
    {"employee_number": "1442", "name": "Kalpit Visavadiya", "job_title": "Sr Technical Analyst", "department": "Customer Delivery - Data Collection", "location": "Ahmedabad", "email": "kalpit@tatvic.com"},
    {"employee_number": "1141", "name": "Kamal Aggarwal", "job_title": "Head Of Delivery", "department": "Customer Delivery", "location": "Ahmedabad", "email": "kamal@tatvic.com"},
    {"employee_number": "IN190", "name": "Kavya Tiwari", "job_title": "Technical Trainee", "department": "Customer Delivery - Data Analysis & Insights", "location": "Ahmedabad", "email": "kavya.tiwari@tatvic.com"},
    {"employee_number": "1284", "name": "Khilav Joshi", "job_title": "Head of Strategy", "department": "Strategy", "location": "Ahmedabad", "email": "khilav@tatvic.com"},
    {"employee_number": "IN192", "name": "Khush Patel", "job_title": "Technical Trainee", "department": "Strategy", "location": "Ahmedabad", "email": "khush@tatvic.com"},
    {"employee_number": "IN209", "name": "Krishi Thakkar", "job_title": "Technical Trainee", "department": "Customer Delivery - Data Engineering", "location": "Ahmedabad", "email": "krishi@tatvic.com"},
    {"employee_number": "1353", "name": "Kshitija Bakre", "job_title": "CRO Lead", "department": "Customer Delivery - CRO", "location": "Ahmedabad", "email": "kshitija@tatvic.com"},
    {"employee_number": "1657", "name": "Lakshin Pathak", "job_title": "Solution Engineer", "department": "Strategy", "location": "Ahmedabad", "email": "lakshin@tatvic.com"},
    {"employee_number": "1678", "name": "Lakshit Bhavinkumar Pathak", "job_title": "Data Engineer", "department": "Customer Delivery - Data Engineering", "location": "Ahmedabad", "email": "lakshit@tatvic.com"},
    {"employee_number": "1656", "name": "Mahesh Varhat", "job_title": "Admin Support", "department": "IT & Admin", "location": "Ahmedabad", "email": "maheshvarhat022@gmail.com"},
    {"employee_number": "1680", "name": "MAHIMA DAGA", "job_title": "Assistant Manager-Legal", "department": "Accounts & Finance", "location": "Ahmedabad", "email": "mahima@tatvic.com"},
    {"employee_number": "IN211", "name": "Manasvi Parmar", "job_title": "Technical Trainee", "department": "Customer Delivery - Data Engineering", "location": "Ahmedabad", "email": "manasvi@tatvic.com"},
    {"employee_number": "1541", "name": "Maulik Patel", "job_title": "Sr Technical Analyst", "department": "Customer Delivery - Data Collection", "location": "Ahmedabad", "email": "maulik.patel@tatvic.com"},
    {"employee_number": "1408", "name": "Maulin Joshi", "job_title": "Manager-Customer Development", "department": "Customer Development - India", "location": "Ahmedabad", "email": "maulin@tatvic.com"},
    {"employee_number": "1676", "name": "Mittal Desai", "job_title": "Cloud Engineer", "department": "Customer Delivery - Data Engineering", "location": "Ahmedabad", "email": "mittal@tatvic.com"},
    {"employee_number": "1477", "name": "Mohammedimad", "job_title": "CRO Specialist", "department": "Customer Delivery - CRO", "location": "Ahmedabad", "email": "mohammedimad@tatvic.com"},
    {"employee_number": "1677", "name": "Mohit Keshvani", "job_title": "Data Analyst", "department": "Customer Delivery - Data Analysis & Insights", "location": "Ahmedabad", "email": "mohit@tatvic.com"},
    {"employee_number": "1651", "name": "Neha Singh", "job_title": "Account Manager", "department": "Account Management", "location": "Mumbai", "email": "neha.singh@tatvic.com"},
    {"employee_number": "1463", "name": "Neha Turakhia", "job_title": "Account Manager", "department": "Account Management", "location": "Mumbai", "email": "neha.turakhia@tatvic.com"},
    {"employee_number": "1176", "name": "Nirmit Titiya", "job_title": "CRO Specialist", "department": "Customer Delivery - CRO", "location": "Ahmedabad", "email": "nirmit@tatvic.com"},
    {"employee_number": "1674", "name": "Palak Jain", "job_title": "Data Scientist", "department": "Customer Delivery - Data Engineering", "location": "Ahmedabad", "email": "palak.j@tatvic.com"},
    {"employee_number": "IN196", "name": "Parshwa Salot", "job_title": "Technical Trainee", "department": "Customer Delivery - Data Collection", "location": "Ahmedabad", "email": "parshwa@tatvic.com"},
    {"employee_number": "1396", "name": "Parthiv Gandhi", "job_title": "Admin Executive", "department": "IT & Admin", "location": "Ahmedabad", "email": "parthiv@tatvic.com"},
    {"employee_number": "1650", "name": "Pavan Patel", "job_title": "Admin Executive", "department": "IT & Admin", "location": "Ahmedabad", "email": "pavan.patel@tatvic.com"},
    {"employee_number": "1613", "name": "Pragya Trivedi", "job_title": "Account Manager - West Region", "department": "Account Management", "location": "Mumbai", "email": "pragya.trivedi@tatvic.com"},
    {"employee_number": "1209", "name": "Prakash Katariya", "job_title": "Lead - Analytics Hub", "department": "Customer Delivery", "location": "Ahmedabad", "email": "prakash.katariya@tatvic.com"},
    {"employee_number": "1621", "name": "Pratham Mehta", "job_title": "Software Development Engineer - Level 2", "department": "Strategy", "location": "Ahmedabad", "email": "pratham@tatvic.com"},
    {"employee_number": "IN184", "name": "Pratik Motwani", "job_title": "Technical Trainee", "department": "Marketing", "location": "Ahmedabad", "email": "pratik.m@tatvic.com"},
    {"employee_number": "1590", "name": "Priyanshu Soni", "job_title": "Campaign Manager", "department": "Customer Delivery - Campaign Management", "location": "Ahmedabad", "email": "priyanshu@tatvic.com"},
    {"employee_number": "1104", "name": "Rajiv Pathak", "job_title": "Partner - Plugin", "department": "Corporate", "location": "Ahmedabad", "email": "rajiv@tatvic.com"},
    {"employee_number": "1000", "name": "Ravi Pathak", "job_title": "Founder", "department": "Corporate", "location": "Singapore", "email": "ravi@tatvic.com"},
    {"employee_number": "1612", "name": "Riddhi Shah", "job_title": "Sr Technical Analyst", "department": "Customer Delivery - Data Collection", "location": "Ahmedabad", "email": "riddhi@tatvic.com"},
    {"employee_number": "1647", "name": "Riddhi Shah", "job_title": "Sr Accounts Executive", "department": "Accounts & Finance", "location": "Ahmedabad", "email": "riddhi.s@tatvic.com"},
    {"employee_number": "1675", "name": "Riddhika Salecha", "job_title": "Executive - HR", "department": "Human Resource", "location": "Ahmedabad", "email": "riddhika@tatvic.com"},
    {"employee_number": "1088", "name": "Rikita Shukla", "job_title": "Account Management Lead - South Region", "department": "Account Management", "location": "Ahmedabad", "email": "rikita.s@tatvic.com"},
    {"employee_number": "1633", "name": "Ronak Gajjar", "job_title": "MIS Expert", "department": "Accounts & Finance", "location": "Ahmedabad", "email": "ronak@tatvic.com"},
    {"employee_number": "IN202", "name": "Ronit Rajput", "job_title": "Technical Trainee", "department": "Customer Delivery - Data Engineering", "location": "Ahmedabad", "email": "ronit@tatvic.com"},
    {"employee_number": "1635", "name": "Ruchika Parikh", "job_title": "Associate Manager - HR", "department": "Human Resource", "location": "Ahmedabad", "email": "ruchika.p@tatvic.com"},
    {"employee_number": "1549", "name": "Ruhbir Singh", "job_title": "Global CEO", "department": "Corporate", "location": "Ahmedabad", "email": "ruhbir@tatvic.com"},
    {"employee_number": "1685", "name": "RUSHABH R SHAH", "job_title": "Senior Data Scientist", "department": "Customer Delivery - Data Science", "location": "Ahmedabad", "email": "rushabh@tatvic.com"},
    {"employee_number": "IN189", "name": "Saanvi Kothari", "job_title": "Technical Trainee", "department": "Customer Delivery - Data Analysis & Insights", "location": "Ahmedabad", "email": "saanvi@tatvic.com"},
    {"employee_number": "1653", "name": "Sanjay Vala", "job_title": "Website Developer", "department": "Marketing", "location": "Ahmedabad", "email": "sanjay@tatvic.com"},
    {"employee_number": "Vistior_65", "name": "Sarjak Patel", "job_title": "Consultant", "department": "Customer Delivery", "location": "Ahmedabad", "email": "sarjak@tatvic.com"},
    {"employee_number": "1684", "name": "SHANI JANGID", "job_title": "Sr Accounts Executive", "department": "Accounts & Finance", "location": "Ahmedabad", "email": "shani@tatvic.com"},
    {"employee_number": "IN199", "name": "Shantanu Srivastava", "job_title": "Technical Trainee", "department": "Customer Delivery - Data Collection", "location": "Ahmedabad", "email": "shantanu@tatvic.com"},
    {"employee_number": "1642", "name": "Shilpi Senguptta", "job_title": "Business Analyst", "department": "Strategy", "location": "Ahmedabad", "email": "shilpi.s@tatvic.com"},
    {"employee_number": "IN203", "name": "Shivangi Gajjar", "job_title": "Technical Trainee", "department": "Customer Delivery - CRO", "location": "Ahmedabad", "email": "shivangi.g@tatvic.com"},
    {"employee_number": "1690", "name": "Shruti Godha", "job_title": "Account Manager", "department": "Account Management", "location": "Ahmedabad", "email": "ruchika.pp@tatvic.com"},
    {"employee_number": "IN212", "name": "Shruti Gupta", "job_title": "Technical Trainee", "department": "Customer Delivery - Data Engineering", "location": "Ahmedabad", "email": "shruti@tatvic.com"},
    {"employee_number": "1624", "name": "Shubham Bohra", "job_title": "Sr Technical Analyst", "department": "Customer Delivery - Data Collection", "location": "Ahmedabad", "email": "shubham.bohra@tatvic.com"},
    {"employee_number": "IN191", "name": "Shubham Lakhani", "job_title": "Technical Trainee", "department": "Customer Delivery - CRO", "location": "Ahmedabad", "email": "shubham.l@tatvic.com"},
    {"employee_number": "1495", "name": "Sohel Visalpurwala", "job_title": "Assistant Manager - Accounts & Finance", "department": "Accounts & Finance", "location": "Ahmedabad", "email": "sohel@tatvic.com"},
    {"employee_number": "1630", "name": "Soniya Sonwani", "job_title": "Sr Executive - HR", "department": "Human Resource", "location": "Ahmedabad", "email": "soniya@tatvic.com"},
    {"employee_number": "1683", "name": "Tanya Tulsyan", "job_title": "Sr Consultant - Digital Analytics", "department": "Customer Delivery - Data Analysis & Insights", "location": "Ahmedabad", "email": "tanya@tatvic.com"},
    {"employee_number": "Test_1", "name": "Tatvic Test", "job_title": "Account Manager", "department": "Customer Delivery - Technical Program Management", "location": "Ahmedabad", "email": "career@tatvic.com"},
    {"employee_number": "IN183", "name": "Urmi Lalchandani", "job_title": "Management Trainee", "department": "Marketing", "location": "Ahmedabad", "email": "urmi@tatvic.com"},
    {"employee_number": "1625", "name": "Urvashi Vaniya", "job_title": "Sr Technical Analyst", "department": "Customer Delivery - Data Collection", "location": "Ahmedabad", "email": "urvashi@tatvic.com"},
    {"employee_number": "1607", "name": "Vaishali Rawat", "job_title": "Sr Technical Analyst", "department": "Customer Delivery - Data Collection", "location": "Ahmedabad", "email": "vaishali@tatvic.com"},
    {"employee_number": "IN206", "name": "Vaishnavi Zope", "job_title": "Technical Trainee", "department": "Customer Delivery - Data Engineering", "location": "Ahmedabad", "email": "vaishnavi@tatvic.com"},
    {"employee_number": "1671", "name": "Vandan Soni", "job_title": "Jr Accounts Executive", "department": "Accounts & Finance", "location": "Ahmedabad", "email": "vandan@tatvic.com"},
    {"employee_number": "1622", "name": "Vanshit Shah", "job_title": "Cloud Engineer", "department": "Customer Delivery - Data Engineering", "location": "Ahmedabad", "email": "vanshit@tatvic.com"},
    {"employee_number": "IN195", "name": "Veli Kadia", "job_title": "Management Trainee", "department": "Human Resource", "location": "Ahmedabad", "email": "veli@tatvic.com"},
    {"employee_number": "1395", "name": "Vikram Bhavsar", "job_title": "IT Executive", "department": "IT & Admin", "location": "Ahmedabad", "email": "itadmin@tatvic.com"},
    {"employee_number": "IN194", "name": "Viral Jain", "job_title": "Technical Trainee", "department": "Strategy", "location": "Ahmedabad", "email": "viral.jain@tatvic.com"},
    {"employee_number": "1660", "name": "Vishakha Bhatia", "job_title": "Executive - HR", "department": "Human Resource", "location": "Ahmedabad", "email": "vishakha.b@tatvic.com"},
    {"employee_number": "IN186", "name": "Vishnu Nair", "job_title": "Technical Trainee", "department": "Customer Delivery - Data Analysis & Insights", "location": "Ahmedabad", "email": "vishnu@tatvic.com"},
    {"employee_number": "IN205", "name": "Vishva Pethani", "job_title": "Technical Trainee", "department": "Customer Delivery - Data Collection", "location": "Ahmedabad", "email": "vishva@tatvic.com"},
    {"employee_number": "1662", "name": "VRAJ SHAH", "job_title": "Investment Analyst", "department": "Accounts & Finance", "location": "Ahmedabad", "email": "vraj.shah@tatvic.com"},
    {"employee_number": "1654", "name": "Yash Dediya", "job_title": "Account Manager", "department": "Account Management", "location": "Mumbai", "email": "yash.d@tatvic.com"},
    {"employee_number": "1679", "name": "Yash Kumar Jha", "job_title": "Inside Sales Expert", "department": "Marketing", "location": "Ahmedabad", "email": "yashkumar@tatvic.com"},
    {"employee_number": "1535", "name": "Zeel Bhatt", "job_title": "Campaign Manager", "department": "Customer Delivery - Campaign Management", "location": "Ahmedabad", "email": "zeel@tatvic.com"},
    # Adding additional HR head mentioned in data
    {"employee_number": "1686", "name": "DHWANI SHAH", "job_title": "Head - People & Culture", "department": "Human Resource", "location": "Ahmedabad", "email": "dhwani@tatvic.com"},
]

DEFAULT_PASSWORD = "Admin@123"


async def seed_users():
    """Create all users in the database."""
    print("=" * 60)
    print("Seed Users Script - Project Nexus RBAC")
    print("=" * 60)
    
    print("\nConnecting to database...")
    await db.connect()
    database = db.db
    
    # Hash password once
    hashed_password = get_password_hash(DEFAULT_PASSWORD)
    
    created = 0
    updated = 0
    errors = 0
    
    print(f"\nProcessing {len(EMPLOYEES)} employees...")
    print("-" * 60)
    
    for emp in EMPLOYEES:
        try:
            role = get_role_from_title(emp["job_title"], emp["name"])
            
            user_data = {
                "email": emp["email"],
                "hashed_password": hashed_password,
                "full_name": emp["name"],
                "employee_number": emp["employee_number"],
                "job_title": emp["job_title"],
                "department": emp["department"],
                "location": emp["location"],
                "role": role.value,
                "reportees_count": 0,
                "manager_email": None,
                "is_active": True,
                "is_superuser": role == UserRole.DIRECTOR,  # Directors get superuser
                "created_at": datetime.utcnow()
            }
            
            # Check if user exists
            existing = await database.users.find_one({"email": emp["email"]})
            
            if existing:
                # Update existing user
                await database.users.update_one(
                    {"email": emp["email"]},
                    {"$set": {
                        "full_name": emp["name"],
                        "employee_number": emp["employee_number"],
                        "job_title": emp["job_title"],
                        "department": emp["department"],
                        "location": emp["location"],
                        "role": role.value,
                    }}
                )
                updated += 1
                print(f"  Updated: {emp['name']} ({emp['email']}) - {role.value}")
            else:
                # Insert new user
                await database.users.insert_one(user_data)
                created += 1
                print(f"  Created: {emp['name']} ({emp['email']}) - {role.value}")
                
        except Exception as e:
            errors += 1
            print(f"  ERROR: {emp['name']} - {str(e)}")
    
    print("-" * 60)
    print(f"\nSummary:")
    print(f"  Created: {created}")
    print(f"  Updated: {updated}")
    print(f"  Errors: {errors}")
    print(f"  Total processed: {len(EMPLOYEES)}")
    
    # Count users by role
    print("\nUsers by Role:")
    for role in UserRole:
        count = await database.users.count_documents({"role": role.value})
        print(f"  {role.value.capitalize()}: {count}")
    
    # Highlight special users
    print("\nSpecial Access Users (HEAD level or higher):")
    async for user in database.users.find({"role": {"$in": ["head", "admin", "director"]}}):
        print(f"  - {user['full_name']} ({user['email']}) - {user['role']}")
    
    await db.close()
    print("\n✅ Seed completed!")


if __name__ == "__main__":
    asyncio.run(seed_users())
