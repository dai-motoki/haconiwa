def add(a: int | float, b: int | float) -> int | float:
    """a と b の和を返す"""
    return a + b

def multiply(x: int | float, y: int | float) -> int | float:
    """x と y の積を返す"""
    return x * y

def greet(name: str) -> str:
    """挨拶メッセージを返す"""
    return f"Hello, {name}!"