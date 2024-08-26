mappings={"properties": 
        {"url": 
            {"type": "text"},
        "amount_info": 
            {"type": "text"},
        "site_grant_type": 
            {"type": "text"},
        "modified_date": 
            {"type": "date",
            "format": "yyyy-MM-dd HH:mm:ss||yyyy-MM-dd"},
        "application_url": 
            {"type": "text"},
        "title": 
            {"type": "text"},
        "all_titles": 
            {"type": "text"},
        "submission_info": 
            {"type": "text"},
        "all_grant_source_urls": 
            {"type": "text"},
        "status": 
            {"type": "keyword"},
        "description": 
            {"type": "text"},
        "eligibility": 
            {"type": "text"},
        "categories_display": 
            {"type": "text"},
        "limited_grant_info": 
            {"type": "text"},
        "user_categories": 
            {"type": "text"},
        "submit_date": 
            {"type": "date",
            "format": "yyyy-MM-dd HH:mm:ss||yyyy-MM-dd"},
        "is_limited": 
            {"type": "short"},
        "site_categories": 
            {"type": "text"},
        "cost_sharing": 
            {"type": "text"},
        "grant_source_url": 
            {"type": "text"},
        "deadlines": 
            {"properties": 
                {"type": {"type": "text"},
                "date": {"type": "date",
                        "format": "yyyy-MM-dd HH:mm:ss||yyyy-MM-dd"}
            }},
        "amounts": 
            {"properties": 
                {"confirmed": {"type": "byte"},
                "currency": {"type": "text"},
                "type": {"type": "text"},
                "value": {"type": "double"}
            }},
        "all_types": 
            {"type": "text"},
        "all_applicant_types": 
            {"type": "text"},
        "locations": 
            {"properties": 
                {"is_exclude": {"type": "byte"},
                "is_primary": {"type": "byte"},
                "type": {"type": "text"},
                "text": {"type": "text"}
            }},
        "sponsors": 
            {"properties": 
                {"id": {"type": "text"},
                "name": {"type": "text"}
            }}
        }
    }