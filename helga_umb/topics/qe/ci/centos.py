""" Announce CentOS messages. """


def consume(client, channel, frame):
    msg_type = frame.headers['type']  # "centos-image"
    message = 'centos %s' % msg_type
    if msg_type == 'centos-image':
        # image_name eg. "CentOS-Atomic-Host-7.1711-Vagrant-VirtualBox.box"
        image_name = frame.headers.get('image-name')
        if image_name is None:
            # Not sure why some messages lack image-name. Let's get more
            # information when we hit this.
            from pprint import pprint
            pprint(frame.headers)
            try:
                pprint(frame.body.decode())
            except UnicodeDecodeError:
                pass
        image_type = frame.headers['image-type']  # "atomic"
        message = 'centos published %s image %s' % (image_type, image_name)
    client.msg(channel, message)
