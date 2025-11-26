"""
Metacrafter Registry Server

A Flask-based web server for serving semantic data types and tools registry.
Supports both HTML and JSON endpoints.
"""
import json
import logging
import os
import collections
from pathlib import Path
from flask import Flask, jsonify, render_template, abort

# Configuration from environment variables with defaults
DEBUG = os.environ.get('REGISTRY_DEBUG', 'False').lower() == 'true'
SECRET_KEY = os.environ.get(
    'REGISTRY_SECRET_KEY',
    os.urandom(32).hex() if hasattr(os, 'urandom') else 'change_this_a_very_unique_secret_key'
)
REGISTRY_HOST = os.environ.get('REGISTRY_HOST', '127.0.0.1')
REGISTRY_PORT = int(os.environ.get('REGISTRY_PORT', '8089'))

# Resolve data paths relative to this file's directory
BASE_DIR = Path(__file__).parent.parent
DATATYPES_DATA_PATH = BASE_DIR / 'data' / 'datatypes_latest.json'
TOOLS_DATA_PATH = BASE_DIR / 'data' / 'tools_latest.json'

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RegistryData:
    """Manages registry data loading and access."""
    
    def __init__(self, datatypes_path, tools_path):
        """Initialize registry data from JSON files.
        
        Args:
            datatypes_path: Path to datatypes JSON file
            tools_path: Path to tools JSON file
            
        Raises:
            FileNotFoundError: If data files cannot be found
            json.JSONDecodeError: If data files contain invalid JSON
        """
        self.datatypes_path = Path(datatypes_path)
        self.tools_path = Path(tools_path)
        self._datatypes = None
        self._tools = None
        self._load_data()
    
    def _load_data(self):
        """Load data from JSON files."""
        try:
            logger.info(f"Loading datatypes from {self.datatypes_path}")
            with open(self.datatypes_path, 'r', encoding='utf-8') as f:
                self._datatypes = collections.OrderedDict(sorted(json.load(f).items()))
            logger.info(f"Loaded {len(self._datatypes)} datatypes")
        except FileNotFoundError:
            logger.error(f"Datatypes file not found: {self.datatypes_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in datatypes file: {e}")
            raise
        
        try:
            logger.info(f"Loading tools from {self.tools_path}")
            with open(self.tools_path, 'r', encoding='utf-8') as f:
                self._tools = collections.OrderedDict(sorted(json.load(f).items()))
            logger.info(f"Loaded {len(self._tools)} tools")
        except FileNotFoundError:
            logger.error(f"Tools file not found: {self.tools_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in tools file: {e}")
            raise
    
    @property
    def datatypes(self):
        """Get datatypes dictionary."""
        return self._datatypes
    
    @property
    def tools(self):
        """Get tools dictionary."""
        return self._tools
    
    def get_datatype(self, slug):
        """Get a datatype by slug.
        
        Args:
            slug: Datatype identifier
            
        Returns:
            Datatype object
            
        Raises:
            KeyError: If datatype not found
        """
        if slug not in self._datatypes:
            raise KeyError(f"Datatype '{slug}' not found")
        return self._datatypes[slug]
    
    def get_tool(self, slug):
        """Get a tool by slug.
        
        Args:
            slug: Tool identifier
            
        Returns:
            Tool object
            
        Raises:
            KeyError: If tool not found
        """
        if slug not in self._tools:
            raise KeyError(f"Tool '{slug}' not found")
        return self._tools[slug]


# Global registry data instance (initialized in create_app)
registry_data = None


def create_app():
    """Create and configure Flask application.
    
    Returns:
        Configured Flask application
    """
    global registry_data
    
    app = Flask("Metacrafter registry", static_url_path='/assets')
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['PROPAGATE_EXCEPTIONS'] = True
    
    # Initialize registry data
    try:
        registry_data = RegistryData(DATATYPES_DATA_PATH, TOOLS_DATA_PATH)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Failed to initialize registry data: {e}")
        raise
    
    # Register routes
    add_views_rules(app)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        logger.error(f"Internal server error: {error}")
        return jsonify({'error': 'Internal server error'}), 500
    
    return app


def root_view():
    """Root view showing list of datatypes."""
    return render_template('datatype_list.tmpl', objects=registry_data.datatypes.values())


def datatype_view(slug):
    """View a single datatype by slug."""
    try:
        obj = registry_data.get_datatype(slug)
        return render_template('datatype.tmpl', object=obj)
    except KeyError:
        abort(404)


def datatype_view_json(slug):
    """Get a single datatype as JSON."""
    try:
        obj = registry_data.get_datatype(slug)
        return jsonify(obj)
    except KeyError:
        abort(404)


def tools_list_view():
    """View showing list of tools."""
    return render_template('tool_list.tmpl', objects=registry_data.tools.values())


def tool_view(slug):
    """View a single tool by slug."""
    try:
        obj = registry_data.get_tool(slug)
        return render_template('tool.tmpl', object=obj)
    except KeyError:
        abort(404)


def tool_view_json(slug):
    """Get a single tool as JSON."""
    try:
        obj = registry_data.get_tool(slug)
        return jsonify(obj)
    except KeyError:
        abort(404)


def registry_view_json():
    """Get all datatypes as JSON."""
    return jsonify(registry_data.datatypes)


def add_views_rules(app):
    """Register all URL rules with the Flask app.
    
    Args:
        app: Flask application instance
    """
    app.add_url_rule('/', 'root', root_view)
    app.add_url_rule('/registry.json', 'registry.json', registry_view_json)
    app.add_url_rule('/datatype/<slug>', 'datatype', datatype_view)
    app.add_url_rule('/datatype/<slug>.json', 'datatype_json', datatype_view_json)
    app.add_url_rule('/tool', 'tools', tools_list_view)
    app.add_url_rule('/tool/<slug>', 'tool', tool_view)
    app.add_url_rule('/tool/<slug>.json', 'tool_json', tool_view_json)


def run_server(host=None, port=None, debug=None):
    """Run the registry server.
    
    Args:
        host: Server host (defaults to REGISTRY_HOST env var or '127.0.0.1')
        port: Server port (defaults to REGISTRY_PORT env var or 8089)
        debug: Enable debug mode (defaults to REGISTRY_DEBUG env var or False)
    """
    host = host or REGISTRY_HOST
    port = port or REGISTRY_PORT
    debug = debug if debug is not None else DEBUG
    
    app = create_app()
    
    logger.info(f"Starting Metacrafter registry server on {host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_server()
