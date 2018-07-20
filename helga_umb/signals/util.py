def product_from_branch(branch):
    """
    Return a product name from this branch name.

    :param branch: eg. "ceph-3.0-rhel-7"
    :returns: eg. "ceph"
    """
    if branch.startswith('private-'):
        # Let's just return the thing after "private-" and hope there's a
        # product string match somewhere in there.
        return branch[8:]
    # probably not gonna work for "stream" branches :(
    parts = branch.split('-', 1)
    return parts[0]
