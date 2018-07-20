import posixpath


BASEURL = 'https://datagrepper.engineering.redhat.com/'


def get_url(headers):
    """
    return the datagrepper URL for this frame.

    :param headers: this frame's headers (dict)
    """
    id_ = headers['message-id']
    path = 'id?id=%s&is_raw=true&size=extra-large' % id_
    return posixpath.join(BASEURL, path)
