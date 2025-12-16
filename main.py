import json
import re
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
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
    print(f"\n--- STRICT ANALYSIS: {file.filename} ---")
    
    # 1. READ FILE
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
        return {"status": "error", "msg": "File Read Failed"}

    # 2. STRICT GATEKEEPER (Deny Random Files)
    # Check for domain-specific keywords. If none exist, this isn't an RFP.
    keywords = ["viscosity", "salt spray", "corrosion", "coating", "paint", "epoxy", "technical specifications"]
    if not any(keyword in content_text.lower() for keyword in keywords):
        print("REJECTED: No domain keywords found.")
        return {
            "status": "rejected",
            "match_score": 0,
            "recommended_product": {"name": "Invalid Document", "description": "This file does not appear to be a valid technical RFP. No technical keywords found.", "price_per_liter": 0},
            "financial_impact": "Analysis Aborted",
            "reasoning": [{"status": "fail", "msg": "Document lacks required technical keywords (e.g., Viscosity, Coating)."}]
        }

    # 3. EXTRACT SPECS (Robust Regex)
    rfp_specs = {"viscosity": 0, "salt_spray_hours": 0}
    
    # Viscosity: Look for "Viscosity" followed by numbers within 20 chars
    visc_match = re.search(r"(?:viscosity|cp).{0,20}?(\d+)", content_text, re.IGNORECASE | re.DOTALL)
    if visc_match: rfp_specs["viscosity"] = int(visc_match.group(1))
        
    # Salt Spray: Look for "Salt Spray" followed by numbers
    salt_match = re.search(r"(?:salt|spray|corrosion|hours).{0,20}?(\d+)", content_text, re.IGNORECASE | re.DOTALL)
    if salt_match: rfp_specs["salt_spray_hours"] = int(salt_match.group(1))

    print(f"EXTRACTED: {rfp_specs}")

    # 4. HANDLE MISSING DATA (Reject if NO numbers found)
    if rfp_specs['viscosity'] == 0 and rfp_specs['salt_spray_hours'] == 0:
        return {
            "status": "rejected",
            "match_score": 0,
            "recommended_product": {"name": "Data Missing", "description": "Technical terms found, but no numeric requirements extracted.", "price_per_liter": 0},
            "financial_impact": "Analysis Failed",
            "reasoning": [{"status": "fail", "msg": "Found keywords but could not extract numeric values."}]
        }

    # 5. SMART MATCHING & SCORING
    scored_products = []
    
    for product in PRODUCT_DB:
        p_specs = product['specs']
        score = 0
        reasons = []
        is_compliant = True

        # Check Viscosity (if requirement exists)
        if rfp_specs['viscosity'] > 0:
            if p_specs['viscosity'] >= rfp_specs['viscosity']:
                score += 50
                reasons.append({"status": "pass", "msg": f"Viscosity: {p_specs['viscosity']} >= {rfp_specs['viscosity']}"})
            else:
                score -= 50 # Heavy penalty for failure
                is_compliant = False
                reasons.append({"status": "fail", "msg": f"Viscosity: {p_specs['viscosity']} < {rfp_specs['viscosity']}"})

        # Check Salt Spray (if requirement exists)
        if rfp_specs['salt_spray_hours'] > 0:
            if p_specs['salt_spray_hours'] >= rfp_specs['salt_spray_hours']:
                score += 50
                reasons.append({"status": "pass", "msg": f"Salt Spray: {p_specs['salt_spray_hours']} >= {rfp_specs['salt_spray_hours']}"})
            else:
                score -= 50
                is_compliant = False
                reasons.append({"status": "fail", "msg": f"Salt Spray: {p_specs['salt_spray_hours']} < {rfp_specs['salt_spray_hours']}"})

        scored_products.append({
            "product": product,
            "score": score,
            "compliant": is_compliant,
            "reasons": reasons
        })

    # 6. SELECT WINNER
    # Sort by Compliance (True first), then Score (High first), then Price (Low first)
    scored_products.sort(key=lambda x: (-x['compliant'], -x['score'], x['product']['price_per_liter']))

    best_match = scored_products[0]
    winner = best_match['product']
    
    # Financial Logic
    if best_match['compliant']:
        # If we have a compliant winner, calculate savings vs expensive option
        # Find expensive option
        expensive_options = [p for p in scored_products if p['compliant']]
        expensive_options.sort(key=lambda x: x['product']['price_per_liter'], reverse=True)
        most_expensive = expensive_options[0]['product']
        
        savings = most_expensive['price_per_liter'] - winner['price_per_liter']
        financial_msg = f"Cost Optimization: Saved ${savings}/L" if savings > 0 else "Best market price."
        
        return {
            "status": "success",
            "match_score": 100,
            "recommended_product": winner,
            "financial_impact": financial_msg,
            "reasoning": best_match['reasons']
        }
    else:
        # 7. PARTIAL MATCH (Best Product when no exact match)
        # We picked the one with the highest score (closest), even if it failed.
        return {
            "status": "partial",
            "match_score": 50,
            "recommended_product": winner,
            "financial_impact": "Partial Match: Closest available alternative.",
            "reasoning": best_match['reasons'] + [{"status": "fail", "msg": "Note: Product does not fully meet all specs."}]
        }