import os
import sys
import json
from datetime import datetime
import psycopg2

import requests
from flask import Flask, request

app = Flask(__name__)

'''
DATABASE_URL = os.environ['DATABASE_URL']

conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS jobs (job_name varchar, members varchar, notif_1 int, notif_2 int, notification_times_bools varchar, chores varchar);")
conn.commit()
cur.close()
conn.close()
'''

### EXAMPLE OF HOW TO INSERT ###
'''
cur.execute("INSERT INTO jobs (job_name, members, notifications, chores) VALUES (%s, %s, %s, %s);", ("TEST", "['member1', 'member2']", "notifications_test", "chores_test"))
cur.execute("SELECT * FROM jobs;")
print(cur.fetchone())

conn.commit()
cur.close()
conn.close()
'''

@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    print('verify')
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args.get('hub.challenge', ''), 200
        #return request.args["hub.challenge"], 200

    return "Hello world", 200

@app.route('/', methods=['POST'])
def webhook():
    print('webhook')
    # endpoint for processing incoming messaging events

    data = request.get_json()
    #log(data)  # you may not want to log every incoming message in production, but it's good for testing
    print(data)

    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                if messaging_event.get("message"):  # someone sent us a message

                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                    message_text = messaging_event["message"]["text"]  # the message's text

                    message_parsed = message_text.split(' ')
                    print('MESSAGE PARSED: ', message_parsed)
                    if message_parsed[0] == '!create':
                        params = message_parsed[1:]
                        params[-1] = str(params[-1])
                        params = params + [sender_id]
                        print(params)
                        #create_job(*params)

                    #send_message(sender_id, "roger that!")

                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    pass

    return "ok", 200

def create_job(job_name, notif_1, notif_2, chores, senderid):
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()

    cur.execute("SELECT job_name FROM jobs;")
    current_jobs = cur.fetchone()
    print(current_jobs)
    if current_jobs is None or job_name not in current_jobs:
        cur.execute("INSERT INTO jobs (job_name, members, notif_1, notif_2, notification_times_bools, chores) VALUES (%s, %s, %, %, %s);", (job_name, str([senderid]), int(notif_1), int(notif_2), str([[int(notif_1), int(notif_2)]]), chores))
    else:
        send_message(senderid, "That job already exists!")
    cur.execute("SELECT job_name FROM jobs;")
    print(current_jobs)

    conn.commit()
    cur.close()
    conn.close()


def send_message(recipient_id, message_text):

    print("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        print(r.status_code)
        print(r.text)


def log(msg, *args, **kwargs):  # simple wrapper for logging to stdout on heroku
    try:
        if type(msg) is dict:
            msg = json.dumps(msg)
        else:
            msg = unicode(msg).format(*args, **kwargs)
        print(u"{}: {}".format(datetime.now(), msg))
    except UnicodeEncodeError:
        pass  # squash logging errors in case of non-ascii text
    sys.stdout.flush()


if __name__ == '__main__':
    app.run(debug=True)
