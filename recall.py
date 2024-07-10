import os
import requests
from bs4 import BeautifulSoup
from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAI
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

app = Flask(__name__)

load_dotenv(dotenv_path='api.env')      #my api key

@app.route('/')
def index():
    return render_template('final.html')


def scrape_website(url):
    try:
        print("Fetching URL")
        # Added User-Agent header to mimic a regular browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }
        response = requests.get(url, headers=headers)  
        print(f"Response status code: {response.status_code}")
        if response.status_code != 200:
            print(f"Error fetching URL: {response.status_code}")
            return None
        
        print("Parsing content...")
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Attempt to find articles within <article> tags
        articles = soup.find_all('article')
        
        # If no <article> tags are found, attempt to find <div> tags with common class names
        if not articles:
            print("No <article> tags found, searching for common <div> tags")
            articles = soup.find_all('div', {'class': lambda x: x and 'article' in x.split()})
        
        # If still no articles found, attempt to find <section> tags
        if not articles:
            print("No common <div> tags found, searching for <section> tags")
            articles = soup.find_all('section', {'class': lambda x: x and 'article' in x.split()})
        
        # If still no articles found, look for generic <div> tags
        if not articles:
            print("No specific tags found, searching for generic <div> tags")
            articles = soup.find_all('div')

        # If still no articles found, return an error message
        if not articles:
            print("No articles found")
            return "This article does not have any <article>, <div>, or <section> tags containing content. I am unable to scrape its information. Please choose another one"
        
        print(f"Found {len(articles)} articles")
        
        paragraph_list = []
        for article in articles:
            paragraphs = article.find_all('p')
            for paragraph in paragraphs:
                paragraph_list.append(paragraph.get_text())
        
        print(f"Extracted {len(paragraph_list)} paragraphs")
        return paragraph_list
    except Exception as e:
        print(f"Error scraping website: {e}")
        return None

    
def find_main_title(url):
    try:
        # Added User-Agent header to mimic a regular browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }
        response = requests.get(url, headers=headers)  # Updated to include headers
        soup = BeautifulSoup(response.content, 'html.parser')

        h1_tag = soup.find('h1')
        h2_tag = soup.find('h2')
        if h1_tag:
            return h1_tag.get_text()
        elif h2_tag:
            return h2_tag.get_text()
        else:
            return None
    except Exception as e:
        print(f"Error finding title: {e}")
        return None

template = """
You are a helpful assistant that provides answers based on the latest news articles. Here are some recent news snippets:
{news_snippets}

Based on the above information, please answer the following question:
{user_question}
"""

def generate_response(user_question,news_url):
    info = scrape_website(news_url)
    if not info:
        return "failed to scrape website"
    
    combined_info = '\n'.join(info[:10])    #this grabs the first 10 paragraphs from the article 
    if not combined_info:
        return "failed to grab 10 paragraphs"

    prompt = template.format(news_snippets = combined_info , user_question = user_question)  #format the question to AI
    
    llm = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    try:
        response = llm.invoke(prompt)  # Using invoke instead of __call__
    except Exception as e:
        error_message = str(e)
        if "insufficient_quota" in error_message:
            print("Error generating response with LLM: Insufficient quota")
            return "Error: Insufficient quota. Please check your OpenAI plan and billing details."
        print(f"Error generating response with LLM: {e}")
        return str(e)
    
    return response

@app.route('/generate-response',methods=['POST'])
def generate_response_route():
    data = request.json             
    news_url = data.get("news_url")
    user_question = data.get("user_question")

    if not news_url or not user_question:
        return jsonify({'error': 'news_url and user_question are required'}), 400       #400 means bad request 
    try:
        response = generate_response(user_question,news_url)
        return jsonify({'response':response})
    except Exception as e:                              #as e will let you know what error it is 
        return jsonify({'error':str(e)}),500                #500 means internal server error 
    



if __name__ == '__main__':
    app.run(debug=True)