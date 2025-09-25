#!/usr/bin/env python3
"""
Direct test of the analyze-contract route registration
"""

# Test if the route is registered correctly by checking the blueprint directly
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_blueprint_registration():
    """Test if the analyze-contract route is in the blueprint"""
    
    try:
        # Import the blueprint directly
        from app.api.routes.analysis import analysis_bp
        
        print("🔍 Testing Blueprint Registration")
        print("=" * 50)
        
        print(f"Blueprint name: {analysis_bp.name}")
        print(f"Blueprint url_prefix: {getattr(analysis_bp, 'url_prefix', 'None')}")
        
        # Check the blueprint's deferred functions (routes)
        print(f"\nBlueprint deferred functions: {len(analysis_bp.deferred_functions)}")
        
        route_count = 0
        analyze_contract_found = False
        
        for func in analysis_bp.deferred_functions:
            # Each deferred function is a partial that contains route info
            if hasattr(func, 'func') and hasattr(func.func, '__name__'):
                if func.func.__name__ == 'add_url_rule':
                    args = func.args
                    if len(args) >= 2:
                        rule = args[0]
                        endpoint = args[1] if len(args) > 1 else 'unknown'
                        
                        route_count += 1
                        print(f"  Route {route_count}: {rule} -> {endpoint}")
                        
                        if 'analyze-contract' in rule:
                            analyze_contract_found = True
                            print(f"    ✅ Found analyze-contract route!")
        
        if analyze_contract_found:
            print(f"\n✅ analyze-contract route IS registered in blueprint")
        else:
            print(f"\n❌ analyze-contract route NOT FOUND in blueprint")
            
        # Try to find the actual function
        import importlib
        import inspect
        
        # Get all functions in the analysis module
        analysis_module = importlib.import_module('app.api.routes.analysis')
        
        functions = [name for name, obj in inspect.getmembers(analysis_module) 
                    if inspect.isfunction(obj)]
        
        print(f"\nFunctions in analysis module: {len(functions)}")
        for func_name in functions:
            if 'analyze' in func_name.lower():
                print(f"  • {func_name}")
        
        # Check if analyze_contract function exists
        if hasattr(analysis_module, 'analyze_contract'):
            print(f"\n✅ analyze_contract function EXISTS in module")
        else:
            print(f"\n❌ analyze_contract function NOT FOUND in module")
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing blueprint: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_route_in_context():
    """Test route registration in Flask app context"""
    try:
        print(f"\n🔍 Testing Route in Flask Context")
        print("=" * 50)
        
        # We can't create the full app due to dependencies, but we can test 
        # if the blueprint has the route registered
        from flask import Flask
        from app.api.routes.analysis import analysis_bp
        
        # Create minimal Flask app just for testing
        test_app = Flask(__name__)
        test_app.register_blueprint(analysis_bp, url_prefix='/api')
        
        with test_app.app_context():
            routes = []
            for rule in test_app.url_map.iter_rules():
                methods = ','.join(rule.methods - {'HEAD', 'OPTIONS'})
                routes.append({
                    'rule': str(rule),
                    'methods': methods,
                    'endpoint': rule.endpoint
                })
            
            print(f"Total routes in test app: {len(routes)}")
            
            analyze_routes = [r for r in routes if 'analyze-contract' in r['rule']]
            
            if analyze_routes:
                print(f"✅ Found analyze-contract routes:")
                for route in analyze_routes:
                    print(f"  {route['methods']} {route['rule']} -> {route['endpoint']}")
                return True
            else:
                print(f"❌ No analyze-contract routes found")
                print(f"Available routes:")
                for route in routes:
                    print(f"  {route['methods']} {route['rule']} -> {route['endpoint']}")
                return False
                
    except Exception as e:
        print(f"❌ Error testing in Flask context: {e}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("Testing analyze-contract route registration...")
    
    success1 = test_blueprint_registration()
    success2 = test_route_in_context()
    
    if success1 and success2:
        print(f"\n🎉 Route registration tests PASSED")
        print("The analyze-contract route should be available when the full app runs")
    else:
        print(f"\n❌ Route registration tests FAILED")
        print("There may be an issue with the route definition")