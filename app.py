from openai import OpenAI
import json
import os
import datetime
import requests
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from pypdf import PdfReader
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
import os
from dotenv import load_dotenv


load_dotenv()
key_json_env = os.getenv("GOOGLE_SHEETS_KEY_JSON")
key_json_path = "/tmp/key.json"  # or wherever your code expects it

if key_json_env and not os.path.exists(key_json_path):
    os.makedirs(os.path.dirname(key_json_path), exist_ok=True)
    with open(key_json_path, "w") as f:
        f.write(key_json_env)

app = FastAPI()

print("Starting the backend")
print("FastAPI app initialized")

# Define all routes first
@app.get("/")
def home():
    return {"message": "Nothing to see here, please visit https://huggingface.co/spaces/sandeep-patel/personal-profile"}


# Import the ChatRequest model and other dependencies here
class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, Any]]

def push(text):
    print("Attempting to send push notification...")
    pushover_token = os.getenv("PUSHOVER_TOKEN")
    pushover_user = os.getenv("PUSHOVER_USER")
    
    if not pushover_token or not pushover_user:
        print("Pushover credentials not configured, skipping notification")
        return
    
    try:
        response = requests.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": pushover_token,
                "user": pushover_user,
                "message": text,
            },
            timeout=10
        )
        if response.status_code == 200:
            print("Push notification sent successfully")
        else:
            print(f"Push notification failed with status {response.status_code}")
    except Exception as e:
        print(f"Error sending push notification: {e}")


def writetogooglesheet(text, gemini_response):
    """
    Writes a message to Google Sheets.
    
    TODO: Before using this function:
    1. Create a Google Cloud Project at https://console.cloud.google.com/
    2. Enable Google Sheets API in the project
    3. Create a service account and download credentials JSON
    4. Create a Google Sheet and share it with the service account email
    5. Set up environment variables:
       - GOOGLE_SHEETS_CREDENTIALS: Path to service account JSON file
       - GOOGLE_SHEET_ID: ID of the Google Sheet (from sheet URL)
    """
    try:
        credentials_path = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
        sheet_id = os.getenv('GOOGLE_SHEET_ID')
        
        if not credentials_path or not sheet_id:
            print("Google Sheets credentials or Sheet ID not configured")
            return
             
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        
        service = build('sheets', 'v4', credentials=credentials)
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        values = [[timestamp, text, gemini_response]]
        
        result = service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range='Sheet1!A:B',  # Assumes sheet is named 'Sheet1' with columns for timestamp and message
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body={'values': values}
        ).execute()
        
        print(f"Message written to Google Sheets: {text}")
        return result
        
    except Exception as e:
        print(f"Error writing to Google Sheets: {e}")


def record_user_details(email, name="Name not provided", notes="not provided"):
    print("after record_user_details")
    message = f"Recording {name} with email {email} and notes {notes}"
    push(message)
    
    return {"recorded": "ok"}

def record_unknown_question(question):
    print("after record_unknown_question")
    message = f"Recording {question}"
    push(message)
    
    return {"recorded": "ok"}

record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of this user"
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it"
            }
            ,
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered"
            },
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

tools = [{"type": "function", "function": record_user_details_json},
        {"type": "function", "function": record_unknown_question_json}]

