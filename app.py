import sys
try:
    from flask import Flask, request, jsonify
except ModuleNotFoundError:
    print("Error: Flask is not installed.\nInstall dependencies with: python -m pip install -r requirements.txt")
    sys.exit(1)

import math
import traceback
import re

# Try to import flask_cors (optional)
try:
    from flask_cors import CORS
    _CORS_AVAILABLE = True
except Exception:
    CORS = None
    _CORS_AVAILABLE = False

app = Flask(__name__)

# Enable CORS if available
if _CORS_AVAILABLE:
    CORS(app, resources={r"/api/*": {"origins": "*"}})
else:
    print("Warning: flask-cors is not installed. "
          "Browser requests from other origins may be blocked.")

# ---------------------------------------------------
# Custom math functions
# ---------------------------------------------------
def factorial(n):
    """Custom factorial function"""
    if not isinstance(n, int) or n < 0:
        raise ValueError("Factorial only for non-negative integers")
    return math.factorial(n)

def modulus(a, b):
    """Modulus function for % operator"""
    return a % b

def percentage(x):
    """Convert percentage to decimal"""
    return x / 100.0

# ---------------------------------------------------
# Allowed functions for safe evaluation
# ---------------------------------------------------
SAFE_ENV = {
    # Basic operations
    "abs": abs,
    "round": round,
    
    # Trigonometric functions (in radians)
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    
    # Hyperbolic functions
    "sinh": math.sinh,
    "cosh": math.cosh,
    "tanh": math.tanh,
    
    # Exponential and logarithmic functions
    "exp": math.exp,
    "log": math.log10,  # log base 10
    "ln": math.log,     # natural log
    "log2": math.log2,
    
    # Power and root functions
    "sqrt": math.sqrt,
    "pow": math.pow,
    "cbrt": lambda x: x ** (1/3) if x >= 0 else -((-x) ** (1/3)),
    
    # Special functions
    "factorial": factorial,
    
    # Constants
    "pi": math.pi,
    "e": math.e,
    "inf": math.inf,
    
    # Math utility functions
    "ceil": math.ceil,
    "floor": math.floor,
    "trunc": math.trunc,
    "degrees": math.degrees,
    "radians": math.radians,
    
    # Custom functions
    "mod": modulus,
    "percent": percentage,
    
    "__builtins__": {}  # block unsafe operations
}

# ---------------------------------------------------
# Expression preprocessing
# ---------------------------------------------------
def preprocess_expression(expr: str) -> str:
    """Preprocess expression to handle various formats and conversions"""
    if not expr:
        return ""
    
    # Remove any whitespace
    expr = expr.strip()
    
    # Handle implied multiplication: 2(3) -> 2*(3), (2)(3) -> (2)*(3)
    expr = re.sub(r'(\d)(\()', r'\1*\2', expr)
    expr = re.sub(r'(\))(\()', r'\1*\2', expr)
    expr = re.sub(r'(\))(\d)', r'\1*\2', expr)
    expr = re.sub(r'(pi)(\d)', r'\1*\2', expr)
    expr = re.sub(r'(e)(\d)', r'\1*\2', expr)
    
    # Handle percentage: 50% -> percent(50)
    expr = re.sub(r'(\d+(?:\.\d+)?)%', r'percent(\1)', expr)
    
    # Replace ^ with ** for exponentiation
    expr = expr.replace('^', '**')
    
    # Handle modulus: 10%3 -> mod(10, 3)
    # This is complex because % is used for both percentage and modulus
    # We'll handle modulus separately after percentage conversion
    
    # Handle factorial: 5! -> factorial(5)
    expr = re.sub(r'(\d+)!', r'factorial(\1)', expr)
    
    # Handle implied multiplication with constants: 2pi -> 2*pi
    expr = re.sub(r'(\d)(pi)', r'\1*\2', expr)
    expr = re.sub(r'(\d)(e)', r'\1*\2', expr)
    
    # Handle negative numbers and subtraction properly
    expr = re.sub(r'(\d|\))\s*-\s*(\d|\()', r'\1-\2', expr)
    
    return expr

def validate_expression(expr: str) -> tuple:
    """Validate expression before evaluation"""
    if not expr:
        return False, "Empty expression"
    
    # Check for division by zero patterns
    if re.search(r'/0(?!\.\d)', expr) or re.search(r'/\([^)]*0[^)]*\)', expr):
        return False, "Division by zero"
    
    # Check for invalid factorial usage
    if re.search(r'factorial\(-?\d*\.\d+\)', expr):
        return False, "Factorial requires integer"
    
    # Check for valid characters (basic safety)
    valid_chars = r'^[0-9+\-*/().\s^!%a-zA-Z_,]+$'
    if not re.match(valid_chars, expr):
        return False, "Invalid characters in expression"
    
    # Check for balanced parentheses
    stack = []
    for char in expr:
        if char == '(':
            stack.append(char)
        elif char == ')':
            if not stack:
                return False, "Unbalanced parentheses"
            stack.pop()
    
    if stack:
        return False, "Unbalanced parentheses"
    
    return True, ""

