from flask import Flask, render_template, request, redirect, url_for
from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import requests
from datetime import datetime

app = Flask(__name__)

# Initialize ChatterBot instance
bot = ChatBot(name='WeatherBot', read_only=True)
trainer = ChatterBotCorpusTrainer(bot)
trainer.train("chatterbot.corpus.english")

engine = create_engine('sqlite:///chatbot_conversations.db', echo=True)
Base = declarative_base()


class Conversation(Base):
    __tablename__ = 'conversation'
    id = Column(Integer, primary_key=True)
    user_input = Column(String)
    bot_response = Column(String)
    timestamp = Column(DateTime, default=datetime.now)


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# OpenWeather API key
OPENWEATHER_API_KEY = "7555dc2eff25e4d40d479ae928d8f2b2"


# Route to handle chatbot conversation
@app.route("/chat", methods=["POST"])
def chat():
    try:
        user_input = request.form["user_input"]

        # Get chatbot response
        bot_response = bot.get_response(user_input)

        # Store the conversation in the database
        conversation = Conversation(user_input=user_input, bot_response=str(bot_response))
        session.add(conversation)
        session.commit()

        # If user asks for weather information, retrieve and display weather data
        if 'weather' in user_input.lower():
            location = user_input.split('weather in ')[-1]
            weather_data = get_weather_data(location)

            return render_template("weather.html", location_name=location, weather_data=weather_data)

        return str(bot_response)

    except KeyError:
        return "Invalid input. Please provide 'user_input' in the request."

    except Exception as e:
        return f"An error occurred: {str(e)}"

# Function to fetch weather data from OpenWeather API


def get_weather_data(location_name):
    try:
        openweather_endpoint = "https://api.openweathermap.org/data/2.5/forecast"
        params = {
            'q': location_name,
            'appid': OPENWEATHER_API_KEY
        }

        response = requests.get(openweather_endpoint, params=params)

        if response.status_code == 200:
            return response.json()
        else:
            return None

    except requests.RequestException as e:
        return {'error': f'Request Exception: {str(e)}'}


if __name__ == "__main__":
    app.run()
