from enum import Enum


class PurchaseIntent(Enum):
    COLD = "冷淡"
    NEUTRAL = "一般"
    INTERESTED = "感兴趣"
    VERY_INTERESTED = "非常感兴趣"
