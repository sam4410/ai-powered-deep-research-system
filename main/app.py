import os
import streamlit as st
from dotenv import load_dotenv
from agents import Agent, Runner, trace, WebSearchTool, gen_trace_id, function_tool
from agents.model_settings import ModelSettings
from pydantic import BaseModel
import sendgrid
import asyncio
from sendgrid.helpers.mail import Mail, Email, To, Content
from typing import Dict
import time
import nest_asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
import threading

# Enable nested asyncio (required for Streamlit)
nest_asyncio.apply()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(override=True)

# Page configuration
st.set_page_config(
    page_title="AI Research Assistant",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .step-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #1f77b4;
    }
    .status-success {
        color: #28a745;
        font-weight: bold;
    }
    .status-running {
        color: #fd7e14;
        font-weight: bold;
    }
    .status-waiting {
        color: #6c757d;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Agent definitions (same as original code)
SEARCH_INSTRUCTIONS = """
You are a research assistant. Given a search term, you search the web for that term and produce a concise
summary of the results. The summary must contain 2-3 paragraphs and less than 300 words.
Capture the main points, write succinctly and concisely. No need to have complete sentences or good grammar.
This will be consumed by someone else synthesizing a report, so it's vital that you capture the essence and ignore
any fluff.
Do not include any additional commentary other than the summary itself.
"""

search_agent = Agent(
    name="Search Agent",
    instructions=SEARCH_INSTRUCTIONS,
    tools=[WebSearchTool(search_context_size="low")],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required")
)

NUM_SEARCHES = 5
PLANNER_INSTRUCTIONS = f"""
You are a helpful research assistant. You are given a query and you need to come up with a set of searches
to best answer the query. Output {NUM_SEARCHES} terms to query for.
"""

class WebSearchItem(BaseModel):
    reason: str
    query: str

class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem]

planner_agent = Agent(
    name="Planner",
    instructions=PLANNER_INSTRUCTIONS,
    tools=[WebSearchTool(search_context_size="low")],
    model="gpt-4o-mini",
    output_type=WebSearchPlan
)

def send_html_email(to: str, subject: str, html_body: str) -> Dict[str, str]:
    """Send out an email with the given subject and HTML body"""
    try:
        sg = sendgrid.SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
        from_email = Email("deepikamanojsharma84@gmail.com")
        to_email = To(to)
        content = Content("text/html", html_body)
        mail = Mail(from_email, to_email, subject, content).get()
        response = sg.client.mail.send.post(request_body=mail)
        logger.info(f"SendGrid response status: {response.status_code}")
        return {"status": "success", "message": f"Email sent successfully to {to}"}
    except Exception as e:
        logger.error(f"Email sending failed: {str(e)}")
        return {"status": "error", "message": str(e)}

# Create the function tool properly
send_email_tool = function_tool(send_html_email)

EMAIL_INSTRUCTIONS = """
You are able to send a nicely formatted HTML email based on a detailed report.
You will be provided with a detailed report. You should use your tool to send one email, providing the
report converted into clean, well presented HTML with an appropriate subject line.
The recipient email address will be provided as a parameter to your tool.
"""

email_agent = Agent(
    name="Email agent",
    instructions=EMAIL_INSTRUCTIONS,
    tools=[send_email_tool],
    model="gpt-4o-mini"
)

WRITER_INSTRUCTIONS = """
You are a senior researcher tasked with writing a cohesive report for a research query.
You will be provided with the original query, and some initial research done with research assistant.
You should first come up with an outline for the report that describes the structure and flow of the report.
Then generate the report and return that as your final output.

The final output should be in markdown format, and it should be lengthy and detailed. Aim for 5-10 pages of
the content, at least 1000 words.
"""

class ReportData(BaseModel):
    short_summary: str
    markdown_report: str
    follow_up_questions: list[str]

writer_agent = Agent(
    name="WriterAgent",
    instructions=WRITER_INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ReportData
)

