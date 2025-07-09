import os
from dotenv import load_dotenv
import sys

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


load_dotenv()
WORKDIR=os.getenv("WORKDIR")
os.chdir(WORKDIR)
sys.path.append(WORKDIR)

from langchain_core.tools import tool
from src.validators.agent_validators import *
from typing import  Literal
import pandas as pd
import json
from src.vector_database.main import PineconeManagment
from src.utils import format_retrieved_docs

pinecone_conn = PineconeManagment()
pinecone_conn.loading_vdb(index_name = 'textbook')
retriever = pinecone_conn.vdb.as_retriever(search_type="similarity", 
                                    search_kwargs={"k": 3, "score_threshold": 0.0})
rag_chain = retriever | format_retrieved_docs

@tool
def check_availability_by_doctor(desired_date:DateModel, doctor_name:Literal["john doe","emily johnson",\
                                                        "jane smith","lisa brown","michael green",\
                                                            "sarah wilson","daniel miller","susan davis",\
                                                                "robert martinez","kevin anderson","James Hahn",\
                                                                    "Destiny Williams","Kara Shaffer","Christopher Holden","Terry Cooper","Cassie Andrade"]):
    """
    Checking the database if we have availability for the specific doctor.
    The parameters should be mentioned by the user in the query
    """
    
    df = pd.read_csv(f"{WORKDIR}/data/synthetic_data/availability.csv")
    df['date_slot_time'] = df['date_slot'].apply(lambda input: input.split(' ')[-1])
    rows = list(df[(df['date_slot'].apply(lambda input: input.split(' ')[0]) == desired_date.date)&(df['doctor_name'] == doctor_name)&(df['is_available'] == True)]['date_slot_time'])

    if len(rows) == 0:
        output = "No availability in the entire day"
    else:
        output = f'This availability for {desired_date.date}\n'
        output += "Available slots: " + ', '.join(rows)

    return output

@tool
def check_availability_by_specialization(desired_date:DateModel, specialization:Literal["dentists","Cardiologist","Neurologist,Dermatologist",\
                                                                                        "Orthopedic_Surgeon","Pediatrician","Oncologist",\
                                                                                            "Otolaryngologist","Radiologist","Gastroenterologist","Psychiatrist"]):
    """
    Checking the database if we have availability for the specific specialization.
    The parameters should be mentioned by the user in the query
    """
    
    df = pd.read_csv(f"{WORKDIR}/data/synthetic_data/availability.csv")
    df['date_slot_time'] = df['date_slot'].apply(lambda input: input.split(' ')[-1])
    rows = df[(df['date_slot'].apply(lambda input: input.split(' ')[0]) == desired_date.date) & (df['specialization'] == specialization) & (df['is_available'] == True)].groupby(['specialization', 'doctor_name'])['date_slot_time'].apply(list).reset_index(name='available_slots')

    if len(rows) == 0:
        output = "No availability in the entire day"
    else:
        output = f'This availability for {desired_date.date}\n'
        for row in rows.values:
            output += row[1] + ". Available slots: " + ', '.join(row[2])+'\n'

    return output

@tool
def reschedule_appointment(old_date:DateTimeModel, new_date:DateTimeModel, id_number:IdentificationNumberModel,doctor_name:Literal["john doe","emily johnson",\
                                                        "jane smith","lisa brown","michael green",\
                                                            "sarah wilson","daniel miller","susan davis",\
                                                                "robert martinez","kevin anderson","James Hahn",\
                                                                    "Destiny Williams","Kara Shaffer","Christopher Holden","Terry Cooper","Cassie Andrade"]):
    """
    Rescheduling an appointment.
    The parameters MUST be mentioned by the user in the query.
    """
    
    df = pd.read_csv(f'{WORKDIR}/data/synthetic_data/availability.csv')
    available_for_desired_date = df[(df['date_slot'] == new_date.date)&(df['is_available'] == True)&(df['doctor_name'] == doctor_name)]
    if len(available_for_desired_date) == 0:
        return "Not available slots in the desired period"
    else:
        cancel_appointment.invoke({'date':old_date, 'id_number':id_number, 'doctor_name':doctor_name})
        set_appointment.invoke({'desired_date':new_date, 'id_number': id_number, 'doctor_name': doctor_name})
        return "Succesfully rescheduled for the desired time"

