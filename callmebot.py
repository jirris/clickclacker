import requests

import aux


def send_message(phone_number, api_key, message, service):

    url = ""
    message.replace(" ", "+")
    whatsapp = 'https://api.callmebot.com/whatsapp.php?phone=' + phone_number \
               + '&text=' + message + '&apikey=' + api_key
    signal = 'https://api.callmebot.com/signal/send.php?phone=' + phone_number \
             + '&apikey=' + api_key + '&text=' + message
    telegram = 'https://api.callmebot.com/text.php?user=@' + phone_number + '&text=' + message

    if service == "telegram":
        url = telegram
    elif service == "signal":
        url = signal
    elif service == "whatsapp":
        url = whatsapp

    if url == "":
        aux.errorhandler("No service set for messages", 1, 1)
        return 0

    response = requests.get(url)

    if response.status_code == 200:
        return 0
    else:
        return response.text


if __name__ == '__main__':
    send_message('x', 'x', 'ClickClack ddd', 'whatsapp')
