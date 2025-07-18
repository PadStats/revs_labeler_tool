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
                "Staircase": None,
                "Mudroom": None
            },
            "Dedicated Utility Spaces": {
                "Laundry Room": None
            },
            "Additional Spaces": {
                "Basement": None,
                "Attic": None,
                "Sunroom": None
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
                    "Interior": None,
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
        "livability status": ["unfinished", "livable/finished"],
        "kitchen_has_island": [True, False]
    }
}

# Feature taxonomy (location-dependent)
FEATURE_TAXONOMY: dict[str, dict[str, list[str]]] = {
    # === RESIDENTIAL INTERIOR =================================================
    "Kitchen": {
        "Appliances": [
            "Refrigerator – Built‑In",
            "Refrigerator – Built‑In | Stainless Steel",
            "Refrigerator – Built‑In | White",
            "Refrigerator – Built‑In | Black",
            "Refrigerator – Built‑In | Black Stainless Steel",
            "Refrigerator – Built‑In | Smart",
            "Refrigerator – Built‑In | Antique",
            "Refrigerator – Freestanding",
            "Refrigerator – Freestanding | Stainless Steel",
            "Refrigerator – Freestanding | White",
            "Refrigerator – Freestanding | Black",
            "Refrigerator – Freestanding | Black Stainless Steel",
            "Refrigerator – Freestanding | Smart",
            "Refrigerator – Freestanding | Antique",
            "Range – Gas",
            "Range – Gas | Stainless Steel",
            "Range – Gas | White",
            "Range – Gas | Black",
            "Range – Gas | Black Stainless Steel",
            "Range – Gas | Smart",
            "Range – Gas | Antique",
            "Range – Electric",
            "Range – Electric | Stainless Steel",
            "Range – Electric | White",
            "Range – Electric | Black",
            "Range – Electric | Black Stainless Steel",
            "Range – Electric | Smart",
            "Range – Electric | Antique",
            "Range – Induction",
            "Range – Induction | Stainless Steel",
            "Range – Induction | White",
            "Range – Induction | Black",
            "Range – Induction | Black Stainless Steel",
            "Range – Induction | Smart",
            "Range – Induction | Antique",
            "Double Oven",
            "Double Oven | Stainless Steel",
            "Double Oven | White",
            "Double Oven | Black",
            "Double Oven | Black Stainless Steel",
            "Double Oven | Smart",
            "Double Oven | Antique",
            "Dishwasher",
            "Dishwasher | Stainless Steel",
            "Dishwasher | White",
            "Dishwasher | Black",
            "Dishwasher | Black Stainless Steel",
            "Dishwasher | Smart",
            "Dishwasher | Antique",
            "Microwave – Built‑In",
            "Microwave – Built‑In | Stainless Steel",
            "Microwave – Built‑In | White",
            "Microwave – Built‑In | Black",
            "Microwave – Built‑In | Black Stainless Steel",
            "Microwave – Built‑In | Smart",
            "Microwave – Built‑In | Antique",
            "Wine Cooler",
            "Wine Cooler | Stainless Steel",
            "Wine Cooler | White",
            "Wine Cooler | Black",
            "Wine Cooler | Black Stainless Steel",
            "Wine Cooler | Smart",
            "Wine Cooler | Antique",
            "Range Hood",
            "Range Hood | Stainless Steel",
            "Range Hood | White",
            "Range Hood | Black",
            "Range Hood | Black Stainless Steel",
            "Range Hood | Smart",
            "Range Hood | Antique",
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
            "Wood",
            "Other"
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
        "Lighting Fixtures": [
            "Pendant",
            "Recessed / Can Lighting",
            "Under-Cabinet",
        ],
        "Trim Baseboards": [],
        "Wall Finish": [],
        "Ceiling": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
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
        "Lighting Fixtures": [
            "Chandelier",
            "Recessed / Can",
            "Ceiling Fan / Light",
        ],
        "Trim Baseboards": [],
        "Wall Finish": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },

    "Dining Room": {
        "Flooring": ["Hardwood", "Tile", "Carpet", "Vinyl/Laminate"],
        "Ceiling & Trim": ["Tray", "Coffered", "Crown Molding"],
        "Lighting Fixtures": ["Chandelier", "Pendant", "Recessed"],
        "Trim Baseboards": [],
        "Built‑Ins": ["Buffet/Sideboard", "China Cabinet", "Wainscoting"],
        "Windows": ["Bay/Bow", "Picture", "French Doors"],
        "Wall Finish": [],
        "Ceiling": [],
        "Window Treatments": [],
        "Doors": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },

    "Loft": {
        "Flooring": ["Hardwood", "Carpet", "Laminate"],
        "Railing": ["Wood", "Metal", "Glass"],
        "Ceiling": ["Open Beam", "Vaulted", "Flat"],
        "Lighting Fixtures": ["Skylight", "Recessed", "Track"],
        "Trim Baseboards": [],
        "Wall Finish": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },

    "Bedroom": {
        "Flooring": ["Carpet", "Hardwood", "Laminate"],
        "Closet": ["Reach‑In", "Walk‑In", "Wardrobe"],
        "Ceiling": ["Tray", "Standard Flat", "Ceiling Fan"],
        "Windows": ["Standard", "Bay/Bow", "Balcony Access"],
        "Lighting Fixtures": ["Overhead Fixture", "Bedside Sconces", "Recessed"],
        "Trim Baseboards": [],
        "Wall Finish": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },
    "Master": {
        "Flooring": ["Hardwood", "Carpet", "Luxury Vinyl"],
        "Closet": ["Walk‑In", "Dual Walk‑In"],
        "Luxury Features": ["Fireplace", "Sitting Area", "Private Balcony"],
        "Ceiling": ["Coffered", "Tray", "Vaulted"],
        "Lighting Fixtures": ["Chandelier", "Recessed", "Bedside Sconces"],
        "Trim Baseboards": [],
        "Wall Finish": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },
    "Secondary": {
        "Flooring": ["Carpet", "Hardwood", "Laminate"],
        "Closet": ["Reach‑In", "Walk‑In"],
        "Ceiling": ["Standard", "Ceiling Fan"],
        "Lighting Fixtures": ["Overhead Fixture", "Desk Lamp"],
        "Trim Baseboards": [],
        "Wall Finish": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },

    # --- BATHS ---------------------------------------------------------------
    "Bathroom": {
        "Vanity": ["Single", "Double", "Floating"],
        "Countertop": ["Granite", "Quartz", "Marble", "Solid Surface"],
        "Shower": ["Walk‑In", "Tub/Shower Combo", "Glass Enclosure"],
        "Tub": ["Standard", "Soaking", "Jetted"],
        "Fixtures": ["Brushed Nickel", "Chrome", "Matte Black"],
        "Flooring": ["Tile – Ceramic", "Tile – Porcelain", "Natural Stone"],
        "Lighting Fixtures": ["Vanity Bar", "Recessed", "Skylight"],
        "Trim Baseboards": [],
        "Wall Finish": [],
        "Ceiling": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },
    "Full Bath": {
        "Vanity": ["Single", "Double"],
        "Shower": ["Walk‑In", "Tub/Shower Combo"],
        "Tub": ["Standard", "Soaking"],
        "Flooring": ["Tile – Ceramic", "Tile – Porcelain"],
        "Wall Finish": [],
        "Ceiling": [],
        "Lighting Fixtures": [],
        "Trim Baseboards": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },
    "Half Bath": {
        "Vanity": ["Pedestal", "Console", "Cabinet"],
        "Fixtures": ["Chrome", "Brass", "Matte Black"],
        "Flooring": ["Tile", "Luxury Vinyl"],
        "Wall Finish": [],
        "Ceiling": [],
        "Lighting Fixtures": [],
        "Trim Baseboards": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },
    "Ensuite": {
        "Vanity": ["Double", "Floating"],
        "Shower": ["Walk‑In", "Rain Shower"],
        "Tub": ["Soaking", "Jetted"],
        "Flooring": ["Tile – Porcelain", "Natural Stone"],
        "Wall Finish": [],
        "Ceiling": [],
        "Lighting Fixtures": [],
        "Trim Baseboards": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },

    "Home Office": {
        "Built‑Ins": ["Desk", "Shelving", "Cabinets"],
        "Technology": ["Multiple Monitors", "Cable Management", "Hard‑Wired Ethernet"],
        "Flooring": ["Hardwood", "Carpet", "Laminate"],
        "Lighting Fixtures": ["Task Lighting", "Recessed", "Natural Window Light"],
        "Trim Baseboards": [],
        "Wall Finish": [],
        "Ceiling": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },

    "Laundry Room": {
        "Appliances": [
            "Top‑Load Washer",
            "Top‑Load Washer | Stainless Steel",
            "Top‑Load Washer | White",
            "Top‑Load Washer | Black",
            "Top‑Load Washer | Black Stainless Steel",
            "Top‑Load Washer | Smart",
            "Top‑Load Washer | Antique",
            "Front‑Load Washer",
            "Front‑Load Washer | Stainless Steel",
            "Front‑Load Washer | White",
            "Front‑Load Washer | Black",
            "Front‑Load Washer | Black Stainless Steel",
            "Front‑Load Washer | Smart",
            "Front‑Load Washer | Antique",
            "Dryer – Electric",
            "Dryer – Electric | Stainless Steel",
            "Dryer – Electric | White",
            "Dryer – Electric | Black",
            "Dryer – Electric | Black Stainless Steel",
            "Dryer – Electric | Smart",
            "Dryer – Electric | Antique",
            "Dryer – Gas",
            "Dryer – Gas | Stainless Steel",
            "Dryer – Gas | White",
            "Dryer – Gas | Black",
            "Dryer – Gas | Black Stainless Steel",
            "Dryer – Gas | Smart",
            "Dryer – Gas | Antique"
        ],
        "Utility Sink": ["Deep Basin", "Stainless", "Composite"],
        "Cabinetry": ["Upper Cabinets", "Lower Cabinets", "Open Shelving"],
        "Countertop": ["Laminate", "Quartz", "Butcher Block"],
        "Flooring": ["Tile", "Luxury Vinyl"],
        "Wall Finish": [],
        "Ceiling": [],
        "Lighting Fixtures": [],
        "Trim Baseboards": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },

    "Laundry Equipment": {
        "Appliances": [
            "Top‑Load Washer",
            "Top‑Load Washer | Stainless Steel",
            "Top‑Load Washer | White",
            "Top‑Load Washer | Black",
            "Top‑Load Washer | Black Stainless Steel",
            "Top‑Load Washer | Smart",
            "Top‑Load Washer | Antique",
            "Front‑Load Washer",
            "Front‑Load Washer | Stainless Steel",
            "Front‑Load Washer | White",
            "Front‑Load Washer | Black",
            "Front‑Load Washer | Black Stainless Steel",
            "Front‑Load Washer | Smart",
            "Front‑Load Washer | Antique",
            "Dryer – Electric",
            "Dryer – Electric | Stainless Steel",
            "Dryer – Electric | White",
            "Dryer – Electric | Black",
            "Dryer – Electric | Black Stainless Steel",
            "Dryer – Electric | Smart",
            "Dryer – Electric | Antique",
            "Dryer – Gas",
            "Dryer – Gas | Stainless Steel",
            "Dryer – Gas | White",
            "Dryer – Gas | Black",
            "Dryer – Gas | Black Stainless Steel",
            "Dryer – Gas | Smart",
            "Dryer – Gas | Antique"
        ],
        "Wall Finish": [],
        "Ceiling": [],
        "Flooring": [],
        "Lighting Fixtures": [],
        "Trim Baseboards": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },

    "Foyer": {
        "Doors": ["Solid Wood", "Glass Panel", "Side‑Lights"],
        "Flooring": ["Hardwood", "Tile", "Stone"],
        "Lighting Fixtures": ["Chandelier", "Pendant", "Recessed"],
        "Trim Baseboards": [],
        "Closet": ["Coat Closet", "None"],
        "Wall Finish": [],
        "Ceiling": [],
        "Windows": [],
        "Window Treatments": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },
    "Hallway": {
        "Flooring": ["Hardwood", "Carpet", "Laminate"],
        "Lighting Fixtures": ["Recessed", "Wall Sconce"],
        "Trim Baseboards": [],
        "Width": ["Standard", "Wide"],
        "Wall Finish": [],
        "Ceiling": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },
    "Staircase": {
        "Railing": ["Wood", "Metal", "Glass"],
        "Treads": ["Wood", "Carpeted", "Tile"],
        "Style": ["Open", "Closed", "Spiral"],
        "Lighting Fixtures": ["Pendant", "Wall Sconce"],
        "Trim Baseboards": [],
        "Wall Finish": [],
        "Ceiling": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },

    # --- ADDITIONAL INTERIOR SPACES -----------------------------------------
    "Basement": {
        "Finish": ["Finished", "Partially Finished", "Unfinished"],
        "Flooring": ["Carpet", "Concrete", "Vinyl", "Tile"],
        "Ceiling Height": ["Standard", "Extra‑Tall"],
        "Egress": ["Window", "Walk‑Out Door", "None"],
        "Moisture Control": ["Sump Pump", "Dehumidifier", "None"],
        "Wall Finish": [],
        "Ceiling": [],
        "Lighting Fixtures": [],
        "Trim Baseboards": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },
    "Attic": {
        "Finish": ["Finished", "Unfinished"],
        "Insulation": ["Blown‑In", "Batt", "Spray Foam"],
        "Flooring": ["Plywood", "None", "Carpet"],
        "Skylight": ["Present", "None"],
        "Wall Finish": [],
        "Ceiling": [],
        "Lighting Fixtures": [],
        "Trim Baseboards": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },

    # === RESIDENTIAL EXTERIOR ===============================================
    "Backyard/Garden": {
        "Landscaping": ["Professionally Landscaped", "Basic", "Xeriscape"],
        "Fencing": ["Wood", "Vinyl", "Chain‑Link", "None"],
        "Irrigation": ["Sprinkler System", "Drip", "None"],
        "Outbuildings": ["Shed", "Greenhouse", "None"],
        "Lighting Fixtures": [],
    },
    "Frontyard": {
        "Landscaping": ["Professionally Landscaped", "Basic", "Zero‑Scape"],
        "Walkway": ["Concrete", "Paver", "Stone"],
        "Porch": ["Covered", "Open", "None"],
        "Lighting Fixtures": [],
    },
    "Patio/Deck/Balcony": {
        "Surface Material": ["Wood", "Composite", "Concrete", "Stone/Paver"],
        "Cover": ["Pergola", "Awning", "Covered Roof", "None"],
        "Railing": ["Wood", "Metal", "Glass", "None"],
        "Outdoor Kitchen": ["Built‑In Grill", "Sink", "Refrigerator", "None"],
        "Lighting Fixtures": ["String Lights", "Wall Sconce", "Recessed"],
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
        "Lighting Fixtures": [],
    },

    # --- OUTDOOR RECREATION --------------------------------------------------
    "Sports Court": {
        "Court Type": ["Tennis", "Basketball", "Multi‑Sport"],
        "Surface": ["Asphalt", "Concrete", "Sport Tile"],
        "Fence": ["Chain‑Link", "None"],
        "Lighting Fixtures": ["Yes", "No"],
    },
    "Playground": {
        "Equipment": ["Swings", "Slide", "Climbing Structure"],
        "Surface": ["Mulch", "Rubber", "Grass"],
        "Fence": ["Yes", "No"],
    },
    "Rooftop": {
        "Surface": ["Decking", "Green Roof", "Gravel"],
        "Amenities": ["Seating", "Pergola", "Planters"],
    },
    "Barbecue Area": {
        "Grill Type": ["Built‑In", "Freestanding"],
        "Countertop": ["Stone", "Concrete", "Tile"],
        "Seating": ["Bar Seating", "Table Seating", "None"],
        "Cover": ["Pergola", "Gazebo", "None"],
    },

    # === PARKING & SERVICE ===================================================
    "Residential Garage": {
        "Flooring": ["Concrete", "Epoxy", "Gravel"],
        "Wall Finish": [],
        "Ceiling": [],
        "Lighting Fixtures": [],
        "Trim Baseboards": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },
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
        "HVAC Vents": ["HVAC", "Fans", "Windows"],
        "Wall Finish": [],
        "Ceiling": [],
        "Lighting Fixtures": [],
        "Trim Baseboards": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "Electrical Outlets": [],
        "Misc": [],
    },
    "Game Room": {
        "Flooring": ["Carpet", "Hardwood", "Vinyl"],
        "Equipment": ["Pool Table", "Arcade", "Ping‑Pong"],
        "Lighting Fixtures": ["Pendant", "Recessed"],
        "Trim Baseboards": [],
        "Wall Finish": [],
        "Ceiling": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },
    "Home Theater": {
        "Seating": ["Tiered", "Recliner", "Sofa"],
        "Screen": ["Fixed", "Retractable", "Projector"],
        "Sound": ["Surround", "Soundbar"],
        "Lighting Fixtures": ["Wall Sconce", "Star Ceiling", "Dimmable Recessed"],
        "Trim Baseboards": [],
        "Wall Finish": [],
        "Ceiling": [],
        "Flooring": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },
    "Wine Cellar": {
        "Racking": ["Wood", "Metal", "Custom"],
        "Cooling System": ["Active", "Passive"],
        "Door": ["Glass", "Solid Wood"],
        "Flooring": ["Stone", "Tile", "Concrete"],
        "Wall Finish": [],
        "Ceiling": [],
        "Lighting Fixtures": [],
        "Trim Baseboards": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },
    "Home Bar": {
        "Countertop": ["Granite", "Quartz", "Wood"],
        "Cabinetry": ["Glass Front", "Open Shelving", "Closed"],
        "Appliances": [
            "Under‑Counter Fridge",
            "Under‑Counter Fridge | Stainless Steel",
            "Under‑Counter Fridge | White",
            "Under‑Counter Fridge | Black",
            "Under‑Counter Fridge | Black Stainless Steel",
            "Under‑Counter Fridge | Smart",
            "Under‑Counter Fridge | Antique",
            "Wine Cooler",
            "Wine Cooler | Stainless Steel",
            "Wine Cooler | White",
            "Wine Cooler | Black",
            "Wine Cooler | Black Stainless Steel",
            "Wine Cooler | Smart",
            "Wine Cooler | Antique",
            "Ice Maker",
            "Ice Maker | Stainless Steel",
            "Ice Maker | White",
            "Ice Maker | Black",
            "Ice Maker | Black Stainless Steel",
            "Ice Maker | Smart",
            "Ice Maker | Antique"
        ],
        "Sink": ["Wet Bar Sink", "None"],
        "Wall Finish": [],
        "Ceiling": [],
        "Flooring": [],
        "Lighting Fixtures": [],
        "Trim Baseboards": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
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
    "Interior": {
        "Wall Finish": [],
        "Ceiling": [],
        "Flooring": [],
        "Lighting Fixtures": [],
        "Trim Baseboards": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },
    "Closet": {
        "Wall Finish": [],
        "Ceiling": [],
        "Flooring": [],
        "Lighting Fixtures": [],
        "Trim Baseboards": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },
    "Walk-in Closet": {
        "Wall Finish": [],
        "Ceiling": [],
        "Flooring": [],
        "Lighting Fixtures": [],
        "Trim Baseboards": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },
    "Common Room": {
        "Wall Finish": [],
        "Ceiling": [],
        "Flooring": [],
        "Lighting Fixtures": [],
        "Trim Baseboards": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },
    "Shared Laundry Room": {
        "Wall Finish": [],
        "Ceiling": [],
        "Flooring": [],
        "Lighting Fixtures": [],
        "Trim Baseboards": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },
    "Mail Room": {
        "Wall Finish": [],
        "Ceiling": [],
        "Flooring": [],
        "Lighting Fixtures": [],
        "Trim Baseboards": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },
    "Office": {
        "Wall Finish": [],
        "Ceiling": [],
        "Flooring": [],
        "Lighting Fixtures": [],
        "Trim Baseboards": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },
    "Conference Room": {
        "Wall Finish": [],
        "Ceiling": [],
        "Flooring": [],
        "Lighting Fixtures": [],
        "Trim Baseboards": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },
    "Reception/Lobby": {
        "Wall Finish": [],
        "Ceiling": [],
        "Flooring": [],
        "Lighting Fixtures": [],
        "Trim Baseboards": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },
    "Break Room": {
        "Wall Finish": [],
        "Ceiling": [],
        "Flooring": [],
        "Lighting Fixtures": [],
        "Trim Baseboards": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },
    "Retail Area": {
        "Wall Finish": [],
        "Ceiling": [],
        "Flooring": [],
        "Lighting Fixtures": [],
        "Trim Baseboards": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },
    "Showroom": {
        "Wall Finish": [],
        "Ceiling": [],
        "Flooring": [],
        "Lighting Fixtures": [],
        "Trim Baseboards": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },
    "Warehouse": {
        "Wall Finish": [],
        "Ceiling": [],
        "Flooring": [],
        "Lighting Fixtures": [],
        "Trim Baseboards": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },
    "Stock Room": {
        "Wall Finish": [],
        "Ceiling": [],
        "Flooring": [],
        "Lighting Fixtures": [],
        "Trim Baseboards": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },
    "Commercial Kitchen": {
        "Wall Finish": [],
        "Ceiling": [],
        "Flooring": [],
        "Lighting Fixtures": [],
        "Trim Baseboards": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },
    "Restroom": {
        "Wall Finish": [],
        "Ceiling": [],
        "Flooring": [],
        "Lighting Fixtures": [],
        "Trim Baseboards": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },
    "Boiler/Mechanical Room": {
        "Wall Finish": [],
        "Ceiling": [],
        "Flooring": [],
        "Lighting Fixtures": [],
        "Trim Baseboards": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },
    "Utility Closet": {
        "Wall Finish": [],
        "Ceiling": [],
        "Flooring": [],
        "Lighting Fixtures": [],
        "Trim Baseboards": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },
    "Electrical/Server Room": {
        "Wall Finish": [],
        "Ceiling": [],
        "Flooring": [],
        "Lighting Fixtures": [],
        "Trim Baseboards": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },
    "Industrial/Warehouse": {
        "Wall Finish": [],
        "Ceiling": [],
        "Flooring": [],
        "Lighting Fixtures": [],
        "Trim Baseboards": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },
    "Restaurant": {
        "Wall Finish": [],
        "Ceiling": [],
        "Flooring": [],
        "Lighting Fixtures": [],
        "Trim Baseboards": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },
    "Bar/Nightclub": {
        "Wall Finish": [],
        "Ceiling": [],
        "Flooring": [],
        "Lighting Fixtures": [],
        "Trim Baseboards": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },
    "Medical Office": {
        "Wall Finish": [],
        "Ceiling": [],
        "Flooring": [],
        "Lighting Fixtures": [],
        "Trim Baseboards": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },
    "Laboratory": {
        "Wall Finish": [],
        "Ceiling": [],
        "Flooring": [],
        "Lighting Fixtures": [],
        "Trim Baseboards": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },
    "Workshop": {
        "Wall Finish": [],
        "Ceiling": [],
        "Flooring": [],
        "Lighting Fixtures": [],
        "Trim Baseboards": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },
    "Manufacturing": {
        "Wall Finish": [],
        "Ceiling": [],
        "Flooring": [],
        "Lighting Fixtures": [],
        "Trim Baseboards": [],
        "Windows": [],
        "Window Treatments": [],
        "Doors": [],
        "Built-Ins": [],
        "HVAC Vents": [],
        "Electrical Outlets": [],
        "Misc": [],
    },
}


# Attribute rules - which attributes apply to which location types
ATTRIBUTE_RULES = {
    "furnishing status": ["Residential Interior"],  # Only for interior spaces
    "livability status": ["Residential Interior", "Commercial Interior"],  # Interior spaces
    "kitchen_has_island": ["Kitchen"],  # Only when Kitchen is selected
}

# --------------------------------------------------------------------------- #
# Standardize common feature option lists across all locations                #
# --------------------------------------------------------------------------- #
from standard_feature_values import STANDARD_FEATURE_VALUES as _STD_FEATURE_VALUES

def _standard_key(name: str) -> str:
    """Normalize feature names: lower-case, spaces & hyphens → underscores."""
    return name.lower().replace(" ", "_").replace("-", "_")

for _loc, _feat_dict in FEATURE_TAXONOMY.items():
    for _feat_name in list(_feat_dict.keys()):
        _key = _standard_key(_feat_name)
        if _key in _STD_FEATURE_VALUES:
            _feat_dict[_feat_name] = _STD_FEATURE_VALUES[_key]

# --------------------------------------------------------------------------- #
# Ensure every location has the required standard-feature placeholders         #
# (per condensed mapping guide)                                               #
# --------------------------------------------------------------------------- #
import collections.abc

def _get_leaf_locations(tax):
    leaves = []
    for k, v in tax.items():
        if isinstance(v, dict):
            leaves.extend(_get_leaf_locations(v))
        elif v is None:
            leaves.append(k)
    return leaves

# Define the root for interior leaves
_INTERIOR_ROOTS = [
    "Residential Interior",
    "Residential Amenities",
    "Shared & Common Areas",
    "Commercial Interior",
    "Utility & Mechanical",
    "Special-Purpose Commercial",
    # Parking & Service handled below
]

# Find all interior leaf locations
_interior_leaves = set()
for root in _INTERIOR_ROOTS:
    node = LOCATION_TAXONOMY["spatial"].get(root, {})
    _interior_leaves.update(_get_leaf_locations(node))

# Add interior leaves from Parking & Service
parking_node = LOCATION_TAXONOMY["spatial"].get("Parking & Service", {})
for k, v in parking_node.items():
    if isinstance(v, dict):
        # Special case: only include 'Interior' under 'Residential Garage' as an interior leaf
        if k == "Parking":
            residential_garage = v.get("Residential Garage", {})
            if isinstance(residential_garage, dict) and "Interior" in residential_garage:
                _interior_leaves.add("Interior")
        # All other parking leaves are excluded
    elif v is None:
        continue

# Outdoor Living leaves for Lighting Fixtures
_OUTDOOR_LIVING_LEAVES = [
    "Backyard/Garden",
    "Frontyard",
    "Patio/Deck/Balcony",
    "Driveway",
    "Pool Area",
    "Sports Court",
    "Playground",
    "Rooftop",
    "Barbecue Area",
]

# Standard features
_FEATURE_STANDARD_KEYS = [
    "Flooring",
    "Wall Finish",
    "Ceiling",
    "Lighting Fixtures",
    "Trim Baseboards",
    "Windows",
    "Window Treatments",
    "Doors",
    "Built-Ins",
    "HVAC Vents",
    "Electrical Outlets",
    "Misc",
]

# --- MANUAL PATCH: Explicitly define all standard features for every interior leaf and Lighting Fixtures for Outdoor Living leaves ---

_EXCLUDED_FROM_STANDARD_FEATURES = {"Attached", "Detached", "Carport", "Outdoor Lot", "Exterior/Multilevel", "Service Areas", "Loading Dock", "Recycling/Garbage", "EV Charging Station"}

for loc, features in FEATURE_TAXONOMY.items():
    # Outdoor Living leaves: only Lighting Fixtures
    if loc in _OUTDOOR_LIVING_LEAVES:
        if "Lighting Fixtures" not in features:
            features["Lighting Fixtures"] = []
        continue
    # Only add standard features to interior leaves, EXCLUDING certain locations
    if loc in _interior_leaves and loc not in _EXCLUDED_FROM_STANDARD_FEATURES:
        for key in _FEATURE_STANDARD_KEYS:
            if key == "Window Treatments" and "Windows" not in features:
                # Skip window treatments if the location has no windows category
                continue

            if key not in features:
                # Populate with standard values if available, otherwise empty list
                _std_key = _standard_key(key)
                features[key] = _STD_FEATURE_VALUES.get(_std_key, [])

# Clean up helper vars
for _tmp in ["_get_leaf_locations", "_INTERIOR_ROOTS", "_interior_leaves", "_OUTDOOR_LIVING_LEAVES", "_FEATURE_STANDARD_KEYS", "parking_node", "node", "k", "v", "leaf", "path", "_EXCLUDED_FROM_STANDARD_FEATURES"]:
    globals().pop(_tmp, None)