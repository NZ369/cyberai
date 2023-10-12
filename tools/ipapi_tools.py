import re
import requests
# Import things that are needed generically
from langchain.tools import BaseTool, Tool
from typing import Optional

from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)

def extract_ips_urls_domains(text):
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
    domain_pattern = r'(?:[-\w]+\.)+[a-zA-Z]{2,}'

    ips = re.findall(ip_pattern, text)
    urls = re.findall(url_pattern, text)
    domains = re.findall(domain_pattern, text)

    return ips, urls, domains

def make_request(url):
    try:
        req = requests.get(url)
        return req.text
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while making the request: {e}")
        return "IP-API request failed for : "+str(url)
            
def get_ipapi_response(query_list):
    response = []
    for elem in query_list:
        url = 'http://ip-api.com/json/'+elem
        answer = make_request(url)
        response.append(answer)
    return response

def ipapi_processing(query):
    ips, urls, domains = extract_ips_urls_domains(query)
    if len(ips) > 0 or len(domains) > 0:
        query_list = ips+domains
        response = get_ipapi_response(query_list)
        result = '\n'.join(response)
        return (result)
    else:
        return None

class ipapi_tool(BaseTool):
    name = "IP info"
    description = "Use to get an ip address from a domain, as well as geolocation and internet provider information"
    
    def _run(
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool."""
        try:
            return ipapi_processing(query)
        except Exception as e:
            return str(e)

    async def _arun(
        self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("custom_search does not support async")
    
ipapi_tool = Tool(
    name = "IP info",
    description = "Use to get an ip address from a domain, as well as geolocation and internet provider information",
    func= ipapi_tool().run
    )
