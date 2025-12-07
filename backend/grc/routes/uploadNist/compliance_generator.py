"""
Compliance and Risk Records Generator

This module generates compliance and risk records from Excel files containing subpolicy data.
It uses OpenAI's language models via LangChain to create detailed compliance and risk records.

Usage:
    1. As a standalone script:
        python text_generate.py
    
    2. As an imported module in other scripts:
        from text_generate import generate_compliance_and_risk
        
        compliance, risk, comp_file, risk_file = generate_compliance_and_risk(
            excel_file_path="input.xlsx",
            output_prefix="output",
            output_dir="output_folder"
        )

Functions:
    - generate_compliance_and_risk(): Main function to generate records (can be called from other scripts)
    - process_excel_data(): Process Excel data and generate records
    - setup_llm_chain(): Setup LangChain with OpenAI
    - load_excel_data(): Load data from Excel file
    - save_results(): Save results to Excel files
    - main(): CLI entry point for standalone usage

Requirements:
    - OPENAI_API_KEY must be set in environment variables or .env file
    - Input Excel file must contain: SubPolicyId, SubPolicyName, Description, Control columns
"""

import os
import pandas as pd
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from dotenv import load_dotenv
import json
from datetime import datetime
 
# Use Django settings for OpenAI API key
from django.conf import settings

def get_api_key():
    """Get OpenAI API key from Django settings"""
    api_key = getattr(settings, 'OPENAI_API_KEY', None)
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found in Django settings. "
            "Please set it in .env file and restart Django server."
        )
    return api_key
 
def load_excel_data(file_path):
    """Load data from Excel file"""
    try:
        df = pd.read_excel(file_path)
        return df
    except Exception as e:
        print(f"Error loading Excel file: {e}")
        return None
 
def setup_llm_chain(api_key=None):
    """Set up LangChain with OpenAI"""
    if api_key is None:
        api_key = get_api_key()
    
    # Initialize the LLM
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.3,
        openai_api_key=api_key
    )
   
    # Define the prompt template
    template = """
    You are a compliance expert that generates detailed compliance and risk records for policies.
   
    Based on the following subpolicy information:
    - Subpolicy Name: {SubPolicyName}
    - Description: {Description}
    - Control: {Control}
   
    Generate 1-3 different compliance records that would be relevant for this subpolicy. Each compliance should cover different aspects or requirements of the subpolicy.
    For each compliance record, also generate associated risk information.
   
    Provide the following information in valid JSON format:
   
    {{
        "compliances": [
            {{
                "Identifier": "Unique identifier code for this compliance (e.g., COMP-001)",
                "ComplianceTitle": "Clear, specific title for the compliance requirement",
                "ComplianceItemDescription": "Detailed description of what needs to be complied with",
                "ComplianceType": "One of: Regulatory, Internal, Industry Standard, Legal, Operational",
                "Scope": "Description of what/who this compliance applies to",
                "Objective": "What this compliance aims to achieve",
                "BusinessUnitsCovered": "Which business units this applies to",
                "IsRisk": 1,
                "PossibleDamage": "Description of potential damage if not complied with",
                "mitigation": {{"1": "first mitigation strategy", "2": "second mitigation strategy", "3": "third mitigation strategy"}},
                "Criticality": "One of: Low, Medium, High, Critical",
                "MandatoryOptional": "One of: Mandatory, Optional",
                "ManualAutomatic": "One of: Manual, Automatic, Semi-Automatic",
                "Impact": float between 1.0-10.0 (Risk impact severity),
                "Probability": float between 1.0-10.0 (probability of occurrence),
                "MaturityLevel": "One of: Initial, Developing, Defined, Managed, Optimizing",
                "ActiveInactive": "Active",
                "PermanentTemporary": "Permanent",
                "CreatedByName": "radha.sharma",
                "CreatedByDate": "{current_date}",
                "ComplianceVersion": "1.0",
                "Status": "Approved",
                "Applicability": "One of: Global, Regional, Local, Specific",
                "PotentialRiskScenarios": "Description of potential risk scenarios",
                "RiskType": "One of: Current, Residual, Inherent, Emerging, Accepted",
                "RiskCategory": "One of: Operational, Financial, IT, Legal, Compliance, Strategic, Reputational, Environmental",
                "RiskBusinessImpact": "Description of which business units would be impacted by this risk",
                "risk": {{
                    "RiskTitle": "Clear, descriptive title for the associated risk",
                    "Criticality": "One of: Low, Medium, High, Critical (should match compliance Criticality)",
                    "PossibleDamage": "Description of potential damage (should match compliance PossibleDamage)",
                    "Category": "One of: Operational, Financial, IT, Legal, Compliance, Strategic, Reputational, Environmental",
                    "RiskType": "One of: Current, Residual, Inherent, Emerging, Accepted",
                    "BusinessImpact": "Description of business impact",
                    "RiskDescription": "Detailed description of the risk and its potential consequences",
                    "RiskLikelihood": integer between 1-10 (likelihood of risk occurrence),
                    "RiskImpact": integer between 1-10 (impact severity),
                    "RiskExposureRating": float (calculated as RiskImpact * RiskLikelihood),
                    "RiskPriority": "One of: Low, Medium, High",
                    "RiskMitigation": {{"1": "first mitigation strategy", "2": "second mitigation strategy", "3": "third mitigation strategy"}},
                    "CreatedAt": "{current_date}",
                    "RiskMultiplierX": 0.1,
                    "RiskMultiplierY": 0.1
                }}
            }}
        ]
    }}
   
    Ensure the JSON is valid and each compliance record with its associated risk is comprehensive and realistic based on the subpolicy information provided.
    """
   
    prompt = ChatPromptTemplate.from_template(template)
   
    # Create the chain using modern langchain 1.0+ approach
    chain = prompt | llm
   
    return chain
 
