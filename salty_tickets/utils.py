import re


def string_to_key(str_var):
    key = str_var.lower()
    key = re.sub(r'[^a-zA-Z0-9]', '_', key)
    key = re.sub(r'\s', '_', key)
    key = re.sub(r'_+', '_', key)
    return key