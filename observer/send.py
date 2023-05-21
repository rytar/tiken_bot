import requests

def send(data: dict, url: str):
    """
        This function sends data to the server for processing notes and queries.

        The dict (`dict`) is the payload like below:
        ```
            {
                "type": "mention" or "note",
                "note": Note
            }
        ```
        The string (`url`) is the address of the server.

        Args:
            data: the payload
            url: the server address
        Return:
            Response
    """

    return requests.post(url, data=data)