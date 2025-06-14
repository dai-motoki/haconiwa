class Calculator:
    """簡易計算機クラス（加算・減算を順次適用）"""
    
    def __init__(self) -> None:
        self.result: int | float = 0
    
    def add(self, x: int | float) -> 'Calculator':
        """数値を加算する"""
        if not isinstance(x, (int, float)):
            raise TypeError("x must be a number")
        self.result += x
        return self
    
    def subtract(self, x: int | float) -> 'Calculator':
        """数値を減算する"""
        if not isinstance(x, (int, float)):
            raise TypeError("x must be a number")
        self.result -= x
        return self
    
    @property
    def value(self) -> int | float:
        """現在の計算結果を返す"""
        return self.result
    
    def get_result(self) -> int | float:
        """現在の計算結果を返す（互換性のため残す）"""
        return self.result