import json
import random

def calculate(expression: str) -> str:
    """
    Evaluates a mathematical expression and returns the result.

    :param expression: The mathematical expression to evaluate.
    :return: Result of the calculation as a JSON string.
    """
    try:
        # WARNING: Using eval can be dangerous; ensure to sanitize inputs in production.
        result = eval(expression)
        return json.dumps({"result": result})
    except Exception as e:
        return json.dumps({"error": str(e)})


def get_secret_word() -> str:
    """
    Provides a random secret word.

    :return: A random secret word.
    """
    print("[debug-server] get_secret_word()")
    return random.choice(["apple", "banana", "cherry"])


# Set of user-defined functions to be registered with the server

user_functions = {calculate, get_secret_word}