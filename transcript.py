from youtube_transcript_api import YouTubeTranscriptApi

url = 'https://www.youtube.com/watch?v=NXJqHVZJ9lI'
print(url)

video_id = url.replace('https://www.youtube.com/watch?v=', '')
print(video_id)

transcript = YouTubeTranscriptApi.get_transcript(video_id)  #creates json with timestamps and transcript. text tag, start tag, duration tag.

#print(transcript)

output=''
for x in transcript:
  sentence = x['text']
  output += f' {sentence}\n'        #creates a string where each line has the transcipt with only words

print(output)


def scrape_youtube_tags(url):
  response = openai.ChatCompletion.create(    #all of tags for youtube video 
    model="gpt-3.5-turbo",
    messages=[
      {"role": "system", "content": "You are a journalist."},
      {"role": "assistant", "content": "output a list of tags for this blog post in a python list such as ['item1', 'item2','item3']"},
      {"role": "user", "content": output}
    ]
  )
  tag = response["choices"][0]["message"]["content"]
  return tag