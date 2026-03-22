# config.py

# 品牌溢价权重（锚定身价）：海力士 4.5 倍对标高端 A-die 约 ¥3600+
BRAND_WEIGHTS = {
    "海力士": 4.5, "芝奇": 2.8, "美商海盗船": 2.0,
    "金士顿": 1.2, "威刚": 1.0, "三星": 1.1
}

PLATFORMS = ["京东", "天猫", "淘宝"]

# 基础均价（人民币 ¥）
BASE_PRICES = {
    "DDR4-3200-16GB-Laptop": 240.0,
    "DDR5-4800-16GB-Laptop": 380.0,
    "DDR5-5600-32GB-Laptop": 750.0,
    "DDR5-5600-32GB-Desktop": 820.0
}