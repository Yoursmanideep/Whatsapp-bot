from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

@app.route("/")
def home():
    return "Twilio bot running", 200

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    incoming_msg = request.values.get("Body", "")
    sender = request.values.get("From")

    print("User:", sender)
    print("Message:", incoming_msg)

    resp = MessagingResponse()
    resp.message("got your message")

    return str(resp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
