import pandas as pd
import random
import numpy as np

def generate_sample_dataset(n_records: int = 3000) -> pd.DataFrame:
    """Generate sample historical delivery dataset for Indore"""
    
    # Sample locations in Indore
    locations = [
        {"locality": "Vijay Nagar", "lat": 22.7206, "lng": 75.8789, "pincode": "452010"},
        {"locality": "Palasia", "lat": 22.7246, "lng": 75.8729, "pincode": "452001"},
        {"locality": "Rajendra Nagar", "lat": 22.7346, "lng": 75.8829, "pincode": "452012"},
        {"locality": "New Palasia", "lat": 22.7226, "lng": 75.8689, "pincode": "452001"},
        {"locality": "AB Road", "lat": 22.7186, "lng": 75.8749, "pincode": "452008"},
        {"locality": "MG Road", "lat": 22.7266, "lng": 75.8709, "pincode": "452001"},
        {"locality": "Sudama Nagar", "lat": 22.7146, "lng": 75.8629, "pincode": "452009"},
        {"locality": "Bengali Square", "lat": 22.7306, "lng": 75.8769, "pincode": "452001"},
        {"locality": "Chhatripura", "lat": 22.7126, "lng": 75.8689, "pincode": "452009"},
        {"locality": "Annapurna", "lat": 22.7286, "lng": 75.8649, "pincode": "452008"}
    ]
    
    # Sample address patterns
    address_patterns = [
        "Flat {num}, {building} Apartments",
        "Shop {num}, {market} Market", 
        "House {num}, {area} Area",
        "{num} {road} Road",
        "Building {num}, {locality}",
        "{num}/{num2}, {society} Society",
        "Room {num}, {building} Complex"
    ]
    
    # Common landmarks/relations
    landmarks = [
        "near chai tapri", "behind big tree", "opposite police station",
        "near temple", "behind dukaan", "opposite school", 
        "near bus stop", "behind hospital", "opposite bank",
        "near market", "behind petrol pump", "opposite mall"
    ]
    
    # Hinglish variations
    hinglish_variations = [
        "ke paas chai tapri", "ke peeche bada ped", "ke samne police station",
        "paas mandir", "peeche dukaan", "samne school",
        "gali mein", "tapri ke paas", "dukaan ke piche"
    ]
    
    data = []
    
    for i in range(n_records):
        # Select random location
        loc = random.choice(locations)
        
        # Generate address
        pattern = random.choice(address_patterns)
        building_names = ["Sunshine", "Moonlight", "Star", "Ocean", "Mountain", "River", "Garden", "Park"]
        market_names = ["Main", "Central", "Big", "New", "Old", "Local"]
        road_names = ["Main", "First", "Second", "Third", "Fourth", "Fifth"]
        society_names = ["Green", "Blue", "Red", "White", "Golden", "Silver"]
        
        address = pattern.format(
            num=random.randint(1, 200),
            num2=random.randint(1, 20),
            building=random.choice(building_names),
            market=random.choice(market_names),
            area=loc["locality"],
            road=random.choice(road_names),
            society=random.choice(society_names),
            locality=loc["locality"]
        )
        
        # Add landmark/relation
        if random.random() > 0.3:  # 70% chance to add landmark
            if random.random() > 0.5:
                landmark = random.choice(landmarks)
            else:
                landmark = random.choice(hinglish_variations)
            address += f", {landmark}"
        
        # Add locality and city
        address += f", {loc['locality']}, Indore"
        
        # Add some noise to coordinates
        lat_noise = random.uniform(-0.005, 0.005)
        lng_noise = random.uniform(-0.005, 0.005)
        
        record = {
            "order_id": f"ORD{i+1:06d}",
            "city": "Indore",
            "locality": loc["locality"],
            "raw_address": address,
            "lat": loc["lat"] + lat_noise,
            "lng": loc["lng"] + lng_noise,
            "status": random.choice(["delivered", "completed", "successful"])
        }
        
        data.append(record)
    
    return pd.DataFrame(data)

def generate_pincode_mapping() -> pd.DataFrame:
    """Generate locality to pincode mapping"""
    pincode_data = [
        {"locality": "Vijay Nagar", "pincode": "452010"},
        {"locality": "Palasia", "pincode": "452001"},
        {"locality": "Rajendra Nagar", "pincode": "452012"},
        {"locality": "New Palasia", "pincode": "452001"},
        {"locality": "AB Road", "pincode": "452008"},
        {"locality": "MG Road", "pincode": "452001"},
        {"locality": "Sudama Nagar", "pincode": "452009"},
        {"locality": "Bengali Square", "pincode": "452001"},
        {"locality": "Chhatripura", "pincode": "452009"},
        {"locality": "Annapurna", "pincode": "452008"}
    ]
    
    return pd.DataFrame(pincode_data)

if __name__ == "__main__":
    # Generate sample dataset
    print("Generating sample dataset...")
    df = generate_sample_dataset(3000)
    df.to_csv("indore_delivery_events_3000.csv", index=False)
    print(f"Generated {len(df)} records")
    print(df.head())
    
    # Generate pincode mapping
    print("\nGenerating pincode mapping...")
    pincode_df = generate_pincode_mapping()
    pincode_df.to_csv("indore_locality_pincode.csv", index=False)
    print("Generated pincode mapping:")
    print(pincode_df)
    
    print("\n✅ Sample files created successfully!")
    print("- indore_delivery_events_3000.csv")
    print("- indore_locality_pincode.csv")