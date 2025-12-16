import json
import re
import asyncio
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
# Ensure you run 'pip install pypdf' if you haven't already
from pypdf import PdfReader 

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Database
try:
    with open("products.json", "r") as f:
        PRODUCT_DB = json.load(f)
except Exception:
    PRODUCT_DB = []

@app.post("/analyze")
async def analyze_rfp(file: UploadFile = File(...)):
    print(f"\n--- SMART ANALYSIS: {file.filename} ---")
    
    # 1. READ FILE (Supports PDF and Text)
    content_text = ""
    try:
        if file.filename.endswith(".pdf"):
            reader = PdfReader(file.file)
            for page in reader.pages:
                text = page.extract_text()
                if text: content_text += text
        else:
            content = await file.read()
            content_text = content.decode("utf-8")
    except Exception:
        return {"status": "error", "msg": "Read Failed"}

    # 2. EXTRACT SPECS (Regex Pattern Matching)
    rfp_specs = {"viscosity": 0, "salt_spray_hours": 0}
    
    # Looks for "Viscosity" followed by numbers
    visc_match = re.search(r"(?:viscosity|cp)[^\d]*(\d+)", content_text, re.IGNORECASE)
    if visc_match: rfp_specs["viscosity"] = int(visc_match.group(1))
        
    # Looks for "Salt Spray" followed by numbers
    salt_match = re.search(r"(?:salt|spray|corrosion)[^\d]*(\d+)", content_text, re.IGNORECASE)
    if salt_match: rfp_specs["salt_spray_hours"] = int(salt_match.group(1))

    print(f"RFP NEEDS -> Viscosity: {rfp_specs['viscosity']}, Salt Spray: {rfp_specs['salt_spray_hours']}")

    # 3. SMART MATCHING ALGORITHM
    valid_products = []
    
    for product in PRODUCT_DB:
        p_specs = product['specs']
        is_valid = True
        
        # Check Viscosity
        if p_specs['viscosity'] < rfp_specs['viscosity']:
            is_valid = False
        
        # Check Salt Spray
        if p_specs['salt_spray_hours'] < rfp_specs['salt_spray_hours']:
            is_valid = False

        if is_valid:
            valid_products.append(product)

    # 4. SELECT WINNER (Cost Optimization Logic)
    # Sort valid products by PRICE (Ascending). 
    # The first item is the cheapest valid option.
    valid_products.sort(key=lambda x: x['price_per_liter'])

    if valid_products:
        winner = valid_products[0] 
        
        # Calculate Savings Logic
        # Compare against the most expensive valid option to show "Savings"
        most_expensive = valid_products[-1]
        savings = most_expensive['price_per_liter'] - winner['price_per_liter']
        
        financial_msg = ""
        if savings > 0:
            financial_msg = f"Cost Optimization: Saved ${savings}/L vs {most_expensive['name']}"
        else:
            financial_msg = "Best available market price."

        return {
            "status": "success",
            "match_score": 100,
            "recommended_product": winner,
            "financial_impact": financial_msg,
            "reasoning": [
                {"status": "pass", "msg": f"Technical Compliance: 100% Match on Specs"},
                {"status": "pass", "msg": f"Commercial Logic: Selected lowest cost compliant SKU"}
            ]
        }
    else:
        # No exact match? Suggest the highest spec alternative
        # Sort by Viscosity Descending to find the "Strongest" paint
        PRODUCT_DB.sort(key=lambda x: x['specs']['viscosity'], reverse=True)
        closest = PRODUCT_DB[0]
        return {
            "status": "partial",
            "match_score": 50,
            "recommended_product": closest,
            "financial_impact": "No exact match. Showing highest spec alternative.",
            "reasoning": [{"status": "fail", "msg": "Requirements exceeded current inventory limits."}]
        }