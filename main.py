from flask import Flask, request, jsonify, render_template, url_for
from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from tools import duck_tool, wiki_tool, save_tool, txt_to_pdf
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_tool_calling_agent, AgentExecutor # note alternative calling agents available
import logging
import os

# Initial setup
load_dotenv()
api_key = os.getenv("ANTHROPIC_API_KEY")
app = Flask(__name__, static_folder='static', template_folder='templates')
logging.basicConfig(level=logging.DEBUG)
os.makedirs('static/downloads', exist_ok=True) # Create directories if they don't exist

# Define llm's output
class ResearchResponse(BaseModel):
    topic: str
    summary: str
    sources: list[str]
    tools_used: list[str]

# Setup the LLM and parser
llm = ChatAnthropic(model="claude-3-7-sonnet-20250219") # note other Claude and OpenAI models are available
parser = PydanticOutputParser(pydantic_object=ResearchResponse)

# Setup the prompt template
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            You are a research assistant that will help generate answers to a user's query.
            Answer the user query and use necessary tools.
            Wrap the output in this format and provide no other text\n{format_instructions}
            """,
        ),
        ("placeholder", "{chat_history}"),
        ("human", "{query}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
).partial(format_instructions=parser.get_format_instructions())

# Setup the agent
tools = [duck_tool, wiki_tool, save_tool]
agent = create_tool_calling_agent(
    llm=llm,
    prompt=prompt,
    tools=tools # 3rd party tools, see tools.py
)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools, # 3rd party tools, see tools.py
    verbose=True # mark False if thought-process of agent is not essential
)

# Define the Flask routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/research', methods=['POST'])
def research():
    data = request.get_json()
    name = data.get('name', 'User')
    query = data.get('query', '')
    
    try:
        # Execute the agent
        raw_response = agent_executor.invoke({"query": query})
        print(f"Raw response: {raw_response}")
        
        # Fix the syntax error in accessing the output
        if "output" in raw_response and isinstance(raw_response["output"], list) and len(raw_response["output"]) > 0:
            output_text = raw_response["output"][0]["text"]
        elif "output" in raw_response:
            output_text = raw_response["output"]
        else:
            output_text = str(raw_response)
            
        print(f"Output text: {output_text}")
        
        structured_response = parser.parse(output_text)
        
        # Clean filenames to avoid invalid characters
        safe_name = ''.join(c for c in name if c.isalnum() or c == '_' or c == ' ').strip().replace(' ', '_')
        safe_topic = ''.join(c for c in structured_response.topic if c.isalnum() or c == '_' or c == ' ').strip().replace(' ', '_')
        
        txt_filename = f"static/downloads/research_{safe_name}_{safe_topic}.txt"
        pdf_filename = f"static/downloads/research_{safe_name}_{safe_topic}.pdf"
        
        print(f"Attempting to write to text file: {txt_filename}")
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(txt_filename), exist_ok=True)
            
            # Test if we can write to the directory
            test_path = os.path.join(os.path.dirname(txt_filename), "test_write.txt")
            with open(test_path, 'w') as test_file:
                test_file.write("Test write")
            os.remove(test_path)
            print("Directory is writable")
            
            # Save txt content
            with open(txt_filename, 'w') as f:
                f.write(f"Topic: {structured_response.topic}\n")
                f.write(f"Summary: {structured_response.summary}\n")
                f.write("Sources:\n")
                for source in structured_response.sources:
                    f.write(f"- {source}\n")
            
            print(f"Successfully wrote text file: {txt_filename}")
            
            # Verify text file exists
            if os.path.exists(txt_filename):
                print(f"Text file exists, size: {os.path.getsize(txt_filename)} bytes")
            else:
                print(f"Failed to create text file: {txt_filename}")
                return jsonify({'error': f"Could not create text file: {txt_filename}"}), 500
            
            # Convert text to PDF
            print(f"Attempting to convert to PDF: {pdf_filename}")
            txt_to_pdf(txt_filename, pdf_filename)
            
            # Verify PDF file exists
            if os.path.exists(pdf_filename):
                print(f"PDF file created successfully, size: {os.path.getsize(pdf_filename)} bytes")
            else:
                print(f"Failed to create PDF file: {pdf_filename}")
                return jsonify({
                    'topic': structured_response.topic,
                    'summary': structured_response.summary,
                    'sources': structured_response.sources,
                    'tools_used': structured_response.tools_used,
                    'pdf_path': None,
                    'txt_path': '/static/downloads/' + os.path.basename(txt_filename)
                })
            
            return jsonify({
                'topic': structured_response.topic,
                'summary': structured_response.summary,
                'sources': structured_response.sources,
                'tools_used': structured_response.tools_used,
                'pdf_path': '/static/downloads/' + os.path.basename(pdf_filename),
                'txt_path': '/static/downloads/' + os.path.basename(txt_filename)
            })
            
        except IOError as io_error:
            print(f"IO Error: {io_error}")
            return jsonify({'error': f"File IO Error: {str(io_error)}"}), 500
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    
if __name__ == '__main__':
    app.run(debug=True)