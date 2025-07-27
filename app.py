import streamlit as st
import requests
import json
import asyncio
import aiohttp
from typing import List, Dict, Any
import time
import plotly.express as px
import plotly.graph_objects as go
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import io
import base64
from config import (
    GEMINI_API_KEY, 
    GEMINI_API_URL, 
    GENERATION_CONFIG, 
    APP_CONFIG, 
    DEFAULT_EXPERTS, 
    DEFAULT_TONE,
    MAX_HISTORY_CONTEXT,
    REQUEST_TIMEOUT
)

# Configure page
st.set_page_config(**APP_CONFIG)

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = []

# Expert domain configurations with detailed expert profiles and qualifications
EXPERT_CONFIGS = {
    "Healthcare": {
        "domain_name": "Healthcare",
        "description": "Medical and health-related advice",
        "prompt_template": "You are {name}, a {tone} healthcare expert with the following qualifications: {qualifications}. Your specialization is {specialization} and you have {experience} level experience. Provide professional medical advice and health recommendations. Always remind users to consult healthcare professionals for serious medical concerns. Respond to: {question}",
        "avatar": "🏥",
        "expert_pool": [
            {
                "name": "Dr. Sarah Johnson",
                "qualifications": "MD, MPH, Board Certified in Internal Medicine",
                "specialization": "General Medicine",
                "experience": "Senior Consultant",
                "communication_style": "Professional",
                "years_experience": 15,
                "certifications": ["American Board of Internal Medicine", "Public Health Certification"],
                "expertise_areas": ["Preventive Care", "Chronic Disease Management", "Health Screening"]
            },
            {
                "name": "Dr. Michael Chen",
                "qualifications": "MD, PhD in Nutrition Science, Certified Nutritionist",
                "specialization": "Nutrition",
                "experience": "Specialist",
                "communication_style": "Educational",
                "years_experience": 12,
                "certifications": ["Board Certified in Nutrition", "Sports Nutrition Certification"],
                "expertise_areas": ["Sports Nutrition", "Weight Management", "Dietary Planning"]
            },
            {
                "name": "Dr. Emily Rodriguez",
                "qualifications": "MD, Sports Medicine Fellowship, Physical Therapy License",
                "specialization": "Fitness",
                "experience": "Specialist",
                "communication_style": "Encouraging",
                "years_experience": 10,
                "certifications": ["Sports Medicine Board Certification", "Physical Therapy License"],
                "expertise_areas": ["Exercise Prescription", "Injury Prevention", "Rehabilitation"]
            },
            {
                "name": "Dr. James Wilson",
                "qualifications": "MD, Emergency Medicine Residency, Trauma Surgery Experience",
                "specialization": "Emergency Medicine",
                "experience": "Senior Consultant",
                "communication_style": "Direct",
                "years_experience": 18,
                "certifications": ["Emergency Medicine Board Certification", "Advanced Trauma Life Support"],
                "expertise_areas": ["Emergency Care", "Trauma Management", "Critical Care"]
            }
        ],
        "specializations": ["General Medicine", "Nutrition", "Fitness", "Preventive Care", "Emergency Medicine"],
        "experience_levels": ["Resident", "General Practitioner", "Specialist", "Senior Consultant"],
        "communication_styles": ["Professional", "Friendly", "Direct", "Educational"]
    },
    "Mental Health": {
        "domain_name": "Mental Health",
        "description": "Psychological and emotional support",
        "prompt_template": "You are {name}, a {tone} mental health expert with the following qualifications: {qualifications}. Your specialization is {specialization} and you have {experience} level experience. Provide supportive psychological guidance and emotional wellness advice. Always encourage professional help for serious mental health concerns. Respond to: {question}",
        "avatar": "🧠",
        "expert_pool": [
            {
                "name": "Dr. Lisa Thompson",
                "qualifications": "PhD in Clinical Psychology, Licensed Clinical Psychologist",
                "specialization": "Clinical Psychology",
                "experience": "Senior Therapist",
                "communication_style": "Empathetic",
                "years_experience": 14,
                "certifications": ["Licensed Clinical Psychologist", "CBT Certification"],
                "expertise_areas": ["Anxiety Disorders", "Depression", "Trauma Therapy"]
            },
            {
                "name": "Dr. Robert Kim",
                "qualifications": "PhD in Counseling Psychology, Certified Mindfulness Instructor",
                "specialization": "Mindfulness",
                "experience": "Clinical Psychologist",
                "communication_style": "Gentle",
                "years_experience": 11,
                "certifications": ["Licensed Professional Counselor", "Mindfulness-Based Stress Reduction"],
                "expertise_areas": ["Stress Management", "Meditation", "Mindfulness Training"]
            },
            {
                "name": "Dr. Amanda Foster",
                "qualifications": "MSW, LCSW, Trauma-Informed Care Specialist",
                "specialization": "Trauma Therapy",
                "experience": "Senior Therapist",
                "communication_style": "Supportive",
                "years_experience": 13,
                "certifications": ["Licensed Clinical Social Worker", "EMDR Certification"],
                "expertise_areas": ["PTSD", "Trauma Recovery", "EMDR Therapy"]
            }
        ],
        "specializations": ["Clinical Psychology", "Counseling", "Cognitive Behavioral Therapy", "Mindfulness", "Trauma Therapy"],
        "experience_levels": ["Counselor", "Clinical Psychologist", "Senior Therapist", "Psychiatrist"],
        "communication_styles": ["Empathetic", "Supportive", "Professional", "Gentle"]
    },
    "Education": {
        "domain_name": "Education",
        "description": "Learning and academic guidance",
        "prompt_template": "You are {name}, a {tone} education expert with the following qualifications: {qualifications}. Your specialization is {specialization} and you have {experience} level experience. Provide educational guidance, study tips, and learning strategies. Help with academic planning and skill development. Respond to: {question}",
        "avatar": "📚",
        "expert_pool": [
            {
                "name": "Prof. David Martinez",
                "qualifications": "PhD in Education, Master's in Curriculum Development",
                "specialization": "K-12 Education",
                "experience": "Professor",
                "communication_style": "Structured",
                "years_experience": 16,
                "certifications": ["Teaching License", "Curriculum Development Certification"],
                "expertise_areas": ["Curriculum Design", "Student Assessment", "Educational Technology"]
            },
            {
                "name": "Dr. Jennifer Lee",
                "qualifications": "PhD in Higher Education, Online Learning Specialist",
                "specialization": "Online Learning",
                "experience": "Educational Consultant",
                "communication_style": "Interactive",
                "years_experience": 12,
                "certifications": ["Online Teaching Certification", "Instructional Design"],
                "expertise_areas": ["E-Learning", "Digital Pedagogy", "Student Engagement"]
            },
            {
                "name": "Dr. Thomas Brown",
                "qualifications": "PhD in Career Development, Certified Career Counselor",
                "specialization": "Career Development",
                "experience": "Academic Advisor",
                "communication_style": "Mentoring",
                "years_experience": 15,
                "certifications": ["Career Development Specialist", "Academic Advising Certification"],
                "expertise_areas": ["Career Planning", "Academic Advising", "Professional Development"]
            }
        ],
        "specializations": ["K-12 Education", "Higher Education", "Online Learning", "Special Education", "Career Development"],
        "experience_levels": ["Teacher", "Professor", "Educational Consultant", "Academic Advisor"],
        "communication_styles": ["Encouraging", "Structured", "Interactive", "Mentoring"]
    },
    "Finance": {
        "domain_name": "Finance",
        "description": "Financial planning and advice",
        "prompt_template": "You are {name}, a {tone} finance expert with the following qualifications: {qualifications}. Your specialization is {specialization} and you have {experience} level experience. Provide financial planning advice, investment guidance, and money management tips. Always include appropriate disclaimers about financial decisions. Respond to: {question}",
        "avatar": "💰",
        "expert_pool": [
            {
                "name": "Sarah Williams",
                "qualifications": "CFP, MBA in Finance, Certified Financial Planner",
                "specialization": "Personal Finance",
                "experience": "Senior Financial Planner",
                "communication_style": "Practical",
                "years_experience": 14,
                "certifications": ["Certified Financial Planner", "Series 7 License"],
                "expertise_areas": ["Budgeting", "Debt Management", "Financial Planning"]
            },
            {
                "name": "Michael Davis",
                "qualifications": "CFA, MBA in Investment Management, Portfolio Manager",
                "specialization": "Investment Management",
                "experience": "Investment Manager",
                "communication_style": "Analytical",
                "years_experience": 17,
                "certifications": ["Chartered Financial Analyst", "Series 65 License"],
                "expertise_areas": ["Portfolio Management", "Risk Assessment", "Market Analysis"]
            },
            {
                "name": "Lisa Anderson",
                "qualifications": "CPA, CFP, Tax Planning Specialist",
                "specialization": "Tax Planning",
                "experience": "Wealth Manager",
                "communication_style": "Conservative",
                "years_experience": 13,
                "certifications": ["Certified Public Accountant", "Certified Financial Planner"],
                "expertise_areas": ["Tax Strategy", "Estate Planning", "Retirement Planning"]
            }
        ],
        "specializations": ["Personal Finance", "Investment Management", "Retirement Planning", "Tax Planning", "Estate Planning"],
        "experience_levels": ["Financial Advisor", "Investment Manager", "Senior Financial Planner", "Wealth Manager"],
        "communication_styles": ["Analytical", "Practical", "Conservative", "Progressive"]
    },
    "Legal": {
        "domain_name": "Legal",
        "description": "Legal information and guidance",
        "prompt_template": "You are {name}, a {tone} legal expert with the following qualifications: {qualifications}. Your specialization is {specialization} and you have {experience} level experience. Provide general legal information and guidance. Always recommend consulting qualified legal professionals for specific legal matters. Respond to: {question}",
        "avatar": "⚖️",
        "expert_pool": [
            {
                "name": "Attorney Robert Johnson",
                "qualifications": "JD, LLM in Corporate Law, Bar Certified",
                "specialization": "Corporate Law",
                "experience": "Senior Partner",
                "communication_style": "Authoritative",
                "years_experience": 19,
                "certifications": ["State Bar License", "Corporate Law Specialization"],
                "expertise_areas": ["Business Formation", "Contract Law", "Corporate Governance"]
            },
            {
                "name": "Attorney Maria Garcia",
                "qualifications": "JD, Family Law Specialist, Mediation Certification",
                "specialization": "Family Law",
                "experience": "Attorney",
                "communication_style": "Cautious",
                "years_experience": 11,
                "certifications": ["State Bar License", "Family Law Certification"],
                "expertise_areas": ["Divorce", "Child Custody", "Family Mediation"]
            },
            {
                "name": "Attorney David Chen",
                "qualifications": "JD, Intellectual Property Law, Patent Attorney",
                "specialization": "Intellectual Property",
                "experience": "Legal Consultant",
                "communication_style": "Precise",
                "years_experience": 15,
                "certifications": ["State Bar License", "Patent Attorney Registration"],
                "expertise_areas": ["Patent Law", "Trademark Law", "Copyright Law"]
            }
        ],
        "specializations": ["Civil Law", "Criminal Law", "Corporate Law", "Family Law", "Intellectual Property"],
        "experience_levels": ["Legal Assistant", "Attorney", "Senior Partner", "Legal Consultant"],
        "communication_styles": ["Precise", "Authoritative", "Explanatory", "Cautious"]
    },
    "Technology": {
        "domain_name": "Technology",
        "description": "Tech advice and digital solutions",
        "prompt_template": "You are {name}, a {tone} technology expert with the following qualifications: {qualifications}. Your specialization is {specialization} and you have {experience} level experience. Provide technical guidance, software recommendations, and digital solutions. Help with tech troubleshooting and innovation. Respond to: {question}",
        "avatar": "💻",
        "expert_pool": [
            {
                "name": "Alex Thompson",
                "qualifications": "MS in Computer Science, AWS Solutions Architect",
                "specialization": "Cloud Computing",
                "experience": "Tech Lead",
                "communication_style": "Technical",
                "years_experience": 12,
                "certifications": ["AWS Solutions Architect", "Google Cloud Professional"],
                "expertise_areas": ["Cloud Architecture", "DevOps", "Infrastructure Design"]
            },
            {
                "name": "Dr. Sarah Kim",
                "qualifications": "PhD in Data Science, Machine Learning Specialist",
                "specialization": "AI/ML",
                "experience": "CTO",
                "communication_style": "Innovative",
                "years_experience": 16,
                "certifications": ["TensorFlow Developer", "Deep Learning Specialization"],
                "expertise_areas": ["Machine Learning", "Deep Learning", "Data Analytics"]
            },
            {
                "name": "Mike Rodriguez",
                "qualifications": "BS in Cybersecurity, CISSP Certified",
                "specialization": "Cybersecurity",
                "experience": "Senior Developer",
                "communication_style": "Practical",
                "years_experience": 10,
                "certifications": ["CISSP", "CompTIA Security+", "CEH"],
                "expertise_areas": ["Network Security", "Penetration Testing", "Security Auditing"]
            }
        ],
        "specializations": ["Software Development", "Cybersecurity", "Data Science", "Cloud Computing", "AI/ML"],
        "experience_levels": ["Junior Developer", "Senior Developer", "Tech Lead", "CTO"],
        "communication_styles": ["Technical", "Simplified", "Innovative", "Practical"]
    },
    "Business": {
        "domain_name": "Business",
        "description": "Business strategy and management advice",
        "prompt_template": "You are {name}, a {tone} business expert with the following qualifications: {qualifications}. Your specialization is {specialization} and you have {experience} level experience. Provide business strategy, management advice, and organizational guidance. Help with business planning and growth strategies. Respond to: {question}",
        "avatar": "🏢",
        "expert_pool": [
            {
                "name": "Jennifer Martinez",
                "qualifications": "MBA, PMP, Strategic Management Consultant",
                "specialization": "Strategic Management",
                "experience": "Senior Consultant",
                "communication_style": "Strategic",
                "years_experience": 14,
                "certifications": ["Project Management Professional", "Strategic Management Certification"],
                "expertise_areas": ["Business Strategy", "Project Management", "Organizational Development"]
            },
            {
                "name": "David Chen",
                "qualifications": "MBA, CPA, Business Operations Specialist",
                "specialization": "Operations Management",
                "experience": "Operations Director",
                "communication_style": "Analytical",
                "years_experience": 13,
                "certifications": ["Certified Public Accountant", "Six Sigma Black Belt"],
                "expertise_areas": ["Process Optimization", "Cost Management", "Quality Control"]
            },
            {
                "name": "Lisa Johnson",
                "qualifications": "MBA, Marketing Strategy Expert",
                "specialization": "Marketing Strategy",
                "experience": "Marketing Director",
                "communication_style": "Creative",
                "years_experience": 11,
                "certifications": ["Digital Marketing Certification", "Brand Management"],
                "expertise_areas": ["Digital Marketing", "Brand Strategy", "Market Research"]
            }
        ],
        "specializations": ["Strategic Management", "Operations Management", "Marketing Strategy", "Human Resources", "Supply Chain"],
        "experience_levels": ["Business Analyst", "Manager", "Director", "Executive"],
        "communication_styles": ["Strategic", "Analytical", "Creative", "Professional"]
    },
    "Science": {
        "domain_name": "Science",
        "description": "Scientific research and discovery guidance",
        "prompt_template": "You are {name}, a {tone} science expert with the following qualifications: {qualifications}. Your specialization is {specialization} and you have {experience} level experience. Provide scientific guidance, research methodology, and discovery insights. Help with scientific understanding and innovation. Respond to: {question}",
        "avatar": "🔬",
        "expert_pool": [
            {
                "name": "Dr. Robert Wilson",
                "qualifications": "PhD in Physics, Research Scientist",
                "specialization": "Physics",
                "experience": "Senior Researcher",
                "communication_style": "Analytical",
                "years_experience": 18,
                "certifications": ["Research Excellence Award", "Physics Society Member"],
                "expertise_areas": ["Quantum Physics", "Theoretical Physics", "Research Methodology"]
            },
            {
                "name": "Dr. Emily Davis",
                "qualifications": "PhD in Chemistry, Materials Scientist",
                "specialization": "Chemistry",
                "experience": "Research Director",
                "communication_style": "Precise",
                "years_experience": 15,
                "certifications": ["Materials Science Certification", "Chemistry Society Fellow"],
                "expertise_areas": ["Materials Science", "Chemical Analysis", "Nanotechnology"]
            },
            {
                "name": "Dr. Michael Brown",
                "qualifications": "PhD in Biology, Geneticist",
                "specialization": "Biology",
                "experience": "Senior Scientist",
                "communication_style": "Educational",
                "years_experience": 12,
                "certifications": ["Genetics Certification", "Biological Research Award"],
                "expertise_areas": ["Genetics", "Molecular Biology", "Biotechnology"]
            }
        ],
        "specializations": ["Physics", "Chemistry", "Biology", "Mathematics", "Environmental Science"],
        "experience_levels": ["Research Assistant", "Scientist", "Senior Scientist", "Research Director"],
        "communication_styles": ["Analytical", "Precise", "Educational", "Innovative"]
    },
    "Arts": {
        "domain_name": "Arts",
        "description": "Creative arts and design guidance",
        "prompt_template": "You are {name}, a {tone} arts expert with the following qualifications: {qualifications}. Your specialization is {specialization} and you have {experience} level experience. Provide creative guidance, artistic techniques, and design principles. Help with artistic expression and creative projects. Respond to: {question}",
        "avatar": "🎨",
        "expert_pool": [
            {
                "name": "Sophie Anderson",
                "qualifications": "MFA in Fine Arts, Professional Artist",
                "specialization": "Fine Arts",
                "experience": "Professional Artist",
                "communication_style": "Creative",
                "years_experience": 16,
                "certifications": ["Fine Arts Certification", "Gallery Representation"],
                "expertise_areas": ["Painting", "Sculpture", "Art History", "Exhibition Design"]
            },
            {
                "name": "Carlos Rodriguez",
                "qualifications": "BFA in Graphic Design, Creative Director",
                "specialization": "Graphic Design",
                "experience": "Creative Director",
                "communication_style": "Innovative",
                "years_experience": 13,
                "certifications": ["Adobe Creative Suite Expert", "Design Thinking Certification"],
                "expertise_areas": ["Brand Design", "Digital Art", "Typography", "User Experience"]
            },
            {
                "name": "Emma Thompson",
                "qualifications": "MFA in Photography, Visual Artist",
                "specialization": "Photography",
                "experience": "Professional Photographer",
                "communication_style": "Artistic",
                "years_experience": 11,
                "certifications": ["Professional Photography", "Visual Arts Award"],
                "expertise_areas": ["Portrait Photography", "Digital Imaging", "Visual Storytelling"]
            }
        ],
        "specializations": ["Fine Arts", "Graphic Design", "Photography", "Digital Art", "Art History"],
        "experience_levels": ["Student", "Professional Artist", "Creative Director", "Art Curator"],
        "communication_styles": ["Creative", "Innovative", "Artistic", "Expressive"]
    },
    "Sports": {
        "domain_name": "Sports",
        "description": "Sports training and athletic performance",
        "prompt_template": "You are {name}, a {tone} sports expert with the following qualifications: {qualifications}. Your specialization is {specialization} and you have {experience} level experience. Provide sports training advice, performance optimization, and athletic guidance. Help with fitness goals and sports performance. Respond to: {question}",
        "avatar": "⚽",
        "expert_pool": [
            {
                "name": "Coach Mike Johnson",
                "qualifications": "MS in Sports Science, Certified Strength Coach",
                "specialization": "Strength Training",
                "experience": "Head Coach",
                "communication_style": "Motivational",
                "years_experience": 14,
                "certifications": ["Certified Strength Coach", "Sports Science Certification"],
                "expertise_areas": ["Strength Training", "Athletic Performance", "Injury Prevention"]
            },
            {
                "name": "Sarah Williams",
                "qualifications": "BS in Kinesiology, Sports Nutritionist",
                "specialization": "Sports Nutrition",
                "experience": "Sports Nutritionist",
                "communication_style": "Encouraging",
                "years_experience": 10,
                "certifications": ["Sports Nutrition Certification", "Athletic Training"],
                "expertise_areas": ["Sports Nutrition", "Performance Diet", "Recovery Nutrition"]
            },
            {
                "name": "Coach David Lee",
                "qualifications": "MS in Exercise Physiology, Performance Specialist",
                "specialization": "Performance Training",
                "experience": "Performance Director",
                "communication_style": "Direct",
                "years_experience": 12,
                "certifications": ["Exercise Physiology", "Performance Training Certification"],
                "expertise_areas": ["Performance Training", "Conditioning", "Sports Psychology"]
            }
        ],
        "specializations": ["Strength Training", "Sports Nutrition", "Performance Training", "Team Sports", "Individual Sports"],
        "experience_levels": ["Assistant Coach", "Coach", "Head Coach", "Performance Director"],
        "communication_styles": ["Motivational", "Encouraging", "Direct", "Supportive"]
    },
    "Travel": {
        "domain_name": "Travel",
        "description": "Travel planning and destination guidance",
        "prompt_template": "You are {name}, a {tone} travel expert with the following qualifications: {qualifications}. Your specialization is {specialization} and you have {experience} level experience. Provide travel advice, destination recommendations, and trip planning guidance. Help with travel logistics and cultural experiences. Respond to: {question}",
        "avatar": "✈️",
        "expert_pool": [
            {
                "name": "Maria Garcia",
                "qualifications": "Travel Consultant, Cultural Tourism Specialist",
                "specialization": "Cultural Tourism",
                "experience": "Senior Travel Consultant",
                "communication_style": "Enthusiastic",
                "years_experience": 15,
                "certifications": ["Travel Consultant Certification", "Cultural Tourism Specialist"],
                "expertise_areas": ["Cultural Tourism", "Heritage Sites", "Local Experiences", "Cultural Exchange"]
            },
            {
                "name": "James Wilson",
                "qualifications": "Adventure Travel Guide, Wilderness Expert",
                "specialization": "Adventure Travel",
                "experience": "Adventure Guide",
                "communication_style": "Adventurous",
                "years_experience": 11,
                "certifications": ["Wilderness First Aid", "Adventure Travel Certification"],
                "expertise_areas": ["Adventure Travel", "Wilderness Expeditions", "Outdoor Activities", "Safety Planning"]
            },
            {
                "name": "Lisa Chen",
                "qualifications": "Luxury Travel Specialist, Concierge Services",
                "specialization": "Luxury Travel",
                "experience": "Luxury Travel Consultant",
                "communication_style": "Sophisticated",
                "years_experience": 13,
                "certifications": ["Luxury Travel Certification", "Concierge Services"],
                "expertise_areas": ["Luxury Travel", "VIP Services", "Exclusive Destinations", "Premium Experiences"]
            }
        ],
        "specializations": ["Cultural Tourism", "Adventure Travel", "Luxury Travel", "Business Travel", "Budget Travel"],
        "experience_levels": ["Travel Agent", "Travel Consultant", "Senior Consultant", "Travel Director"],
        "communication_styles": ["Enthusiastic", "Adventurous", "Sophisticated", "Helpful"]
    }
}

