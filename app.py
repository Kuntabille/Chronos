import os
from dotenv import load_dotenv
import chainlit as cl
import openai
import asyncio
import json
from datetime import datetime
from prompts import ASSESSMENT_PROMPT, SYSTEM_PROMPT, CLASS_CONTEXT, CHARACTER_CREATION
from langsmith.wrappers import wrap_openai
from langsmith import traceable
from player_record import read_player_record, write_player_record, format_player_record, parse_player_record, save_player_character
from rag import load_index_for_rag, fetch_relevant_documents

# Load environment variables
load_dotenv()

configurations = {
    "mistral_7B_instruct": {
        "endpoint_url": os.getenv("MISTRAL_7B_INSTRUCT_ENDPOINT"),
        "api_key": os.getenv("RUNPOD_API_KEY"),
        "model": "mistralai/Mistral-7B-Instruct-v0.2"
    },
    "mistral_7B": {
        "endpoint_url": os.getenv("MISTRAL_7B_ENDPOINT"),
        "api_key": os.getenv("RUNPOD_API_KEY"),
        "model": "mistralai/Mistral-7B-v0.1"
    },
    "openai_gpt-4": {
        "endpoint_url": os.getenv("OPENAI_ENDPOINT"),
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model": "gpt-4"
    }, 
    "openai_gpt-4o": {
        "endpoint_url": os.getenv("OPENAI_ENDPOINT"),
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model": "gpt-4o"
    }
}

# Choose configuration
config_key = "openai_gpt-4o"

# Get selected configuration
config = configurations[config_key]

# Initialize the OpenAI async client
client = wrap_openai(openai.AsyncClient(api_key=config["api_key"], base_url=config["endpoint_url"]))

gen_kwargs = {
    "model": config["model"],
    "temperature": 0.3,
    "max_tokens": 500
}

# Configuration setting to enable or disable the system prompt
ENABLE_SYSTEM_PROMPT = True
ENABLE_CLASS_CONTEXT = True
IS_CREATE_CHARACTER = False
SHOULD_ASSESS_MESSAGE = False
ENABLE_PLAYER_RAG = True
PLAYER_RAG_SCORE_THRESHOLD = 0.63

# Load retriver for Rag:
rag_retriver = load_index_for_rag("PlayerDnDBasicRules_v0.2_PrintFriendly")

@traceable
def get_latest_user_message(message_history):
    # Iterate through the message history in reverse to find the last user message
    for message in reversed(message_history):
        if message['role'] == 'user':
            return message['content']
    return None

@traceable
async def assess_message(message_history):
    file_path = "player_record.md"
    markdown_content = read_player_record(file_path)
    parsed_record = parse_player_record(markdown_content)

    latest_message = get_latest_user_message(message_history)

    # Remove the original prompt from the message history for assessment
    filtered_history = [msg for msg in message_history if msg['role'] != 'system']

    # Convert message history, alerts, and knowledge to strings
    history_str = json.dumps(filtered_history, indent=4)
    alerts_str = json.dumps(parsed_record.get("Alerts", []), indent=4)
    knowledge_str = json.dumps(parsed_record.get("Knowledge", {}), indent=4)
    
    current_date = datetime.now().strftime('%Y-%m-%d')

    # Generate the assessment prompt
    filled_prompt = ASSESSMENT_PROMPT.format(
        latest_message=latest_message,
        history=history_str,
        existing_alerts=alerts_str,
        existing_knowledge=knowledge_str,
        current_date=current_date
    )
    if ENABLE_CLASS_CONTEXT:
        filled_prompt += "\n" + CLASS_CONTEXT
    print("Filled prompt: \n\n", filled_prompt)

    response = await client.chat.completions.create(messages=[{"role": "system", "content": filled_prompt}], **gen_kwargs)

    assessment_output = response.choices[0].message.content.strip()
    print("Assessment Output: \n\n", assessment_output)

    # Parse the assessment output
    new_alerts, knowledge_updates = parse_assessment_output(assessment_output)

    # Update the student record with the new alerts and knowledge updates
    parsed_record["Alerts"].extend(new_alerts)
    for update in knowledge_updates:
        topic = update["topic"]
        note = update["note"]
        parsed_record["Knowledge"][topic] = note

    # Format the updated record and write it back to the file
    updated_content = format_player_record(
        parsed_record["Player Information"],
        parsed_record["Alerts"],
        parsed_record["Knowledge"]
    )
    write_player_record(file_path, updated_content)

