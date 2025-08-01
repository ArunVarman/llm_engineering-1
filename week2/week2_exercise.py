# Imports

import os
import json
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr

# Initialization

load_dotenv(override=True)

openai_api_key = os.getenv('OPENAI_API_KEY')
if openai_api_key:
    print(f"OpenAI API Key exists and begins {openai_api_key[:8]}")
else:
    print("OpenAI API Key not set")
    
MODEL = "gpt-4o-mini"
openai = OpenAI()

system_message = "You are a helpful agent for an Airline called FlightAI. "
system_message += "Give short, courteous answer, no more than 1 sentence. "
system_message += "Always be accurate. If you don't know the answer, say so."

# Create the function for getting the ticket prices

ticket_prices = {"london": "$799", "paris": "$899", "tokyo": "$1400", "berlin": "$499"}

def get_ticket_price(destination_city):
    print(f"Tool get_ticket_prices called for {destination_city}")
    city = destination_city.lower()
    return ticket_prices.get(city, "Unknown")

# Create function for booking confirmation

def confirm_booking(destination_city):
    return "Booking confirmed for " + destination_city

# Describe price function

price_function = {
    "name": "get_ticket_price",
    "description": "Get the price of a ticket with return journey to the destination city. Call this whenever you need to know the ticket price, for example when a customer asks 'How much is a ticket to this city'",
    "parameters": {
        "type": "object",
        "properties": {
            "destination_city": {
                "type": "string",
                "description": "The city that the customer wants to travel to",
            },
        },
        "required": ["destination_city"],
        "additionalProperties": False
    }
}

# Describe booking confirmation function
booking_function = {
    "name": "confirm_booking",
    "description": "Confirm the booking for the customer to the destination city. Call this whenever you need to confirm the booking, for example when a customer asks 'Could you confirm the ticket for the respective city?'",
    "parameters": {
        "type": "object",
        "properties": {
            "destination_city": {
                "type": "string",
                "description": "The city that the customer wants to travel to",
            },
        },
        "required": ["destination_city"],
        "additionalProperties": False
    }
}

# And this is included in a list of tools:

# And this is included in a list of tools:

tools = [
    {"type": "function", "function": price_function},
    {"type": "function", "function": booking_function}
]

# We have to write that function handle_tool_call:

def handle_tool_call(message):
    tool_call = message.tool_calls[0]
    
    # Handle ticket price lookup
    if tool_call.function.name == "get_ticket_price":
        arguments = json.loads(tool_call.function.arguments)
        city = arguments.get('destination_city')
        price = get_ticket_price(city)
        response = {
            "role": "tool", 
            "content": json.dumps({"destination_city": city,"price": price}),
            "tool_call_id": tool_call.id
        }
        return response, city
        
    # Handle booking confirmation
    elif tool_call.function.name == "confirm_booking":
        arguments = json.loads(tool_call.function.arguments)
        city = arguments.get('destination_city')
        confirmation = confirm_booking(city)
        response = {
            "role": "tool",
            "content": json.dumps({"destination_city": city, "confirmation": confirmation}),
            "tool_call_id": tool_call.id
        }
        return response, city

def chat(message, history):
    messages = [{"role": "system", "content": system_message}] + history + [{"role": "user", "content": message}]
    response = openai.chat.completions.create(model=MODEL, messages=messages, tools=tools)

    if response.choices[0].finish_reason == "tool_calls":
        message = response.choices[0].message
        response, city = handle_tool_call(message)
        messages.append(message)
        #print(response)
        messages.append(response)
        response = openai.chat.completions.create(model=MODEL, messages=messages)

    return response.choices[0].message.content

gr.ChatInterface(fn=chat, type="messages").launch()