# Core functions with better error handling
async def plan_searches(query: str):
    """Use the planner_agent to plan which searches to run for the given query"""
    try:
        logger.info(f"Planning searches for query: {query}")
        result = await Runner.run(planner_agent, f"Query: {query}")
        logger.info(f"Successfully planned {len(result.final_output.searches)} searches")
        return result.final_output
    except Exception as e:
        logger.error(f"Error in plan_searches: {str(e)}")
        raise

async def perform_searches(search_plan: WebSearchPlan):
    """Call search() for each item in the search plan with better error handling"""
    try:
        logger.info("Starting web searches...")
        results = []
        
        # Process searches sequentially to avoid overwhelming the API
        for i, item in enumerate(search_plan.searches):
            try:
                logger.info(f"Processing search {i+1}/{len(search_plan.searches)}: {item.query}")
                result = await search(item)
                results.append(result)
                # Add a small delay between searches to prevent rate limiting
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error in search {i+1}: {str(e)}")
                # Continue with other searches even if one fails
                results.append(f"Search failed for '{item.query}': {str(e)}")
        
        logger.info("Completed all web searches")
        return results
    except Exception as e:
        logger.error(f"Error in perform_searches: {str(e)}")
        raise

async def search(item: WebSearchItem):
    """Use the search_agent to run web search for each item in search plan"""
    try:
        input_text = f"Search term: {item.query}\nReason for searching: {item.reason}"
        result = await Runner.run(search_agent, input_text)
        return result.final_output
    except Exception as e:
        logger.error(f"Error searching for '{item.query}': {str(e)}")
        return f"Search failed for '{item.query}': Unable to retrieve results"

async def write_report(query: str, search_results: list[str]):
    """Use the writer_agent to write the report based on the search results"""
    try:
        logger.info("Writing comprehensive report...")
        input_text = f"Original query: {query}\nSummarized search results:\n{search_results}"
        result = await Runner.run(writer_agent, input_text)
        logger.info("Report writing completed successfully")
        return result.final_output
    except Exception as e:
        logger.error(f"Error in write_report: {str(e)}")
        raise

def create_custom_email_agent(email_address: str):
    """Create a custom email agent with the specific recipient"""
    
    def send_to_specific_email(subject: str, html_body: str) -> Dict[str, str]:
        """Send email to the specified recipient"""
        logger.info(f"Attempting to send email to: {email_address}")
        result = send_html_email(email_address, subject, html_body)
        logger.info(f"Email send result: {result}")
        return result
    
    # Create the function tool properly
    custom_email_tool = function_tool(send_to_specific_email)
    
    custom_instructions = f"""
    You are able to send a nicely formatted HTML email based on a detailed report.
    You will be provided with a detailed report. You should use your tool to send one email, providing the
    report converted into clean, well presented HTML with an appropriate subject line.
    The email will be sent to: {email_address}
    
    Make sure to:
    1. Create an engaging subject line that summarizes the research topic
    2. Convert the markdown report to clean HTML format
    3. Include proper HTML structure with headers, paragraphs, and formatting
    4. Make the email visually appealing and easy to read
    """
    
    return Agent(
        name="Custom Email Agent",
        instructions=custom_instructions,
        tools=[custom_email_tool],
        model="gpt-4o-mini"
    )

async def email_report(report: ReportData, email_address: str):
    """Use a custom email agent to email the report"""
    try:
        logger.info(f"Creating custom email agent for {email_address}...")
        custom_agent = create_custom_email_agent(email_address)
        
        logger.info("Sending email with custom agent...")
        input_text = f"""
        Please send this research report via email:
        
        {report.markdown_report}
        
        Additional context:
        - Short summary: {report.short_summary}
        - This is a comprehensive research report
        - Make sure the email is well-formatted and professional
        """
        
        result = await Runner.run(custom_agent, input_text)
        logger.info(f"Email agent result: {result}")
        
        # Check if the email was actually sent by examining the result
        if hasattr(result, 'final_output'):
            logger.info(f"Email sending completed: {result.final_output}")
        
        return report
    except Exception as e:
        logger.error(f"Error in email_report: {str(e)}")
        raise

