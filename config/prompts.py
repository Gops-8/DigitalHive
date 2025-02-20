ANALYSIS_PROMPT = """
You are a marketing expert. Analyze the website content provided below and extract key marketing insights in valid JSON format. Respond ONLY with the JSON and no additional text.

Instructions:
1. "keywords": Identify five detailed, long-tail keywords related to the product or service. Each keyword must be between 2 to 5 words, reflect user's search intent, Separate the keywords with commas.
2. "business_name": Extract the exact name of the business as mentioned on the website.
3. "products_services": Identify and list the products or services offered. Provide a clear, concise, comma-separated list.
4. "target_audience": Summarize the target audience in a focused statement using 4 to 6 words per group. If there are multiple groups, separate them with commas. 
5. "location": Extract the business location if mentioned; otherwise, Ensure there are no commas within the location string.

Guidelines:
- Base your analysis on a thorough review of the website's homepage, About Us, and product/service descriptions.
- Do NOT use the domain name to determine keywords.
- Ensure the JSON is valid, with no newlines, leading spaces, or extraneous characters.

Required JSON structure:
[
    "keywords": "string",
    "business_name": "string",
    "products_services": "string",
    "target_audience": "string",
    "location": "string"
]

Website URL: {url}
Content to analyze:
{content}
"""