def call_gemini_api(prompt: str, api_key: str = GEMINI_API_KEY) -> str:
    """Call the Gemini API with the given prompt"""
    headers = {
        "Content-Type": "application/json"
    }
    
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": GENERATION_CONFIG
    }
    
    try:
        response = requests.post(
            f"{GEMINI_API_URL}?key={api_key}",
            headers=headers,
            json=data,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        
        result = response.json()
        if "candidates" in result and len(result["candidates"]) > 0:
            return result["candidates"][0]["content"]["parts"][0]["text"]
        else:
            return "Sorry, I couldn't generate a response at this time."
            
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Detailed API Error: {error_details}")
        st.error(f"API Error: {str(e)}")
        return f"Error calling API: {str(e)}"

def supervisor_route(user_input: str, chosen_experts: List[str], tone: str, names: Dict[str, str]) -> Dict[str, str]:
    """Supervisor agent that routes the query to appropriate experts"""
    
    # Create a classification prompt for the supervisor
    supervisor_prompt = f"""
    You are a supervisor agent that needs to classify which experts should handle this user query.
    
    Available experts: {', '.join(chosen_experts)}
    User query: {user_input}
    
    For each expert, respond with either "YES" or "NO" based on whether they should be consulted.
    Format your response as a simple list of expert names that should be consulted, separated by commas.
    Only include experts that are directly relevant to the query.
    
    Response (just the expert names, comma-separated):
    """
    
    try:
        supervisor_response = call_gemini_api(supervisor_prompt)
        # Parse the supervisor's response to get relevant experts
        relevant_experts = [expert.strip() for expert in supervisor_response.split(',') if expert.strip() in chosen_experts]
        
        # If supervisor didn't identify any experts, use all chosen experts
        if not relevant_experts:
            relevant_experts = chosen_experts
            
    except:
        # Fallback to all chosen experts if supervisor fails
        relevant_experts = chosen_experts
    
    return relevant_experts

def generate_dynamic_expert(domain: str, expert_number: int, nationality: str = "International", cultural_context: str = "", used_names: set = None) -> Dict:
    """Generate a dynamic expert with nationality and cultural context awareness"""
    
    # Initialize used_names if not provided
    if used_names is None:
        used_names = set()
    
    # Base expert templates for each domain
    expert_templates = {
        "Mental Health": {
            "names": ["Dr. Sarah Chen", "Dr. Maria Rodriguez", "Dr. James Thompson", "Dr. Aisha Patel", "Dr. Hans Mueller", "Dr. Yuki Tanaka", "Dr. Fatima Al-Zahra", "Dr. Carlos Silva", "Dr. Elena Popov", "Dr. Rajesh Kumar", "Dr. Jennifer Lee", "Dr. Wei Zhang", "Dr. Anna Kowalski", "Dr. Isabella Santos", "Dr. Hassan Al-Mansouri"],
            "qualifications": ["Ph.D. Clinical Psychology", "M.D. Psychiatry", "Psy.D. Clinical Psychology", "Ph.D. Counseling Psychology"],
            "specializations": ["Anxiety Disorders", "Depression Treatment", "Trauma Therapy", "Cognitive Behavioral Therapy", "Mindfulness-Based Therapy", "Family Therapy", "Child Psychology", "Geriatric Psychology"],
            "experience_levels": ["Junior", "Mid-Level", "Senior", "Expert"],
            "expertise_areas": ["Stress Management", "Mood Disorders", "Relationship Issues", "Work-Life Balance", "Crisis Intervention", "Preventive Mental Health"]
        },
        "Healthcare": {
            "names": ["Dr. Emily Johnson", "Dr. Ahmed Hassan", "Dr. Lisa Wang", "Dr. Roberto Martinez", "Dr. Priya Sharma", "Dr. Michael O'Connor", "Dr. Sofia Petrov", "Dr. Kenji Yamamoto", "Dr. David Wilson", "Dr. Elena Rodriguez", "Dr. Raj Patel", "Dr. Sarah Mueller", "Dr. Hassan Al-Zahra", "Dr. Wei Chen", "Dr. Maria Santos"],
            "qualifications": ["M.D. Internal Medicine", "Ph.D. Public Health", "M.D. Family Medicine", "Ph.D. Epidemiology"],
            "specializations": ["Preventive Medicine", "Chronic Disease Management", "Nutrition Science", "Exercise Physiology", "Public Health", "Health Policy", "Telemedicine", "Integrative Medicine"],
            "experience_levels": ["Junior", "Mid-Level", "Senior", "Expert"],
            "expertise_areas": ["Lifestyle Medicine", "Disease Prevention", "Health Education", "Patient Advocacy", "Healthcare Systems", "Digital Health"]
        },
        "Education": {
            "names": ["Prof. David Wilson", "Prof. Elena Popov", "Prof. Rajesh Kumar", "Prof. Jennifer Lee", "Prof. Hassan Al-Mansouri", "Prof. Isabella Santos", "Prof. Wei Zhang", "Prof. Anna Kowalski", "Prof. Alex Kim", "Prof. Maria Rodriguez", "Prof. James Thompson", "Prof. Sarah Chen", "Prof. Ahmed Hassan", "Prof. Lisa Wang", "Prof. Roberto Martinez"],
            "qualifications": ["Ph.D. Education", "Ed.D. Educational Leadership", "Ph.D. Learning Sciences", "M.Ed. Curriculum Design"],
            "specializations": ["Educational Technology", "Curriculum Development", "Student Assessment", "Special Education", "Higher Education", "Early Childhood Education", "Adult Learning", "Educational Psychology"],
            "experience_levels": ["Junior", "Mid-Level", "Senior", "Expert"],
            "expertise_areas": ["Learning Strategies", "Educational Innovation", "Student Success", "Teacher Training", "Educational Policy", "Digital Learning"]
        },
        "Finance": {
            "names": ["Mr. Robert Chen", "Ms. Fatima Al-Rashid", "Mr. Alexander Petrov", "Ms. Priya Patel", "Mr. Carlos Rodriguez", "Ms. Yuki Tanaka", "Mr. Ahmed Hassan", "Ms. Sarah Johnson", "Mr. David Wilson", "Ms. Elena Popov", "Mr. Rajesh Kumar", "Ms. Jennifer Lee", "Mr. Hassan Al-Mansouri", "Ms. Isabella Santos", "Mr. Wei Zhang"],
            "qualifications": ["MBA Finance", "CFA Charterholder", "Ph.D. Economics", "CPA Certified"],
            "specializations": ["Investment Management", "Financial Planning", "Risk Management", "Corporate Finance", "Personal Finance", "Retirement Planning", "Tax Planning", "Estate Planning"],
            "experience_levels": ["Junior", "Mid-Level", "Senior", "Expert"],
            "expertise_areas": ["Wealth Management", "Financial Markets", "Budgeting", "Debt Management", "Insurance Planning", "International Finance"]
        },
        "Technology": {
            "names": ["Dr. Alex Kim", "Dr. Elena Rodriguez", "Dr. Raj Patel", "Dr. Sarah Mueller", "Dr. Hassan Al-Zahra", "Dr. Wei Chen", "Dr. Maria Santos", "Dr. James Wilson", "Dr. David Wilson", "Dr. Elena Popov", "Dr. Rajesh Kumar", "Dr. Jennifer Lee", "Dr. Hassan Al-Mansouri", "Dr. Isabella Santos", "Dr. Wei Zhang"],
            "qualifications": ["Ph.D. Computer Science", "M.S. Software Engineering", "Ph.D. Artificial Intelligence", "M.S. Data Science"],
            "specializations": ["Artificial Intelligence", "Software Development", "Cybersecurity", "Data Science", "Cloud Computing", "Mobile Development", "DevOps", "Blockchain"],
            "experience_levels": ["Junior", "Mid-Level", "Senior", "Expert"],
            "expertise_areas": ["Machine Learning", "Web Development", "System Architecture", "Database Design", "API Development", "Emerging Technologies"]
        },
        "Legal": {
            "names": ["Esq. Jennifer Martinez", "Esq. Ahmed Hassan", "Esq. Elena Popov", "Esq. Rajesh Kumar", "Esq. Sarah Johnson", "Esq. Carlos Silva", "Esq. Fatima Al-Rashid", "Esq. Wei Zhang", "Esq. David Wilson", "Esq. Maria Rodriguez", "Esq. James Thompson", "Esq. Sarah Chen", "Esq. Lisa Wang", "Esq. Roberto Martinez", "Esq. Priya Sharma"],
            "qualifications": ["J.D. Law", "LL.M. International Law", "Ph.D. Legal Studies", "J.D. Corporate Law"],
            "specializations": ["Corporate Law", "Criminal Law", "Family Law", "Intellectual Property", "International Law", "Employment Law", "Environmental Law", "Tax Law"],
            "experience_levels": ["Junior", "Mid-Level", "Senior", "Expert"],
            "expertise_areas": ["Contract Law", "Legal Compliance", "Dispute Resolution", "Legal Research", "Regulatory Affairs", "International Trade Law"]
        }
    }
    
    import random
    
    # Get template for the domain
    template = expert_templates.get(domain, expert_templates["Mental Health"])
    
    # Select name based on nationality if specified
    if nationality.lower() != "international":
        # Filter names based on nationality context
        nationality_names = {
            "indian": ["Dr. Rajesh Kumar", "Dr. Priya Sharma", "Dr. Aisha Patel", "Dr. Raj Patel", "Dr. Rajesh Kumar"],
            "chinese": ["Dr. Sarah Chen", "Dr. Lisa Wang", "Dr. Wei Zhang", "Dr. Wei Chen", "Dr. Sarah Chen"],
            "arabic": ["Dr. Ahmed Hassan", "Dr. Fatima Al-Zahra", "Dr. Hassan Al-Mansouri", "Dr. Hassan Al-Zahra", "Dr. Ahmed Hassan"],
            "hispanic": ["Dr. Maria Rodriguez", "Dr. Roberto Martinez", "Dr. Carlos Silva", "Dr. Elena Rodriguez", "Dr. Maria Santos"],
            "european": ["Dr. Hans Mueller", "Dr. Elena Popov", "Dr. Anna Kowalski", "Dr. Elena Rodriguez", "Dr. Hans Mueller"],
            "japanese": ["Dr. Yuki Tanaka", "Dr. Kenji Yamamoto", "Dr. Yuki Tanaka", "Dr. Kenji Yamamoto"],
            "african": ["Dr. Aisha Patel", "Dr. Fatima Al-Rashid", "Dr. Aisha Patel", "Dr. Fatima Al-Rashid"],
            "american": ["Dr. Emily Johnson", "Dr. James Thompson", "Dr. Sarah Johnson", "Dr. David Wilson", "Dr. Emily Johnson"]
        }
        
        for nat_key, names in nationality_names.items():
            if nat_key in nationality.lower():
                template["names"] = names
                break
    
    # Filter out already used names
    available_names = [name for name in template["names"] if name not in used_names]
    
    # If no unique names available, create a unique name with a number
    if not available_names:
        base_name = random.choice(template["names"])
        expert_name = f"{base_name} #{expert_number}"
    else:
        expert_name = random.choice(available_names)
    
    qualifications = random.choice(template["qualifications"])
    specialization = random.choice(template["specializations"])
    experience_level = random.choice(template["experience_levels"])
    years_experience = random.randint(5, 25)
    
    print(f"Generated expert: {expert_name} - {specialization} - {nationality}")
    
    # Add cultural context to specialization if provided
    if cultural_context:
        specialization = f"{specialization} (Cultural Focus: {cultural_context})"
    
    # Generate expertise areas (2-3 areas, but don't exceed available areas)
    available_areas = len(template["expertise_areas"])
    num_areas = min(random.randint(2, 3), available_areas)
    expertise_areas = random.sample(template["expertise_areas"], num_areas)
    
    # Add cultural expertise if nationality is specified
    if nationality.lower() != "international":
        cultural_expertise = f"Cultural Sensitivity ({nationality} context)"
        expertise_areas.append(cultural_expertise)
    
    return {
        "name": expert_name,
        "qualifications": qualifications,
        "specialization": specialization,
        "experience": f"{experience_level} Professional",
        "years_experience": years_experience,
        "expertise_areas": expertise_areas,
        "nationality": nationality,
        "cultural_context": cultural_context
    }

def assign_expert_to_domain(domain: str, user_input: str = "", used_experts: set = None, nationality: str = "International", cultural_context: str = "", used_names: set = None) -> Dict:
    """Dynamically assign or generate the most suitable expert from the domain's expert pool"""
    config = EXPERT_CONFIGS[domain]
    
    # Initialize used_names if not provided
    if used_names is None:
        used_names = set()
    
    # ALWAYS generate dynamic experts for better variety and uniqueness
    if used_experts and len(used_experts) > 0:
        # Generate a new expert dynamically
        expert_number = len(used_experts) + 1
        print(f"Generating dynamic expert {expert_number} for {domain} with nationality: {nationality}")
        return generate_dynamic_expert(domain, expert_number, nationality, cultural_context, used_names)
    
    # For the first expert, also generate dynamically to ensure uniqueness
    expert_number = 1
    print(f"Generating first dynamic expert for {domain} with nationality: {nationality}")
    return generate_dynamic_expert(domain, expert_number, nationality, cultural_context, used_names)
    
    # Create a prompt to select the best expert based on the query
    selection_prompt = f"""
    You are an expert coordinator. Based on the user's query, select the most suitable expert from the available pool.
    
    User Query: {user_input}
    
    Available Experts in {domain}:
    """
    
    for i, expert in enumerate(available_experts):
        selection_prompt += f"""
        Expert {i+1}: {expert['name']}
        - Qualifications: {expert['qualifications']}
        - Specialization: {expert['specialization']}
        - Experience: {expert['experience']} ({expert['years_experience']} years)
        - Expertise Areas: {', '.join(expert['expertise_areas'])}
        """
    
    selection_prompt += """
    Respond with only the expert number (1, 2, 3, etc.) that would be most suitable for this query.
    """
    
    try:
        response = call_gemini_api(selection_prompt)
        # Parse the response to get expert number
        import re
        expert_num = re.search(r'\d+', response)
        if expert_num:
            expert_index = int(expert_num.group()) - 1
            if 0 <= expert_index < len(available_experts):
                return available_experts[expert_index]
            else:
                # If index is out of range, generate a new expert
                expert_number = len(used_experts) + 1 if (used_experts and len(used_experts) > 0) else 1
                return generate_dynamic_expert(domain, expert_number, nationality, cultural_context)
        else:
            # If no number found, generate a new expert
            expert_number = len(used_experts) + 1 if (used_experts and len(used_experts) > 0) else 1
            return generate_dynamic_expert(domain, expert_number, nationality, cultural_context)
    except Exception as e:
        # Log the error and generate a new expert
        print(f"Error in expert assignment for {domain}: {str(e)}")
        expert_number = len(used_experts) + 1 if (used_experts and len(used_experts) > 0) else 1
        return generate_dynamic_expert(domain, expert_number, nationality, cultural_context)

def call_expert_agent(domain: str, user_input: str, tone: str, conversation_history: List[Dict], expert_customization: Dict = None, used_experts: set = None, nationality: str = "International", cultural_context: str = "", used_names: set = None) -> Dict:
    """Call a specific expert agent with dynamic expert assignment and enhanced customization"""
    config = EXPERT_CONFIGS[domain]
    
    # Initialize used_names if not provided
    if used_names is None:
        used_names = set()
    
    # Assign the most suitable expert
    try:
        print(f"Assigning expert for domain: {domain}")
        assigned_expert = assign_expert_to_domain(domain, user_input, used_experts, nationality, cultural_context, used_names)
        print(f"Expert assigned: {assigned_expert['name']}")
    except Exception as e:
        print(f"Error in expert assignment for {domain}: {str(e)}")
        # Fallback to a simple expert
        assigned_expert = {
            "name": f"Expert {len(used_experts) + 1 if used_experts else 1}",
            "qualifications": "Professional",
            "specialization": "General",
            "experience": "Experienced",
            "years_experience": 10,
            "expertise_areas": ["General Expertise"]
        }
    
    # Build conversation context
    context = ""
    if conversation_history:
        context = "\n\nPrevious conversation:\n"
        for msg in conversation_history[-MAX_HISTORY_CONTEXT:]:  # Last messages for context
            context += f"{msg['role']}: {msg['content']}\n"
    
    # Create the expert prompt with full expert details and cultural context
    base_prompt = config["prompt_template"].format(
        tone=tone.lower(),
        name=assigned_expert["name"],
        qualifications=assigned_expert["qualifications"],
        specialization=assigned_expert["specialization"],
        experience=assigned_expert["experience"],
        question=user_input
    )
    
    # Add cultural context if specified
    cultural_instruction = ""
    if assigned_expert.get("nationality") and assigned_expert["nationality"].lower() != "international":
        cultural_instruction += f"\n\nCultural Context: You are an expert with {assigned_expert['nationality']} background and cultural understanding. "
        if assigned_expert.get("cultural_context"):
            cultural_instruction += f"Focus on {assigned_expert['cultural_context']} in your response. "
        cultural_instruction += "Consider cultural nuances, traditional practices, and local perspectives relevant to your expertise area."
    
    expert_prompt = base_prompt + cultural_instruction
    
    # Apply enhanced customizations
    if expert_customization:
        customizations_applied = []
        
        # Experience level customization
        experience_level = expert_customization.get("experience_level")
        if experience_level:
            customizations_applied.append(f"Experience Level: {experience_level}")
            # Adjust the expert's experience description
            if experience_level == "Junior":
                expert_prompt = expert_prompt.replace(assigned_expert["experience"], "Junior Level")
            elif experience_level == "Mid-Level":
                expert_prompt = expert_prompt.replace(assigned_expert["experience"], "Mid-Level Professional")
            elif experience_level == "Senior":
                expert_prompt = expert_prompt.replace(assigned_expert["experience"], "Senior Level")
            elif experience_level == "Expert":
                expert_prompt = expert_prompt.replace(assigned_expert["experience"], "Expert Level")
        
        # Specialization focus
        specialization = expert_customization.get("specialization")
        if specialization:
            customizations_applied.append(f"Specialization Focus: {specialization}")
            expert_prompt += f"\n\nFocus your response specifically on: {specialization}"
        
        # Communication style
        communication_style = expert_customization.get("communication_style")
        if communication_style:
            customizations_applied.append(f"Communication Style: {communication_style}")
            if communication_style == "Gentle":
                expert_prompt += f"\n\nCommunicate in a gentle, supportive manner with empathy and understanding."
            elif communication_style == "Direct":
                expert_prompt += f"\n\nCommunicate directly and clearly, providing straightforward advice."
            elif communication_style == "Educational":
                expert_prompt += f"\n\nCommunicate in an educational manner, explaining concepts clearly."
            elif communication_style == "Professional":
                expert_prompt += f"\n\nCommunicate professionally with formal language and structured responses."
            elif communication_style == "Creative":
                expert_prompt += f"\n\nCommunicate creatively with innovative approaches and artistic perspectives."
            elif communication_style == "Analytical":
                expert_prompt += f"\n\nCommunicate analytically with detailed analysis and data-driven insights."
            elif communication_style == "Strategic":
                expert_prompt += f"\n\nCommunicate strategically with long-term planning and strategic thinking."
            elif communication_style == "Practical":
                expert_prompt += f"\n\nCommunicate practically with actionable advice and real-world solutions."
            elif communication_style == "Technical":
                expert_prompt += f"\n\nCommunicate technically with detailed technical explanations and specifications."
            elif communication_style == "Innovative":
                expert_prompt += f"\n\nCommunicate innovatively with creative solutions and forward-thinking approaches."
        
        # Years of experience
        years_experience = expert_customization.get("years_experience")
        if years_experience:
            customizations_applied.append(f"Years of Experience: {years_experience}")
            expert_prompt += f"\n\nDraw from your {years_experience} years of experience in this field."
        
        # Additional qualifications
        additional_qualifications = expert_customization.get("additional_qualifications")
        if additional_qualifications:
            customizations_applied.append(f"Additional Qualifications: {additional_qualifications}")
            expert_prompt += f"\n\nAdditional qualifications: {additional_qualifications}"
        
        # Add customization summary to prompt
        if customizations_applied:
            expert_prompt += f"\n\nApplied Customizations:"
            for custom in customizations_applied:
                expert_prompt += f"\n- {custom}"
    
    # Add expert's expertise areas
    expert_prompt += f"\n\nYour specific expertise areas include: {', '.join(assigned_expert['expertise_areas'])}"
    
    # Add instruction for concise response with key points
    expert_prompt += f"\n\nProvide a concise response with 3-5 key points that directly address the question. Focus on the most important insights and actionable advice."
    
    if context:
        expert_prompt += f"\n\n{context}"
    
    # Call the API
    try:
        print(f"Calling API for {domain} with expert: {assigned_expert['name']}")
        response = call_gemini_api(expert_prompt)
        print(f"API response received for {domain}")
        
        # Return both the response and expert details
        return {
            "response": response,
            "expert": assigned_expert,
            "domain": domain
        }
    except Exception as e:
        # Return error response with expert details and detailed logging
        import traceback
        error_details = traceback.format_exc()
        print(f"API Error in call_expert_agent for {domain}: {error_details}")
        print(f"Expert details: {assigned_expert}")
        
        error_response = f"Sorry, I encountered an error while processing your request: {str(e)}"
        return {
            "response": error_response,
            "expert": assigned_expert,
            "domain": domain
        }

def aggregate_responses(responses: Dict[str, str], user_input: str) -> str:
    """Aggregate multiple expert responses into a cohesive answer"""
    if not responses:
        return "No expert responses available."
    
    if len(responses) == 1:
        return list(responses.values())[0]
    
    # Create aggregation prompt
    expert_outputs = "\n\n".join([f"{expert}: {response}" for expert, response in responses.items()])
    
    aggregation_prompt = f"""
    You are an expert integrator. Given these domain expert reports, provide a concise, well-structured answer with key points to the user's question.
    
    User Question: {user_input}
    
    Expert Reports:
    {expert_outputs}
    
    Please synthesize these expert opinions into a clear, concise response with 3-5 key points that address the user's question while acknowledging the different perspectives provided by the experts. Focus on the most important insights and actionable recommendations.
    """
    
    return call_gemini_api(aggregation_prompt)

def generate_pdf_report(user_input: str, all_expert_responses: Dict[str, str], all_assigned_experts: Dict[str, Dict], relevant_domains: List[str], final_response: str) -> bytes:
    """Generate a PDF report of the expert panel consultation with structured tables"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1,  # Center alignment
        textColor=colors.darkblue
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        spaceBefore=20,
        textColor=colors.darkgreen
    )
    normal_style = styles['Normal']
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ])
    
    # Title
    story.append(Paragraph("Expert Panel Consultation Report", title_style))
    story.append(Spacer(1, 20))
    
    # User Question Table
    story.append(Paragraph("User Question", heading_style))
    # Wrap long text to prevent truncation
    wrapped_question = user_input
    if len(user_input) > 80:
        # Break into multiple lines for better readability
        words = user_input.split()
        lines = []
        current_line = ""
        for word in words:
            if len(current_line + " " + word) <= 80:
                current_line += " " + word if current_line else word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        wrapped_question = "\n".join(lines)
    
    question_data = [[wrapped_question]]
    question_table = Table(question_data, colWidths=[450])
    question_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('WORDWRAP', (0, 0), (-1, -1), True),
    ]))
    story.append(question_table)
    story.append(Spacer(1, 20))
    
    # Expert Summary Table
    story.append(Paragraph("Expert Panel Summary", heading_style))
    summary_data = [['Domain', 'Expert Name', 'Specialization', 'Experience', 'Key Points']]
    
    for domain in relevant_domains:
        domain_responses = {k: v for k, v in all_expert_responses.items() if k.startswith(domain)}
        domain_experts = {k: v for k, v in all_assigned_experts.items() if k.startswith(domain)}
        
        for expert_key, response in domain_responses.items():
            expert = domain_experts[expert_key]
            expert_name = expert_key.split('_')[1]
            key_points = extract_key_points(response)
            key_points_text = '\n'.join([f"• {point}" for point in key_points])
            
            # Add nationality and cultural context to expert info
            expert_info = f"{expert_name}: {expert['name']}"
            if expert.get('nationality') and expert['nationality'].lower() != 'international':
                expert_info += f" ({expert['nationality']})"
            
            summary_data.append([
                domain,
                expert_info,
                expert['specialization'],
                f"{expert['years_experience']} years",
                key_points_text
            ])
    
    # Adjust column widths for better text display - optimized for 4-word limit
    summary_table = Table(summary_data, colWidths=[60, 100, 80, 40, 200])
    summary_table.setStyle(table_style)
    story.append(summary_table)
    story.append(Spacer(1, 20))
    
    # Panel Consensus Table
    story.append(Paragraph("Panel Consensus", heading_style))
    consensus_points = extract_key_points(final_response)
    consensus_data = [['Consensus Point']]
    for point in consensus_points:
        consensus_data.append([point])
    
    consensus_table = Table(consensus_data, colWidths=[400])
    consensus_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightyellow),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('WORDWRAP', (0, 0), (-1, -1), True),
    ]))
    story.append(consensus_table)
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def extract_key_points(text: str, max_points: int = 5) -> List[str]:
    """Extract key points from expert response - limited to 4 words per sentence"""
    # Split by sentences and identify key points
    sentences = text.split('.')
    key_points = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 20:  # Only meaningful sentences
            # Look for sentences that start with key indicators
            if any(indicator in sentence.lower() for indicator in [
                'key', 'important', 'essential', 'critical', 'main', 'primary',
                'should', 'must', 'need', 'recommend', 'suggest', 'consider',
                'focus', 'emphasize', 'highlight', 'note', 'remember'
            ]):
                # Limit to 4 words maximum to prevent page overflow
                words = sentence.split()
                if len(words) > 4:
                    sentence = ' '.join(words[:4]) + "..."
                key_points.append(sentence)
            elif len(key_points) < max_points and len(sentence) > 30:
                # Add longer sentences as potential key points
                words = sentence.split()
                if len(words) > 4:
                    sentence = ' '.join(words[:4]) + "..."
                key_points.append(sentence)
    
    # If not enough key points found, take first few meaningful sentences
    if len(key_points) < 3:
        meaningful_sentences = [s.strip() for s in sentences if len(s.strip()) > 30]
        for sentence in meaningful_sentences[:max_points - len(key_points)]:
            words = sentence.split()
            if len(words) > 4:
                sentence = ' '.join(words[:4]) + "..."
            key_points.append(sentence)
    
    # Limit to max_points and clean up
    key_points = key_points[:max_points]
    key_points = [point.strip() for point in key_points if point.strip()]
    
    return key_points

def create_expert_visualization(all_assigned_experts: Dict[str, Dict], relevant_domains: List[str]):
    """Create comprehensive visualizations for expert panel"""
    # Prepare data for domain distribution
    domain_counts = {}
    for expert_key, expert in all_assigned_experts.items():
        domain = expert_key.split('_')[0]
        domain_counts[domain] = domain_counts.get(domain, 0) + 1
    
    # 1. Bar chart for domain distribution
    fig_domains = px.bar(
        x=list(domain_counts.keys()),
        y=list(domain_counts.values()),
        title="Expert Distribution by Domain",
        labels={'x': 'Domain', 'y': 'Number of Experts'},
        color=list(domain_counts.values()),
        color_continuous_scale='viridis'
    )
    fig_domains.update_layout(height=400)
    
    # 2. Pie chart for domain distribution
    fig_pie = px.pie(
        values=list(domain_counts.values()),
        names=list(domain_counts.keys()),
        title="Expert Distribution (Pie Chart)",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig_pie.update_layout(height=400)
    
    # 3. Prepare data for experience levels
    experience_data = []
    for expert_key, expert in all_assigned_experts.items():
        domain = expert_key.split('_')[0]
        expert_name = expert_key.split('_')[1]
        experience_data.append({
            'Expert': f"{expert_name}: {expert['name']}",
            'Domain': domain,
            'Years': expert['years_experience'],
            'Specialization': expert['specialization']
        })
    
    # 4. Scatter plot for experience levels
    fig_experience = px.scatter(
        experience_data,
        x='Years',
        y='Expert',
        color='Domain',
        size='Years',
        title="Expert Experience Levels",
        labels={'Years': 'Years of Experience', 'Expert': 'Expert Name'},
        hover_data=['Specialization']
    )
    fig_experience.update_layout(height=600)
    
    # 5. Experience distribution histogram
    years_list = [expert['years_experience'] for expert in all_assigned_experts.values()]
    fig_histogram = px.histogram(
        x=years_list,
        title="Experience Distribution",
        labels={'x': 'Years of Experience', 'y': 'Number of Experts'},
        nbins=10,
        color_discrete_sequence=['lightcoral']
    )
    fig_histogram.update_layout(height=400)
    
    # 6. Specialization treemap
    specialization_counts = {}
    for expert in all_assigned_experts.values():
        spec = expert['specialization']
        specialization_counts[spec] = specialization_counts.get(spec, 0) + 1
    
    fig_treemap = px.treemap(
        names=list(specialization_counts.keys()),
        parents=[''] * len(specialization_counts),
        values=list(specialization_counts.values()),
        title="Expert Specializations",
        color=list(specialization_counts.values()),
        color_continuous_scale='plasma'
    )
    fig_treemap.update_layout(height=400)
    
    # 7. Domain vs Experience box plot
    domain_experience_data = []
    for expert_key, expert in all_assigned_experts.items():
        domain = expert_key.split('_')[0]
        domain_experience_data.append({
            'Domain': domain,
            'Years': expert['years_experience']
        })
    
    fig_box = px.box(
        domain_experience_data,
        x='Domain',
        y='Years',
        title="Experience Distribution by Domain",
        labels={'Years': 'Years of Experience'},
        color='Domain'
    )
    fig_box.update_layout(height=400)
    
    return fig_domains, fig_pie, fig_experience, fig_histogram, fig_treemap, fig_box

# Sidebar: Expert Panel Configuration
st.sidebar.title("🤖 Expert Panel AI Space")

# Initialize session state for expert customizations
if "expert_customizations" not in st.session_state:
    st.session_state.expert_customizations = {}

# Initialize default variables to prevent scope issues
use_default_names = True
expert_names = {0: "Expert 1", 1: "Expert 2"}
expert_customizations = {}
chosen = []
names = {}
tone = DEFAULT_TONE
num_members_per_domain = 2

# Step 1: Domain Selection Mode
st.sidebar.subheader("🎯 Domain Selection")
domain_selection_mode = st.sidebar.radio(
    "Selection Method:",
    ["AI Auto-Select", "Manual Multi-Select"],
    help="AI selects domains or manual selection"
)

domains = list(EXPERT_CONFIGS.keys())

if domain_selection_mode == "AI Auto-Select":
    st.sidebar.info("🤖 AI selects relevant domains")
    st.sidebar.caption("Domains: " + ", ".join(domains))
    
    # AI mode - configuration will be shown after query
    chosen = []  # Will be filled by AI
    names = {}
    expert_customizations = {}
    num_members_per_domain = 2
    expert_names = {0: "Expert 1", 1: "Expert 2"}
    tone = DEFAULT_TONE
    use_default_names = True
    
    # Show basic configuration for AI mode
    st.sidebar.subheader("⚙️ Settings")
    num_members_per_domain = st.sidebar.slider(
        "Experts per domain:",
        min_value=1,
        max_value=10,
        value=2
    )
    
    tone = st.sidebar.select_slider(
        "Tone:",
        options=["Gentle", "Neutral", "Assertive"],
        value=DEFAULT_TONE
    )
    
    # Nationality and Cultural Context
    st.sidebar.subheader("🌍 Cultural Context")
    nationality = st.sidebar.selectbox(
        "Expert Nationality:",
        options=["International", "Indian", "Chinese", "Arabic", "Hispanic", "European", "Japanese", "African", "American"],
        help="Select expert nationality for cultural context awareness"
    )
    
    cultural_context = st.sidebar.text_input(
        "Cultural Focus (Optional):",
        placeholder="e.g., Traditional medicine, Local customs, Regional practices",
        help="Specify any particular cultural context or focus area"
    )
    
    st.sidebar.info("💡 Ask question → AI selects domains")

else:  # Manual Multi-Select
    st.sidebar.subheader("👥 Manual Selection")
    selected_domains = st.sidebar.multiselect(
        "Select domains:",
        options=domains,
        default=["Healthcare", "Finance"]
    )
    
    if selected_domains:
        st.sidebar.success(f"✅ {', '.join(selected_domains)}")
        
        # Calculate total available experts
        total_available = sum(len(EXPERT_CONFIGS[domain]["expert_pool"]) for domain in selected_domains)
        st.sidebar.caption(f"📊 {total_available} experts available")
        
        # Step 2: Expert Configuration
        st.sidebar.subheader("👥 Configuration")
        
        # Number of experts per domain
        num_members_per_domain = st.sidebar.slider(
            "Experts per domain:",
            min_value=1,
            max_value=10,
            value=10
        )
        
        # Expert naming
        use_default_names = st.sidebar.checkbox("Use default names", value=True)
        
        if not use_default_names:
            expert_names = {}
            for i in range(num_members_per_domain):
                default_name = f"Expert {i+1}"
                custom_name = st.sidebar.text_input(
                    f"Expert {i+1}:",
                    value=default_name,
                    key=f"custom_name_{i}"
                )
                expert_names[i] = custom_name if custom_name else default_name
        else:
            expert_names = {i: f"Expert {i+1}" for i in range(num_members_per_domain)}
        
        # Step 3: Basic Expert Customization (Simplified)
        st.sidebar.subheader("⚙️ Customization")
        
        expert_customizations = {}
        
        # Experience level for all experts
        global_experience_level = st.sidebar.selectbox(
            "Experience Level:",
            options=["Auto-Select", "Junior", "Mid-Level", "Senior", "Expert"]
        )
        
        # Communication style for all experts
        global_communication_style = st.sidebar.selectbox(
            "Communication Style:",
            options=["Auto-Select", "Gentle", "Direct", "Educational", "Professional", "Analytical", "Practical"]
        )
        
        # Store global customizations
        for domain in selected_domains:
            domain_customizations = {}
            for i in range(num_members_per_domain):
                expert_name = expert_names[i]
                domain_customizations[expert_name] = {
                    "experience_level": global_experience_level if global_experience_level != "Auto-Select" else None,
                    "communication_style": global_communication_style if global_communication_style != "Auto-Select" else None,
                    "specialization": None,
                    "years_experience": None,
                    "additional_qualifications": None
                }
            expert_customizations[domain] = domain_customizations
        
        # Step 4: Panel Tone
        st.sidebar.subheader("🎭 Tone")
        tone = st.sidebar.select_slider(
            "Style:",
            options=["Gentle", "Neutral", "Assertive"],
            value=DEFAULT_TONE
        )
        
        # Step 5: Cultural Context
        st.sidebar.subheader("🌍 Cultural Context")
        nationality = st.sidebar.selectbox(
            "Expert Nationality:",
            options=["International", "Indian", "Chinese", "Arabic", "Hispanic", "European", "Japanese", "African", "American"],
            help="Select expert nationality for cultural context awareness"
        )
        
        cultural_context = st.sidebar.text_input(
            "Cultural Focus (Optional):",
            placeholder="e.g., Traditional medicine, Local customs, Regional practices",
            help="Specify any particular cultural context or focus area"
        )
        
        # Step 6: Panel Configuration Summary
        st.sidebar.subheader("📋 Summary")
        st.sidebar.markdown(f"**Domains:** {', '.join(selected_domains)}")
        st.sidebar.markdown(f"**Experts/Domain:** {num_members_per_domain}")
        st.sidebar.markdown(f"**Tone:** {tone}")
        
        # Show customization summary
        has_customizations = (global_experience_level != "Auto-Select" or global_communication_style != "Auto-Select")
        if has_customizations:
            st.sidebar.markdown("**Customizations:**")
            if global_experience_level != "Auto-Select":
                st.sidebar.caption(f"• Level: {global_experience_level}")
            if global_communication_style != "Auto-Select":
                st.sidebar.caption(f"• Style: {global_communication_style}")
        
        # Store configuration for manual mode
        chosen = selected_domains
        names = {domain: f"{domain} Panel" for domain in selected_domains}
        
        # Show available experts for selected domains
        with st.sidebar.expander(f"👥 View Available Experts", expanded=False):
            for domain in selected_domains:
                config = EXPERT_CONFIGS[domain]
                st.markdown(f"**{config['avatar']} {domain}** ({len(config['expert_pool'])} experts)")
                for expert in config["expert_pool"][:2]:  # Show first 2
                    st.caption(f"• {expert['name']} - {expert['specialization']}")
                if len(config["expert_pool"]) > 2:
                    st.caption(f"  ... and {len(config['expert_pool']) - 2} more")
                st.divider()
    
    else:
        # Default configuration when no domains are selected
        chosen = DEFAULT_EXPERTS
        names = {d: d for d in chosen}
        tone = DEFAULT_TONE
        expert_customizations = {}
        num_members_per_domain = 2
        expert_names = {0: "Expert 1", 1: "Expert 2"}
        use_default_names = True
        st.sidebar.warning("Please select at least one domain.")

# Main Chat Interface
st.title("🤖 Expert Panel AI Space")

# Display current panel configuration
if domain_selection_mode == "AI Auto-Select":
    st.markdown("## 🤖 AI Auto-Select Mode")
    
    # Panel configuration display
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Mode", "AI Auto-Select")
    with col2:
        st.metric("Experts/Domain", num_members_per_domain)
    with col3:
        st.metric("Available", len(domains))
    with col4:
        st.metric("Tone", tone)

elif domain_selection_mode == "Manual Multi-Select" and chosen:
    st.markdown("## 📋 Expert Panel")
    
    # Panel configuration display
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Domains", len(chosen))
    with col2:
        st.metric("Experts/Domain", num_members_per_domain)
    with col3:
        total_experts = sum(len(EXPERT_CONFIGS[domain]["expert_pool"]) for domain in chosen)
        st.metric("Total Experts", total_experts)
    with col4:
        st.metric("Tone", tone)
    
    # Show selected domains
    st.markdown("### 🎯 Selected Domains:")
    domain_cols = st.columns(min(len(chosen), 3))
    for i, domain in enumerate(chosen):
        config = EXPERT_CONFIGS[domain]
        col_idx = i % 3
        
        with domain_cols[col_idx]:
            st.markdown(f"**{config['avatar']} {domain}**")
            st.caption(f"{len(config['expert_pool'])} experts")

else:
    st.info("👈 Configure panel in sidebar")
    st.markdown("### Available Domains:")
    
    # Show all available domains
    domain_cols = st.columns(4)
    for i, domain in enumerate(domains):
        config = EXPERT_CONFIGS[domain]
        col_idx = i % 4
        
        with domain_cols[col_idx]:
            st.markdown(f"**{config['avatar']} {domain}**")
            st.caption(f"{len(config['expert_pool'])} experts")

# Show all available panel members with expert counts and qualifications
with st.expander("📋 View All Available Panel Members", expanded=False):
    st.markdown("**Complete Expert Panel Directory:**")
    
    # Panel statistics
    total_domains = len(EXPERT_CONFIGS)
    total_experts = sum(len(config["expert_pool"]) for config in EXPERT_CONFIGS.values())
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Domains", total_domains)
    with col2:
        st.metric("Total Experts", total_experts)
    with col3:
        st.metric("Avg Experts/Domain", round(total_experts/total_domains, 1))
    
    st.divider()
    
    # Create a grid layout for all experts
    all_experts = list(EXPERT_CONFIGS.keys())
    expert_cols = st.columns(2)
    
    for i, domain in enumerate(all_experts):
        config = EXPERT_CONFIGS[domain]
        col_idx = i % 2
        
        with expert_cols[col_idx]:
            st.markdown(f"### {config['avatar']} {domain}")
            st.caption(f"**{len(config['expert_pool'])} Available Experts**")
            st.write(config['description'])
            
            # Show expert pool summary
            with st.expander(f"👥 View {len(config['expert_pool'])} Experts", expanded=False):
                for expert in config['expert_pool']:
                    st.markdown(f"**{expert['name']}**")
                    st.caption(f"• {expert['qualifications']}")
                    st.caption(f"• {expert['specialization']} ({expert['years_experience']} years)")
                    st.caption(f"• Expertise: {', '.join(expert['expertise_areas'][:2])}")
                    if len(expert['expertise_areas']) > 2:
                        st.caption(f"  ... and {len(expert['expertise_areas']) - 2} more areas")
                    st.divider()
            
            # Show specializations
            st.markdown("**Available Specializations:**")
            for spec in config['specializations'][:3]:  # Show first 3
                st.caption(f"• {spec}")
            if len(config['specializations']) > 3:
                st.caption(f"• ... and {len(config['specializations']) - 3} more")
            
            # Show experience levels
            st.markdown("**Experience Levels:**")
            for exp in config['experience_levels'][:2]:  # Show first 2
                st.caption(f"• {exp}")
            if len(config['experience_levels']) > 2:
                st.caption(f"• ... and {len(config['experience_levels']) - 2} more")
            
            st.divider()

# Chat history
for message in st.session_state.history:
    if message["role"] == "user":
        st.chat_message("user").write(message["content"])
    else:
        st.chat_message("assistant").write(message["content"])

# Chat input
if user_input := st.chat_input("Ask your question..."):
    # Add user message to history
    st.session_state.history.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)
    
    # Check if panel is configured
    if domain_selection_mode == "AI Auto-Select" or (domain_selection_mode == "Manual Multi-Select" and chosen):
        # Show processing status
        with st.spinner("🤖 Consulting your expert panel..."):
            try:
                # Step 1: Determine domains to consult
                if domain_selection_mode == "AI Auto-Select":
                    # AI determines relevant domains
                    relevant_domains = supervisor_route(user_input, domains, tone, {})
                    st.info(f"🤖 AI selected domains: {', '.join(relevant_domains)}")
                    
                    # Use basic configuration for AI mode (no complex UI)
                    st.success("✅ Using basic configuration for AI-selected domains.")
                    
                    # Step 2: Get expert responses from each domain
                    all_expert_responses = {}
                    all_assigned_experts = {}
                    
                    # Create progress bar for expert responses
                    total_experts = len(relevant_domains) * num_members_per_domain
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    expert_counter = 0
                    used_experts_per_domain = {}  # Track used experts per domain
                    used_names_per_domain = {}  # Track used names per domain
                    
                    for domain in relevant_domains:
                        status_text.text(f"Consulting {domain} experts...")
                        used_experts_per_domain[domain] = set()  # Initialize for this domain
                        used_names_per_domain[domain] = set()  # Initialize for this domain
                        
                        # Get multiple experts from this domain
                        for i in range(num_members_per_domain):
                            expert_name = expert_names[i]
                            status_text.text(f"Consulting {expert_name} from {domain}...")
                            
                            # Get customizations for this expert
                            expert_customization = None
                            if domain in expert_customizations and expert_name in expert_customizations[domain]:
                                expert_customization = expert_customizations[domain][expert_name]
                            
                            try:
                                result = call_expert_agent(
                                    domain, 
                                    user_input, 
                                    tone, 
                                    st.session_state.history,
                                    expert_customization,
                                    used_experts_per_domain[domain],  # used_experts
                                    nationality,  # nationality
                                    cultural_context,  # cultural_context
                                    used_names_per_domain[domain]  # used_names
                                )
                                
                                # Create unique key for each expert
                                expert_key = f"{domain}_{expert_name}"
                                all_expert_responses[expert_key] = result["response"]
                                all_assigned_experts[expert_key] = result["expert"]
                                
                                # Track the used expert and name
                                used_experts_per_domain[domain].add(result["expert"]["name"])
                                used_names_per_domain[domain].add(result["expert"]["name"])
                                
                            except Exception as e:
                                # Handle error for this specific expert
                                st.error(f"Error consulting {expert_name} from {domain}: {str(e)}")
                                # Create a fallback response
                                expert_key = f"{domain}_{expert_name}"
                                all_expert_responses[expert_key] = f"Sorry, {expert_name} encountered an error: {str(e)}"
                                # Generate a fallback expert dynamically
                                fallback_expert = generate_dynamic_expert(domain, len(used_experts_per_domain[domain]) + 1, nationality, cultural_context, used_names_per_domain[domain])
                                all_assigned_experts[expert_key] = fallback_expert
                                # Track the fallback expert and name
                                used_experts_per_domain[domain].add(fallback_expert["name"])
                                used_names_per_domain[domain].add(fallback_expert["name"])
                            
                            expert_counter += 1
                            progress_bar.progress(expert_counter / total_experts)
                    
                    status_text.text("Synthesizing expert responses...")
                    
                    # Step 3: Aggregate responses
                    final_response = aggregate_responses(all_expert_responses, user_input)
                    
                    # Clear progress indicators
                    progress_bar.empty()
                    status_text.empty()
                    
                    # Display expert panel responses
                    st.markdown("## 🤖 Expert Panel Responses")
                    
                    # Create visualizations
                    fig_domains, fig_pie, fig_experience, fig_histogram, fig_treemap, fig_box = create_expert_visualization(all_assigned_experts, relevant_domains)
                    
                    # Display comprehensive visualizations
                    st.subheader("📊 Expert Panel Analytics")
                    
                    # Row 1: Domain Distribution
                    col1, col2 = st.columns(2)
                    with col1:
                        st.plotly_chart(fig_domains, use_container_width=True)
                    with col2:
                        st.plotly_chart(fig_pie, use_container_width=True)
                    
                    # Row 2: Experience Analysis
                    col3, col4 = st.columns(2)
                    with col3:
                        st.plotly_chart(fig_experience, use_container_width=True)
                    with col4:
                        st.plotly_chart(fig_histogram, use_container_width=True)
                    
                    # Row 3: Specialization and Box Plot
                    col5, col6 = st.columns(2)
                    with col5:
                        st.plotly_chart(fig_treemap, use_container_width=True)
                    with col6:
                        st.plotly_chart(fig_box, use_container_width=True)

# Group responses by domain
                    for domain in relevant_domains:
                        st.markdown(f"### {EXPERT_CONFIGS[domain]['avatar']} {domain}")
                        
                        # Get responses for this domain
                        domain_responses = {k: v for k, v in all_expert_responses.items() if k.startswith(domain)}
                        domain_experts = {k: v for k, v in all_assigned_experts.items() if k.startswith(domain)}
                        
                        # Create columns for domain experts
                        if len(domain_responses) <= 2:
                            response_cols = st.columns(len(domain_responses))
                        else:
                            response_cols = st.columns(2)
                        
                        for i, (expert_key, response) in enumerate(domain_responses.items()):
                            assigned_expert = domain_experts[expert_key]
                            config = EXPERT_CONFIGS[domain]
                            expert_name = expert_key.split('_')[1]
                            
                            # Determine column for display
                            if len(domain_responses) <= 2:
                                col_idx = i
                            else:
                                col_idx = i % 2
                            
                            with response_cols[col_idx]:
                                # Expert panel card
                                with st.container():
                                    st.markdown(f"#### {expert_name}")
                                    st.markdown(f"**{assigned_expert['name']}**")
                                    st.caption(f"*{assigned_expert['qualifications']}*")
                                    st.caption(f"**{assigned_expert['specialization']}** ({assigned_expert['years_experience']} years)")
                                    
                                    # Expert response
                                    st.markdown("**Response:**")
                                    st.write(response)
                                    
                                    # Expertise areas
                                    st.caption("**Expertise:** " + ", ".join(assigned_expert['expertise_areas'][:2]))
                                    if len(assigned_expert['expertise_areas']) > 2:
                                        st.caption(f"... and {len(assigned_expert['expertise_areas']) - 2} more areas")
                        
                        st.divider()
                    
                    # Display aggregated response
                    st.markdown("## 📋 Panel Consensus")
                    st.chat_message("assistant").write(final_response)
                    
                    # Generate and offer PDF download
                    pdf_bytes = generate_pdf_report(user_input, all_expert_responses, all_assigned_experts, relevant_domains, final_response)
                    
                    st.markdown("### 📄 Download Report")
                    st.download_button(
                        label="📥 Download PDF Report",
                        data=pdf_bytes,
                        file_name=f"expert_panel_report_{time.strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf"
                    )
                    
                    # Show expert assignment summary
                    st.caption("**🤖 Expert Assignment Summary:**")
                    for domain in relevant_domains:
                        domain_experts = {k: v for k, v in all_assigned_experts.items() if k.startswith(domain)}
                        for expert_key, expert in domain_experts.items():
                            expert_name = expert_key.split('_')[1]
                            st.caption(f"• {domain}: {expert_name} → {expert['name']} ({expert['specialization']})")
                    
                    st.session_state.history.append({"role": "assistant", "content": final_response})
                
                else:  # Manual Multi-Select mode
                    # Use manually selected domains
                    relevant_domains = chosen
                    
                    # Step 2: Get expert responses from each domain
                    all_expert_responses = {}
                    all_assigned_experts = {}
                    
                    # Create progress bar for expert responses
                    total_experts = len(relevant_domains) * num_members_per_domain
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    expert_counter = 0
                    used_experts_per_domain = {}  # Track used experts per domain
                    used_names_per_domain = {}  # Track used names per domain
                    
                    for domain in relevant_domains:
                        status_text.text(f"Consulting {domain} experts...")
                        used_experts_per_domain[domain] = set()  # Initialize for this domain
                        used_names_per_domain[domain] = set()  # Initialize for this domain
                        
                        # Get multiple experts from this domain
                        for i in range(num_members_per_domain):
                            expert_name = expert_names[i]
                            status_text.text(f"Consulting {expert_name} from {domain}...")
                            
                            # Get customizations for this expert
                            expert_customization = None
                            if domain in expert_customizations and expert_name in expert_customizations[domain]:
                                expert_customization = expert_customizations[domain][expert_name]
                            
                            try:
                                result = call_expert_agent(
                                    domain, 
                                    user_input, 
                                    tone, 
                                    st.session_state.history,
                                    expert_customization,
                                    used_experts_per_domain[domain],  # used_experts
                                    nationality,  # nationality
                                    cultural_context,  # cultural_context
                                    used_names_per_domain[domain]  # used_names
                                )
                                
                                # Create unique key for each expert
                                expert_key = f"{domain}_{expert_name}"
                                all_expert_responses[expert_key] = result["response"]
                                all_assigned_experts[expert_key] = result["expert"]
                                
                                # Track the used expert and name
                                used_experts_per_domain[domain].add(result["expert"]["name"])
                                used_names_per_domain[domain].add(result["expert"]["name"])
                                
                            except Exception as e:
                                # Handle error for this specific expert
                                st.error(f"Error consulting {expert_name} from {domain}: {str(e)}")
                                # Create a fallback response
                                expert_key = f"{domain}_{expert_name}"
                                all_expert_responses[expert_key] = f"Sorry, {expert_name} encountered an error: {str(e)}"
                                # Generate a fallback expert dynamically
                                fallback_expert = generate_dynamic_expert(domain, len(used_experts_per_domain[domain]) + 1, nationality, cultural_context, used_names_per_domain[domain])
                                all_assigned_experts[expert_key] = fallback_expert
                                # Track the fallback expert and name
                                used_experts_per_domain[domain].add(fallback_expert["name"])
                                used_names_per_domain[domain].add(fallback_expert["name"])
                            
                            expert_counter += 1
                            progress_bar.progress(expert_counter / total_experts)
                    
                    status_text.text("Synthesizing expert responses...")
                    
                    # Step 3: Aggregate responses
                    final_response = aggregate_responses(all_expert_responses, user_input)
                    
                    # Clear progress indicators
                    progress_bar.empty()
                    status_text.empty()
                    
                    # Display expert panel responses
                    st.markdown("## 🤖 Expert Panel Responses")
                    
                    # Create visualizations
                    fig_domains, fig_pie, fig_experience, fig_histogram, fig_treemap, fig_box = create_expert_visualization(all_assigned_experts, relevant_domains)
                    
                    # Display comprehensive visualizations
                    st.subheader("📊 Expert Panel Analytics")
                    
                    # Row 1: Domain Distribution
                    col1, col2 = st.columns(2)
                    with col1:
                        st.plotly_chart(fig_domains, use_container_width=True)
                    with col2:
                        st.plotly_chart(fig_pie, use_container_width=True)
                    
                    # Row 2: Experience Analysis
                    col3, col4 = st.columns(2)
                    with col3:
                        st.plotly_chart(fig_experience, use_container_width=True)
                    with col4:
                        st.plotly_chart(fig_histogram, use_container_width=True)
                    
                    # Row 3: Specialization and Box Plot
                    col5, col6 = st.columns(2)
                    with col5:
                        st.plotly_chart(fig_treemap, use_container_width=True)
                    with col6:
                        st.plotly_chart(fig_box, use_container_width=True)

# Group responses by domain
                    for domain in relevant_domains:
                        st.markdown(f"### {EXPERT_CONFIGS[domain]['avatar']} {domain}")
                        
                        # Get responses for this domain
                        domain_responses = {k: v for k, v in all_expert_responses.items() if k.startswith(domain)}
                        domain_experts = {k: v for k, v in all_assigned_experts.items() if k.startswith(domain)}
                        
                        # Create columns for domain experts
                        if len(domain_responses) <= 2:
                            response_cols = st.columns(len(domain_responses))
                        else:
                            response_cols = st.columns(2)
                        
                        for i, (expert_key, response) in enumerate(domain_responses.items()):
                            assigned_expert = domain_experts[expert_key]
                            config = EXPERT_CONFIGS[domain]
                            expert_name = expert_key.split('_')[1]
                            
                            # Determine column for display
                            if len(domain_responses) <= 2:
                                col_idx = i
                            else:
                                col_idx = i % 2
                            
                            with response_cols[col_idx]:
                                # Expert panel card
                                with st.container():
                                    st.markdown(f"#### {expert_name}")
                                    st.markdown(f"**{assigned_expert['name']}**")
                                    st.caption(f"*{assigned_expert['qualifications']}*")
                                    st.caption(f"**{assigned_expert['specialization']}** ({assigned_expert['years_experience']} years)")
                                    
                                    # Show customizations if applied
                                    if domain in expert_customizations and expert_name in expert_customizations[domain]:
                                        custom = expert_customizations[domain][expert_name]
                                        if any(custom.values()):
                                            st.caption("**Applied Customizations:**")
                                            if custom.get("experience_level"):
                                                st.caption(f"• Level: {custom['experience_level']}")
                                            if custom.get("specialization"):
                                                st.caption(f"• Focus: {custom['specialization']}")
                                            if custom.get("communication_style"):
                                                st.caption(f"• Style: {custom['communication_style']}")
                                            if custom.get("additional_qualifications"):
                                                st.caption(f"• Additional: {custom['additional_qualifications']}")
                                    
                                    # Expert response
                                    st.markdown("**Response:**")
                                    st.write(response)
                                    
                                    # Expertise areas
                                    st.caption("**Expertise:** " + ", ".join(assigned_expert['expertise_areas'][:2]))
                                    if len(assigned_expert['expertise_areas']) > 2:
                                        st.caption(f"... and {len(assigned_expert['expertise_areas']) - 2} more areas")
                        
                        st.divider()
                    
                    # Display aggregated response
                    st.markdown("## 📋 Panel Consensus")
                    st.chat_message("assistant").write(final_response)
                    
                    # Generate and offer PDF download
                    pdf_bytes = generate_pdf_report(user_input, all_expert_responses, all_assigned_experts, relevant_domains, final_response)
                    
                    st.markdown("### 📄 Download Report")
                    st.download_button(
                        label="📥 Download PDF Report",
                        data=pdf_bytes,
                        file_name=f"expert_panel_report_{time.strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf"
                    )
                    
                    # Show expert assignment summary
                    st.caption("**🤖 Expert Assignment Summary:**")
                    for domain in relevant_domains:
                        domain_experts = {k: v for k, v in all_assigned_experts.items() if k.startswith(domain)}
                        for expert_key, expert in domain_experts.items():
                            expert_name = expert_key.split('_')[1]
                            st.caption(f"• {domain}: {expert_name} → {expert['name']} ({expert['specialization']})")
                    
                    st.session_state.history.append({"role": "assistant", "content": final_response})
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.session_state.history.append({"role": "assistant", "content": f"Sorry, an error occurred while processing your request: {str(e)}"})
    
    else:
        st.error("Please configure your expert panel first (select domains and settings).")

# Sidebar footer
st.sidebar.divider()
st.sidebar.markdown("**Actions:**")

# Clear chat button
if st.sidebar.button("🗑️ Clear Chat"):
    st.session_state.history = []
    st.rerun()

# Reset panel configuration
if st.sidebar.button("🔄 Reset"):
    st.session_state.history = []
    st.session_state.expert_customizations = {}
    st.rerun()

st.sidebar.divider()
st.sidebar.markdown("**About:**")
st.sidebar.markdown("Expert panel chatbot with AI domain selection and PDF reports.") 