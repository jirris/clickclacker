import requests

def senddiscord(url, message):
    data = {
        "content" : message,
        "username" : "ClickClack"
    }

    result = requests.post(url, json = data)

    try:
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        return(err)
    else:
        return 0
