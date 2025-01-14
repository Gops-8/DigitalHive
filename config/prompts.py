ANALYSIS_PROMPT = """
Analyze the website content as a marketing expert and extract detailed information in JSON format.
Only respond with the JSON, no other text.

Focus on these key aspects:
1. Keywords: Identify at least five detailed, long-tail keywords related to the product or service , separated by commas 
2. Business Name: Extract the specific name of the business.
3. Products or Services: Identify and list the products or services mentioned. The list should be simple, clear, and concise, separated by commas.
   Example: "Bengal cats, Bengal kittens, Bengal adult cats."
4. target_audience: Summarize the target audience in a focused and specific statement,only generate shorter version of the audiance group in 4 to 6 words. if multiple audience then separate by commas 
   Example: "Women Intrested in Ethnic wear", "Women seeking Culture attire" , "Desing Enthusiats seeking luxury Home" etc
5. Location of Business: If the location is mentioned, include it in the JSON if not return United States.

DO Ensure the JSON format is valid and does not include newlines, leading spaces, or any invalid characters.

Required format:
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
