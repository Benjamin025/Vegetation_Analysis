# MODIS Vegetation Analysis - Production Version

A scalable, production-ready system for analyzing MODIS vegetation indices with administrative level breakdowns and comprehensive reporting.

## Features

✨ **Key Capabilities:**

- 🌍 **Multi-scale Analysis:** Analyze vegetation at country, province, and district levels
- 📊 **Multiple Indices:** NDVI, EVI, and VCI (Vegetation Condition Index)
- 📈 **Temporal Analysis:** Monthly composites and trend analysis
- 🗺️ **Administrative Breakdown:** Automatic analysis by administrative boundaries
- 📁 **Organized Outputs:** Well-structured output directories
- 📘 **Automated Reports:** PDF and Markdown report generation
- 🔧 **Configurable:** JSON-based configuration system
- 🚀 **Scalable:** Handles large AOIs efficiently

## Installation

### Prerequisites

- Python 3.8 or higher
- Google Earth Engine account
- pip or conda package manager

### Setup

1. **Clone or download the repository**

```bash
git clone <repository-url>
cd modis-vegetation-analysis
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Authenticate with Google Earth Engine**

```bash
earthengine authenticate
```

Follow the authentication flow in your browser.

## Quick Start

### Basic Usage

```bash
python modis_vegetation_analyzer.py --aoi path/to/your/shapefile.shp --year 2024
```

### With Custom Configuration

```bash
python modis_vegetation_analyzer.py \
    --aoi path/to/your/shapefile.shp \
    --config config_template.json \
    --year 2024
```

## Configuration

The system uses a JSON configuration file for customization. Copy `config_template.json` and modify as needed:

```json
{
  "ee_project": "your-ee-project-id",
  "output_base_dir": "modis_outputs",
  "year": 2024,
  "indices": ["NDVI", "EVI", "VCI"],
  "composite_methods": ["mean", "min", "max"],
  "scale": 250,
  "admin_levels": ["ADM0", "ADM1", "ADM2"],
  "admin_name_fields": {
    "ADM0": "admin0Name",
    "ADM1": "admin1Name",
    "ADM2": "admin2Name"
  }
}
```

### Configuration Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `ee_project` | Google Earth Engine project ID | Required |
| `output_base_dir` | Base directory for outputs | "modis_outputs" |
| `year` | Analysis year | Current year |
| `indices` | Vegetation indices to calculate | ["NDVI", "EVI", "VCI"] |
| `composite_methods` | Composite methods | ["mean", "min", "max"] |
| `scale` | Analysis scale in meters | 250 |
| `admin_levels` | Administrative levels to analyze | ["ADM0", "ADM1", "ADM2"] |
| `max_workers` | Parallel processing workers | 4 |

## Input Requirements

### Area of Interest (AOI)

The system accepts the following formats:

- **Shapefile** (`.shp` with associated files)
- **GeoJSON** (`.geojson` or `.json`)
- **Zipped Shapefile** (`.zip` containing shapefile components)

## Advanced Usage

## Output Interpretation

### Vegetation Indices

#### NDVI (Normalized Difference Vegetation Index)
- **Range:** -1 to 1
- **Interpretation:**
  - < 0: Water, snow, clouds
  - 0 - 0.2: Bare soil, rocks
  - 0.2 - 0.4: Sparse vegetation
  - 0.4 - 0.6: Moderate vegetation
  - 0.6 - 0.8: Dense vegetation
  - > 0.8: Very dense vegetation

#### EVI (Enhanced Vegetation Index)
- **Range:** -1 to 1
- **Advantages:** Better performance in high biomass areas, reduced atmospheric and soil effects

#### VCI (Vegetation Condition Index)
- **Range:** 0 - 100
- **Interpretation:**
  - 0 - 10: Extreme drought
  - 10 - 20: Severe drought
  - 20 - 35: Moderate drought
  - 35 - 50: Below normal
  - 50 - 65: Normal
  - > 65: Above normal

## Troubleshooting

### Common Issues

#### 1. Earth Engine Authentication

```bash
# If you encounter authentication errors
earthengine authenticate
```

#### 2. Memory Issues with Large AOIs

Reduce the `scale` parameter in config:
```json
{
  "scale": 500  // Increase from 250 to reduce memory usage
}
```

#### 4. Slow Processing

- Reduce the number of indices analyzed
- Increase `max_workers` in config
- Use a smaller AOI for testing
- Increase the `scale` parameter

## Data Sources

- **MODIS Collection:** MOD13Q1.061
- **Provider:** NASA LP DAAC
- **Spatial Resolution:** 250m
- **Temporal Resolution:** 16-day composite
- **Bands:** NDVI, EVI, Quality flags

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

[Your License Here]

## Citation

If you use this tool in your research, please cite:

```
[Karanja Benjamin Vegetation Monitoring V1.0.0]
```

## Contact

For questions and support:
- Email: [ndungubenjamin025@gmail.com]
- Issues: [[repository-issues-url](https://github.com/Benjamin025/Vegetation_Analysis/issues)]

## Acknowledgments

- NASA LP DAAC for MODIS data
- Google Earth Engine for computing platform
- geemap for Python-Earth Engine integration

## Version History

### v2.0.0 (2024)
- Production-ready refactor
- Administrative level analysis
- Comprehensive reporting
- Improved error handling
- Configuration system
- Parallel processing support

### v1.0.0 (2024)
- Initial notebook version
- Basic MODIS analysis
- Simple visualization

---

**Built with ❤️ for vegetation monitoring and environmental analysis**