def process_excel_data(df, chain):
    """Process each row of Excel data and generate separate compliance and risk records"""
    compliance_results = []
    risk_results = []
   
    # Check if required columns exist
    required_columns = ["SubPolicyId", "SubPolicyName", "Description", "Control"]
    missing_columns = [col for col in required_columns if col not in df.columns]
   
    if missing_columns:
        print(f"Error: Missing required columns: {', '.join(missing_columns)}")
        print(f"Available columns: {', '.join(df.columns)}")
        return None, None
   
    total_rows = len(df)
    current_date = datetime.now().strftime("%Y-%m-%d")
    compliance_id_counter = 1  # Track compliance IDs for risk linking
    risk_id_counter = 1  # Track risk IDs
   
    for index, row in df.iterrows():
        print(f"Processing row {index+1}/{total_rows}...")
       
        try:
            # Extract data from row
            SubPolicyId = int(row["SubPolicyId"])  # Use existing SubPolicyId from Excel
            SubPolicyName = row["SubPolicyName"]
            Description = row["Description"]
            Control = row["Control"]
           
            # Generate compliance records using LangChain
            result = chain.invoke({
                "SubPolicyName": SubPolicyName,
                "Description": Description,
                "Control": Control,
                "current_date": current_date
            })
           
            # Parse the JSON response
            try:
                compliance_data = json.loads(result.content.strip())
                compliances = compliance_data.get("compliances", [])
               
                # Process each compliance and its associated risk
                for compliance in compliances:
                    # Extract risk data if present
                    risk_data = compliance.pop("risk", None)
                   
                    # Create compliance record
                    compliance_record = {
                        "ComplianceId": compliance_id_counter,
                        "SubPolicyId": SubPolicyId,
                        "PreviousComplianceVersionId": None,
                        "Identifier": compliance.get("Identifier", f"COMP-{compliance_id_counter:04d}"),
                        "ComplianceTitle": compliance.get("ComplianceTitle", ""),
                        "ComplianceItemDescription": compliance.get("ComplianceItemDescription", ""),
                        "ComplianceType": compliance.get("ComplianceType", ""),
                        "Scope": compliance.get("Scope", ""),
                        "Objective": compliance.get("Objective", ""),
                        "BusinessUnitsCovered": compliance.get("BusinessUnitsCovered", ""),
                        "IsRisk": compliance.get("IsRisk", 1),
                        "PossibleDamage": compliance.get("PossibleDamage", ""),
                        "mitigation": json.dumps(compliance.get("mitigation", {})),
                        "Criticality": compliance.get("Criticality", ""),
                        "MandatoryOptional": compliance.get("MandatoryOptional", ""),
                        "ManualAutomatic": compliance.get("ManualAutomatic", ""),
                        "Impact": float(compliance.get("Impact", 0)),
                        "Probability": float(compliance.get("Probability", 0)),
                        "MaturityLevel": compliance.get("MaturityLevel", ""),
                        "ActiveInactive": compliance.get("ActiveInactive", "Active"),
                        "PermanentTemporary": compliance.get("PermanentTemporary", "Permanent"),
                        "CreatedByName": compliance.get("CreatedByName", "radha.sharma"),
                        "CreatedByDate": compliance.get("CreatedByDate", current_date),
                        "ComplianceVersion": compliance.get("ComplianceVersion", "1.0"),
                        "Status": compliance.get("Status", ""),
                        "Applicability": compliance.get("Applicability", ""),
                        "PotentialRiskScenarios": compliance.get("PotentialRiskScenarios", ""),
                        "RiskType": compliance.get("RiskType", ""),
                        "RiskCategory": compliance.get("RiskCategory", ""),
                        "RiskBusinessImpact": compliance.get("RiskBusinessImpact", ""),
                        "FrameworkId": None
                    }
                    compliance_results.append(compliance_record)
                   
                    # Create risk record if risk data exists
                    if risk_data:
                        risk_record = {
                            "RiskId": risk_id_counter,
                            "ComplianceId": compliance_id_counter,
                            "RiskTitle": risk_data.get("RiskTitle", ""),
                            "Criticality": risk_data.get("Criticality", compliance.get("Criticality", "")),
                            "PossibleDamage": risk_data.get("PossibleDamage", compliance.get("PossibleDamage", "")),
                            "Category": risk_data.get("Category", compliance.get("RiskCategory", "")),
                            "RiskType": risk_data.get("RiskType", compliance.get("RiskType", "")),
                            "BusinessImpact": risk_data.get("BusinessImpact", compliance.get("RiskBusinessImpact", "")),
                            "RiskDescription": risk_data.get("RiskDescription", ""),
                            "RiskLikelihood": int(risk_data.get("RiskLikelihood", 0)),
                            "RiskImpact": int(risk_data.get("RiskImpact", compliance.get("Impact", 0))),
                            "RiskExposureRating": float(risk_data.get("RiskExposureRating", 0)),
                            "RiskPriority": risk_data.get("RiskPriority", ""),
                            "RiskMitigation": json.dumps(risk_data.get("RiskMitigation", compliance.get("mitigation", {}))),
                            "CreatedAt": risk_data.get("CreatedAt", current_date),
                            "FrameworkId": None,
                            "RiskMultiplierX": float(risk_data.get("RiskMultiplierX", 0.1)),
                            "RiskMultiplierY": float(risk_data.get("RiskMultiplierY", 0.1))
                        }
                        risk_results.append(risk_record)
                        risk_id_counter += 1
                   
                    compliance_id_counter += 1
                   
                print(f"Generated {len(compliances)} compliance and risk records for: {SubPolicyName}")
               
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON response for row {index+1}: {e}")
                print(f"Raw response: {result.content}")
               
        except Exception as e:
            print(f"Error processing row {index+1}: {e}")
   
    return compliance_results, risk_results
 
