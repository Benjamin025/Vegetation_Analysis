"""
MODIS Vegetation Analysis - Production Version
Scalable vegetation monitoring using MODIS data with administrative level analysis

Author: Enhanced from original notebook
Date: 2024
"""

import ee
import json
import datetime
import geemap
import pandas as pd
import geopandas as gpd
import os
import time
import zipfile
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap, BoundaryNorm
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
warnings.filterwarnings('ignore')


class MODISVegetationAnalyzer:
    """
    Production-ready MODIS vegetation analysis with administrative level support
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the analyzer with configuration
        
        Args:
            config_path: Path to configuration JSON file
        """
        self.config = self._load_config(config_path)
        self.logger = self._setup_logger()
        self.aoi = None
        self.aoi_gdf = None
        
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load configuration from file or use defaults"""
        default_config = {
            "ee_project": "ee-my-ndungu",
            "output_base_dir": "modis_outputs",
            "year": datetime.datetime.now().year,
            "indices": ["NDVI", "EVI", "VCI"],
            "composite_methods": ["mean", "min", "max"],
            "modis_collection": "MODIS/061/MOD13Q1",
            "scale": 250,
            "max_workers": 4,
            "visualizations": {
                "NDVI": {"min": 0, "max": 1, "palette": ["red", "yellow", "green"]},
                "EVI": {"min": 0, "max": 1, "palette": ["brown", "yellow", "darkgreen"]},
                "VCI": {"min": 0, "max": 100, "palette": ["red", "orange", "yellow", "lightgreen", "darkgreen"]}
            }
        }
        
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logging configuration"""
        log_dir = Path(self.config["output_base_dir"]) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logger = logging.getLogger("MODISAnalyzer")
        logger.setLevel(logging.INFO)
        
        # File handler
        fh = logging.FileHandler(
            log_dir / f"analysis_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        fh.setLevel(logging.INFO)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
        
        return logger
    
    def initialize_ee(self):
        """Initialize Earth Engine with authentication"""
        try:
            ee.Initialize(project=self.config["ee_project"])
            self.logger.info(f"✅ Earth Engine initialized with project: {self.config['ee_project']}")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Earth Engine: {e}")
            self.logger.info("Attempting authentication...")
            ee.Authenticate()
            ee.Initialize(project=self.config["ee_project"])
            self.logger.info("✅ Earth Engine authenticated and initialized")
    
    def load_aoi(self, filepath: str):
        """
        Load Area of Interest from file
        
        Args:
            filepath: Path to shapefile, GeoJSON, or ZIP file
        """
        self.logger.info(f"📂 Loading AOI from: {filepath}")
        
        try:
            # Load the file
            ext = os.path.splitext(filepath)[1].lower()
            
            if ext == ".zip":
                extract_dir = Path(self.config["output_base_dir"]) / "temp_aoi"
                extract_dir.mkdir(parents=True, exist_ok=True)
                
                with zipfile.ZipFile(filepath, "r") as zip_ref:
                    zip_ref.extractall(extract_dir)
                
                shp_files = list(extract_dir.glob("*.shp"))
                if not shp_files:
                    raise ValueError("No shapefile found in ZIP")
                
                self.aoi_gdf = gpd.read_file(shp_files[0])
            else:
                self.aoi_gdf = gpd.read_file(filepath)
            
            # Convert to EPSG:4326 if needed
            if self.aoi_gdf.crs and self.aoi_gdf.crs.to_epsg() != 4326:
                self.aoi_gdf = self.aoi_gdf.to_crs("EPSG:4326")
            
            # Convert to Earth Engine geometry
            self.aoi = geemap.geopandas_to_ee(self.aoi_gdf)
            
            self.logger.info(f"✅ AOI loaded successfully with {len(self.aoi_gdf)} features")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load AOI: {e}")
            raise
    
    def create_output_structure(self) -> Path:
        """
        Create organized output directory structure
        
        Returns:
            Base output directory path
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        base_dir = Path(self.config["output_base_dir"]) / f"analysis_{timestamp}"
        
        # Create directory structure
        dirs = [
            base_dir,
            base_dir / "composites",
            base_dir / "trends",
            base_dir / "statistics",
            base_dir / "maps",
            base_dir / "exports",
            base_dir / "metadata"
        ]
        
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        self.output_dir = base_dir
        self.logger.info(f"📁 Output structure created at: {base_dir}")
        
        # Save configuration
        with open(base_dir / "metadata" / "config.json", 'w') as f:
            json.dump(self.config, f, indent=2)
        
        return base_dir
    
    def get_modis_data(self, start_date: str, end_date: str) -> ee.ImageCollection:
        """
        Fetch MODIS vegetation data with proper scaling
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Earth Engine ImageCollection with scaled NDVI and EVI
        """
        self.logger.info(f"📡 Fetching MODIS data from {start_date} to {end_date}")
        
        # Fetch raw MODIS data
        raw_collection = (ee.ImageCollection(self.config["modis_collection"])
                         .filterBounds(self.aoi)
                         .filterDate(start_date, end_date))
        
        count = raw_collection.size().getInfo()
        self.logger.info(f"   Found {count} MODIS images")
        
        if count == 0:
            self.logger.warning("⚠️  No MODIS data found for this date range!")
            return raw_collection
        
        def scale_modis_image(image):
            """
            Scale MODIS NDVI and EVI from integer to float
            MODIS stores as integers (-2000 to 10000)
            Must multiply by 0.0001 to get actual values (-0.2 to 1.0)
            """
            # Get original bands
            original_ndvi = image.select('NDVI')
            original_evi = image.select('EVI')
            
            # Scale to proper range
            scaled_ndvi = original_ndvi.multiply(0.0001).rename('NDVI')
            scaled_evi = original_evi.multiply(0.0001).rename('EVI')
            
            # Create new image with scaled bands
            # Keep other properties/metadata
            return image.select([]).addBands([scaled_ndvi, scaled_evi]).copyProperties(image, image.propertyNames())
        
        # Apply scaling to entire collection
        scaled_collection = raw_collection.map(scale_modis_image)
        
        self.logger.info("   ✅ Applied scaling factor (×0.0001) to NDVI and EVI")
        
        return scaled_collection
    
    def calculate_vci(self, collection: ee.ImageCollection, 
                     historical_start: str, historical_end: str) -> ee.ImageCollection:
        """
        Calculate Vegetation Condition Index (VCI)
        VCI shows current vegetation condition relative to historical range
        
        Args:
            collection: MODIS ImageCollection (must already be scaled!)
            historical_start: Start of historical baseline period
            historical_end: End of historical baseline period
            
        Returns:
            ImageCollection with VCI band added
        """
        self.logger.info(f"🧮 Calculating VCI using historical baseline")
        self.logger.info(f"   Historical period: {historical_start} to {historical_end}")
        
        # Get historical MODIS data and scale it
        historical_raw = (ee.ImageCollection(self.config["modis_collection"])
                         .filterBounds(self.aoi)
                         .filterDate(historical_start, historical_end))
        
        hist_count = historical_raw.size().getInfo()
        self.logger.info(f"   Found {hist_count} historical images")
        
        def scale_ndvi(image):
            """Scale historical NDVI"""
            scaled = image.select('NDVI').multiply(0.0001).rename('NDVI')
            return image.select([]).addBands(scaled).copyProperties(image, image.propertyNames())
        
        historical = historical_raw.map(scale_ndvi)
        
        # Calculate historical min and max (for VCI baseline)
        ndvi_min = historical.select('NDVI').min()
        ndvi_max = historical.select('NDVI').max()
        
        self.logger.info("   ✅ Historical baseline calculated")
        
        def compute_vci(image):
            """
            Compute VCI for one image
            VCI = (NDVI - NDVI_min) / (NDVI_max - NDVI_min) × 100
            """
            # Get the NDVI band (already scaled from get_modis_data)
            ndvi = image.select('NDVI')
            
            # Calculate VCI
            vci = (ndvi.subtract(ndvi_min)
                      .divide(ndvi_max.subtract(ndvi_min))
                      .multiply(100)
                      .clamp(0, 100)  # Ensure 0-100 range
                      .rename('VCI'))
            
            # Add VCI band to existing image
            return image.addBands(vci)
        
        # Apply VCI calculation to all images
        collection_with_vci = collection.map(compute_vci)
        
        self.logger.info("   ✅ VCI calculated and added to collection")
        
        return collection_with_vci
    
    def create_monthly_composites(self, collection: ee.ImageCollection, 
                                 year: int) -> Dict:
        """
        Create monthly composites for all indices and methods
        
        Args:
            collection: MODIS ImageCollection with indices
            year: Year for analysis
            
        Returns:
            Dictionary of composite images
        """
        composites = {}
        
        for month in range(1, 13):
            month_start = f"{year}-{month:02d}-01"
            
            # Calculate end of month
            if month == 12:
                month_end = f"{year}-{month:02d}-31"
            else:
                next_month = datetime.datetime(year, month, 1) + datetime.timedelta(days=32)
                month_end = f"{year}-{month:02d}-{(next_month.replace(day=1) - datetime.timedelta(days=1)).day}"
            
            month_collection = collection.filterDate(month_start, month_end)
            
            for index in self.config["indices"]:
                for method in self.config["composite_methods"]:
                    key = f"{index}_{method}_{year}_{month:02d}"
                    
                    if method == "mean":
                        composite = month_collection.select(index).mean()
                    elif method == "min":
                        composite = month_collection.select(index).min()
                    elif method == "max":
                        composite = month_collection.select(index).max()
                    
                    composites[key] = composite.clip(self.aoi)
        
        self.logger.info(f"✅ Created {len(composites)} monthly composites")
        return composites
    
    def export_composite_images(self, composites: Dict, save_locally: bool = True):
        """
        Export composite images as visualizations
        
        Args:
            composites: Dictionary of composite images
            save_locally: Whether to save images locally
        """
        self.logger.info("🖼️  Exporting composite visualizations...")
        
        composite_dir = self.output_dir / "composites"
        
        for key, composite in composites.items():
            try:
                parts = key.split('_')
                index = parts[0]
                method = parts[1]
                
                vis_params = self.config["visualizations"].get(index, {})
                
                # Get thumbnail URL
                url = composite.getThumbURL({
                    'dimensions': 1024,
                    'region': self.aoi.geometry(),
                    'format': 'png',
                    **vis_params
                })
                
                if save_locally:
                    filename = composite_dir / f"{key}.png"
                    self._download_image(url, filename)
                    
            except Exception as e:
                self.logger.warning(f"⚠️  Failed to export {key}: {e}")
        
        self.logger.info("✅ Composite export complete")
    
    def _download_image(self, url: str, filepath: Path):
        """Download image from URL"""
        import urllib.request
        try:
            urllib.request.urlretrieve(url, filepath)
        except Exception as e:
            self.logger.warning(f"Failed to download {filepath.name}: {e}")
    
    def debug_collection_values(self, collection: ee.ImageCollection, name: str = "Collection"):
        """
        Debug helper to check actual values in the collection
        
        Args:
            collection: Collection to check
            name: Name for logging
        """
        self.logger.info(f"🐛 DEBUG: Checking {name}")
        
        try:
            # Get first image
            first = collection.first()
            
            # Get a sample point from AOI center
            centroid = self.aoi.geometry().centroid()
            
            # Check each band
            for band in ['NDVI', 'EVI', 'VCI']:
                try:
                    stats = first.select(band).reduceRegion(
                        reducer=ee.Reducer.mean(),
                        geometry=centroid,
                        scale=self.config["scale"]
                    ).getInfo()
                    
                    value = stats.get(band)
                    self.logger.info(f"  {band}: {value}")
                    
                except Exception as e:
                    self.logger.debug(f"  {band}: not available ({e})")
                    
        except Exception as e:
            self.logger.error(f"  Debug failed: {e}")
    
    def calculate_statistics(self, collection: ee.ImageCollection, 
                            year: int) -> pd.DataFrame:
        """
        Calculate monthly statistics for all indices
        
        Args:
            collection: MODIS ImageCollection
            year: Year for analysis
            
        Returns:
            DataFrame with monthly statistics
        """
        self.logger.info("📊 Calculating monthly statistics...")
        
        stats_list = []
        
        for month in range(1, 13):
            month_start = f"{year}-{month:02d}-01"
            
            if month == 12:
                month_end = f"{year}-{month:02d}-31"
            else:
                next_month = datetime.datetime(year, month, 1) + datetime.timedelta(days=32)
                month_end = f"{year}-{month:02d}-{(next_month.replace(day=1) - datetime.timedelta(days=1)).day}"
            
            month_collection = collection.filterDate(month_start, month_end)
            
            # Check if we have data for this month
            month_count = month_collection.size().getInfo()
            if month_count == 0:
                self.logger.warning(f"⚠️  No data for month {month}")
                continue
            
            month_stats = {"Year": year, "Month": month}
            
            for index in self.config["indices"]:
                try:
                    mean_img = month_collection.select(index).mean()
                    
                    stats = mean_img.reduceRegion(
                        reducer=ee.Reducer.mean().combine(
                            ee.Reducer.stdDev(), '', True
                        ).combine(
                            ee.Reducer.min(), '', True
                        ).combine(
                            ee.Reducer.max(), '', True
                        ),
                        geometry=self.aoi.geometry(),
                        scale=self.config["scale"],
                        maxPixels=1e9
                    ).getInfo()
                    
                    # Extract values and validate
                    mean_val = stats.get(f"{index}_mean")
                    stddev_val = stats.get(f"{index}_stdDev")
                    min_val = stats.get(f"{index}_min")
                    max_val = stats.get(f"{index}_max")
                    
                    # Validate NDVI and EVI are in expected range
                    if index in ['NDVI', 'EVI']:
                        if mean_val is not None:
                            if mean_val < -1 or mean_val > 1:
                                self.logger.warning(
                                    f"⚠️  {index} value out of range for month {month}: {mean_val:.4f}"
                                )
                    
                    # Validate VCI is in 0-100 range
                    if index == 'VCI':
                        if mean_val is not None:
                            if mean_val < 0 or mean_val > 100:
                                self.logger.warning(
                                    f"⚠️  VCI value out of range for month {month}: {mean_val:.2f}"
                                )
                    
                    month_stats[f"{index}_mean"] = mean_val
                    month_stats[f"{index}_stdDev"] = stddev_val
                    month_stats[f"{index}_min"] = min_val
                    month_stats[f"{index}_max"] = max_val
                    
                except Exception as e:
                    self.logger.warning(f"⚠️  Failed to calculate stats for {index} in month {month}: {e}")
            
            stats_list.append(month_stats)
        
        df = pd.DataFrame(stats_list)
        
        # Save statistics
        stats_file = self.output_dir / "statistics" / f"monthly_summary_{year}.csv"
        df.to_csv(stats_file, index=False)
        self.logger.info(f"✅ Statistics saved to {stats_file}")
        
        # Log summary for validation
        self.logger.info("\n📈 Statistics Summary:")
        for index in self.config["indices"]:
            mean_col = f"{index}_mean"
            if mean_col in df.columns:
                mean_val = df[mean_col].mean()
                min_val = df[mean_col].min()
                max_val = df[mean_col].max()
                self.logger.info(
                    f"   {index}: mean={mean_val:.4f}, min={min_val:.4f}, max={max_val:.4f}"
                )
        
        return df
    
    def create_trend_plots(self, stats_df: pd.DataFrame, year: int):
        """
        Create trend line plots for vegetation indices
        
        Args:
            stats_df: DataFrame with monthly statistics
            year: Year for analysis
        """
        self.logger.info("📈 Creating trend plots...")
        
        trends_dir = self.output_dir / "trends"
        
        for index in self.config["indices"]:
            mean_col = f"{index}_mean"
            
            if mean_col not in stats_df.columns:
                continue
            
            try:
                fig, ax = plt.subplots(figsize=(12, 6))
                
                months = stats_df['Month']
                values = stats_df[mean_col]
                
                ax.plot(months, values, marker='o', linewidth=2, 
                       markersize=8, color='steelblue', label=f'{index} Mean')
                
                # Add confidence interval if stdDev available
                stddev_col = f"{index}_stdDev"
                if stddev_col in stats_df.columns:
                    std = stats_df[stddev_col]
                    ax.fill_between(months, values - std, values + std, 
                                   alpha=0.2, color='steelblue')
                
                ax.set_xlabel('Month', fontsize=12)
                ax.set_ylabel(f'{index} Value', fontsize=12)
                ax.set_title(f'{index} Monthly Trend ({year})', 
                           fontsize=14, fontweight='bold')
                ax.set_xticks(range(1, 13))
                ax.set_xticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
                ax.grid(True, alpha=0.3)
                ax.legend()
                
                plt.tight_layout()
                plt.savefig(trends_dir / f"{index}_trend_{year}.png", 
                           dpi=300, bbox_inches='tight')
                plt.close()
                
            except Exception as e:
                self.logger.warning(f"Failed to create trend plot for {index}: {e}")
        
        self.logger.info("✅ Trend plots created")
    
    def generate_metadata(self):
        """Generate comprehensive metadata file"""
        metadata = {
            "analysis_timestamp": datetime.datetime.now().isoformat(),
            "configuration": self.config,
            "aoi_info": {
                "feature_count": len(self.aoi_gdf) if self.aoi_gdf is not None else 0,
                "crs": str(self.aoi_gdf.crs) if self.aoi_gdf is not None else None,
                "bounds": self.aoi_gdf.total_bounds.tolist() if self.aoi_gdf is not None else None,
                "area_km2": self.aoi_gdf.to_crs(epsg=3857).area.sum() / 1e6 if self.aoi_gdf is not None else None
            },
            "output_directory": str(self.output_dir)
        }
        
        metadata_file = self.output_dir / "metadata" / "analysis_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        self.logger.info(f"📄 Metadata saved to {metadata_file}")
    
    def run_complete_analysis(self, aoi_path: str, year: Optional[int] = None):
        """
        Run complete analysis pipeline
        
        Args:
            aoi_path: Path to AOI file
            year: Year for analysis (default: current year - 1)
        """
        if year is None:
            year = self.config["year"]
        
        self.logger.info(f"🚀 Starting complete MODIS analysis for {year}")
        
        # Initialize
        self.initialize_ee()
        
        # Load AOI
        self.load_aoi(aoi_path)
        
        # Create output structure
        self.create_output_structure()
        
        # Define date ranges
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        historical_start = f"{year-10}-01-01"
        historical_end = f"{year-1}-12-31"
        
        # Get MODIS data
        collection = self.get_modis_data(start_date, end_date)
        self.debug_collection_values(collection, "After get_modis_data (should be scaled)")
        
        # Calculate VCI
        collection = self.calculate_vci(collection, historical_start, historical_end)
        self.debug_collection_values(collection, "After calculate_vci (should have VCI band)")
        
        # Create monthly composites
        composites = self.create_monthly_composites(collection, year)
        
        # Export composite images
        self.export_composite_images(composites)
        
        # Calculate statistics
        stats_df = self.calculate_statistics(collection, year)
        
        # Create trend plots
        self.create_trend_plots(stats_df, year)
        
        # Generate metadata
        self.generate_metadata()
        
        self.logger.info(f"✅ Analysis complete! Results saved to: {self.output_dir}")
        
        return self.output_dir


def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="MODIS Vegetation Analysis - Production Version"
    )
    parser.add_argument(
        "--aoi", 
        required=True,
        help="Path to AOI file (shapefile, GeoJSON, or ZIP)"
    )
    parser.add_argument(
        "--config",
        help="Path to configuration JSON file"
    )
    parser.add_argument(
        "--year",
        type=int,
        help="Year for analysis (default: previous year)"
    )
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = MODISVegetationAnalyzer(config_path=args.config)
    
    # Run analysis
    output_dir = analyzer.run_complete_analysis(
        aoi_path=args.aoi,
        year=args.year
    )
    
    print(f"\n{'='*60}")
    print(f"Analysis Complete!")
    print(f"Results location: {output_dir}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()