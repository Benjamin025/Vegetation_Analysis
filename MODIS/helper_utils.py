"""
Helper utilities for MODIS Vegetation Analysis
Contains functions for file handling, widgets, and common operations
"""

import os
import time
from pathlib import Path
from typing import Union


def save_uploaded_file(upload_widget) -> str:
    """
    Save file from ipywidgets FileUpload widget
    
    Handles both old and new versions of ipywidgets
    
    Args:
        upload_widget: ipywidgets.FileUpload widget with uploaded file
        
    Returns:
        Path to saved file
        
    Example:
        >>> upload_widget = widgets.FileUpload(accept='.shp,.zip')
        >>> filename = save_uploaded_file(upload_widget)
    """
    if not upload_widget.value:
        raise ValueError("No file uploaded")
    
    # Handle different ipywidgets formats
    if isinstance(upload_widget.value, dict):
        # Newer ipywidgets version (dict format)
        uploaded_file = list(upload_widget.value.values())[0]
        filename = uploaded_file['metadata']['name']
        content = uploaded_file['content']
    else:
        # Older ipywidgets version (tuple format)
        uploaded_file = upload_widget.value[0]
        filename = uploaded_file['name']
        content = uploaded_file['content']
    
    # Save to current directory
    with open(filename, 'wb') as f:
        f.write(content)
    
    return filename


def wait_for_upload(upload_widget, timeout: int = 300) -> bool:
    """
    Wait for file to be uploaded
    
    Args:
        upload_widget: ipywidgets.FileUpload widget
        timeout: Maximum seconds to wait (default: 300)
        
    Returns:
        True if file uploaded, False if timeout
        
    Example:
        >>> upload_widget = widgets.FileUpload()
        >>> if wait_for_upload(upload_widget):
        ...     filename = save_uploaded_file(upload_widget)
    """
    elapsed = 0
    while not upload_widget.value and elapsed < timeout:
        time.sleep(1)
        elapsed += 1
    
    return bool(upload_widget.value)


def create_upload_widget(**kwargs):
    """
    Create a file upload widget with common settings
    
    Args:
        **kwargs: Additional arguments passed to FileUpload
        
    Returns:
        Configured FileUpload widget
        
    Example:
        >>> widget = create_upload_widget()
        >>> display(widget)
    """
    try:
        import ipywidgets as widgets
    except ImportError:
        raise ImportError("ipywidgets not installed. Install with: pip install ipywidgets")
    
    default_kwargs = {
        'accept': '.zip,.geojson,.json,.shp,.dbf,.shx,.prj',
        'multiple': False,
        'description': '📁 Upload AOI'
    }
    default_kwargs.update(kwargs)
    
    return widgets.FileUpload(**default_kwargs)


def format_area(area_km2: float) -> str:
    """
    Format area in km² with appropriate units
    
    Args:
        area_km2: Area in square kilometers
        
    Returns:
        Formatted string with units
        
    Example:
        >>> format_area(1234.56)
        '1,234.56 km²'
        >>> format_area(0.05)
        '5.0 ha'
    """
    if area_km2 < 0.01:
        # Convert to m²
        return f"{area_km2 * 1_000_000:,.1f} m²"
    elif area_km2 < 1:
        # Convert to hectares
        return f"{area_km2 * 100:,.1f} ha"
    else:
        return f"{area_km2:,.2f} km²"


def format_date_range(start_date: str, end_date: str) -> str:
    """
    Format date range for display
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        
    Returns:
        Formatted date range string
        
    Example:
        >>> format_date_range('2024-01-01', '2024-12-31')
        'January 1, 2024 - December 31, 2024'
    """
    from datetime import datetime
    
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    return f"{start.strftime('%B %d, %Y')} - {end.strftime('%B %d, %Y')}"


def get_month_name(month: int, short: bool = False) -> str:
    """
    Get month name from number
    
    Args:
        month: Month number (1-12)
        short: Return short name (3 letters) if True
        
    Returns:
        Month name
        
    Example:
        >>> get_month_name(1)
        'January'
        >>> get_month_name(1, short=True)
        'Jan'
    """
    from datetime import datetime
    
    d = datetime(2024, month, 1)
    return d.strftime('%b' if short else '%B')


