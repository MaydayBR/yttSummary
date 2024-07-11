from flask import Flask, request, jsonify, render_template
import os
from youtube_transcript_api import YouTubeTranscriptApi
import openai
from dotenv import load_dotenv
from flask_cors import CORS  # Added this line to import CORS

load_dotenv(dotenv_path='key.env')

app = Flask(__name__)
CORS(app) 

openai.api_key = os.getenv('OPENAI_API_KEY')
print(f"Loaded API Key: {openai.api_key}") 

@app.route('/')
def index():
    return render_template('page.html')

def summary(url):
  #we only want the last part of the url 
  video_id = url.replace('https://www.youtube.com/watch?v=', '')
  print(video_id)

  #creates json with -  text tag, start tag, duration tag.
  try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
  except Exception as e:
      print(f"Error fetching transcript: {e}")
      return None

  output=''
  for x in transcript:
    sentence = x['text']
    output += f' {sentence}\n'    #creates a string where each line has the transcipt with only words

  response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a journalist."},
        {"role": "user", "content": output},
    ])
  #response holds the entire response from chat gpt
  #summary has all of the content 
  summary = response.choices[0].message['content']
  return summary


def scrape_youtube_video(url):
  #we only want the last part of the url 
  video_id = url.replace('https://www.youtube.com/watch?v=', '')
  print(f"Video ID: {video_id}")

  #creates json with -  text tag, start tag, duration tag.
  try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
  except Exception as e:
      print(f"Error fetching transcript: {e}")
      return None

  output=''
  for x in transcript:
    sentence = x['text']
    output += f' {sentence}\n'    #creates a string where each line has the transcipt with only words

  return output


template = """
You are a helpful assistant that provides answers based on the given information. Here is some information:
{youtube_transcript}

Based on the above information, please answer the following question:
{user_question}
"""

def generate_response(user_question,yt_url):
    info = scrape_youtube_video(yt_url) #info = summary
    if not info:
        return "failed to scrape website"

    prompt = template.format(youtube_transcript = info , user_question = user_question)  #format the question to AI

    try:
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ])
    except Exception as e:
        error_message = str(e)
        if "insufficient_quota" in error_message:
            print("Error generating response with OpenAI: Insufficient quota")
            return "Error: Insufficient quota. Please check your OpenAI plan and billing details."
        print(f"Error generating response with OpenAI: {e}")
        return str(e)

    return response.choices[0].message.content.strip()


@app.route('/generate-response',methods=['POST'])
def generate_response_route():
    data = request.json             
    yt_url = data.get("yt_url")
    user_question = data.get("user_question")

    yt_summary = summary(yt_url)
    if not yt_summary:
        return jsonify({'error': 'Error with summary'}), 500

    if not yt_url or not user_question:
        return jsonify({'error': 'yt_url and user_question are required'}), 400       #400 means bad request 
    try:
        response = generate_response(user_question,yt_url)
        return jsonify({'response':response,'summary':yt_summary})
    except Exception as e:                              #as e will let you know what error it is 
        return jsonify({'error':str(e)}),500                #500 means internal server error 




if __name__ == '__main__':
    app.run(debug=True)