@tool
def cancel_appointment(date:DateTimeModel, id_number:IdentificationNumberModel, doctor_name:Literal["john doe","emily johnson",\
                                                        "jane smith","lisa brown","michael green",\
                                                            "sarah wilson","daniel miller","susan davis",\
                                                                "robert martinez","kevin anderson","James Hahn",\
                                                                    "Destiny Williams","Kara Shaffer","Christopher Holden","Terry Cooper","Cassie Andrade"]):
    """
    Canceling an appointment.
    The parameters MUST be mentioned by the user in the query.
    """
    df = pd.read_csv(f'{WORKDIR}/data/synthetic_data/availability.csv')
    case_to_remove = df[(df['date_slot'] == date.date)&(df['patient_to_attend'] == id_number.id)&(df['doctor_name'] == doctor_name)]
    if len(case_to_remove) == 0:
        return "You don´t have any appointment with that specifications"
    else:
        df.loc[(df['date_slot'] == date.date) & (df['patient_to_attend'] == id_number.id) & (df['doctor_name'] == doctor_name), ['is_available', 'patient_to_attend']] = [True, None]
        df.to_csv(f'{WORKDIR}/data/synthetic_data/availability.csv', index = False)

        return "Succesfully cancelled"

@tool
def get_catalog_specialists():
    """
    Obtain information about the doctors and specializations/services we provide.
    The parameters MUST be mentioned by the user in the query
    """
    with open(f"{WORKDIR}/data/catalog.json","r") as file:
        file = json.loads(file.read())
    
    return file

@tool
def set_appointment(desired_date:DateTimeModel, id_number:IdentificationNumberModel, doctor_name:Literal["john doe","emily johnson",\
                                                        "jane smith","lisa brown","michael green",\
                                                            "sarah wilson","daniel miller","susan davis",\
                                                                "robert martinez","kevin anderson","James Hahn",\
                                                                    "Destiny Williams","Kara Shaffer","Christopher Holden","Terry Cooper","Cassie Andrade"]):
    """
    Set appointment with the doctor.
    The parameters MUST be mentioned by the user in the query.
    """
    df = pd.read_csv(f'{WORKDIR}/data/synthetic_data/availability.csv')
    case = df[(df['date_slot'] == desired_date.date)&(df['doctor_name'] == doctor_name)&(df['is_available'] == True)]
    if len(case) == 0:
        return "No available appointments for that particular case"
    else:
        df.loc[(df['date_slot'] == desired_date.date)&(df['doctor_name'] == doctor_name) & (df['is_available'] == True), ['is_available','patient_to_attend']] = [False, id_number.id]

        df.to_csv(f'{WORKDIR}/data/synthetic_data/availability.csv', index = False)

        return "Succesfully done"

@tool
def check_results(id_number:IdentificationNumberModel):
    """
    Check if the result of the pacient is available.
    The parameters MUST be mentioned by the user in the query
    """
    
    df = pd.read_csv(f'{WORKDIR}/data/synthetic_data/studies_status.csv')
    rows = df[(df['patient_id'] == id_number.id)][['medical_study','is_available']]
    if len(rows) == 0:
        return "The patient doesn´t have any study made"
    else:
        return rows

@tool
def reminder_appointment(id_number:IdentificationNumberModel):
    """
    Returns when the pacient has its appointment with the doctor
    The parameters MUST be mentioned by the user in the query
    """
    df = pd.read_csv(f'{WORKDIR}/data/synthetic_data/availability.csv')
    rows = df[(df['patient_to_attend'] == id_number.id)][['time_slot','doctor_name','specialization']]
    if len(rows) == 0:
        return "The patient doesn´t have any appointment yet"
    else:
        return rows


