# Your existing taxonomy structure
LOCATION_TAXONOMY = {
    "spatial": {
        "Residential Interior": {
            "Living Areas": {
                "Living Room": None,
                "Dining Room": None,
                "Kitchen": None,
                "Loft": None
            },
            "Private Spaces": {
                "Bedroom": {
                    "Master": None,
                    "Secondary": None
                },
                "Bathroom": {
                    "Full Bath": None,
                    "Half Bath": None,
                    "Ensuite": None
                },
                "Home Office": None
            },
            "Entry & Circulation": {
                "Foyer": None,
                "Hallway": None,
                "Staircase": None
            },
            "Dedicated Utility Spaces": {
                "Laundry Room": None
            },
            "Additional Spaces": {
                "Basement": None,
                "Attic": None
            }
        },
        "Residential Amenities": {
            "Recreation & Wellness": {
                "Home Gym": None,
                "Game Room": None,
                "Home Theater": None,
                "Indoor Pool": None,
                "Sauna/Spa": None,
                "Jacuzzi": None
            },
            "Storage & Utility": {
                "Closet": None,
                "Walk-in Closet": None,
                "Laundry Equipment": None
            },
            "Other Amenities": {
                "Wine Cellar": None,
                "Home Bar": None
            }
        },
        "Residential Exterior": {
            "Facade & Views": {
                "Building Type": {
                    "House": None,
                    "Apartment/Condo": None,
                    "Commercial": None,
                    "Townhome": None,
                    "Mobile Home/Trailer": None
                },
                "View": {
                    "Front View": None,
                    "Side/Rear View": None,
                    "Entryway/Front Door": None,
                    "Landscape/Natural View": None,
                    "Aerial View": None,
                    "Street/Neighborhood View": None
                }
            },
            "Outdoor Living": {
                "Backyard/Garden": None,
                "Patio/Deck/Balcony": None,
                "Driveway": None,
                "Frontyard": None,
                "Pool Area": None
            },
            "Recreational Outdoors": {
                "Sports Court": None,
                "Playground": None,
                "Park": None,
                "Rooftop": None,
                "Barbecue Area": None
            },
            "Other Exteriors": {
                "Boat Dock": None,
                "Basement Access": None,
                "Waterfront Access": None
            }
        },
        "Parking & Service": {
            "Parking": {
                "Commercial Garage": {
                    "Interior": None,
                    "Exterior/Multilevel": None
                },
                "Outdoor Lot": None,
                "Residential Garage": {
                    "Attached": None,
                    "Detached": None
                },
                "Carport": None
            },
            "Service Areas": {
                "Loading Dock": None,
                "Recycling/Garbage": None,
                "EV Charging Station": None
            }
        },
        "Shared & Common Areas": {
            "Residential Common Spaces": {
                "Lobby": None,
                "Shared Hallway": None,
                "Common Room": None,
                "Shared Laundry Room": None,
                "Mail Room": None
            },
            "Recreational Facilities": {
                "Shared Gym": None,
                "Shared Pool": None,
                "Shared Restroom": None
            },
            "Business Centers": {
                "Co-working Space": None
            }
        },
        "Commercial Interior": {
            "Workspaces": {
                "Office": None,
                "Conference Room": None,
                "Reception/Lobby": None,
                "Break Room": None
            },
            "Retail & Storage": {
                "Retail Area": None,
                "Showroom": None,
                "Warehouse": None,
                "Stock Room": None
            },
            "Facilities": {
                "Commercial Kitchen": None,
                "Restroom": None
            }
        },
        "Utility & Mechanical": {
            "Mechanical Spaces": {
                "Boiler/Mechanical Room": None,
                "Utility Closet": None
            },
            "Technical Spaces": {
                "Electrical/Server Room": None,
                "Industrial/Warehouse": None
            }
        },
        "Special-Purpose Commercial": {
            "Dining & Entertainment": {
                "Restaurant": None,
                "Bar/Nightclub": None
            },
            "Healthcare & Research": {
                "Medical Office": None,
                "Laboratory": None
            },
            "Production": {
                "Workshop": None,
                "Manufacturing": None
            },
            "Religious": {
                "Church/Religious Facility": None
            }
        },
        "Other": {
            "Out-of-Domain": {
                "Unknown/Irrelevant": None
            },
            "Miscellaneous Objects": {
                "Object/Misc": None,
                "Leasing Advertisement": None
            },
            "Documents & Plans": {
                "Map": None,
                "Floorplan": None
            }
        }
    },
    "attributes": {
        "furnishing status": ["furnished", "unfurnished"],
        "condition status": ["unfinished", "renovation"],
        "kitchen_has_island": [True, False]
    }
}

