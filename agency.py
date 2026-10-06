import os
from typing import Literal

# Ensure Pydantic model compatibility between openai>=2.54.0 and openai-agents
try:
    import openai.types.responses.response_usage as _ru
    for _field in ["cache_write_tokens", "cached_tokens"]:
        if _field in _ru.InputTokensDetails.model_fields:
            _ru.InputTokensDetails.model_fields[_field].default = 0
    _ru.InputTokensDetails.model_rebuild(force=True)

    if "reasoning_tokens" in _ru.OutputTokensDetails.model_fields:
        _ru.OutputTokensDetails.model_fields["reasoning_tokens"].default = 0
        _ru.OutputTokensDetails.model_rebuild(force=True)
except Exception:
    pass

# Strip additionalProperties from tool schemas for Google Gemini and OmniKey compatibility
try:
    from agents.models.chatcmpl_converter import Converter
    _orig_tool_to_openai = Converter.tool_to_openai
    _orig_convert_handoff_tool = Converter.convert_handoff_tool

    def _clean_schema(schema):
        if isinstance(schema, dict):
            return {k: _clean_schema(v) for k, v in schema.items() if k != "additionalProperties"}
        elif isinstance(schema, list):
            return [_clean_schema(x) for x in schema]
        return schema

    def _patched_tool_to_openai(cls, tool):
        res = _orig_tool_to_openai(tool)
        if isinstance(res, dict) and "function" in res and "parameters" in res["function"]:
            res["function"]["parameters"] = _clean_schema(res["function"]["parameters"])
            res["function"]["strict"] = False
        return res

    def _patched_convert_handoff(cls, handoff):
        res = _orig_convert_handoff_tool(handoff)
        if isinstance(res, dict) and "function" in res and "parameters" in res["function"]:
            res["function"]["parameters"] = _clean_schema(res["function"]["parameters"])
            res["function"]["strict"] = False
        return res

    Converter.tool_to_openai = classmethod(_patched_tool_to_openai)
    Converter.convert_handoff_tool = classmethod(_patched_convert_handoff)
except Exception:
    pass

# Gracefully handle hallucinated tool calls from models
try:
    import agents._run_impl as _run_impl
    from agents.tools import FunctionTool

    def _adhoc_fallback_fn(output):
        async def on_invoke_tool(_ctx, value):
            return f"Tool {output.name} executed. Please provide your complete analysis and recommendations directly in markdown text."
        return FunctionTool(
            name=output.name,
            description=output.name,
            params_json_schema={},
            on_invoke_tool=on_invoke_tool,
            strict_json_schema=False,
            is_enabled=True,
        )
    _run_impl._build_adhoc_fallback_tool_call = _adhoc_fallback_fn
except Exception:
    pass



from openai import AsyncOpenAI
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
from agents.models._openai_shared import set_default_openai_client, set_use_responses_by_default
from agency_swarm import Agent, Agency, BaseTool, ModelSettings
from pydantic import Field
import streamlit as st

class AnalyzeProjectRequirements(BaseTool):
    """Analyze project requirements and feasibility."""

    project_name: str = Field(..., description="Name of the project")
    project_description: str = Field(..., description="Project description and goals")
    project_type: Literal["Web Application", "Mobile App", "API Development", 
                         "Data Analytics", "AI/ML Solution", "Other"] = Field(..., 
                         description="Type of project")
    budget_range: Literal["$10k-$25k", "$25k-$50k", "$50k-$100k", "$100k+"] = Field(..., 
                         description="Budget range for the project")

    class ToolConfig:
        name = "analyze_project"
        description = "Analyzes project requirements and feasibility"
        one_call_at_a_time = True

    def run(self) -> str:
        """Analyzes project and stores results in shared state"""
        analysis = {
            "name": self.project_name,
            "type": self.project_type,
            "complexity": "high",
            "timeline": "6 months",
            "budget_feasibility": "within range",
            "requirements": ["Scalable architecture", "Security", "API integration"]
        }
        
        self.context.set("project_analysis", analysis)
        return "Project analysis completed. Please proceed with technical specification."

