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
        "sweet leaf",
        "7-eleven",
        "starbucks",
        "dunkin",
        "peet's coffee",
        "blue bottle",
        "coffee",
        "sugar & twine",
        "blanchard",
        "sugar shack"
    ]):
        return "Food", "Coffee"

    if any(x in m for x in [
        "doughnut",
        "donut",
        "toastique",
        "tatte bakery",
        "bakery",
        "playa bowls",
        "tous les jours",
        "capital one arena",
        "capitalonearena",
        "jumbo slice",
        "highs 36 annapolis",
        "union station",
        "perch & post"
    ]):
        return "Food", "Snacks"

    if any(x in m for x in [
        "chicken and whiskey", 
        "burger",
        "cava",
        "chai pani"
        ]):
        return "Food", "Lunch/Dinner"

    if any(x in m for x in [
        "bethesda bagels"
        "bagel",
        "call your mother",
        "ihop"
    ]):
        return "Food", "Breakfast"
    
    if any(x in m for x in [
        "wunder garten"
    ]):
        return "Food", "Drinks"

    if any(x in m for x in [
        "uber eats",
        "eats"
    ]):
        return "Food", "Delivery"

    # -------------------------
    # INTEREST / FEES
    # -------------------------
    if "interest" in m or (("fee" in m or "fees" in m)):
        return "Anomalies", "Interest / Fees"

    # -------------------------
    # GROOMING
    # -------------------------
    if any(x in m for x in [
        "nail",
        "jefferson hotel"
    ]):
        return "Grooming", "Nails"

    if any(x in m for x in [
        "silver mirror",
        "facial",
        "everbody"
    ]):
        return "Grooming", "Facials/Skin/Filler"
    
    if any(x in m for x in [
        "gloss bar",
    ]):
        return "Grooming", "Hair"
    
    if any(x in m for x in [
        "european wax center",
        "puspa day spa",
        "illa spa"
    ]):
        return "Grooming", "Hair Removal"
    
    if any(x in m for x in [
        "deluca",
        "unwind"
    ]):
        return "Grooming", "Massage/Spa"


    # -------------------------
    # DINING
    # -------------------------
    if any(x in m for x in [
        "tst*yellow",
        "restaurant",
        "cafe",
        "toast",
        "bar",
        "bistro",
        "grill",
        "earls",
        "lillie pearl"
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
        "whole foods",
        "safeway",
        "stellas",
        "union market",
        "shields market",
        "a litteriwasbingtondc"
        "ansel"
    ]):
        return "Groceries", "Store"

    # -------------------------
    # TRANSPORTATION
    # -------------------------
    if "capbike" in m or ("lyft" in m and "ride" in m and "bike" in m):
        return "Transportation", "Bikes"

    if any(x in m for x in [
        "uber trip",
        "uber *trip",
        "uber",
        "lyft"
    ]):
        return "Transportation", "Uber/Lyft"

    if any(x in m for x in [
        "amtrak",
        "wanderu"
    ]):
        return "Transportation", "Train/Bus"

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
        "google one",
        "medium"
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
        "claude",
        "cursor"
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
        "beauty",
        "unwind"
    ]):
        return "Beauty / Grooming", "Services"

    # -------------------------
    # SHOPPING
    # -------------------------
    
    if any(x in m for x in [
        "ann taylor",
        "skims",
        "reformation",
        "urbanoutfitters",
        "babyboo",
        "meshki",
        "uniqlo",
        "salt sundry"
    ]):
        return "Shopping", "Clothes"

    if any(x in m for x in [
        "sephora",
        "wayfair",
        "amazon",
        "tiktok shop",
        "ross",
        "cvs",
        "bluemercury"
    ]):
        return "Shopping", "Retail"

    # -------------------------
    # OTHER
    # -------------------------
    if any(x in m for x in [
        "dryydc",
        "dry clean",
        "elite cleaners"
    ]):
        return "Other", "Dry Cleaning"
    
    if any(x in m for x in [
        "niche pilates",
        "pilates"
    ]):
        return "Other", "Pilates"

    if "rhino" in m:
        return "Other", "Rent Insurance"

    # -------------------------
    # DEFAULT
    # -------------------------
    return "Other", "Other"
