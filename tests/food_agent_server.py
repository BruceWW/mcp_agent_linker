import fastmcp

mcp = fastmcp.FastMCP("food-agent")


@mcp.prompt(name="init")
def init_prompt() -> str:
    return "你是一个外卖助手，帮助用户查询菜单、下单。下单前先确认地址和预算。"


@mcp.resource("skill:///ordering-guide", description="外卖点餐标准流程：确认地址 → 查菜单 → 下单")
def ordering_guide() -> str:
    return "# 点餐指南\n\n## 流程\n1. 调用 query_menu 获取菜单\n2. 根据预算筛选套餐\n3. 调用 create_order 下单\n\n## 注意\n- 下单前必须确认收货地址\n- 预算不足时主动告知用户"


@mcp.resource("skill:///coupon-strategy", description="优惠券叠加规则与使用优先级")
def coupon_strategy() -> str:
    return "# 优惠券策略\n\n## 规则\n- 满30减5：订单总价 >= 30 元时可用\n- 新用户首单立减8元，与满减不叠加\n\n## 优先级\n优先使用节省金额更大的券"


@mcp.tool()
def query_menu(max_price: float = 50.0) -> list[dict]:
    """查询菜单，返回价格在 max_price 以内的套餐"""
    return [
        {"id": "m1", "name": "麦辣鸡腿堡套餐", "price": 28.9},
        {"id": "m2", "name": "双层牛堡套餐", "price": 35.0},
    ]


@mcp.tool()
def create_order(meal_id: str, address: str) -> dict:
    """创建外卖订单"""
    return {"order_id": "ORD_001", "status": "confirmed", "eta": "30分钟"}


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8765)