class CreateTechnicalSpecification(BaseTool):
    """Create a technical specification based on project analysis."""

    architecture_type: Literal["monolithic", "microservices", "serverless", "hybrid"] = Field(
        ..., 
        description="Proposed architecture type"
    )
    core_technologies: str = Field(
        ..., 
        description="Comma-separated list of main technologies and frameworks"
    )
    scalability_requirements: Literal["high", "medium", "low"] = Field(
        ..., 
        description="Scalability needs"
    )

    class ToolConfig:
        name = "create_technical_spec"
        description = "Creates technical specifications based on project analysis"
        one_call_at_a_time = True

    def run(self) -> str:
        """Creates technical specification based on analysis"""
        project_analysis = self.context.get("project_analysis", None) or {}
        project_name = project_analysis.get("name", "Project")
        
        spec = {
            "project_name": project_name,
            "architecture": self.architecture_type,
            "technologies": [t.strip() for t in self.core_technologies.split(",") if t.strip()],
            "scalability": self.scalability_requirements
        }
        
        self.context.set("technical_specification", spec)
        return f"Technical specification created for {project_name}."

def init_session_state() -> None:
    """Initialize session state variables"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'api_key' not in st.session_state:
        st.session_state.api_key = None

def main() -> None:
    st.set_page_config(page_title="AI Services Agency", layout="wide")
    init_session_state()
    
    st.title("🚀 AI Services Agency")
    
    # Provider definitions with endpoints and default models
    providers = {
        "OmniKey AI": {
            "base_url": "https://omnikey-ai-unified-key-manager.onrender.com/v1",
            "models": [
                "gemini-2.5-flash",
                "gemini-1.5-flash",
                "gpt-4o-mini",
                "gpt-4o",
                "llama-3.3-70b-versatile",
                "claude-3-5-sonnet"
            ],
            "key_help": "OmniKey Unified API Key (OpenAI format, starts with omnikey-...)",
            "key_link": "https://omnikey-ai-unified-key-manager.onrender.com",
            "needs_key": True,
            "badge": "OmniKey Unified Router (OpenAI Format)",
            "note": "Make sure you have added at least one provider key (e.g. Gemini, Groq) in your OmniKey dashboard under 'Add a provider key'."
        },
        "Google Gemini": {
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "models": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash"],
            "key_help": "Google AI Studio API Key (starts with AIza...)",
            "key_link": "https://aistudio.google.com/app/apikey",
            "needs_key": True,
            "badge": "Free Tier Available"
        },
        "OpenRouter": {
            "base_url": "https://openrouter.ai/api/v1",
            "models": [
                "google/gemini-2.0-flash-exp:free",
                "meta-llama/llama-3.3-70b-instruct:free",
                "openai/gpt-4o-mini",
                "deepseek/deepseek-chat",
                "openai/gpt-4o"
            ],
            "key_help": "OpenRouter API Key (starts with sk-or-...)",
            "key_link": "https://openrouter.ai/keys",
            "needs_key": True,
            "badge": "Free & Low-Cost Models"
        },
        "Groq": {
            "base_url": "https://api.groq.com/openai/v1",
            "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
            "key_help": "Groq API Key (starts with gsk_...)",
            "key_link": "https://console.groq.com/keys",
            "needs_key": True,
            "badge": "Free Tier / Ultra Fast"
        },
        "OpenAI": {
            "base_url": "https://api.openai.com/v1",
            "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
            "key_help": "OpenAI API Key (starts with sk-...)",
            "key_link": "https://platform.openai.com/api-keys",
            "needs_key": True,
            "badge": "Requires Paid Credits"
        },
        "DeepSeek": {
            "base_url": "https://api.deepseek.com/v1",
            "models": ["deepseek-chat", "deepseek-reasoner"],
            "key_help": "DeepSeek API Key (starts with sk-...)",
            "key_link": "https://platform.deepseek.com/api_keys",
            "needs_key": True,
            "badge": "Low Cost"
        },
        "Ollama (Local)": {
            "base_url": "http://localhost:11434/v1",
            "models": ["llama3.2", "llama3.1", "mistral", "qwen2.5"],
            "key_help": "No API key needed for local Ollama",
            "key_link": "https://ollama.com",
            "needs_key": False,
            "badge": "100% Free / Local"
        },
        "Custom (OpenAI-Compatible)": {
            "base_url": "http://localhost:1234/v1",
            "models": ["default-model"],
            "key_help": "API Key for your custom endpoint",
            "key_link": "",
            "needs_key": False,
            "badge": "Custom Endpoint"
        }
    }
    
    # Provider & API Configuration Sidebar
    with st.sidebar:
        st.header("🔑 Provider & API Configuration")
        
        provider_name = st.selectbox(
            "AI Provider",
            list(providers.keys()),
            index=0,
            help="Choose your AI provider or any OpenAI-compatible service"
        )
        
        prov_info = providers[provider_name]
        st.caption(f"ℹ️ {prov_info['badge']}")
        if prov_info.get("note"):
            st.info(f"💡 {prov_info['note']}")
        
        # Base URL configuration
        if provider_name == "Custom (OpenAI-Compatible)":
            base_url = st.text_input(
                "API Base URL",
                value=st.session_state.get("custom_base_url", prov_info["base_url"]),
                help="Base URL of your OpenAI-compatible endpoint"
            )
            st.session_state.custom_base_url = base_url
        else:
            base_url = prov_info["base_url"]
            with st.expander("⚙️ Advanced: Endpoint URL", expanded=False):
                base_url = st.text_input("Endpoint Base URL", value=base_url)

        # API Key input
        api_key_session_val = st.session_state.get(f"key_{provider_name}") or st.session_state.get("api_key") or ""
        if prov_info["needs_key"]:
            api_key = st.text_input(
                f"{provider_name} API Key",
                type="password",
                value=api_key_session_val,
                help=prov_info["key_help"]
            )
            if not api_key:
                st.warning(f"⚠️ Please enter your {provider_name} API Key to proceed")
                if prov_info["key_link"]:
                    st.markdown(f"[👉 Get your {provider_name} API key here]({prov_info['key_link']})")
                return
            st.session_state[f"key_{provider_name}"] = api_key
            st.session_state.api_key = api_key
            st.success(f"{provider_name} Key accepted!")
        else:
            api_key = st.text_input(
                "API Key (Optional)",
                type="password",
                value=api_key_session_val or "local-key",
                help=prov_info["key_help"]
            ) or "local-key"
            st.session_state[f"key_{provider_name}"] = api_key
            st.session_state.api_key = api_key
            st.info(f"Using {provider_name}")

        # Model Selection
        model_options = prov_info["models"] + ["Custom model name..."]
        chosen_model = st.selectbox(
            "Model",
            model_options,
            index=0,
            help="Select a model preset or enter a custom model identifier"
        )
        if chosen_model == "Custom model name...":
            model_name = st.text_input("Custom Model Name", value="").strip()
            if not model_name:
                st.warning("Please enter a custom model name to continue.")
                return
        else:
            model_name = chosen_model

    # Configure Environment and Global Client
    os.environ["OPENAI_API_KEY"] = api_key
    os.environ["OPENAI_BASE_URL"] = base_url
    os.environ["OPENAI_DEFAULT_MODEL"] = model_name

    # Create universal ChatCompletions model instance for the selected provider
    async_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    try:
        from agents import set_tracing_disabled
        set_tracing_disabled(True)
    except Exception:
        pass
    set_default_openai_client(async_client)
    set_use_responses_by_default(False)

    agent_model = OpenAIChatCompletionsModel(model=model_name, openai_client=async_client)
    
    # Project Input Form
    with st.form("project_form"):
        st.subheader("Project Details")
        
        project_name = st.text_input("Project Name")
        project_description = st.text_area(
            "Project Description",
            help="Describe the project, its goals, and any specific requirements"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            project_type = st.selectbox(
                "Project Type",
                ["Web Application", "Mobile App", "API Development", 
                 "Data Analytics", "AI/ML Solution", "Other"]
            )
            timeline = st.selectbox(
                "Expected Timeline",
                ["1-2 months", "3-4 months", "5-6 months", "6+ months"]
            )
        
        with col2:
            budget_range = st.selectbox(
                "Budget Range",
                ["$10k-$25k", "$25k-$50k", "$50k-$100k", "$100k+"]
            )
            priority = st.selectbox(
                "Project Priority",
                ["High", "Medium", "Low"]
            )
        
        tech_requirements = st.text_area(
            "Technical Requirements (optional)",
            help="Any specific technical requirements or preferences"
        )
        
        special_considerations = st.text_area(
            "Special Considerations (optional)",
            help="Any additional information or special requirements"
        )
        
        submitted = st.form_submit_button("Analyze Project")
        
        if submitted and project_name and project_description:
            try:
                # Create agents with provider-agnostic ChatCompletions model
                ceo = Agent(
                    name="Project Director",
                    description="You are a CEO of multiple companies in the past and have a lot of experience in evaluating projects and making strategic decisions.",
                    instructions="""
                    You are an experienced CEO who evaluates projects. Follow these steps strictly:

                    1. FIRST, use the AnalyzeProjectRequirements tool with:
                       - project_name: The name from the project details
                       - project_description: The full project description
                       - project_type: The type of project (Web Application, Mobile App, etc)
                       - budget_range: The specified budget range

                    2. WAIT for the analysis to complete before proceeding.
                    
                    3. Review the analysis results and provide strategic recommendations.
                    """,
                    tools=[AnalyzeProjectRequirements],
                    model=agent_model,
                    model_settings=ModelSettings(temperature=0.7, max_tokens=4096),
                )

                cto = Agent(
                    name="Technical Architect",
                    description="Senior technical architect with deep expertise in system design.",
                    instructions="""
                    You are a technical architect. Follow these steps strictly:

                    1. WAIT for the project analysis to be completed by the CEO.
                    
                    2. Use the CreateTechnicalSpecification tool with:
                       - architecture_type: Choose from monolithic/microservices/serverless/hybrid
                       - core_technologies: List main technologies as comma-separated values
                       - scalability_requirements: Choose high/medium/low based on project needs

                    3. Review the technical specification and provide additional recommendations.
                    """,
                    tools=[CreateTechnicalSpecification],
                    model=agent_model,
                    model_settings=ModelSettings(temperature=0.5, max_tokens=4096),
                )

                product_manager = Agent(
                    name="Product Manager",
                    description="Experienced product manager focused on delivery excellence.",
                    instructions="""
                    You are an experienced Product Manager.
                    IMPORTANT: You do not have any tools. Do NOT attempt to call any tools or functions.
                    Provide your complete analysis, roadmap, scope management, and feature recommendations directly in detailed, structured Markdown text.
                    - Manage project scope and timeline giving the roadmap of the project
                    - Define product requirements and provide potential products and features that can be built for the startup
                    """,
                    model=agent_model,
                    model_settings=ModelSettings(temperature=0.4, max_tokens=4096),
                )

                developer = Agent(
                    name="Lead Developer",
                    description="Senior developer with full-stack expertise.",
                    instructions="""
                    You are the Lead Developer.
                    IMPORTANT: You do not have any tools. Do NOT attempt to call any tools or functions.
                    Provide your complete technical implementation plan, effort estimates, tech stack analysis, and cloud costs directly in detailed, structured Markdown text.
                    - Plan technical implementation
                    - Provide effort estimates
                    - Review technical feasibility
                    """,
                    model=agent_model,
                    model_settings=ModelSettings(temperature=0.3, max_tokens=4096),
                )

                client_manager = Agent(
                    name="Client Success Manager",
                    description="Experienced client manager focused on project delivery.",
                    instructions="""
                    You are the Client Success Manager.
                    IMPORTANT: You do not have any tools. Do NOT attempt to call any tools or functions.
                    Provide your complete client success strategy, customer acquisition plan, and go-to-market plan directly in detailed, structured Markdown text.
                    - Ensure client satisfaction
                    - Manage expectations
                    - Handle feedback
                    """,
                    model=agent_model,
                    model_settings=ModelSettings(temperature=0.6, max_tokens=4096),
                )

                # Create agency
                agency = Agency(
                    ceo,
                    cto,
                    product_manager,
                    developer,
                    client_manager,
                    communication_flows=[
                        (ceo, cto),
                        (ceo, product_manager),
                        (ceo, developer),
                        (ceo, client_manager),
                        (cto, developer),
                        (product_manager, developer),
                        (product_manager, client_manager),
                    ],
                )
                
                # Prepare project info
                project_info = {
                    "name": project_name,
                    "description": project_description,
                    "type": project_type,
                    "timeline": timeline,
                    "budget": budget_range,
                    "priority": priority,
                    "technical_requirements": tech_requirements,
                    "special_considerations": special_considerations
                }

                st.session_state.messages.append({"role": "user", "content": str(project_info)})
                # Create tabs and run analysis
                with st.spinner(f"AI Services Agency ({provider_name} / {model_name}) is analyzing your project..."):
                    try:
                        # Get analysis from each agent using get_response_sync.
                        ceo_response = str(
                            agency.get_response_sync(
                            message=f"""Analyze this project using the AnalyzeProjectRequirements tool:
                            Project Name: {project_name}
                            Project Description: {project_description}
                            Project Type: {project_type}
                            Budget Range: {budget_range}
                            
                            Use these exact values with the tool and wait for the analysis results.""",
                            recipient_agent=ceo
                            ).final_output
                        )
                        
                        cto_response = str(
                            agency.get_response_sync(
                            message=f"""Review the project analysis and create technical specifications using the CreateTechnicalSpecification tool.
                            Choose the most appropriate:
                            - architecture_type (monolithic/microservices/serverless/hybrid)
                            - core_technologies (comma-separated list)
                            - scalability_requirements (high/medium/low)
                            
                            Base your choices on the project requirements and analysis.""",
                            recipient_agent=cto
                            ).final_output
                        )
                        
                        pm_response = str(
                            agency.get_response_sync(
                            message=f"""Provide a comprehensive product management plan in markdown text for the project (do NOT call any tools, write your response directly in markdown):
{str(project_info)}""",
                            recipient_agent=product_manager,
                            additional_instructions="Do not call any tools. Provide your analysis directly in detailed Markdown covering product-market fit, timeline, feature roadmap, and prioritization."
                            ).final_output
                        )

                        developer_response = str(
                            agency.get_response_sync(
                            message=f"""Provide a comprehensive technical implementation plan in markdown text based on CTO's specifications (do NOT call any tools, write your response directly in markdown):
{str(project_info)}""",
                            recipient_agent=developer,
                            additional_instructions="Do not call any tools. Provide your analysis directly in detailed Markdown covering implementation architecture, optimal tech stack, estimated cloud costs, and delivery timeline."
                            ).final_output
                        )
                        
                        client_response = str(
                            agency.get_response_sync(
                            message=f"""Provide a comprehensive client success and go-to-market strategy in markdown text (do NOT call any tools, write your response directly in markdown):
{str(project_info)}""",
                            recipient_agent=client_manager,
                            additional_instructions="Do not call any tools. Provide your analysis directly in detailed Markdown covering client satisfaction, go-to-market strategy, customer acquisition, and communication frameworks."
                            ).final_output
                        )
                        
                        # Create tabs for different analyses
                        tabs = st.tabs([
                            "CEO's Project Analysis",
                            "CTO's Technical Specification",
                            "Product Manager's Plan",
                            "Developer's Implementation",
                            "Client Success Strategy"
                        ])
                        
                        with tabs[0]:
                            st.markdown("## CEO's Strategic Analysis")
                            st.markdown(ceo_response)
                            st.session_state.messages.append({"role": "assistant", "content": ceo_response})
                        
                        with tabs[1]:
                            st.markdown("## CTO's Technical Specification")
                            st.markdown(cto_response)
                            st.session_state.messages.append({"role": "assistant", "content": cto_response})
                        
                        with tabs[2]:
                            st.markdown("## Product Manager's Plan")
                            st.markdown(pm_response)
                            st.session_state.messages.append({"role": "assistant", "content": pm_response})
                        
                        with tabs[3]:
                            st.markdown("## Lead Developer's Development Plan")
                            st.markdown(developer_response)
                            st.session_state.messages.append({"role": "assistant", "content": developer_response})
                        
                        with tabs[4]:
                            st.markdown("## Client Success Strategy")
                            st.markdown(client_response)
                            st.session_state.messages.append({"role": "assistant", "content": client_response})

                    except Exception as e:
                        error_msg = str(e)
                        cause = getattr(e, "__cause__", None)
                        if cause:
                            error_msg += f"\n\n**Cause**: {str(cause)}"
                        st.error(f"Error during analysis: {error_msg}")
                        st.error("Please check your provider selection, model, and API key and try again.")

            except Exception as e:
                error_msg = str(e)
                cause = getattr(e, "__cause__", None)
                if cause:
                    error_msg += f"\n\n**Cause**: {str(cause)}"
                st.error(f"Error during analysis: {error_msg}")
                st.error("Please check your API key and try again.")

    # Add history management in sidebar
    with st.sidebar:
        st.subheader("Options")
        if st.checkbox("Show Analysis History"):
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        
        if st.button("Clear History"):
            st.session_state.messages = []
            st.rerun()

if __name__ == "__main__":
    main()