# Feature taxonomy (location-dependent)
FEATURE_TAXONOMY: dict[str, dict[str, list[str]]] = {
    # === RESIDENTIAL INTERIOR =================================================
    "Kitchen": {
        "Appliances": [
            "Refrigerator – Built‑In",
            "Refrigerator – Freestanding",
            "Range – Gas",
            "Range – Electric",
            "Range – Induction",
            "Double Oven",
            "Dishwasher",
            "Microwave – Built‑In",
            "Wine Cooler",
            "Range Hood",
        ],
        "Countertops": [
            "Granite",
            "Quartz",
            "Marble",
            "Solid Surface",
            "Butcher Block",
            "Laminate",
        ],
        "Cabinetry": [
            "Shaker Style",
            "Raised Panel",
            "Flat Panel / Slab",
            "Glass‑Front",
            "Open Shelving",
        ],
        "Sink": [
            "Single Basin",
            "Double Basin",
            "Farmhouse / Apron",
            "Undermount",
        ],
        "Layout & Work Zones": [
            "Island",
            "Peninsula",
            "Breakfast Bar",
            "Walk‑In Pantry",
        ],
        "Flooring": [
            "Tile",
            "Hardwood",
            "Engineered Wood",
            "Luxury Vinyl / Laminate",
        ],
        "Backsplash": [
            "Subway Tile",
            "Mosaic / Glass Tile",
            "Natural Stone",
            "Metal / Stainless",
        ],
        "Lighting": [
            "Pendant",
            "Recessed / Can Lighting",
            "Under‑Cabinet",
        ],
    },

    "Living Room": {
        "Flooring": [
            "Hardwood",
            "Carpet",
            "Luxury Vinyl / Laminate",
            "Tile",
        ],
        "Fireplace": [
            "Wood‑Burning",
            "Gas",
            "Electric",
            "No Fireplace",
        ],
        "Ceiling": [
            "Vaulted / Cathedral",
            "Tray",
            "Coffered",
            "Standard Flat",
        ],
        "Built‑Ins": [
            "Entertainment Center",
            "Bookcases",
            "Window Seat",
        ],
        "Windows": [
            "Bay / Bow",
            "Picture",
            "Sliding / French Doors",
        ],
        "Lighting": [
            "Chandelier",
            "Recessed / Can",
            "Ceiling Fan / Light",
        ],
    },

    "Dining Room": {
        "Flooring": ["Hardwood", "Tile", "Carpet", "Vinyl/Laminate"],
        "Ceiling & Trim": ["Tray", "Coffered", "Crown Molding"],
        "Lighting": ["Chandelier", "Pendant", "Recessed"],
        "Built‑Ins": ["Buffet/Sideboard", "China Cabinet", "Wainscoting"],
        "Windows": ["Bay/Bow", "Picture", "French Doors"],
    },

    "Loft": {
        "Flooring": ["Hardwood", "Carpet", "Laminate"],
        "Railing": ["Wood", "Metal", "Glass"],
        "Ceiling": ["Open Beam", "Vaulted", "Flat"],
        "Lighting": ["Skylight", "Recessed", "Track"],
    },

    "Bedroom": {
        "Flooring": ["Carpet", "Hardwood", "Laminate"],
        "Closet": ["Reach‑In", "Walk‑In", "Wardrobe"],
        "Ceiling": ["Tray", "Standard Flat", "Ceiling Fan"],
        "Windows": ["Standard", "Bay/Bow", "Balcony Access"],
        "Lighting": ["Overhead Fixture", "Bedside Sconces", "Recessed"],
    },
    "Master": {
        "Flooring": ["Hardwood", "Carpet", "Luxury Vinyl"],
        "Closet": ["Walk‑In", "Dual Walk‑In"],
        "Luxury Features": ["Fireplace", "Sitting Area", "Private Balcony"],
        "Ceiling": ["Coffered", "Tray", "Vaulted"],
        "Lighting": ["Chandelier", "Recessed", "Bedside Sconces"],
    },
    "Secondary": {
        "Flooring": ["Carpet", "Hardwood", "Laminate"],
        "Closet": ["Reach‑In", "Walk‑In"],
        "Ceiling": ["Standard", "Ceiling Fan"],
        "Lighting": ["Overhead Fixture", "Desk Lamp"],
    },

    # --- BATHS ---------------------------------------------------------------
    "Bathroom": {
        "Vanity": ["Single", "Double", "Floating"],
        "Countertop": ["Granite", "Quartz", "Marble", "Solid Surface"],
        "Shower": ["Walk‑In", "Tub/Shower Combo", "Glass Enclosure"],
        "Tub": ["Standard", "Soaking", "Jetted"],
        "Fixtures": ["Brushed Nickel", "Chrome", "Matte Black"],
        "Flooring": ["Tile – Ceramic", "Tile – Porcelain", "Natural Stone"],
        "Lighting": ["Vanity Bar", "Recessed", "Skylight"],
    },
    "Full Bath": {
        "Vanity": ["Single", "Double"],
        "Shower": ["Walk‑In", "Tub/Shower Combo"],
        "Tub": ["Standard", "Soaking"],
        "Flooring": ["Tile – Ceramic", "Tile – Porcelain"],
    },
    "Half Bath": {
        "Vanity": ["Pedestal", "Console", "Cabinet"],
        "Fixtures": ["Chrome", "Brass", "Matte Black"],
        "Flooring": ["Tile", "Luxury Vinyl"],
    },
    "Ensuite": {
        "Vanity": ["Double", "Floating"],
        "Shower": ["Walk‑In", "Rain Shower"],
        "Tub": ["Soaking", "Jetted"],
        "Flooring": ["Tile – Porcelain", "Natural Stone"],
    },

    "Home Office": {
        "Built‑Ins": ["Desk", "Shelving", "Cabinets"],
        "Technology": ["Multiple Monitors", "Cable Management", "Hard‑Wired Ethernet"],
        "Flooring": ["Hardwood", "Carpet", "Laminate"],
        "Lighting": ["Task Lighting", "Recessed", "Natural Window Light"],
    },

    "Laundry Room": {
        "Appliances": ["Top‑Load Washer", "Front‑Load Washer", "Dryer – Electric", "Dryer – Gas"],
        "Utility Sink": ["Deep Basin", "Stainless", "Composite"],
        "Cabinetry": ["Upper Cabinets", "Lower Cabinets", "Open Shelving"],
        "Countertop": ["Laminate", "Quartz", "Butcher Block"],
        "Flooring": ["Tile", "Luxury Vinyl"],
    },

    "Foyer": {
        "Door": ["Solid Wood", "Glass Panel", "Side‑Lights"],
        "Flooring": ["Hardwood", "Tile", "Stone"],
        "Lighting": ["Chandelier", "Pendant", "Recessed"],
        "Closet": ["Coat Closet", "None"],
    },
    "Hallway": {
        "Flooring": ["Hardwood", "Carpet", "Laminate"],
        "Lighting": ["Recessed", "Wall Sconce"],
        "Width": ["Standard", "Wide"],
    },
    "Staircase": {
        "Railing": ["Wood", "Metal", "Glass"],
        "Treads": ["Wood", "Carpeted", "Tile"],
        "Style": ["Open", "Closed", "Spiral"],
        "Lighting": ["Pendant", "Wall Sconce"],
    },

    # --- ADDITIONAL INTERIOR SPACES -----------------------------------------
    "Basement": {
        "Finish": ["Finished", "Partially Finished", "Unfinished"],
        "Flooring": ["Carpet", "Concrete", "Vinyl", "Tile"],
        "Ceiling Height": ["Standard", "Extra‑Tall"],
        "Egress": ["Window", "Walk‑Out Door", "None"],
        "Moisture Control": ["Sump Pump", "Dehumidifier", "None"],
    },
    "Attic": {
        "Finish": ["Finished", "Unfinished"],
        "Insulation": ["Blown‑In", "Batt", "Spray Foam"],
        "Flooring": ["Plywood", "None", "Carpet"],
        "Skylight": ["Present", "None"],
    },

    # === RESIDENTIAL EXTERIOR ===============================================
    "Backyard/Garden": {
        "Landscaping": ["Professionally Landscaped", "Basic", "Xeriscape"],
        "Fencing": ["Wood", "Vinyl", "Chain‑Link", "None"],
        "Irrigation": ["Sprinkler System", "Drip", "None"],
        "Outbuildings": ["Shed", "Greenhouse", "None"],
    },
    "Frontyard": {
        "Landscaping": ["Professionally Landscaped", "Basic", "Zero‑Scape"],
        "Walkway": ["Concrete", "Paver", "Stone"],
        "Porch": ["Covered", "Open", "None"],
    },
    "Patio/Deck/Balcony": {
        "Surface Material": ["Wood", "Composite", "Concrete", "Stone/Paver"],
        "Cover": ["Pergola", "Awning", "Covered Roof", "None"],
        "Railing": ["Wood", "Metal", "Glass", "None"],
        "Outdoor Kitchen": ["Built‑In Grill", "Sink", "Refrigerator", "None"],
        "Lighting": ["String Lights", "Wall Sconce", "Recessed"],
    },
    "Driveway": {
        "Material": ["Concrete", "Asphalt", "Paver", "Gravel"],
        "Condition": ["Excellent", "Good", "Cracked"],
        "Parking Capacity": ["Single", "Double", "Multiple"],
    },
    "Pool Area": {
        "Pool Type": ["In‑Ground", "Above‑Ground"],
        "Surface": ["Gunite", "Vinyl", "Fiberglass"],
        "Safety": ["Fence", "Screen Enclosure", "None"],
        "Deck Material": ["Concrete", "Paver", "Travertine"],
        "Spa / Hot Tub": ["Integrated", "Separate", "None"],
    },

    # --- OUTDOOR RECREATION --------------------------------------------------
    "Sports Court": {
        "Court Type": ["Tennis", "Basketball", "Multi‑Sport"],
        "Surface": ["Asphalt", "Concrete", "Sport Tile"],
        "Fence": ["Chain‑Link", "None"],
        "Lighting": ["Yes", "No"],
    },
    "Playground": {
        "Equipment": ["Swings", "Slide", "Climbing Structure"],
        "Surface": ["Mulch", "Rubber", "Grass"],
        "Fence": ["Yes", "No"],
    },
    "Rooftop": {
        "Surface": ["Decking", "Green Roof", "Gravel"],
        "Railing": ["Metal", "Glass", "None"],
        "Amenities": ["Seating", "Pergola", "Planters"],
    },
    "Barbecue Area": {
        "Grill Type": ["Built‑In", "Freestanding"],
        "Countertop": ["Stone", "Concrete", "Tile"],
        "Seating": ["Bar Seating", "Table Seating", "None"],
        "Cover": ["Pergola", "Gazebo", "None"],
    },

    # === PARKING & SERVICE ===================================================
    "Attached": {
        "Car Capacity": ["Single", "Double", "Triple+"],
        "Door Type": ["Sectional", "Carriage", "Roll‑Up"],
        "Flooring": ["Concrete", "Epoxy"],
        "Storage": ["Cabinets", "Overhead Racks", "None"],
    },
    "Detached": {
        "Car Capacity": ["Single", "Double", "Triple+"],
        "Door Type": ["Sectional", "Roll‑Up"],
        "Flooring": ["Concrete", "Gravel"],
        "Workshop Area": ["Yes", "No"],
    },
    "Carport": {
        "Structure": ["Metal", "Wood"],
        "Enclosure": ["Open", "Partial", "Fully Enclosed"],
        "Storage": ["Attached Shed", "None"],
    },

    # === AMENITY ROOMS =======================================================
    "Home Gym": {
        "Flooring": ["Rubber", "Carpet", "Hardwood"],
        "Mirrors": ["Full Wall", "Partial", "None"],
        "Equipment": ["Cardio", "Weights", "Multi‑Station"],
        "Ventilation": ["HVAC", "Fans", "Windows"],
    },
    "Game Room": {
        "Flooring": ["Carpet", "Hardwood", "Vinyl"],
        "Equipment": ["Pool Table", "Arcade", "Ping‑Pong"],
        "Lighting": ["Pendant", "Recessed"],
    },
    "Home Theater": {
        "Seating": ["Tiered", "Recliner", "Sofa"],
        "Screen": ["Fixed", "Retractable", "Projector"],
        "Sound": ["Surround", "Soundbar"],
        "Lighting": ["Wall Sconce", "Star Ceiling", "Dimmable Recessed"],
    },
    "Wine Cellar": {
        "Racking": ["Wood", "Metal", "Custom"],
        "Cooling System": ["Active", "Passive"],
        "Door": ["Glass", "Solid Wood"],
        "Flooring": ["Stone", "Tile", "Concrete"],
    },
    "Home Bar": {
        "Countertop": ["Granite", "Quartz", "Wood"],
        "Cabinetry": ["Glass Front", "Open Shelving", "Closed"],
        "Appliances": ["Under‑Counter Fridge", "Wine Cooler", "Ice Maker"],
        "Sink": ["Wet Bar Sink", "None"],
    },

    # === SPECIAL EXTERIOR FEATURES ==========================================
    "Boat Dock": {
        "Dock Type": ["Fixed", "Floating"],
        "Material": ["Wood", "Composite"],
        "Boat Lift": ["Yes", "No"],
        "Condition": ["Excellent", "Good", "Fair"],
    },
    "Waterfront Access": {
        "Shoreline": ["Seawall", "Natural Beach", "Bulkhead"],
        "Dock": ["Present", "None"],
    },
    "Basement Access": {
        "Entrance": ["Walk‑Up", "Bilco Door", "Interior Stair"],
        "Stair Material": ["Concrete", "Wood", "Metal"],
    },
}


# Attribute rules - which attributes apply to which location types
ATTRIBUTE_RULES = {
    "furnishing status": ["Residential Interior"],  # Only for interior spaces
    "condition status": ["Residential Interior", "Commercial Interior"],  # Interior spaces
    "kitchen_has_island": ["Kitchen"]  # Only when Kitchen is selected
}