def save_results(compliance_results, risk_results, output_prefix, output_dir="excel_output_nist"):
    """Save compliance and risk results to separate Excel files"""
   
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
   
    compliance_file = None
    risk_file = None
    
    # Save compliance results
    if compliance_results:
        compliance_file = os.path.join(output_dir, f"{output_prefix}_Compliance.xlsx")
        df_compliance = pd.DataFrame(compliance_results)
        df_compliance.to_excel(compliance_file, index=False)
        print(f"\nCompliance results saved to {compliance_file}")
        print(f"Total compliance records generated: {len(compliance_results)}")
    else:
        print("\nNo compliance records to save.")
   
    # Save risk results
    if risk_results:
        risk_file = os.path.join(output_dir, f"{output_prefix}_Risk.xlsx")
        df_risk = pd.DataFrame(risk_results)
        df_risk.to_excel(risk_file, index=False)
        print(f"Risk results saved to {risk_file}")
        print(f"Total risk records generated: {len(risk_results)}")
    else:
        print("No risk records to save.")
    
    return compliance_file, risk_file
 
def generate_compliance_for_single_subpolicy(
    subpolicy_id,
    subpolicy_name,
    description,
    control,
    api_key=None
):
    """
    Generate compliance and risk records for a single subpolicy.
    
    Args:
        subpolicy_id (int): ID of the subpolicy
        subpolicy_name (str): Name of the subpolicy
        description (str): Description of the subpolicy
        control (str): Control information
        api_key (str): OpenAI API key (optional, will use Django settings if not provided)
    
    Returns:
        list: List of compliance records with associated risks
    """
    try:
        # Setup LangChain
        chain = setup_llm_chain(api_key)
        
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Generate compliance records using LangChain
        result = chain.invoke({
            "SubPolicyName": subpolicy_name,
            "Description": description,
            "Control": control,
            "current_date": current_date
        })
        
        # Parse the JSON response
        compliance_data = json.loads(result.content.strip())
        compliances = compliance_data.get("compliances", [])
        
        # Process each compliance and add subpolicy reference
        processed_compliances = []
        for compliance in compliances:
            # Extract risk data if present
            risk_data = compliance.pop("risk", None)
            
            # Add subpolicy reference
            compliance["SubPolicyId"] = subpolicy_id
            compliance["SubPolicyName"] = subpolicy_name
            
            # Include risk data in compliance record
            if risk_data:
                compliance["risk_details"] = risk_data
            
            processed_compliances.append(compliance)
        
        return processed_compliances
        
    except Exception as e:
        print(f"Error generating compliance for subpolicy {subpolicy_id}: {e}")
        return []


