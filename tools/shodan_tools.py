import json
import shodan
import re
import tiktoken
from langchain.tools import BaseTool, Tool
from typing import Optional
from llms.azure_llms import create_llm
from langchain.chains import LLMChain, SimpleSequentialChain
from langchain.prompts import PromptTemplate 

tool_llm = create_llm(temp=0.2)

from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)

# your shodan API key
SHODAN_API_KEY = 'QPWbPNV5UODo5TMNvUdFpXEiSG8DbnWm'
api = shodan.Shodan(SHODAN_API_KEY)

def shodan_ip_search(ip):
    result = ""
    try:
        host = api.host(ip)
        general_info = """
            IP: {}
            Organization: {}
            Operating System: {}
        """.format(host['ip_str'], host.get('org', 'n/a'), host.get('os', 'n/a'))
        result += general_info
        banners = ""
        for item in host['data']:
            banner = """
                Port: {}
                Banner: {}

            """.format(item['port'], item['data'])
            banners += banner
        result += banners

    except shodan.APIError as e:
        result = 'Error: {}'.format(e)

    return result

class shodan_ip_lookup_tool(BaseTool):
    name = "Shodan IP Lookup"
    description = "Use Shodan to get info on any exposed services and potential vulnerabilities associated with an IP. Input is an ip address"
    def _run(
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool."""
        try:
            ip = re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', query).group()
            response = shodan_ip_search(ip)
            prompt = "/n Analyze above data and report on exposed services and potential vulnerabilities"
            return (response+prompt)
        except:
            return "Shodan ip host search tool not available for use."

    async def _arun(
        self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("custom_search does not support async")

shodan_ip_lookup_tool = Tool(
    name = "Shodan IP Lookup",
    description = "Use Shodan to get info on any exposed services and potential vulnerabilities associated with an IP. Input is an ip address",
    func= shodan_ip_lookup_tool().run
    )

enc = tiktoken.encoding_for_model("gpt-3.5-turbo")

def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens
    
def shodan_search(input, limit_num):
    result = ""
    try:
        hits = api.search(input, limit=limit_num, minify=True)
        for hit in hits['matches']:
            ip = hit['ip_str']
            data = hit['data']
            package = {"ip": ip, "data": data}
            package_str = json.dumps(package)
            result += package_str
    except shodan.APIError as e:
        result = 'Error: {}'.format(e)
    return result

search_template = """Given this user input: {query}
Use these filters:
ip:	Filters results by a specific IP address.Ex: ip:192.168.2.1
asn:Filters results by a specific ASN (Autonomous System Number) ID.Ex: asn:AS8160
hostname:Filters results by a specific hostname or find values that match the hostname.Ex: hostname:google.com
port:Filters results by a specific port number of a service or find particular ports that are open.Ex: port:21
net:Filters results from a specified CIDR (Classless Inter-Domain Routing) block.Ex: net:192.0.2.0/24
isp:Filters results by devices assigned a particular address (space) from a specified ISP (Internet Service Provider).Ex: isp:Bell
city:Filters results by a specific city or find devices in a particular city.Ex: city:Vancouver
country:Use two-digit country code or find devices in a particular country. Ex: country:CA
os: Filters results by a particular operating system or search based on the operating system.Ex: os:Linux
product:Filters results by a particular software or product identified in the banner.Ex: product:Apache
version: Filters results by a specified software version.Ex: version:2.2.5
geo:Search for specific GPS coordinates.Ex: geo:42.3601,-71.0589  (command line only)
before/after:Find results within a specific timeframe.Ex: after:2022-01-01 (command line only)

Use info provided by user input to create a Shodan search query.

Example output:
product:"Apache" os:"Linux" port:"80" country:"US"
"""
search_prompt = PromptTemplate(input_variables=["query"], template=search_template)
search_chain = LLMChain(llm=create_llm(0, 2000), prompt=search_prompt)

verify_template = """Given this Shodan search input: {query}
Change any country names to use two-digit country code.
Make sure all continent mentions are replaced with country code for all countries within that continent. For example: "North America" would be "CA,US".
Example Input:
product:"Apache" country:"Canada"
Example Output:
product:"Apache" country:"CA"
"""
verify_prompt = PromptTemplate(input_variables=["query"], template=verify_template)
verify_chain = LLMChain(llm=create_llm(0, 100), prompt=verify_prompt)

search_input_chain = SimpleSequentialChain(chains=[search_chain, verify_chain], verbose=True)

class shodan_search_tool(BaseTool):
    name = "Shodan Search"
    description = "Use to search for internet connected devices and servers and provides a comprehensive view of all exposed services"
    def _run(
        self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool."""
        try:
            limit = 7
            input = search_input_chain.run(query)
            response = shodan_search(input, limit)  
            return response
        except:
            return "Shodan search tool not available for use."

    async def _arun(
        self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("custom_search does not support async")
    
shodan_search_tool = Tool(
    name = "Shodan Search",
    description = "Use to search for internet connected devices and servers and provides a comprehensive view of all exposed services",
    func= shodan_search_tool().run
)
