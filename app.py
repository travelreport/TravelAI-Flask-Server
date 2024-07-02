from flask import Flask, request, jsonify
from dotenv import load_dotenv
from openai import OpenAI
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from uuid import uuid1
from apscheduler.schedulers.background import BackgroundScheduler
import os, requests, time, threading

app = Flask(__name__)

# Define database and users
app.config['MONGO_URI'] = 'mongodb+srv://yoshiroito0630:chBbUzT8PuxznEIq@cluster-travelai.mjnhe9t.mongodb.net/'
# app.config['MONGO_URI'] = 'mongodb://127.0.0.1:27017'
client = MongoClient(app.config['MONGO_URI'])
db_name = 'TravelAI'

# if db_name not in client.list_database_names():
#     db = client[db_name]

db = client[db_name]
collection_name = 'reports'

if collection_name not in db.list_collection_names():
    db.create_collection(collection_name)

reports = db.reports


load_dotenv()

API_KEY = os.getenv('API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=OPENAI_API_KEY)
selections = []
prompts = []
id = ""
location = ""
start_date = ""
end_date = ""
ans = ""


scheduler = BackgroundScheduler()

def delete_expired_reports():
    current_time = time.time()
    criteria_time = current_time - 30 * 60
    delete_criteria = {
        "created_time": {"$lt": criteria_time}
    }
    reports.delete_many(delete_criteria)

scheduler.add_job(delete_expired_reports, 'interval', minutes=30)
scheduler.start()

@app.route('/hello', methods=['GET'])
def hello_world():
    return "Hello world!"

@app.route('/request', methods=['POST'])
def index():
    global selections, prompts, id, location, start_date, end_date, ans
    location = request.json["location"]
    start_date = request.json["start_date"]
    end_date = request.json["end_date"]
    selections = request.json["selections"]
    print('>>>>>>>>>>>selections------------------>', selections)
    selections = sorted(selections)
    ans = ""

    if request.headers.get("Authorization"):
        current_auth_key = request.headers.get("Authorization")

        Basic, current_auth_key = current_auth_key.split()

        if current_auth_key == API_KEY:
            id = str(uuid1().hex)

            prompt1 = (f"GENERAL AREA INFO"
            f"Develop an all-encompassing travel report for {location}, focusing on the months of from {start_date} to {end_date}. This report is crafted for a broad audience, highlighting the city’s cultural diversity, iconic landmarks, diverse cuisine, and specific summer climate considerations. It aims to guide travelers through the destination’s unique neighborhoods, showcasing their cultural and entertainment values. The report prioritizes engagement with local culture and community through etiquette tips, local expressions, and slang, encouraging respectful and enriching interactions. Additionally, it underscores the importance of sustainable travel practices and offers practical advice for a comfortable visit during the selected date range. Provide the list of data sources with hyperlinked addresses related to general area info in {location}")

            prompt2 = ("BRIEF HISTORY"
            f"Create a concise, engaging history report on {location} covering the last 250 years, focusing on notable historical events, cultural significance, and landmarks. This narrative, designed for personal use within a larger travel document, will maintain a casual, storytelling tone without exceeding one page. It will feature a selection of the city's most impactful landmarks and cultural highlights, offering insights into the city's dynamic evolution and vibrant identity. The report will provide a straightforward, informative overview without the inclusion of thematic organization, specific event preferences, colloquial expressions, or local slang. Provide in the following format."
            "Begin with an introduction to the locations founding and early development. Proceed to highlight significant historical events in a clear, chronological order."
            "Detail the cultural history of the location, focusing on the broad influences from Latin America and the Caribbean, and their impact on City’s music, art, and food scenes. Highlight landmarks."
            "Ensure the narrative is accessible, using straightforward language that enriches the story of the location without the need for local jargon or slang."
            "End with a brief look at the location recent developments and its current role as a cosmopolitan hub, reflecting on how the city continues to grow and attract visitors from around the world."
            f"List of data sources with hyperlinked addresses for important Landmarks to History in {location}")

            prompt4 = ("WEATHER / HISTORIC AND PREDITIONS"
            f"To generate the final report on {location} weather, incorporating your detailed requirements, here's how I'd construct the prompt:"
            f"Utilizing data primarily from the National Oceanic and Atmospheric Administration (NOAA) and The Weather Channel, compile an immediate, detailed travel weather report for {location}, focusing on the dates of from {start_date} to {end_date}. This report should encompass:"
            "Add the list of links to NOAA of other sources to get most accurate during travel."
            "Historic Weather Analysis: Include a comprehensive overview of the weather for the last 10 years, highlighting average temperatures, precipitation levels, humidity, and wind speeds. Note any significant weather events or anomalies within this period."
            "Predictive Weather Trends: Based on the historic data and current climate models, outline the general weather trends expected for the current year and future summers. Focus on changes in temperature, precipitation patterns, humidity levels, and wind speeds, with an emphasis on general trends rather than specific predictions."
            "Practical Implications for Travelers: Considering the historic data and predictive trends, offer advice for travelers planning personal or business trips during these months. This could include recommended clothing, best times of day for outdoor activities, and any precautions to take based on weather patterns."
            "Ensure the report is clear, concise, and immediately usable for planning both personal and business travel. There are no specific requirements for additional travel-related information, data visualization, report formatting, or accessibility features. The report is needed as soon as possible to aid in immediate travel planning decisions.")

            prompt5 = ("PUBLIC TRANSPORTATION"
            f"Create a lively and comprehensive overview of all public transportation options available in {location} for inclusion in a travel report targeting a general audience. This overview should detail the types of transportation (such as buses, trains, subways, ferries, etc.), their accessibility features (including services for individuals with disabilities, bike-friendly options, and family services), operating hours, fare structures, and any special considerations for peak travel periods. Additionally, incorporate local tips for navigating the system, cultural or historical facts about the public transportation system, and brief safety tips or etiquette. Highlight the availability of language support for non-native speakers and discuss the integration of technology, such as mobile apps for ticket purchases or route planning. Also, mention any significant local events or festivals and their impact on public transportation."
            f"List of data sources with hyperlinked addresses in {location} for following: Public transit websites (buses, trains, subways) for schedules, routes, and fare information; Ride-sharing services like Uber or Lyft for airport transfers and local transportation; Car rental company websites to book rental cars; website links related the transportation to and from Major airports; Airline websites to book flights;"
            "Key Points for Implementation"
            "Customize for Location: Adapt the overview to the specific location you are focusing on by researching local public transportation details and unique cultural or historical aspects."
            "Language and Technology Support: Include information on language support for tourists and the use of technology to enhance the travel experience."
            "Local Events and Peak Periods: Tailor information about local events and peak travel periods that could affect public transportation usage."
            "Engagement and Accessibility: Ensure the report is engaging with lively language and accessible to a broad audience, including those with specific accessibility needs.")

            prompt3 = ("CURRENCY AND CONVERSION RATES"
            f"Craft a detailed and engaging section on currency and conversion rates for inclusion in a travel report targeting a general audience, focusing on {location}. This section should cover the local currency used, including denominations of bills and coins, tips for currency exchange (such as recommended locations for exchanging currency, any fees to be aware of, and the best practices for getting favorable rates), and guidance on typical payment methods accepted (cash, credit cards, mobile payments, etc.). Additionally, provide insights into the cost of living and average prices for common expenses like meals, transportation, and accommodations. Incorporate local tips on managing currency and spending wisely, and include any relevant cultural nuances related to tipping or bargaining. Highlight any technology or apps that can assist travelers with currency conversion and budget management in real-time. Also, consider mentioning any significant fluctuations in exchange rates or economic conditions that travelers should be aware of during their visit. Provide list of data sources with hyperlinked addresses related to above in {location}."
            "Key Points for Implementation"
            "Local Currency Details: Start with basic information about the local currency, focusing on practical aspects like recognizing denominations and understanding the coin system."
            "Currency Exchange Insights: Offer advice on where and how to exchange currency, including how to avoid common pitfalls and fees."
            "Payment Practices: Describe the local payment landscape, highlighting if there's a preference for cash over digital payments or vice versa, and any peculiarities (like places not accepting foreign credit cards)."
            "Cost of Living Overview: Provide a snapshot of the cost of living to help travelers budget their trip, covering typical expenses they might incur."
            "Cultural Considerations: Touch on cultural practices related to money, such as tipping etiquette or the acceptability of bargaining in markets."
            "Technology Tools: Suggest apps or websites that are helpful for currency conversion and tracking spending, especially those that might offer offline functionality."
            "Economic Conditions: Briefly note if the local currency is subject to significant fluctuations or if there are any economic conditions that could impact travelers financially.")

            prompt6 = ("Health Report"
            f"create a travel health report for {location} from {start_date} to {end_date}. populate the report template below using the most relevant and up to date info available. Start with an Introduction: Provide an overview of the destination, noting its appeal during the selected time and the importance of health preparedness for travelers. COVID-19 Guidelines and Vaccination Requirements: Consult the WHO and CDC websites for the latest travel advisories and COVID-19 guidelines. Summarize current entry requirements, vaccination, testing, and mask guidelines. General Health Risks: Food and Water Safety: Tips on consuming local foods and drinks safely. Sun Radiation Exposure: Advice on sun protection measures specific to the location climate. Animal Safety: Guidelines on interacting with local wildlife and pets. Heatwaves and Extreme Weather: Safety measures during high temperature periods. Navigating locations Health System: How to find and access healthcare services, including English-speaking healthcare providers. Information on emergency services, including a list of hospitals and clinics with emergency contact numbers. Health Insurance and Medical Services: Advice on selecting health insurance for travel. Information on pharmacies and how to access medical supplies and services. Protective Gear and Local Practices: Recommendations for protective gear against the sun and dehydration. Insight into local practices like siesta to avoid the hottest part of the day. Summary and weblinks A concise summary of key points for quick reference. provide weblinks to the WHO, CDC, and local health ministry for real-time updates. Conclusion: Wrap up the report, reinforcing the importance of health safety while traveling and encouraging travelers to stay informed. List of data sources with hyperlinked addresses in {location} for following: Travel clinic websites for vaccination and medication recommendations; Local hospital and medical facility listings with contact details; links with map coordinates to hospitals so people can click on them if they get hurt; Travel insurance provider sites for coverage information"
            )

            prompt10 = ("Crime Report"
            f"Generate a comprehensive crime and safety report for {location}, during the time of {start_date} to {end_date}, aimed at enhancing tourist safety. This report will draw on data from local law enforcement and the U.S. Department of State's STEP program, designed for transformation into a structured outline in the following format"
            "Final Structure"
            "Introduction"
            "Purpose of the report"
            f"Detail the purpose of the report, emphasizing the importance of providing tourists with comprehensive and up-to-date information on crime and safety to enhance their travel experience in {location}. Include specific examples of past incidents involving tourists in {location} to underscore the importance of the report. Importance of Tourist Safety Highlight the significance of ensuring tourist safety, including statistics on tourist visits to {location} during the peak travel season and the economic impact of tourism. Mention how safety influences tourist satisfaction and local business prosperity."
            "Methodology"
            f"List of data sources with hyperlinked addresses for following:Local Law Enforcement Data; U.S. Department of State's STEP Program;{location} Crime Statistics."
            "Crime Analysis"
            "Crime Analysis should contain following: Breakdown by Crime Type - Provide a detailed breakdown of crimes by type, including specific examples and recent incidents(Violent Crimes: Include incidents of assault, robbery, and sexual assault, particularly in busy tourist areas; Property Crimes: Detail high rates of pickpocketing, theft, and burglary in popular tourist spots, mentioning specific tactics used by thieves; Scams and Frauds: Describe common scams targeting tourists, including fake police officers and overcharging taxi drivers - based on Patterns, Timings, and Demographics). Expand on the analysis with specific data - Hotspots: Identify and map exact locations with high crime rates, possibly using a color-coded crime intensity index; Timings: Provide a statistical breakdown of crimes by hour and day of the week; Demographics: Analyze victim profiles, such as age groups and nationalities most frequently targeted."
            "Traveler Safety Information"
            "Legal advice and general safety tips"
            "Brief pointers on using foreign mobile phones for local emergencies, presented in a bulleted list format"
            "Details of embassies and consulates with hyperlinked contacts"
            "Prioritized Safety Recommendations"
            "Organized by areas most affected by severe crimes, aimed at tourists"
            "Reference Section"
            "Hyperlinked texts to all data sources and safety resources, each followed by a descriptive phrase containing keywords"
            "Considerations"
            "Ensure the brief pointers for using foreign phones are concise and user-friendly."
            "Organize safety recommendations in a way that prioritizes information for tourists based on the areas most impacted by severe crimes."
            "Include keyword-rich phrases in the reference section to facilitate easy scanning or searching."
            f"This structure should provide a comprehensive and navigable report for enhancing the safety of tourists in {location} during the peak travel season. If there's anything more you'd like to add or adjust, feel free to let me know!"
            )

            prompt7 = ("Pharmacy locations"
            f"Develop an informative and accessible section on pharmacy locations for inclusion in a travel report, catering to a general audience and focused on {location}. This section should detail the availability of pharmacies in the area, including notable chains, local pharmacies, and their operating hours. Highlight any differences in availability in urban versus rural areas, if applicable. Provide guidance on how to find a pharmacy, such as recognizable signs, local terms for a pharmacy, and whether there's a central directory or app useful for locating them. Discuss the process for purchasing medication, including any prescriptions required, over-the-counter drug availability, and typical documentation needed for purchasing medication specific to the location. Include tips for travelers on commonly sought-after medications and alternatives, advice on travel insurance coverage for medications, and any cultural or legal nuances related to buying medication in that area. If possible, offer insights into emergency services, including how to contact them and the availability of English-speaking staff or translation services."
            "Key Points for Implementation"
            "Pharmacy Chains and Local Options: Provide names of widely recognized pharmacy chains and advice on finding local pharmacies, which might offer unique or regional services."
            "Operating Hours: Clarify any variations in operating hours, especially for 24-hour pharmacies or those with limited hours on weekends and holidays."
            "Finding Pharmacies: Offer practical tips for locating pharmacies, including signage, local language terms, and digital resources for finding the nearest option."
            "Purchasing Process: Describe the process for buying medication, highlighting the distinction between prescription and over-the-counter drugs and any necessary documentation."
            "Common Medications: Advise on common travel-related medications that might be needed and their availability or local equivalents."
            "Insurance and Legal Considerations: Discuss how travel insurance might cover medications abroad and any legal considerations or restrictions on medication purchases."
            "Emergency Services: Include information on accessing emergency medical services, focusing on availability and language support for travelers.")

            # prompt9 = ("about and benefits of Travel Insurance "
            # f"Create an informative and engaging section on travel insurance for inclusion in a travel report, targeted at a general audience and adaptable to {location}. This section should start by defining what travel insurance is and the various types that exist, such as trip cancellation, medical, evacuation, and baggage insurance. Elaborate on what each type covers, including specific scenarios and examples to illustrate the benefits (e.g., trip cancellations due to illness, emergency medical treatments abroad, lost luggage, etc.). Discuss the importance of travel insurance, emphasizing its role in mitigating financial risks associated with unexpected events during travel. Include guidance on how to choose the right travel insurance policy, considering factors like the length of the trip, destinations, planned activities, and the traveler's personal and medical history. Provide tips on understanding policy terms, recognizing common exclusions, and the process for filing a claim. Highlight the potential consequences of traveling without insurance to underscore its importance. If relevant, mention considerations for travel insurance in the context of current global health issues or other timely concerns."
            # "Key Points for Implementation"
            # "Understanding Travel Insurance: Clearly explain the concept of travel insurance and break down the different types available to travelers."
            # "Coverage Details: Detail the coverage provided by each type of insurance, using tangible examples to clarify how they apply in real-world travel situations."
            # "The Importance of Insurance: Convey the significance of having travel insurance, including how it protects against unforeseen events and financial losses."
            # "Choosing a Policy: Offer advice on selecting a travel insurance policy, covering what factors should influence the decision and how to tailor coverage to individual travel needs."
            # "Policy Understanding: Provide tips for reading and understanding the fine print of insurance policies, including how to spot important clauses and exclusions."
            # "Claim Process: Describe the typical process for filing an insurance claim, including necessary documentation and timelines."
            # "Traveling Without Insurance: Discuss the risks and potential consequences of traveling without insurance, reinforcing why it is a critical component of travel planning."
            # )

            prompt12 = ("Embassy Location Links"
            f"Compose a detailed and helpful section on embassy locations for inclusion in a travel report, aimed at a general audience and tailored to {location}. This section should enumerate the locations of major international embassies and consulates within the area, including addresses, contact information (phone numbers and email addresses), and operating hours. Provide an overview of the services these diplomatic missions offer to travelers, such as emergency assistance, passport and visa services, and legal aid. Highlight the importance of knowing the nearest embassy or consulate location for safety and emergency purposes, including instructions on what to do and whom to contact in various types of emergencies (lost passports, legal issues, etc.). Offer advice on how to interact with embassy staff and the typical procedures for securing appointments or assistance. If relevant, include information on multilingual support or services available for non-native speakers, and emphasize any cultural or procedural nuances that travelers should be aware of when seeking assistance from their country's embassy abroad."
            "Key Points for Implementation"
            "Embassy and Consulate Locations: Start with a list of embassies and consulates, focusing on those most relevant to your audience, including full contact details and location."
            "Services Offered: Detail the range of services provided by these diplomatic missions, clarifying what travelers can expect in terms of assistance."
            "Emergency Protocols: Explain the protocols for contacting and receiving help from an embassy or consulate in emergencies, providing clear steps for common situations."
            "Interacting with Embassy Staff: Give tips on etiquette and procedures for interacting with embassy and consulate staff, including how to make appointments."
            "Language Support: Note any available language support services at embassies and consulates for travelers who might not speak the local language or the embassy's official language fluently."
            "Cultural and Procedural Nuances: Mention any cultural considerations or procedural details specific to the country that might affect interactions with embassies and consulates."
            )

            prompt8 = ("Air Quality"
            f"Craft a thorough and insightful section on air quality for inclusion in a travel report, designed for a general audience and applicable to {location}. This section should introduce the concept of air quality and its importance to travelers, especially those with respiratory conditions or sensitivity to pollution. Detail the common pollutants and factors affecting air quality, such as industrial emissions, vehicle exhaust, and seasonal variations (e.g., smog in summer, indoor heating pollution in winter). Include information on how air quality can vary between urban and rural areas, and during different times of the day or year. Provide guidance on how to find current air quality indexes (AQI) for specific locations, recommending websites, apps, or local resources for real-time data. Discuss practical tips for travelers on minimizing exposure to poor air quality, such as wearing masks, choosing accommodations in areas with better air quality, and planning outdoor activities for times of day when air quality tends to be better. Emphasize the significance of checking air quality forecasts when planning trips, especially for those with health concerns, and suggest precautions to take when visiting areas known for poor air quality."
            "List of data sources with hyperlinked addresses for environmental protection agency websites with air quality data and advisories."
            "Key Points for Implementation"
            "Introduction to Air Quality: Begin with a basic explanation of air quality and why it matters to travelers, focusing on health implications."
            "Pollutants and Factors: Enumerate key pollutants (like PM2.5, NO2, ozone) and discuss factors that contribute to air quality levels, including geographic and industrial influences."
            "Urban vs. Rural Air Quality: Highlight differences in air quality trends between urban centers and rural areas, noting how geography, weather, and human activity influence these variations."
            "Finding Air Quality Information: Provide strategies for accessing reliable air quality data, including specific tools, apps, or websites that offer AQI readings and forecasts."
            "Minimizing Exposure: Offer actionable advice for travelers on how to reduce their exposure to air pollutants, underscoring the importance of preparedness."
            "Planning with Air Quality in Mind: Stress the need for all travelers, particularly those with pre-existing health conditions, to consider air quality in their travel plans and take appropriate precautions."
            )

            prompt10 = ("Water Quality"
            f"Compose a detailed and informative section on water quality for inclusion in a travel report, aimed at a general audience and adaptable to {location}. This section should explain the significance of water quality for travelers, particularly focusing on drinking water and recreational water bodies. Discuss common concerns related to water quality, such as contamination with pathogens, chemicals, and pollutants, and the potential health risks they pose. Provide an overview of the standards for safe drinking water and how water quality can vary between different areas, such as urban versus rural settings, and in various accommodations like hotels versus local homes. Guide readers on how to ascertain the safety of drinking water in their travel destination, including tips on using bottled water, water purification methods (tablets, filters), and identifying safe sources. Additionally, offer advice on safe practices for engaging in activities in or around natural water bodies, highlighting precautions to avoid waterborne diseases. Emphasize the importance of staying informed about local water quality advisories and how to find this information through reputable sources, websites, or local health departments."
            "List of data sources with hyperlinked addresses for water utility company sites with information on tap water safety."
            "Key Points for Implementation"
            "Understanding Water Quality: Start with a primer on water quality and its impact on health, especially for travelers."
            "Water Quality Concerns: Enumerate typical water quality issues travelers might face, including contaminants that could affect health."
            "Drinking Water Safety Standards: Clarify what constitutes safe drinking water, touching on international or national standards if applicable."
            "Assessing Water Safety: Provide strategies for travelers to determine the safety of water, from bottled water to treatment options available for making water safe to drink."
            "Recreational Water Safety: Offer guidelines for safe participation in activities involving natural water sources, including swimming, boating, and other water sports."
            "Staying Informed: Stress the importance of accessing current water quality information and advisories for the intended travel destination."
            "Practical Tips and Precautions: Suggest practical tips for ensuring access to safe drinking water and precautions to take when dealing with uncertain water quality."
            "This prompt is designed to aid in crafting a comprehensive section on water quality for travel reports, providing essential information to help travelers make informed decisions about water consumption and recreational water activities, thereby ensuring their health and safety while exploring new destinations."
            )

            prompt13 = ("Events in the area of travel during duration of travel"
            f"Develop an engaging and informative section on events and festivals for inclusion in a travel report, targeted at a general audience and from {start_date} to {end_date} and {location} of travel. This section should start by highlighting the cultural and recreational importance of local events and festivals, offering travelers a glimpse into the destination's traditions, arts, and community spirit. Provide a curated list of key events and festivals occurring during the travel dates, including details such as names, dates, locations, brief descriptions, and any entry fees or ticket information. Explain the significance of each event, including any historical or cultural background that might enrich a traveler’s experience. Offer practical advice on attending these events, such as how to get tickets, best times to visit, and tips for enjoying the festivities like a local. Also, include guidance on cultural etiquette or norms to observe during these events, any language considerations, and how to access more information or updates about the events. Encourage travelers to consider transportation and accommodation options early, especially for major festivals that might attract large crowds, and suggest ways to participate in or observe local traditions respectfully."
            f"List of data sources with hyperlinked addresses in {location} from {start_date} to {end_date} for following: links related to The Importance of Local Events and Festivals; Curated List of Key Events and Festivals; Cultural Etiquette and Norms"
            "Key Points for Implementation"
            "Introduction to Local Culture: Emphasize the role of events and festivals in experiencing the local culture and community."
            "Event Listings: Provide a comprehensive list of events and festivals, including essential details that would help travelers plan their visits."
            "Historical and Cultural Background: Enrich the descriptions with background information to enhance understanding and appreciation of each event."
            "Attendance Tips: Share logistical tips for attending, including ticket purchase, transportation, and accommodation advice."
            "Cultural Etiquette: Advise on cultural norms and etiquette to ensure respectful participation in local festivities."
            "Language and Information Access: Note any language considerations and recommend resources for finding up-to-date event information."
            "Planning for Participation: Encourage early planning for attending high-demand events, considering the impact on local transportation and accommodations."
            "This prompt is designed to guide the creation of a detailed and enriching section on local events and festivals within a travel report, ensuring travelers can fully engage with the destination’s culture and enjoy unique experiences tailored to the timing of their visit."
            )

            prompt14 = ("top 10 things to do in this area"
            f"Compile a compelling and informative section on the top 10 things to do for inclusion in a travel report, tailored for a general audience and {location}. This section should offer a curated selection of activities and attractions that showcase the diversity and uniqueness of the area, ranging from cultural landmarks and natural wonders to culinary experiences and recreational activities. For each item on the list, provide a concise description that captures its essence and appeal, including any historical significance, natural beauty, or cultural value. Include practical information such as location, admission fees (if any), recommended visiting hours, and any tips for making the most of the visit (e.g., best time of year to go, lesser-known viewpoints). Highlight any experiences that are unique to the destination or particularly popular among locals to give travelers an authentic experience. Additionally, provide advice on accessibility and options for different types of travelers, including families, solo travelers, and those with mobility considerations. Encourage exploration beyond the typical tourist paths by including a mix of well-known attractions and hidden gems."
            f"List of data sources with hyperlinked addresses in {location} for following: Local tourism board sites with attraction listings and ticket purchase links; Online ticket vendors like Viator or GetYourGuide for tours and activities; Sites like TripAdvisor for top-rated attractions and experiences; Venue websites for shows, concerts, sports events, etc."
            "Key Points for Implementation"
            "Diverse Selection: Ensure the list represents a wide range of experiences, from historical sites to modern attractions and natural landscapes."
            "Engaging Descriptions: Craft descriptions that are both informative and enticing, encouraging travelers to explore these highlights."
            "Practical Information: Offer essential details like location, costs, and visiting tips to help travelers plan their activities efficiently."
            "Unique and Authentic Experiences: Emphasize activities or places that offer a genuine insight into the destination's culture or natural beauty."
            "Accessibility Considerations: Provide information on accessibility for travelers with different needs to ensure the suggestions are inclusive."
            "Local Favorites: Include activities or spots favored by locals to offer an insider’s perspective on the destination."
            "Seasonal Recommendations: Mention any seasonal considerations that could affect the experience of visiting the attractions."
            "This prompt is crafted to guide the creation of a vibrant and practical section on the top 10 things to do in a travel report, ensuring travelers have a memorable and well-rounded experience of the destination. The focus is on providing a mix of attractions and activities that cater to diverse interests and provide a deep understanding of the area's culture and environment."
            )

            prompts = [prompt1, prompt2, prompt3, prompt4, prompt5, prompt6, prompt7, prompt8, prompt10, prompt11, prompt12, prompt13, prompt14]

            t = threading.Thread(target=thread_treat)
            t.start()
            
            return jsonify({"Status":"OK", "ID": id}), 200
        else:
            return {'error': 'You are not unauthorized'}, 401 
    else:
        return {'error': 'API key is required'}, 401


@app.route("/get_report", methods=['POST'])
def get_report():
    if request.headers.get("Authorization"):
        current_auth_key = request.headers.get("Authorization")
        Basic, current_auth_key = current_auth_key.split()
        if current_auth_key == API_KEY:
            report_id = request.json['Report id']
            print(report_id)
            if reports.find_one({"id": report_id}):
                content = reports.find_one({"id": report_id})
                print(content)
                if content["progress"] == 100:
                    return jsonify({'ans': content["ans"], 'Success': 100}), 200
                else: return {'status': content["progress"]}, 200
            else:
                return {'error': 'This report does not exist'}, 401
        else:
            return {'error': 'You are not unauthorized'}, 401
    else:
        return {'error': 'API key is required'}, 401

def thread_treat():
    global selections, prompts, id, location, start_date, end_date, ans
    for index, selection in enumerate(selections):
        if index == 0:
            if selection == 1:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "assistant", "content": "Start with one h2 tag which must be underlined, left aligned, and upper-case for only title of prompt-first line. These headings help in breaking down the information for easy understanding and implementation. shouldn't use h1 or h2 tag for other information or title. If other information or title have already got h1 or h2 tag, must replace with h3 tag. Make sure not to miss any section. Apply p tags within each section to elaborate on the main information that might be interesting to the users. When detailing steps or listing anything, use ul for an unordered list to present the information clearly. Emphasize crucial instructions or points with italics or bold, ensuring they are prominently noticeable.  Mustn't write markdown symbols like '*' or '**' in answer. Must not write anything outside HTML tags.  I need only answer with HTML styles. Also another main thing to follow is that replace ChatGPT/OpenAI or your name/reference to TravelReportAI. Give me more than 500 words about the whole response."},
                        {"role": "user", "content": prompts[selection-1]}
                    ],
                    max_tokens=2000
                )
            else:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "assistant", "content": "Start with one h2 tag which must be left aligned and upper-case for only title of prompt-first line. These headings help in breaking down the information for easy understanding and implementation. shouldn't use h1 or h2 tag for other information or title. If other information or title have already got h1 or h2 tag, must replace with h3 tag. Make sure not to miss any section. Apply p tags within each section to elaborate on the main information that might be interesting to the users. When detailing steps or listing anything, use ul for an unordered list to present the information clearly. Emphasize crucial instructions or points with italics or bold, ensuring they are prominently noticeable.  Mustn't write markdown symbols like '*' or '**' in answer Must not write anything outside HTML tags.  I need only answer with HTML styles. Also another main thing to follow is that replace ChatGPT/OpenAI or your name/reference to TravelReportAI. Give me more than 500 words about the whole response."},
                        {"role": "user", "content": prompts[selection-1]}
                    ],
                    max_tokens=2000
                )
            print(response)
            ans = f'<h1 style="text-align: center;">Travel Report for {location} </h1><h1 style="text-align: center;">({start_date} to {end_date})</h1>\n\n'
            content = response.choices[0].message.content.strip()
            if "*" in content: 
                text = content.replace("*", "")
            else:
                text = content
            if text.startswith("```html") and text.endswith("```"):
                ans = ans + "<div>" + text[7:-3] + "</div>"
            else:
                ans = ans + "<div>" + text + "</div>"
            print(response.usage)
            progress = int(1/len(selections) * 100)
            print("progress----------->", progress)
            content = {"id": id, "progress": progress}
            reports.insert_one(content)
        else: 
            if selection == 1:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "assistant", "content": "Start with one h2 tag which must be underlined, left aligned, and upper-case for only title of prompt-first line. These headings help in breaking down the information for easy understanding and implementation. shouldn't use h1 or h2 tag for other information or title. If other information or title have already got h1 or h2 tag, must replace with h3 tag. Make sure not to miss any section. Apply p tags within each section to elaborate on the main information that might be interesting to the users. When detailing steps or listing anything, use ul for an unordered list to present the information clearly. Emphasize crucial instructions or points with italics or bold, ensuring they are prominently noticeable. Mustn't write markdown symbols like '*' or '**' in answer Must not write anything outside HTML tags.  I need only answer with HTML styles. Also another main thing to follow is that replace ChatGPT/OpenAI or your name/reference to TravelReportAI. Give me more than 500 words about the whole response."},
                        {"role": "user", "content": prompts[selection-1]}
                    ],
                    max_tokens=2000
                )
            else:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "assistant", "content": "Start with one h2 tag which must be left aligned and upper-case for only title of prompt-first line. These headings help in breaking down the information for easy understanding and implementation. shouldn't use h1 or h2 tag for other information or title. If other information or title have already got h1 or h2 tag, must replace with h3 tag. Make sure not to miss any section. Apply p tags within each section to elaborate on the main information that might be interesting to the users. When detailing steps or listing anything, use ul for an unordered list to present the information clearly. Emphasize crucial instructions or points with italics or bold, ensuring they are prominently noticeable. Mustn't write markdown symbols like '*' or '**' in answer Must not write anything outside HTML tags.  I need only answer with HTML styles. Also another main thing to follow is that replace ChatGPT/OpenAI or your name/reference to TravelReportAI. Give me more than 500 words about the whole response."},
                        {"role": "user", "content": prompts[selection-1]}
                    ],
                    max_tokens=2000
                )
            print(response)
            content = response.choices[0].message.content.strip()
            if "*" in content: 
                text = content.replace("*", "")
            else:
                text = content
            if text.startswith("```html") and text.endswith("```"):
                ans = ans + "<div>" + text[7:-3] + "</div>"
            else:
                ans = ans + "<div>" + text + "</div>"
            print(response.usage)
            progress = progress + 1/len(selections) * 100
            if progress >= 95:
                progress = 100
            print("progress----------->", progress)
            current_time = time.time()
            filter = {"id": id}
            new_content = {"$set": {"progress": progress, "ans": ans, "created_time": current_time}}
            reports.update_one(filter, new_content)
if __name__ == '__main__':
    app.run(host='0.0.0.0')
