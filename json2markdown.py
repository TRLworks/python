#!/usr/env/python
from __future__ import print_function
import json
from jinja2 import Template

class WikiError(Exception):
    """
    Wikipage cannot be generated
    """
    pass


def read_json(filename):
    """
    Reads a json file and returns a dictionary of its content

    Args:
        filename (str): path to the json file to read

    Return:
        (dict): dictionary representation of the json file

    Raises:
        WikiError
    """
    with open('wiki.json', 'r') as f_in:
     json_data = f_read()
    return (json_data(f_in))
    pass


def render_template(filename, data):
    """
    Reads a template file and returns a string with the content of the wikipage

    Args:
        filename (str): path to the template file to read

        data (dict): data to be rendered in the template

    Return:
        (dict): dictionary representation of the json file

    Raises:
        WikiError
    """
    with open('generalsheet.md', 'r') as f_in:
        template = f_in.read()

    template = Template(template)
    return template.render(data)


if __name__ == '__main__':
    data = {'data': ['Developement', 'Testing', 'Staging', 'staging_signoff', 'Internal_production', 'Internal_prodcution_signoff', 'Production']}
    print(render_template(filename='wiki.j2', data=data))
