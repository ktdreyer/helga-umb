""" Announce CentOS messages. """


def consume(client, channel, frame):
    msg_type = frame.headers['type']  # "centos-image"
    message = 'centos %s' % msg_type
    if msg_type == 'centos-image':
        # image_name eg. "CentOS-Atomic-Host-7.1711-Vagrant-VirtualBox.box"
        image_name = frame.headers['image_name']
        image_type = frame.headers['image_type']  # "atomic"
        message = 'centos published %s image %s' % (image_type, image_name)
    client.msg(channel, message)