def generate_compliance_and_risk(
    excel_file_path, 
    output_prefix="compliance_risk_output", 
    output_dir="excel_output_nist",
    api_key=None,
    save_to_file=True
):
    """
    Main function to generate compliance and risk records from Excel file.
    Can be called from other scripts.
    
    Args:
        excel_file_path (str): Path to the input Excel file
        output_prefix (str): Prefix for output files (default: "compliance_risk_output")
        output_dir (str): Directory to save output files (default: "excel_output_nist")
        api_key (str): OpenAI API key (optional, will use environment variable if not provided)
        save_to_file (bool): Whether to save results to Excel files (default: True)
    
    Returns:
        tuple: (compliance_results, risk_results, compliance_file_path, risk_file_path)
               If save_to_file=False, file paths will be None
    """
    # Load data
    df = load_excel_data(excel_file_path)
    if df is None:
        return None, None, None, None
   
    # Setup LangChain
    print("Setting up AI model...")
    chain = setup_llm_chain(api_key)
   
    # Process data
    print("Processing data and generating records...")
    compliance_results, risk_results = process_excel_data(df, chain)
   
    compliance_file = None
    risk_file = None
    
    if compliance_results is not None or risk_results is not None:
        if save_to_file:
            # Save results to separate files
            compliance_file, risk_file = save_results(
                compliance_results, 
                risk_results, 
                output_prefix,
                output_dir
            )
            print("\n✓ Generation complete!")
        else:
            print("\n✓ Data processing complete! (Results not saved to file)")
    else:
        print("\nNo results generated. Please check the input file format.")
    
    return compliance_results, risk_results, compliance_file, risk_file


def main():
    """CLI entry point for standalone usage"""
    print("Compliance and Risk Records Generator")
    print("--------------------------------------")
   
    # Get Excel file path
    excel_file = input("Enter the path to your Excel file: ")
   
    # Call the main function
    compliance_results, risk_results, compliance_file, risk_file = generate_compliance_and_risk(
        excel_file_path=excel_file,
        output_prefix="compliance_risk_output",
        output_dir="excel_output_nist"
    )
    
    if compliance_results or risk_results:
        print("\n✓ Process completed successfully!")
    else:
        print("\n✗ Process failed. Please check the input file.")


if __name__ == "__main__":
    main()
 
 