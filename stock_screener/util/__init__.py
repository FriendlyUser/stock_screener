import requests
import os
import json

def post_webhook(content: str):
  url = os.getenv('DISCORD_WEBHOOK')
  data = {}
  #for all params, see https://discordapp.com/developers/docs/resources/webhook#execute-webhook
  data["content"] = content

  result = requests.post(url, data=json.dumps(data), headers={"Content-Type": "application/json"})

  try:
      result.raise_for_status()
  except requests.exceptions.HTTPError as err:
      print(err)
  else:
      print("Payload delivered successfully, code {}.".format(result.status_code))