@tool
def retrieve_faq_info(question: str):
    """
    Return the top 5 matching textbook chunks (with cosine score and chunk ID),
    then append the medical‐advice disclaimer.
    """

    logger.info(f"🔍 retrieve_faq_info called with question={question!r}")
    print(f"[DEBUG] Calling vector DB for question: {question!r}")

    results = pinecone_conn.vdb.similarity_search_with_relevance_scores(
        query=question,
        k=3,
        score_threshold=0.0
    )
    logger.info(f"   → tool got {len(results)} results")
    print(f"[DEBUG] raw results count: {len(results)}")

    if not results:
        return "Sorry, I couldn’t find anything on that topic."

    lines = []
    for i, (doc, score) in enumerate(results, start=1):
        chunk = doc.metadata.get("chunk", "n/a")
        snippet = doc.page_content.replace("\n", " ")
        if len(snippet) > 200:
            snippet = snippet[:200] + "…"
        lines.append(f"Result {i} (score={score:.4f}, chunk={chunk}):\n{snippet}\n")

    output = "\n".join(lines)
    output += "\n⚠️ This information is for reference only and not a substitute for professional medical advice."
    return output

@tool
def obtain_specialization_by_doctor(doctor_name:Literal["john doe","emily johnson",\
                                                        "jane smith","lisa brown","michael green",\
                                                            "sarah wilson","daniel miller","susan davis",\
                                                                "robert martinez","kevin anderson","James Hahn",\
                                                                    "Destiny Williams","Kara Shaffer","Christopher Holden","Terry Cooper","Cassie Andrade"]):
    """
    Retrieve which specialization covers a specific doctor.
    Use this internal tool if you need more information about a doctor for setting an appointment.
    """
    with open(f"{WORKDIR}/data/catalog.json","r") as file:
        catalog = json.loads(file.read())

    return str([{specialization['specialization']: [dentist['name'] for dentist in specialization['dentists']]} for specialization in catalog])

@tool
def get_department_location(department_name: str):
    """
    Returns the floor and building location for a specific hospital department.
    Example: 'Cardiology', 'Radiology', etc.
    """
    with open(f"{WORKDIR}/data/departments.json", "r") as file:
        departments = json.load(file)
    
    for dept in departments:
        if dept["name"].lower() == department_name.lower():
            return f"The {dept['name']} department is located on floor {dept['floor_number']} in {dept['building']}."
    
    return "Sorry, I couldn't find that department in our directory."

from typing import Optional
@tool
def get_patient_info(
    id_number: Optional[int] = None,
    full_name: Optional[str] = None,
    date_of_birth: Optional[str] = None   # format: '1977-02-14'
):
    """
    Look up a patient.

    Provide *either*:
      • id_number
      • or full_name + date_of_birth  (exact, case-insensitive name match)

    Returns JSON with id_number, name, dob, and sex.
    """

    df = pd.read_csv(f"{WORKDIR}/data/synthetic_data/patients_info.csv")

    if id_number is not None:
        hits = df[df["id_number"] == id_number]

    elif full_name is not None:
        if date_of_birth is None:
            return (
                "Please provide the date of birth as well, so I can find the "
                "correct record for that name."
            )
        name_mask = df["name"].str.lower() == full_name.lower()
        dob_mask  = df["birth_date"] == date_of_birth
        hits      = df[name_mask & dob_mask]

    else:
        return "Please supply either an ID number *or* a full name with DOB."

    if hits.empty:
        return "Sorry, I couldn’t find a matching record."

    rec = hits.iloc[0]
    return {
        "id_number": int(rec["id_number"]),
        "name":      rec["name"],
        "dob":       rec["birth_date"],
        "sex":       rec["sex"],
    }