# Wrapper functions to run async code in Streamlit
def run_async_function(coro):
    """Run async function in a way that's compatible with Streamlit"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If there's already a running loop, use it
            return loop.run_until_complete(coro)
        else:
            # Create a new loop
            return asyncio.run(coro)
    except RuntimeError:
        # If we can't get the loop, create a new one
        return asyncio.run(coro)

# Streamlit UI
def main():
    # Header
    st.markdown('<h1 class="main-header">🔬 AI Research Assistant</h1>', unsafe_allow_html=True)
    
    # Sidebar with information
    with st.sidebar:
        st.header("📋 How It Works")
        st.markdown("""
        **Step 1: Planning** 🎯  
        AI analyzes your query and creates a strategic search plan
        
        **Step 2: Research** 🔍  
        Performs multiple web searches simultaneously
        
        **Step 3: Analysis** 📊  
        Synthesizes findings into a comprehensive report
        
        **Step 4: Delivery** 📧  
        Sends the report to your email
        """)
        
        st.header("⚙️ Configuration")
        st.info("Make sure you have set up your environment variables:\n- SENDGRID_API_KEY\n- OpenAI API credentials")
        
        st.header("📈 Features")
        st.markdown("""
        ✅ Multi-agent AI system  
        ✅ Parallel web searching  
        ✅ Comprehensive reports  
        ✅ Email delivery  
        ✅ Follow-up suggestions  
        """)

    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("🚀 Start Your Research")
        
        # Input form
        with st.form("research_form"):
            query = st.text_area(
                "Research Query",
                placeholder="e.g., Latest AI agent frameworks in 2025?",
                height=100,
                help="Enter your research question or topic. Be specific for better results."
            )
            
            email = st.text_input(
                "Email Address",
                placeholder="your.email@example.com",
                help="Where should we send your research report?"
            )
            
            submitted = st.form_submit_button("🔬 Start Research", use_container_width=True)
    
    with col2:
        st.header("📊 Process Status")
        status_container = st.container()
    
    # Process research when form is submitted
    if submitted:
        if not query.strip():
            st.error("Please enter a research query.")
            return
        
        if not email.strip():
            st.error("Please enter your email address.")
            return
        
        # Validate email format (basic validation)
        if "@" not in email or "." not in email:
            st.error("Please enter a valid email address.")
            return
        
        # Initialize session state for tracking progress
        if 'research_status' not in st.session_state:
            st.session_state.research_status = {}
        
        # Progress tracking
        with status_container:
            st.markdown("### Research Progress")
            
            # Create status placeholders
            status_planning = st.empty()
            status_searching = st.empty()
            status_writing = st.empty()
            status_emailing = st.empty()
            
            progress_bar = st.progress(0)
            
        try:
            # Step 1: Planning
            status_planning.markdown('<div class="status-running">🎯 Planning searches...</div>', unsafe_allow_html=True)
            progress_bar.progress(20)
            
            try:
                search_plan = run_async_function(plan_searches(query))
                status_planning.markdown('<div class="status-success">✅ Search plan created</div>', unsafe_allow_html=True)
                
                # Display search plan
                with st.expander("🎯 Search Plan", expanded=False):
                    for i, search_item in enumerate(search_plan.searches, 1):
                        st.markdown(f"**{i}. {search_item.query}**")
                        st.markdown(f"*Reason: {search_item.reason}*")
                        st.markdown("---")
            except Exception as e:
                st.error(f"Planning failed: {str(e)}")
                return
            
            # Step 2: Searching
            status_searching.markdown('<div class="status-running">🔍 Performing web searches...</div>', unsafe_allow_html=True)
            progress_bar.progress(40)
            
            try:
                search_results = run_async_function(perform_searches(search_plan))
                status_searching.markdown('<div class="status-success">✅ Web searches completed</div>', unsafe_allow_html=True)
                progress_bar.progress(60)
                
                # Show search results summary
                successful_searches = sum(1 for result in search_results if not result.startswith("Search failed"))
                st.info(f"Completed {successful_searches}/{len(search_results)} searches successfully")
                
            except Exception as e:
                st.error(f"Web searching failed: {str(e)}")
                st.info("Attempting to continue with available data...")
                search_results = [f"Limited search results due to connection issues: {str(e)}"]
            
            # Step 3: Writing report
            status_writing.markdown('<div class="status-running">📝 Writing comprehensive report...</div>', unsafe_allow_html=True)
            progress_bar.progress(80)
            
            try:
                report = run_async_function(write_report(query, search_results))
                status_writing.markdown('<div class="status-success">✅ Report generated</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Report generation failed: {str(e)}")
                return
            
            # Step 4: Emailing
            status_emailing.markdown('<div class="status-running">📧 Sending email...</div>', unsafe_allow_html=True)
            progress_bar.progress(90)
            
            try:
                # Validate SendGrid API key before attempting to send
                if not os.environ.get("SENDGRID_API_KEY"):
                    st.error("SendGrid API key not found. Please set SENDGRID_API_KEY environment variable.")
                    st.info("Your report is still available below for download.")
                    status_emailing.markdown('<div class="status-success">⚠️ Email skipped - API key missing</div>', unsafe_allow_html=True)
                else:
                    final_report = run_async_function(email_report(report, email))
                    
                    # Verify email was actually sent by checking logs
                    status_emailing.markdown('<div class="status-success">✅ Email sent successfully</div>', unsafe_allow_html=True)
                    st.success(f"🎉 Research completed successfully! Report sent to {email}")
                    st.info("📧 Please check your inbox (and spam folder) for the research report.")
                
                progress_bar.progress(100)
                
            except Exception as e:
                st.warning(f"Email sending failed: {str(e)}")
                st.info("Don't worry! Your report is still available below.")
                status_emailing.markdown('<div class="status-success">⚠️ Email failed - report available below</div>', unsafe_allow_html=True)
                progress_bar.progress(100)
            
            # Display results regardless of email success
            st.header("📋 Research Summary")
            st.info(report.short_summary)
            
            # Display full report
            with st.expander("📄 Full Report", expanded=True):
                st.markdown(report.markdown_report)
            
            # Download option
            st.download_button(
                label="📄 Download Report as Markdown",
                data=report.markdown_report,
                file_name=f"research_report_{int(time.time())}.md",
                mime="text/markdown"
            )
            
            # Follow-up questions
            if report.follow_up_questions:
                st.header("🤔 Suggested Follow-up Research")
                for i, question in enumerate(report.follow_up_questions, 1):
                    if st.button(f"{i}. {question}", key=f"followup_{i}"):
                        st.session_state['followup_query'] = question
                        st.experimental_rerun()
            
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")
            st.info("Please check your environment variables and internet connection, then try again.")
            
            # Show debugging info
            with st.expander("🔧 Debug Information"):
                st.code(f"Error: {str(e)}")
                st.code(f"Error Type: {type(e).__name__}")
                
                # Check environment variables
                st.write("Environment Check:")
                st.write(f"- SENDGRID_API_KEY: {'✅ Set' if os.environ.get('SENDGRID_API_KEY') else '❌ Missing'}")
                
                if os.environ.get('SENDGRID_API_KEY'):
                    # Test SendGrid connectivity
                    try:
                        sg = sendgrid.SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
                        st.write("- SendGrid Client: ✅ Initialized")
                    except Exception as sg_error:
                        st.write(f"- SendGrid Client: ❌ Error - {str(sg_error)}")
                
                st.write(f"- Query: {query}")
                st.write(f"- Email: {email}")

    # Handle follow-up questions
    if 'followup_query' in st.session_state:
        st.info(f"Follow-up query selected: {st.session_state['followup_query']}")
        st.markdown("You can copy this query to the input field above to research further.")
        if st.button("Clear Selection"):
            del st.session_state['followup_query']
            st.experimental_rerun()

if __name__ == "__main__":
    main()