def validate_aoi_file(filepath: Union[str, Path]) -> bool:
    """
    Validate that AOI file exists and has correct extension
    
    Args:
        filepath: Path to AOI file
        
    Returns:
        True if valid, raises ValueError if not
        
    Example:
        >>> validate_aoi_file('my_region.shp')
        True
    """
    filepath = Path(filepath)
    
    if not filepath.exists():
        raise ValueError(f"File not found: {filepath}")
    
    valid_extensions = ['.shp', '.geojson', '.json', '.zip']
    if filepath.suffix.lower() not in valid_extensions:
        raise ValueError(
            f"Invalid file type: {filepath.suffix}. "
            f"Supported: {', '.join(valid_extensions)}"
        )
    
    return True


def print_progress_bar(iteration: int, total: int, prefix: str = '', 
                      suffix: str = '', length: int = 50, fill: str = '█'):
    """
    Print a progress bar to console
    
    Args:
        iteration: Current iteration (0 to total)
        total: Total iterations
        prefix: Prefix string
        suffix: Suffix string
        length: Character length of bar
        fill: Bar fill character
        
    Example:
        >>> for i in range(100):
        ...     print_progress_bar(i, 100, prefix='Progress:', suffix='Complete')
    """
    percent = f"{100 * (iteration / float(total)):.1f}"
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end='\r')
    
    if iteration == total:
        print()


def estimate_processing_time(area_km2: float, scale: int = 250) -> str:
    """
    Estimate processing time based on AOI size
    
    Args:
        area_km2: Area in square kilometers
        scale: Analysis scale in meters
        
    Returns:
        Estimated time string
        
    Example:
        >>> estimate_processing_time(5000, scale=250)
        '~20-30 minutes'
    """
    # Rough estimates based on testing
    # These are approximations and will vary
    pixels = (area_km2 * 1_000_000) / (scale * scale)
    
    if pixels < 100_000:
        return "~5-10 minutes"
    elif pixels < 500_000:
        return "~10-20 minutes"
    elif pixels < 1_000_000:
        return "~20-40 minutes"
    elif pixels < 5_000_000:
        return "~40-90 minutes"
    else:
        return "~1.5-3 hours"


def create_color_ramp(values: list, colormap: str = 'RdYlGn') -> list:
    """
    Create color ramp for values
    
    Args:
        values: List of numeric values
        colormap: Matplotlib colormap name
        
    Returns:
        List of hex colors
        
    Example:
        >>> colors = create_color_ramp([0.2, 0.5, 0.8])
        >>> print(colors)
        ['#d7191c', '#ffffbf', '#1a9641']
    """
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    
    cmap = plt.get_cmap(colormap)
    norm = mcolors.Normalize(vmin=min(values), vmax=max(values))
    
    colors = [mcolors.to_hex(cmap(norm(v))) for v in values]
    return colors


# Convenience function for notebook users
def quick_analysis(aoi_path: str, year: int = 2024, 
                   output_dir: str = "modis_outputs") -> Path:
    """
    Run a quick MODIS analysis with default settings
    
    Args:
        aoi_path: Path to AOI file
        year: Analysis year
        output_dir: Output directory
        
    Returns:
        Path to output directory
        
    Example:
        >>> output = quick_analysis("my_region.shp", year=2024)
        >>> print(f"Results: {output}")
    """
    from modis_vegetation_analyzer import MODISVegetationAnalyzer
    
    config = {
        "ee_project": "ee-my-ndungu",
        "output_base_dir": output_dir,
        "year": year,
        "indices": ["NDVI", "EVI"],
        "composite_methods": ["mean"],
        "scale": 250
    }
    
    # Save temporary config
    import json
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config, f)
        config_path = f.name
    
    try:
        analyzer = MODISVegetationAnalyzer(config_path=config_path)
        result = analyzer.run_complete_analysis(aoi_path, year=year)
        return result
    finally:
        # Clean up temp config
        if os.path.exists(config_path):
            os.remove(config_path)


if __name__ == "__main__":
    print("MODIS Vegetation Analysis - Helper Utilities")
    print("=" * 50)
    print("\nAvailable functions:")
    print("  - save_uploaded_file(widget)")
    print("  - wait_for_upload(widget)")
    print("  - create_upload_widget()")
    print("  - format_area(area_km2)")
    print("  - format_date_range(start, end)")
    print("  - validate_aoi_file(path)")
    print("  - quick_analysis(aoi_path, year)")
    print("\nImport in your script:")
    print("  from helper_utils import save_uploaded_file")