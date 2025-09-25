#!/usr/bin/env python3
"""
Test to verify analyze-contract route is properly registered
"""

try:
    # Import Flask app creation
    from app.main import create_app
    from app.config.settings import DevelopmentConfig
    
    print("Creating Flask app...")
    app = create_app(DevelopmentConfig)
    
    print("Checking registered routes...")
    with app.app_context():
        routes = []
        for rule in app.url_map.iter_rules():
            methods = ','.join(rule.methods - {'HEAD', 'OPTIONS'})
            routes.append({
                'endpoint': rule.endpoint,
                'methods': methods,
                'rule': str(rule)
            })
        
        # Look for analyze-contract route
        analyze_routes = [r for r in routes if 'analyze-contract' in r['rule']]
        
        print(f"\nTotal routes registered: {len(routes)}")
        print(f"Analyze-contract routes found: {len(analyze_routes)}")
        
        if analyze_routes:
            for route in analyze_routes:
                print(f"✅ Found: {route['methods']} {route['rule']} -> {route['endpoint']}")
        else:
            print("❌ No analyze-contract routes found!")
            
        # Show all API routes
        api_routes = [r for r in routes if '/api/' in r['rule']]
        print(f"\nAll API routes ({len(api_routes)}):")
        for route in sorted(api_routes, key=lambda x: x['rule']):
            print(f"  {route['methods']:10} {route['rule']:30} -> {route['endpoint']}")

except Exception as e:
    print(f"Error creating app: {e}")
    import traceback
    print(traceback.format_exc())