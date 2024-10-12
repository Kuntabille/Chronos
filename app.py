import os
import base64
import chainlit as cl
from dotenv import load_dotenv
from prompts import  SYSTEM_PROMPT
from player_record import save_player_character
from rag import load_index_for_rag, fetch_relevant_documents
from agents.dungen_master import DungeoMasterAgent

# Load environment variables
load_dotenv()

from langfuse.decorators import observe
from langfuse.openai import AsyncOpenAI
 
client = AsyncOpenAI()

gen_kwargs = {
    "model": "gpt-4",
    "temperature": 0.2
}

@observe
@cl.on_chat_start
def on_chat_start():    
    message_history = [{"role": "system", "content": SYSTEM_PROMPT}]
    cl.user_session.set("message_history", message_history)

# Load retriver for Rag:
rag_retriver = load_index_for_rag("PlayerDnDBasicRules_v0.2_PrintFriendly")

dungen_master = DungeoMasterAgent(client, gen_kwargs)
    
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

@cl.on_message
@observe
async def on_message(message: cl.Message):
    message_history = cl.user_session.get("message_history", [])
    # Processing images exclusively
    images = [file for file in message.elements if "image" in file.mime] if message.elements else []

    if images:
        # Read the first image and encode it to base64
        with open(images[0].path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode('utf-8')
        message_history.append({
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": message.content
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                }
            ]
        })
    else:
        message_history.append({"role": "user", "content": message.content})
    
    appended_messsages = await dungen_master.execute(message_history)

    message_history.extend(appended_messsages)
    # message_history.append({"role": "assistant", "content": response_message})
    cl.user_session.set("message_history", message_history)

if __name__ == "__main__":
    cl.main()