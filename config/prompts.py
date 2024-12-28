# config/prompts.py
ANALYSIS_PROMPT = """
Analyze the website content as a marketing expert and extract detailed information in JSON format.
Only respond with the JSON, no other text.

Focus on these key aspects:
1. Target Audience: Be very specific about demographics, interests, and behaviors
2. Keywords: Focus on long-tail, specific product/service keywords (minimum 5 keywords, each 3-4 words)
3. Business Details: Identify specific business name and detailed services

Required format:
{
    "keywords": [
        "detailed keyword phrase one",
        "detailed keyword phrase two",
        "detailed keyword phrase three",
        "detailed keyword phrase four",
        "detailed keyword phrase five"
    ],
    "business_name": "string",
    "products_services": {
        "main_offering": "string",
        "detailed_offerings": ["string", "string"],
        "unique_features": ["string", "string"]
    },
    "target_audience": {
        "primary": {
            "demographics": "string",
            "interests": ["string", "string"],
            "pain_points": ["string", "string"],
            "location": "string"
        },
        "secondary": {
            "demographics": "string",
            "interests": ["string", "string"]
        }
    }
}

Example Outputs:
1. For a pet store:
   "target_audience": {
       "primary": {
           "demographics": "Upper-middle-class pet owners, ages 25-50",
           "interests": ["Pure-bred cats", "Luxury pet accessories"],
           "pain_points": ["Finding reputable breeders", "Quality pet care"],
           "location": "San Jose metropolitan area"
       }
   }

2. For an activewear store:
   "keywords": [
       "high-waisted compression workout leggings",
       "seamless athletic yoga sets women",
       "moisture-wicking fitness apparel",
       "squat-proof gym leggings sets",
       "premium athletic wear collections"
   ]

Website URL: {url}
Content to analyze:
{content}
"""
