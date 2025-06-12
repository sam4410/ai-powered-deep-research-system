# 🔬 AI Research Assistant

A sophisticated multi-agent AI research system built with OpenAI Agents SDK and Streamlit that automatically conducts comprehensive web research, synthesizes findings, and delivers professional reports via email.

![AI Research Assistant](https://img.shields.io/badge/AI-Research%20Assistant-blue?style=for-the-badge&logo=openai)
![Python](https://img.shields.io/badge/Python-3.8%2B-green?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-red?style=for-the-badge&logo=streamlit)

## 🎯 Purpose

The AI Research Assistant revolutionizes the research process by automating the entire workflow from query planning to report delivery. It's designed for:

- **Researchers** who need comprehensive market analysis
- **Business professionals** requiring industry insights
- **Students** conducting academic research
- **Analysts** gathering competitive intelligence
- **Anyone** who needs thorough, structured research on complex topics

## ✨ Key Features

### 🤖 Multi-Agent Architecture
- **Planner Agent**: Strategically breaks down research queries into targeted searches
- **Search Agent**: Performs intelligent web searches and summarizes findings
- **Writer Agent**: Synthesizes research into comprehensive, structured reports
- **Email Agent**: Delivers professionally formatted reports via email

### 🚀 Advanced Capabilities
- **Parallel Processing**: Simultaneous web searches for faster results
- **Intelligent Planning**: AI-driven search strategy development
- **Comprehensive Reports**: 1000+ word detailed analysis with structure
- **Email Integration**: Automatic delivery with HTML formatting
- **Follow-up Suggestions**: AI-generated topics for deeper research
- **Progress Tracking**: Real-time status updates with visual indicators
- **Error Resilience**: Graceful handling of connection issues and API limits

### 💡 User Experience
- **Modern UI**: Clean, responsive Streamlit interface
- **One-Click Research**: Simple query input and email delivery
- **Download Options**: Markdown report download capability
- **Debug Tools**: Comprehensive error reporting and environment checking

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Query    │───▶│  Planner Agent  │───▶│  Search Plan    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
┌─────────────────┐    ┌─────────────────┐             │
│ Email Delivery  │◀───│  Email Agent    │             │
└─────────────────┘    └─────────────────┘             │
         ▲                                              │
         │              ┌─────────────────┐             │
         │              │  Writer Agent   │             │
         │              └─────────────────┘             │
         │                       ▲                      │
         │                       │                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Final Report    │◀───│ Synthesis &     │◀───│  Search Agent   │
│ (1000+ words)   │    │ Analysis        │    │ (Multiple Web   │
└─────────────────┘    └─────────────────┘    │ Searches)       │
                                              └─────────────────┘
```

## AI Research Assistant - Agent Flow 

![image](https://github.com/user-attachments/assets/ea02568d-ff1b-4490-a983-13e0b7858e8e)


## 🛠️ Implementation Details

### Core Components

#### 1. Agent Configuration
```python
# Planner Agent - Strategic query breakdown
planner_agent = Agent(
    name="Planner",
    instructions=PLANNER_INSTRUCTIONS,
    tools=[WebSearchTool(search_context_size="low")],
    model="gpt-4o-mini",
    output_type=WebSearchPlan
)

# Search Agent - Web research execution
search_agent = Agent(
    name="Search Agent",
    instructions=SEARCH_INSTRUCTIONS,
    tools=[WebSearchTool(search_context_size="low")],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required")
)
```

#### 2. Async Processing Pipeline
- **Sequential Search Processing**: Prevents API rate limiting
- **Error Resilience**: Continues processing even if individual searches fail
- **Progress Tracking**: Real-time status updates via Streamlit

#### 3. Email Integration
- **SendGrid API**: Professional email delivery
- **HTML Formatting**: Rich text reports with proper structure
- **Custom Recipients**: Dynamic email addressing

## 📋 Requirements

### System Requirements
- Python 3.8 or higher
- Internet connection for web searches
- SendGrid account for email functionality
- OpenAI API access for agents

### Python Dependencies
```
streamlit>=1.28.0
python-dotenv>=1.0.0
sendgrid>=6.10.0
nest-asyncio>=1.5.6
pydantic>=2.5.0
requests>=2.31.0
```

### API Keys Required
- **OpenAI API Key**: For agent functionality
- **SendGrid API Key**: For email delivery

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/ai-research-assistant.git
cd ai-research-assistant
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Install OpenAI Agents SDK
```bash
# Check OpenAI documentation for latest installation method
pip install openai-agents
# or
pip install git+https://github.com/openai/openai-agents.git
```

### 4. Environment Configuration
Create a `.env` file in the project root:
```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# SendGrid Configuration
SENDGRID_API_KEY=your_sendgrid_api_key_here
```

### 5. SendGrid Setup
1. Create a SendGrid account at [sendgrid.com](https://sendgrid.com)
2. Generate an API key with "Mail Send" permissions
3. Verify your sender email address
4. Update the sender email in the code if needed

## 🎯 Usage Guide

### Basic Usage
1. **Launch the Application**
   ```bash
   streamlit run app.py
   ```

2. **Access the Interface**
   - Open your browser to `http://localhost:8501`
   - You'll see the AI Research Assistant interface

3. **Conduct Research**
   - Enter your research query in the text area
   - Provide your email address for report delivery
   - Click "Start Research" button

4. **Monitor Progress**
   - Watch real-time status updates
   - View the search plan as it's created
   - Track progress through each stage

5. **Review Results**
   - Read the research summary
   - Expand the full report
   - Download the markdown version
   - Check your email for the formatted report

### Advanced Features

#### Custom Search Strategies
The system automatically creates 5 targeted searches based on your query. For example:
- Query: "Latest AI agent frameworks in 2025"
- Generated searches: Framework comparisons, recent releases, performance benchmarks, etc.

#### Follow-up Research
After completing research, the system suggests related topics for deeper investigation.

#### Error Recovery
If searches fail, the system continues with available data and provides debugging information.

## 📊 Example Workflows

### Business Intelligence
```
Query: "Electric vehicle market trends 2025"
Result: Comprehensive market analysis including:
- Market size and growth projections
- Key players and competitive landscape
- Technology developments
- Regional market variations
- Investment trends
```

### Academic Research
```
Query: "Impact of remote work on productivity"
Result: Detailed research report covering:
- Statistical studies and findings
- Industry-specific impacts
- Long-term trend analysis
- Expert opinions and predictions
- Methodology comparisons
```

### Technology Analysis
```
Query: "Blockchain applications in healthcare"
Result: Technical report including:
- Current implementations
- Regulatory considerations
- Security and privacy aspects
- Future potential applications
- Challenges and limitations
```

## 🔧 Configuration Options

### Customizing Agents
- **Search Depth**: Modify `search_context_size` parameter
- **Report Length**: Adjust word count requirements in instructions
- **Search Count**: Change `NUM_SEARCHES` variable
- **Model Selection**: Switch between different OpenAI models

### Email Customization
- **Sender Email**: Update in `send_html_email` function
- **Email Template**: Modify HTML formatting in email agent instructions
- **Subject Lines**: Customize in email agent configuration

## 🐛 Troubleshooting

### Common Issues

#### Email Not Received
1. Check spam/junk folder
2. Verify SendGrid API key permissions
3. Ensure sender email is verified in SendGrid
4. Check the debug panel for error messages

#### Connection Errors
1. Verify internet connection
2. Check OpenAI API key validity
3. Monitor API rate limits
4. Review firewall settings

#### Performance Issues
1. Reduce number of searches (`NUM_SEARCHES`)
2. Use smaller context size for searches
3. Check system resources
4. Monitor API quotas

### Debug Features
- **Environment Check**: Validates API keys and configuration
- **Error Logging**: Detailed error messages and stack traces
- **Progress Monitoring**: Real-time status updates
- **Fallback Options**: Download reports if email fails

## 🚀 Future Enhancement Ideas

### Short-term Enhancements
- **Multi-language Support**: Research in different languages
- **Export Formats**: PDF, Word, PowerPoint export options
- **Research Templates**: Pre-built templates for common research types
- **Collaboration Features**: Share reports with teams
- **Research History**: Save and manage previous research sessions

### Medium-term Developments
- **Advanced Analytics**: Sentiment analysis, trend detection
- **Visual Reports**: Charts, graphs, and infographics
- **API Integration**: Connect with business intelligence tools
- **Batch Processing**: Multiple queries simultaneously
- **Custom Agents**: User-defined research specialists

### Long-term Vision
- **Knowledge Base**: Build persistent research database
- **AI Recommendations**: Suggest research topics based on history
- **Real-time Monitoring**: Continuous research updates
- **Enterprise Features**: Team management, access controls
- **Mobile App**: Native mobile research experience

### Integration Possibilities
- **CRM Systems**: Salesforce, HubSpot integration
- **Document Management**: SharePoint, Google Drive sync
- **Business Intelligence**: Tableau, Power BI connectors
- **Slack/Teams**: Chat-based research requests
- **Calendar Integration**: Scheduled research reports

## 📈 Performance Optimization

### Current Optimizations
- **Sequential Processing**: Prevents API rate limiting
- **Async Operations**: Non-blocking operations for better performance
- **Error Handling**: Graceful degradation and recovery
- **Caching**: Streamlit caching for improved response times

### Scalability Considerations
- **API Limits**: Implements rate limiting and retry logic
- **Memory Management**: Efficient data handling for large reports
- **Concurrent Users**: Streamlit session management
- **Resource Usage**: Optimized for cloud deployment

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### Areas for Contribution
- **Bug Fixes**: Report and fix issues
- **Feature Development**: Implement new capabilities
- **Documentation**: Improve guides and examples
- **Testing**: Add test cases and quality assurance
- **UI/UX**: Enhance user interface and experience

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Code Standards
- Follow PEP 8 style guidelines
- Add docstrings to functions
- Include type hints where appropriate
- Write clear commit messages
- Test thoroughly before submitting

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** for the Agents SDK and GPT models
- **Streamlit** for the excellent web framework
- **SendGrid** for reliable email delivery
- **Community** for feedback and contributions

## 📞 Support

For support and questions:
- **Issues**: Open a GitHub issue
- **Discussions**: Use GitHub Discussions
- **Email**: [sharma.manoj84@yahoo.co.in]
- **Documentation**: Check the wiki for detailed guides

---

## 🎖️ Star History

If you find this project useful, please consider giving it a star! ⭐

---

**Built with ❤️ by the AI Research Assistant Team**
