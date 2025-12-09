from google import genai

client = genai.Client(api_key="AIzaSyBug1VWTX76TSkUnUawD_pJDhWMR2JmR0s")

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="how many wudu in a rakah?"
)

print(response.text)

