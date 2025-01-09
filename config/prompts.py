ANALYSIS_PROMPT = """
Analyze the website content as a marketing expert and extract detailed information in JSON format.
Only respond with the JSON, no other text.

Focus on these key aspects:
1. Keywords: Identify at least five detailed, long-tail keywords related to the product or service.
2. Business Name: Extract the specific name of the business.
3. Products or Services: Identify and list the products or services mentioned. The list should be simple, clear, and concise, separated by commas.
   Example: "Bengal cats, Bengal kittens, Bengal adult cats."
4. Target Audience: Summarize the target audience in a focused and specific statement, Give shorter version of the audiance group in 5 to 7 words 
   Example: "Women Intrested in Ethnic wear", "Women seeking Culture attire" , "Desing Enthusiats seeking luxury Home" etc
5. Location of Business: If the location is mentioned, include it in the JSON if not return US.

Ensure the JSON format is valid and does not include newlines, leading spaces, or any invalid characters.

Required format:
[
    "keywords": [
        "detailed keyword phrase one",
        "detailed keyword phrase two",
        "detailed keyword phrase three",
        "detailed keyword phrase four",
        "detailed keyword phrase five"
    ],
    "business_name": "string",
    "products_services": "string",
    "target_audience": "string",
    "location": "string"  
]

Website URL: {url}
Content to analyze:
{content}
"""
