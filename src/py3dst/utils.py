def isPowerOfTwo(num: int) -> bool:
    """
    Returns if the number is a power of two.
    """
    return (num & (num - 1)) == 0

def getClosestPowerOfTwo(num: int) -> int:
    """
    Returns a number that is a power of two, greater than or equal to the given number.
    """
    min = 2
    while min < num:
        min *= 2
    return min

def maxIntBits(n: int) -> int:
    """
    Returns the maximun number that can be represented with n bits.
    """
    if n <= 0 or not isinstance(n, int):
        raise ValueError("n must be a positive integer")
    
    max_num = (2 ** n) - 1
    return max_num