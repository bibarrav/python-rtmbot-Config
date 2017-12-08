import requests
import time
import xml.etree.ElementTree as xml

crontable = []
outputs = []

debug            = False

openhab_url      = 'http://10.0.1.13:8088'
slackhab_user_id = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

headers          = { 'Content-Type': 'text/plain' }

def process_message(data):
    print_debug(str(data))

    # check we have sufficient details
    if 'channel' not in data or 'user' not in data or 'text' not in data:
        return

    channel = data['channel']
    user = data['user']
    text = data['text']

    # first check if we are interested in this command
    command_text = get_command_text(channel, user, text)

    if command_text is None:
        return

    tokens = command_text.split()
    if len(tokens) == 0:
        return

    command = tokens[0].lower()

    if command == "send" and len(tokens) >= 3:
        item = tokens[1]
        value = " ".join(tokens[2:])
        url = openhab_url + '/rest/items/' + item
        r = requests.post(url, headers=headers, data=value)

        if check_response(r, channel):
            outputs.append([ channel, "```Sent %s command to %s```" % (value, item) ])

    elif command == "update" and len(tokens) >= 3:
        item = tokens[1]
        value = " ".join(tokens[2:])
        url = openhab_url + '/rest/items/' + item + '/state'
        r = requests.put(url, headers=headers, data=value)

        if check_response(r, channel):
           outputs.append([ channel, "```Sent %s update to %s```" % (value, item) ])

    elif command == "status" and len(tokens) >= 2:
        item = tokens[1]
        url = openhab_url + '/rest/items/' + item + '/state'
        r = requests.get(url, headers=headers)

        if check_response(r, channel):
            outputs.append([ channel, "```%s is %s```" % (item, r.text) ])

    elif command == "items":
        filter = None
        if len(tokens) > 1:
            filter = tokens[1].lower()

        url = openhab_url + '/rest/items'
        r = requests.get(url, headers=headers)

        if check_response(r, channel):
            items = []
            output = ""
            maxtypelen = 0
            maxnamelen = 0

            for item in xml.fromstring(r.content).findall('item'):
                name = item.find('name').text
                type = item.find('type').text
                if filter is None or filter in name.lower():
                    items.append(item)
                    if len(type) > maxtypelen:
                        maxtypelen = len(type)
                    if len(name) > maxnamelen:
                        maxnamelen = len(name)

            for item in items:
                name  = item.find('name').text
                state = item.find('state').text                
                type  = item.find('type').text
                output = output + "%s%s%s\n" % (type.ljust(maxtypelen+5), name.ljust(maxnamelen+5), state) 
                if len(output) >= 8000:
                    output = output + "... (too much output, please specify a filter)"
                    break

            if len(items) == 0:
                if filter is None:
                    outputs.append([ channel, "```No items found```" ])
                else:
                    outputs.append([ channel, "```No items found matching '%s'```" % (filter) ])
            else:
                outputs.append([ channel, "```%s```" % (output) ])

def get_command_text(channel, user, text):
    if channel == "" or channel is None:
        return None
    if user == "" or user is None:
        return None
    if text == "" or text is None:
        return None

    # check for a message directed at our bot
    user_tag = "<@%s>:" % (slackhab_user_id)

    if text.startswith(user_tag):
        return text[len(user_tag):]

    # check for a DM to our bot
    if channel.startswith("D"):
        return text

    return None

def check_response(r, channel):
    # check our rest api call was successful
    if r.status_code == 200:
        return True
    if r.status_code == 201:
        return True

    # log the response code/reason back to our slack channel
    outputs.append([ channel, "```%d: %s```" % (r.status_code, r.reason) ])
    return False

def print_debug(message):
    if debug:
        print message
