# categorizer.py

def categorize_transaction(merchant: str):
    """
    Returns:
        category (str): High-level category
        subcategory (str): Detailed sub-category
    """
    if not merchant:
        return "Other", "Other"

    m = merchant.lower()

    # -------------------------
    # INTEREST / FEES
    # -------------------------
    if "interest" in m or "fee" in m:
        return "Anomalies", "Interest / Fees"

    # -------------------------
    # FOOD DELIVERY
    # -------------------------
    if "uber eats" in m:
        return "Food Delivery", "Uber Eats"

    # -------------------------
    # DINING
    # -------------------------
    if any(x in m for x in [
        "tst*yellow",
        "union market",
        "restaurant",
        "cafe",
        "toast",
        "bar",
        "bistro",
        "grill"
    ]):
        return "Dining", "Restaurants"

    # -------------------------
    # GROCERIES
    # -------------------------
    if any(x in m for x in [
        "trader joe",
        "giant",
        "instacart"
    ]):
        return "Groceries", "Groceries"

    # -------------------------
    # TRANSPORTATION
    # -------------------------
    if "capbike" in m or ("lyft" in m and "ride" in m and "bike" in m):
        return "Transportation", "Bikes"

    if any(x in m for x in [
        "uber trip",
        "uber *trip"
    ]):
        return "Transportation", "Uber"

    if "lyft" in m:
        return "Transportation", "Lyft"

    if "smart trip" in m:
        return "Transportation", "Metro"

    # -------------------------
    # HEALTH / FITNESS
    # -------------------------
    if any(x in m for x in [
        "classpass",
        "ouraring",
        "oura ring",
        "oura"
    ]):
        return "Health / Fitness", "Subscriptions"

    # -------------------------
    # SUBSCRIPTIONS
    # -------------------------
    if any(x in m for x in [
        "prime video",
        "prime video channels",
        "netflix",
        "apple.com",
        "canva",
        "figma",
        "github",
        "gamma",
        "midjourney",
        "google one"
    ]):
        return "Subscriptions", "Digital Services"

    # -------------------------
    # BUSINESS
    # -------------------------
    if "amazon web services" in m or "aws" in m:
        return "Business", "Cloud Services"

    # -------------------------
    # BEAUTY / GROOMING
    # -------------------------
    if any(x in m for x in [
        "brow",
        "salon",
        "beauty",
        "contour"
    ]):
        return "Beauty / Grooming", "Services"

    # -------------------------
    # SHOPPING
    # -------------------------
    if any(x in m for x in [
        "sephora",
        "skims",
        "reformation",
        "wayfair",
        "amazon"
    ]):
        return "Shopping", "Retail"

    # -------------------------
    # DEFAULT
    # -------------------------
    return "Other", "Other"