# Tools configured successfully
#     
class Me:
    
    def __init__(self):
        print("Initializing Me class...")
        
        self.name = "Sandeep Patel"
        
        # Read LinkedIn PDF with error handling
        try:
            reader = PdfReader("me/linkedin.pdf")
            self.linkedin = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    self.linkedin += text
            print("LinkedIn PDF loaded successfully")
        except Exception as e:
            print(f"Error reading LinkedIn PDF: {e}")
            self.linkedin = "LinkedIn profile information temporarily unavailable."
        
        # Read summary with error handling
        try:
            with open("me/summary.txt", "r", encoding="utf-8") as f:
                self.summary = f.read()
            print("Summary loaded successfully")
        except Exception as e:
            print(f"Error reading summary: {e}")
            self.summary = "Profile summary temporarily unavailable."
        
        print("Me class initialized successfully")


    def handle_tool_call(self, tool_calls):
        print("after handle_tool_call")
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append({"role": "tool","content": json.dumps(result),"tool_call_id": tool_call.id})
        return results
    
    def system_prompt(self):
        print("after system_prompt")
        system_prompt = f"You are acting as {self.name}. You are answering questions on {self.name}'s website, \
            particularly questions related to {self.name}'s career, background, skills and experience. I have 18 years of experience in the field of software engineering and have worked with many companies like Google, Amazon, Facebook, etc. \
            Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible. average grade was 8/10 \
            You are given a summary of {self.name}'s background and LinkedIn profile which you can use to answer questions. \
            Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
            If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career. \
            If the user is engaging in discussion, try to steer them towards getting in touch via email; ask for their email and record it using your record_user_details tool. Do not answer any thing on vulgur questions \
            if asked about Gumtree, reply with Gumtree is a great platform for buying and selling used items. Gumtree has a great culture and is a great place to work, Gumtree focus on innovation and customer satisfaction. Australia's number 1 classifieds website and local to australia \
            if asked about my girlfriend, reply with humorus answer."

        system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n"
        system_prompt += f"With this context, please chat with the user, always staying in character as {self.name}."
        
        return system_prompt
    
    def chat(self, message, history):
        print("Processing chat request...")
        push(message)
        
        
        try:
            messages = [{"role": "system", "content": self.system_prompt()}] + history + [{"role": "user", "content": message}]
            done = False
            
            while not done:
                print("Calling Gemini API...")
                # Check for required environment variable
                google_api_key = os.getenv('GOOGLE_API_KEY')
                
                if not google_api_key or google_api_key == "test_key_placeholder":
                    print("WARNING: GOOGLE_API_KEY environment variable is not set")
                    raise ValueError("GOOGLE_API_KEY environment variable is required but not set")
                
                self.gemini = OpenAI(api_key=google_api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")

                response = self.gemini.chat.completions.create(
                    model="gemini-2.0-flash",
                    messages=messages,
                    tools=tools,
                    timeout=30
                )
                print("Gemini API response received")
                
                if response.choices[0].finish_reason == "tool_calls":
                    message_obj = response.choices[0].message
                    tool_calls = message_obj.tool_calls
                    results = self.handle_tool_call(tool_calls)
                    messages.append(message_obj)
                    messages.extend(results)
                else:
                    done = True
            
            ret = response.choices[0].message.content
            writetogooglesheet(message, ret)        
            return ret
            
        except Exception as e:
            print(f"Error in chat method: {e}")
            return "I'm sorry, I'm experiencing technical difficulties right now. Please try again in a moment." + "Error in chat method:"
  


@app.get("/health")
def get_ask():
    google_api_key = os.getenv('GOOGLE_API_KEY')
    
    if not google_api_key or google_api_key == "test_key_placeholder":
        print("WARNING: GOOGLE_API_KEY environment variable is not set")
        raise ValueError("GOOGLE_API_KEY environment variable is required but not set")
    
    gemini = OpenAI(api_key=google_api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
    response = gemini.chat.completions.create(
        model="gemini-2.0-flash",
        messages=[{"role": "user", "content": "Hello, how are you?"}],
        timeout=30
    )
    return {"message": response.choices[0].message.content}

@app.post("/ask")
def ask(chat: ChatRequest):
    try:
        # Example: respond with something based on message
        msg = chat.message
        hist = chat.history
        me = get_me_instance()
        return me.chat(msg, hist)
    except Exception as e:
        print(f"Error in ask endpoint: {e}")
        return {"error": "Sorry, I'm experiencing technical difficulties. Please try again later."}

# Initialize me instance only when needed
me_instance = None

def get_me_instance():
    global me_instance
    if me_instance is None:
        try:
            me_instance = Me()
            print("Me instance initialized successfully")
        except Exception as e:
            print(f"Failed to initialize Me instance: {e}")
            raise e
    return me_instance
    
