from agents.base_agent import Agent, pretty_print_messages
from prompts import DUNGEN_MASTER_PROMPT
import chainlit as cl
import json

class DungeoMasterAgent(Agent):
    
    def __init__(self, client, gen_kwargs=None):
        super().__init__(name="dm", client=client, prompt=DUNGEN_MASTER_PROMPT, gen_kwargs=gen_kwargs)
        # Add any additional initialization specific to SupervisorAgent
        
    async def handle_call_agent(self, tool_calls, message_history):
        appended_messages = []
        contain_call_agent = False
        copied_message_history = message_history.copy()
        
        for tool_call in tool_calls:
            function_name = tool_call["name"]
            arguments = tool_call["arguments"]

            # print(f"DEBUG: function_name: {function_name}")
            # print(f"DEBUG: arguments: {arguments}")        
            
            if function_name == "callAgent":
                try:
                    arguments_dict = json.loads(arguments)
                    agent_name = arguments_dict.get("agent_name")
                    agent_message = arguments_dict.get("message")
                    if agent_name and agent_name in self.known_agents:
                        contain_call_agent = True

                        call_message = cl.Message(content=agent_message)
                        await call_message.send()

                    # Inform the user about the agent call
                    print(f"DEBUG: calling {agent_name} agent with message: {agent_message}")
                    call_message = cl.Message(content=f"Calling the {agent_name.capitalize()} Agent...")
                    await call_message.send()

                    message = {"role": "user", "content": f'[from SUPERVISOR agent]: {agent_message}'}
                    copied_message_history.append(message)
                    appended_messages.append(message)

                    # Execute the called agent
                    call_agent_messages = await self.known_agents[agent_name].execute(copied_message_history)
                    print(f"\n\nDEBUG: response from call_agent_messages:\n {pretty_print_messages(call_agent_messages)}\n\n")
                    appended_messages.extend(call_agent_messages)
                    
                    # Inform the user about the completion of the agent call
                    complete_message = cl.Message(content=f"The {agent_name.capitalize()} Agent has completed its task.")
                    await complete_message.send()

                except Exception as e:
                    print(f"DEBUG: Error in handle_call_agent: {e}")
                    continue

        return contain_call_agent, appended_messages
    
    async def execute(self, message_history):
        print(f'executing dm execute')
        appended_messages = []

        full_response, tool_calls = await self.extract_response(message_history)
    
        text_response = {"role": "assistant", "content": full_response}
        message_history.append(text_response)

        if (tool_calls):
            print("Tool calls")
            print(full_response)
            print(tool_calls)

        return appended_messages