@traceable
def parse_assessment_output(output):
    try:
        parsed_output = json.loads(output)
        new_alerts = parsed_output.get("new_alerts", [])
        knowledge_updates = parsed_output.get("knowledge_updates", [])
        return new_alerts, knowledge_updates
    except json.JSONDecodeError as e:
        print("Failed to parse assessment output:", e)
        return [], []
    
@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="Start a campaign",
            message="Start a campaign",
            icon="/public/start.jpeg",
            ),
        cl.Starter(
            label="Create a character",
            message="Create a character",
            icon="/public/character.jpeg",
            ),
    ]

@traceable
@cl.on_message
async def on_message(message: cl.Message):
    global IS_CREATE_CHARACTER
    
    # Maintain an array of messages in the user session
    message_history = cl.user_session.get("message_history", [])
    message_history.append({"role": "user", "content": message.content})
    
    print("IS_CREATE_CHARACTER: ", IS_CREATE_CHARACTER)

    if ENABLE_SYSTEM_PROMPT and (not message_history or message_history[0].get("role") != "system"):
        if message.content == "Create a character":
            IS_CREATE_CHARACTER = True
            system_prompt_content = CHARACTER_CREATION

            # relevant_documents = fetch_relevant_documents("what are dwarves?", rag_retriver)
            # print(relevant_documents)
        else:
            system_prompt_content = SYSTEM_PROMPT
            if ENABLE_CLASS_CONTEXT:
                system_prompt_content += "\n" + CLASS_CONTEXT
        
        message_history.insert(0, {"role": "system", "content": system_prompt_content})

    if IS_CREATE_CHARACTER:
        relevant_documents = fetch_relevant_documents(message.content, rag_retriver)
        message_history.append({"role": "system", "content": f"Use the following excerpt to answer: \n{relevant_documents}"})
    elif ENABLE_PLAYER_RAG:
        relevant_documents = fetch_relevant_documents(message.content, rag_retriver, score_threshold=PLAYER_RAG_SCORE_THRESHOLD)
        print(relevant_documents)
        message_history.append({"role": "system", "content": f"Use the following excerpt to answer: \n{relevant_documents}"})


    if SHOULD_ASSESS_MESSAGE:
        asyncio.create_task(assess_message(message_history))
    
    response_message = cl.Message(content="")
    await response_message.send()

    if config_key == "mistral_7B":
        stream = await client.completions.create(prompt=message.content, stream=True, **gen_kwargs)
        async for part in stream:
            if token := part.choices[0].text or "":
                await response_message.stream_token(token)
    else:
        stream = await client.chat.completions.create(messages=message_history, stream=True, **gen_kwargs)
        async for part in stream:
            if token := part.choices[0].delta.content or "":
                await response_message.stream_token(token)

    if "\"function\": " in response_message.content:
        print("Function call detected: ", response_message.content)
        
        # extract the json from the message
        json_start = response_message.content.find("{")
        json_end = response_message.content.rfind("}") + 1
        function_call = response_message.content[json_start:json_end]
        print("JSON string: ", function_call)

        handle_function_call(function_call)

    message_history.append({"role": "assistant", "content": response_message.content})
    cl.user_session.set("message_history", message_history)
    await response_message.update()


if __name__ == "__main__":
    cl.main()

def handle_function_call(function_call):
    json_message = json.loads(function_call)

    function_name = json_message.get("function")

    if function_name == "save_player_character":
        character = json_message.get("character_string")
        save_player_character(character=character)