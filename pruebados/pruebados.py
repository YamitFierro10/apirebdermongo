"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import os
import reflex as rx
from openai import OpenAI
from fastapi import Request
from twilio.rest import Client
from dotenv import load_dotenv
from pruebados.api import handle

app = rx.App()

class QA(rx.Base):
    """A question and answer pair."""

    question: str
    answer: str

DEFAULT_CHATS = {
    "Intros": [],
}

chats: dict[str, list[QA]] = DEFAULT_CHATS

# Cargar las variables de entorno desde el archivo .env
load_dotenv()


# Configura las claves de API
OpenAI.api_key = os.getenv("OPENAI_API_KEY")
twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_token = os.getenv("TWILIO_AUTH_TOKEN")

# Checking if the API key is set properly
if not os.getenv("OPENAI_API_KEY"):
    raise Exception("Please set OPENAI_API_KEY environment variable.")


class QA(rx.Base):
    """A question and answer pair."""

    question: str
    answer: str


DEFAULT_CHATS = {
    "Intros": [],
}

class State(rx.State):
    """The app state."""

    # A dict from the chat name to the list of questions and answers.
    chats: dict[str, list[QA]] = DEFAULT_CHATS

    # The current chat name.
    current_chat = "Intros"

    # The current question.
    question: str

    # Whether we are processing the question.
    processing: bool = False

    # The name of the new chat.
    new_chat_name: str = ""

    def create_chat(self):
        """Create a new chat."""
        # Add the new chat to the list of chats.
        self.current_chat = self.new_chat_name
        self.chats[self.new_chat_name] = []

    def delete_chat(self):
        """Delete the current chat."""
        del self.chats[self.current_chat]
        if len(self.chats) == 0:
            self.chats = DEFAULT_CHATS
        self.current_chat = list(self.chats.keys())[0]

    def set_chat(self, chat_name: str):
        """Set the name of the current chat.

        Args:
            chat_name: The name of the chat.
        """
        self.current_chat = chat_name

    @rx.var
    def chat_titles(self) -> list[str]:
        """Get the list of chat titles.

        Returns:
            The list of chat names.
        """
        return list(self.chats.keys())

    async def process_question(self, form_data: dict[str, str]):
        # Get the question from the form
        question = form_data["question"]

        # Check if the question is empty
        if question == "":
            return

        model = self.openai_process_question

        async for value in model(question):
            yield value

    async def openai_process_question(self, question: str):
        """Get the response from the API.

        Args:
            form_data: A dict with the current question.
            
        """
        system_rol='''Eres una asitente util'''
        messages=[{"role": "system", "content": system_rol}]

        # Add the question to the list of questions.
        qa = QA(question=question, answer="")
        self.chats[self.current_chat].append(qa)

        # Clear the input and start the processing.
        self.processing = True
        yield

        # Build the messages.
        for qa in self.chats[self.current_chat]:
            messages.append({"role": "user", "content": qa.question})
            messages.append({"role": "assistant", "content": qa.answer})

        # Remove the last mock answer.
        messages = messages[:-1]

        # Start a new session to answer the question.
        session =OpenAI().chat.completions.create(
                model="gpt-4",
                messages=messages,
        )
        respuesta=session.choices[0].message.content
        yield respuesta

        # Stream the results, yielding after every word.
        # for item in session:
        #     if hasattr(item.choices[0].delta, "content"):
        #         answer_text = item.choices[0].delta.content
        #         # Ensure answer_text is not None before concatenation
        #         if answer_text is not None:
        #             self.chats[self.current_chat][-1].answer += answer_text
        #         else:
        #             # Handle the case where answer_text is None, perhaps log it or assign a default value
        #             # For example, assigning an empty string if answer_text is None
        #             answer_text = ""
        #             self.chats[self.current_chat][-1].answer += answer_text
        #         self.chats = self.chats
        #         yield

        # Toggle the processing flag.
        self.processing = False
        
    async def handle_incoming_message( self,request: Request):
        form = await request.form()  # Extrae el formulario de la solicitud
        incoming_msg = form.get("Body")  # Extrae el mensaje
        from_number = form.get("From")  # Extrae el número de remitente

         # Generar la respuesta AI usando OpenAI
        ai_reply = ""
        async for reply_part in self.openai_process_question(incoming_msg):
            ai_reply += reply_part
            
        client = Client(twilio_sid, twilio_token)
        
        # Enviar la respuesta de vuelta al usuario por WhatsApp
        client.messages.create(
            from_="whatsapp:+14155238886",  # Número de Twilio
            body=ai_reply,
            to=from_number  # Tu número de WhatsApp 
        )
        print(f"Mensaje enviado a {from_number}: {ai_reply}")
        
         # Retornar una respuesta JSON
        return {"status": "success", "response": ai_reply}

# def get_ai_response(respuesta):
#     completar= OpenAI().chat.completions.create(
#         model="gpt-4",
#         messages=mensaje,
#     )
#     respuesta=completar.choices[0].message.content
#     return respuesta


#Reflex app

app.api.add_api_route("/handle",handle) 
app.api.add_api_route("/whatsapp", State.handle_incoming_message, methods=["POST"])