# ---------------------------------------------------
# Safe expression evaluation
# ---------------------------------------------------
def safe_eval(expr: str):
    """Safely evaluate mathematical expression"""
    try:
        # Preprocess expression
        processed_expr = preprocess_expression(expr)
        
        # Validate expression
        is_valid, error_msg = validate_expression(processed_expr)
        if not is_valid:
            raise ValueError(error_msg)
        
        # Special handling for modulus before eval
        # We need to handle a % b pattern after percentage conversion
        processed_expr = re.sub(r'(\d+(?:\.\d+)?)%(\d+(?:\.\d+)?)', r'mod(\1, \2)', processed_expr)
        
        # Evaluate expression
        result = eval(processed_expr, SAFE_ENV, {})
        
        # Handle special cases
        if isinstance(result, float):
            # Remove floating point errors for small numbers
            if abs(result) < 1e-10:
                result = 0.0
            # Format to avoid scientific notation for large numbers
            if abs(result) > 1e10 or (abs(result) < 1e-4 and result != 0):
                return result  # Return as-is for scientific notation
            # Round to avoid floating point precision issues
            result = round(result, 10)
        
        return result
        
    except ZeroDivisionError:
        raise ValueError("Division by zero")
    except ValueError as ve:
        raise ve  # Re-raise validation errors
    except Exception as e:
        # Provide more helpful error messages
        error_msg = str(e).lower()
        if "factorial" in error_msg:
            raise ValueError("Factorial requires non-negative integer")
        elif "math domain" in error_msg:
            raise ValueError("Math domain error (e.g., sqrt of negative)")
        elif "invalid literal" in error_msg:
            raise ValueError("Invalid number format")
        elif "name" in error_msg and "is not defined" in error_msg:
            # Extract the undefined name from error message
            match = re.search(r"'([^']+)' is not defined", error_msg)
            if match:
                raise ValueError(f"Undefined function or variable: {match.group(1)}")
            else:
                raise ValueError("Invalid expression syntax")
        else:
            raise ValueError("Invalid expression")

@app.route("/")
def home():
    return jsonify({
        "message": "Smart Calculator Backend Running!",
        "version": "2.0",
        "endpoints": {
            "/api/evaluate": "POST - Evaluate expression",
            "/api/functions": "GET - List available functions"
        }
    })

# ---------------------------------------------------
# /api/evaluate  → evaluate expression
# ---------------------------------------------------
@app.route("/api/evaluate", methods=["POST"])
def evaluate():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        if "expression" not in data:
            return jsonify({"error": "Expression missing"}), 400

        expr = data["expression"].strip()
        
        if not expr:
            return jsonify({"error": "Empty expression"}), 400
        
        result = safe_eval(expr)
        
        # Format result
        if isinstance(result, float):
            # Check if it's an integer represented as float (e.g., 2.0)
            if result.is_integer():
                result = int(result)
        
        return jsonify({
            "expression": expr,
            "result": result,
            "success": True
        })

    except ValueError as ve:
        return jsonify({
            "error": str(ve),
            "success": False
        }), 400
        
    except Exception as e:
        # Don't expose traceback in production
        app.logger.error(f"Evaluation error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            "error": "Internal server error",
            "success": False
        }), 500

# ---------------------------------------------------
# /api/functions  → list available functions
# ---------------------------------------------------
@app.route("/api/functions", methods=["GET"])
def list_functions():
    """Return list of available mathematical functions"""
    functions = {
        "basic_operations": ["+", "-", "*", "/", "^", "%", "!"],
        "trigonometric": ["sin", "cos", "tan", "asin", "acos", "atan"],
        "hyperbolic": ["sinh", "cosh", "tanh"],
        "logarithmic": ["log", "ln", "log2", "exp"],
        "roots_powers": ["sqrt", "cbrt", "pow"],
        "rounding": ["ceil", "floor", "trunc", "round"],
        "special": ["abs", "factorial", "mod"],
        "constants": ["pi", "e", "inf"],
        "conversion": ["degrees", "radians", "percent"]
    }
    
    return jsonify({
        "functions": functions,
        "message": "Available mathematical functions"
    })

# ---------------------------------------------------
# /api/clear-history  → does not store anything in backend,
# but provided for frontend integration
# ---------------------------------------------------
@app.route("/api/clear-history", methods=["POST"])
def clear_history():
    return jsonify({
        "message": "History cleared (frontend only)",
        "success": True
    }), 200

# ---------------------------------------------------
# /api/health  → health check endpoint
# ---------------------------------------------------
@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "Smart Calculator Backend",
        "timestamp": datetime.datetime.now().isoformat()
    }), 200

# ---------------------------------------------------
# Error handlers
# ---------------------------------------------------
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "available_endpoints": ["/api/evaluate", "/api/functions", "/api/health"]
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "error": "Method not allowed"
    }), 405

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"Internal server error: {error}")
    return jsonify({
        "error": "Internal server error"
    }), 500

# ---------------------------------------------------
# Import datetime for health check
# ---------------------------------------------------
import datetime

# ---------------------------------------------------
# Server start
# ---------------------------------------------------
if __name__ == "__main__":
    print("=" * 50)
    print("Smart Calculator Backend v2.0")
    print("=" * 50)
    print(f"Server starting on: http://localhost:5000")
    print(f"API endpoints:")
    print(f"  POST /api/evaluate  - Evaluate expressions")
    print(f"  GET  /api/functions - List available functions")
    print(f"  GET  /api/health    - Health check")
    print(f"  POST /api/clear-history - Clear history (frontend)")
    print("=" * 50)
    
    app.run(host="0.0.0.0", port=5000, debug=True)