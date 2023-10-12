from tools.prebuilt_tools import python_tool, wikipedia_tool, duckduckgo_tool, calculator_tool, shell_tool
from tools.doc_retrievers import main_retriever_tool
from tools.shodan_tools import shodan_ip_lookup_tool, shodan_search_tool
from tools.ipapi_tools import ipapi_tool
from tools.local_qa_tools import qa_retrieval_tool
from tools.abuseIPDB_tools import abuseIPDB_check_IP

main_tools = [
    shell_tool,
    python_tool,
    wikipedia_tool,
    duckduckgo_tool,
    calculator_tool,
    main_retriever_tool,
    shodan_ip_lookup_tool,
    shodan_search_tool,
    ipapi_tool,
    qa_retrieval_tool,
    abuseIPDB_check_IP
]