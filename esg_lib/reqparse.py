from flask_restx import reqparse


def get_email_request_parse():
    parser = reqparse.RequestParser()
    parser.add_argument("user_email", location="args")
    return parser


def get_email_role_request_parse() -> reqparse.RequestParser:
    parser = get_email_request_parse()
    parser.add_argument("user_role", location="args")
    return parser


def get_default_paginated_request_parse(parser: reqparse.RequestParser = None) -> reqparse.RequestParser:
    if parser is None:
        parser = reqparse.RequestParser()
    parser.add_argument("search_value", location="args")
    parser.add_argument("sort_key", location="args", default="_id")
    parser.add_argument("sort_order", type=int, location="args", default=-1)
    parser.add_argument("page", type=int, location="args", default=1)
    parser.add_argument("size", type=int, location="args", default=10)
    return parser
