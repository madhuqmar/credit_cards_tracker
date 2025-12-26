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
    # FOOD
    # -------------------------
    if any(x in m for x in [
        "espresso",
        "compass",
        "sweet leaf"
    ]):
        return "Food", "Coffee"

    if any(x in m for x in [
        "doughnut",
        "donut",
        "toastique",
        "tatte bakery",
        "bakery"
    ]):
        return "Food", "Snacks"

    if "chicken and whiskey" in m or "burger" in m:
        return "Food", "Lunch/Dinner"

    if "bethesda bagels" in m or "bagel" in m:
        return "Food", "Breakfast"

    if "uber eats" in m:
        return "Food", "Delivery"

    # -------------------------
    # INTEREST / FEES
    # -------------------------
    if "interest" in m or (("fee" in m or "fees" in m)):
        return "Anomalies", "Interest / Fees"

    # -------------------------
    # GROOMING
    # -------------------------
    if "nail" in m:
        return "Grooming", "Nails"

    if "silver mirror" in m or "facial" in m:
        return "Grooming", "Facials/Skin"
    
    if "gloss bar" in m:
        return "Grooming", "Hair"


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
        return "Food", "Dining"

    # -------------------------
    # GROCERIES
    # -------------------------
    if "instacart" in m:
        return "Groceries", "Delivery"

    if any(x in m for x in [
        "trader joe",
        "giant",
        "wholefds",
        "whole foods"
    ]):
        return "Groceries", "Store"

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

    if "smart trip" in m or "metro washington" in m:
        return "Transportation", "Metro"

    # -------------------------
    # SUBSCRIPTIONS
    # -------------------------
    if any(x in m for x in [
        "prime video",
        "prime video channels",
        "netflix",
        "apple.com",
        "google one"
    ]):
        return "Subscriptions", "Digital Services"
    
    if any(x in m for x in [
        "classpass",
        "ouraring",
        "oura ring",
        "oura"
    ]):
        return "Subscriptions", "Health / Fitness"
    

    if any(x in m for x in [
        "canva",
        "figma",
        "github",
        "gamma",
        "midjourney",
    ]):
        return "Subscriptions", "Code / Design"

    # -------------------------
    # BUSINESS
    # -------------------------
    if "amazon web services" in m or "aws" in m:
        return "Business", "Cloud Services"

    # -------------------------
    # BEAUTY / GROOMING
    # -------------------------
    if "brow" in m or "contour" in m:
        return "Grooming", "Threading/Waxing"

    if any(x in m for x in [
        "salon",
        "beauty"
    ]):
        return "Beauty / Grooming", "Services"

    # -------------------------
    # SHOPPING
    # -------------------------
    
    if any(x in m for x in [
        "ann taylor",
        "skims",
        "reformation"
    ]):
        return "Shopping", "Clothes"

    if any(x in m for x in [
        "sephora",
        "wayfair",
        "amazon"
    ]):
        return "Shopping", "Retail"

    # -------------------------
    # OTHER
    # -------------------------
    if "dryydc" in m or "dry clean" in m:
        return "Other", "Dry Cleaning"

    # -------------------------
    # DEFAULT
    # -------------------------
    return "Other", "Other"
