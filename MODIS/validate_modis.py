"""
MODIS Data Validation Script
Checks if MODIS data is properly scaled and within expected ranges
"""

import ee
import pandas as pd
from pathlib import Path


def validate_modis_scaling():
    """
    Test MODIS data scaling with a small sample
    """
    print("🔍 MODIS Data Scaling Validation")
    print("=" * 60)
    
    try:
        # Initialize Earth Engine
        try:
            ee.Initialize()
        except:
            print("⚠️  Earth Engine not initialized. Authenticating...")
            ee.Authenticate()
            ee.Initialize()
        
        print("✅ Earth Engine initialized\n")
        
        # Test point (somewhere in Kenya)
        test_point = ee.Geometry.Point([36.8219, -1.2921])
        
        # Get a single MODIS image
        print("📡 Fetching test MODIS image...")
        image = (ee.ImageCollection('MODIS/061/MOD13Q1')
                .filterBounds(test_point)
                .filterDate('2024-01-01', '2024-01-31')
                .first())
        
        if image is None:
            print("❌ No MODIS data found for test period")
            return False
        
        # Test 1: Raw values (unscaled)
        print("\n--- Test 1: Raw MODIS Values ---")
        raw_ndvi = image.select('NDVI')
        raw_stats = raw_ndvi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=test_point,
            scale=250
        ).getInfo()
        
        raw_value = raw_stats.get('NDVI')
        print(f"Raw NDVI value: {raw_value}")
        print(f"Expected range: -2000 to 10000 (integer)")
        
        if raw_value is None:
            print("❌ No data at test point")
            return False
        
        if raw_value < -2000 or raw_value > 10000:
            print("⚠️  Raw value outside expected range!")
        else:
            print("✅ Raw value in expected range")
        
        # Test 2: Scaled values
        print("\n--- Test 2: Scaled MODIS Values ---")
        scaled_ndvi = image.select('NDVI').multiply(0.0001)
        scaled_stats = scaled_ndvi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=test_point,
            scale=250
        ).getInfo()
        
        scaled_value = scaled_stats.get('NDVI')
        print(f"Scaled NDVI value: {scaled_value:.4f}")
        print(f"Expected range: -0.2 to 1.0 (float)")
        
        if scaled_value < -0.2 or scaled_value > 1.0:
            print("⚠️  Scaled value outside expected range!")
        else:
            print("✅ Scaled value in expected range")
        
        # Test 3: Scaling factor verification
        print("\n--- Test 3: Scaling Factor Verification ---")
        calculated_scaled = raw_value * 0.0001
        print(f"Manual calculation: {raw_value} × 0.0001 = {calculated_scaled:.4f}")
        print(f"EE scaled value: {scaled_value:.4f}")
        
        if abs(calculated_scaled - scaled_value) < 0.0001:
            print("✅ Scaling factor verified!")
        else:
            print("❌ Scaling factor mismatch!")
        
        # Test 4: EVI scaling
        print("\n--- Test 4: EVI Scaling ---")
        raw_evi = image.select('EVI')
        scaled_evi = image.select('EVI').multiply(0.0001)
        
        evi_stats = scaled_evi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=test_point,
            scale=250
        ).getInfo()
        
        evi_value = evi_stats.get('EVI')
        print(f"Scaled EVI value: {evi_value:.4f}")
        print(f"Expected range: -0.2 to 1.0 (float)")
        
        if evi_value < -0.2 or evi_value > 1.0:
            print("⚠️  EVI value outside expected range!")
        else:
            print("✅ EVI value in expected range")
        
        print("\n" + "=" * 60)
        print("✅ Validation complete!")
        print("\nRECOMMENDATIONS:")
        print("- Always multiply MODIS NDVI/EVI by 0.0001")
        print("- Expected NDVI/EVI range: -0.2 to 1.0")
        print("- Typical vegetation NDVI: 0.2 to 0.8")
        print("- Water/clouds NDVI: < 0")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        return False


def validate_statistics_file(csv_path: str):
    """
    Validate a statistics CSV file
    
    Args:
        csv_path: Path to monthly_summary CSV file
    """
    print("\n🔍 Statistics File Validation")
    print("=" * 60)
    
    try:
        df = pd.read_csv(csv_path)
        print(f"✅ Loaded: {csv_path}")
        print(f"   Rows: {len(df)}")
        print(f"   Columns: {list(df.columns)}\n")
        
        issues = []
        
        # Check NDVI values
        if 'NDVI_mean' in df.columns:
            ndvi_vals = df['NDVI_mean'].dropna()
            print("--- NDVI Analysis ---")
            print(f"Mean: {ndvi_vals.mean():.4f}")
            print(f"Min:  {ndvi_vals.min():.4f}")
            print(f"Max:  {ndvi_vals.max():.4f}")
            
            if ndvi_vals.min() < -1 or ndvi_vals.max() > 1:
                issues.append("❌ NDVI values outside valid range (-1 to 1)")
                print("❌ Values outside valid range!")
                print("   This indicates missing scaling factor (multiply by 0.0001)")
            elif ndvi_vals.min() < -0.2 or ndvi_vals.max() > 1:
                issues.append("⚠️  NDVI values in unusual range")
                print("⚠️  Values in unusual range (but technically valid)")
            else:
                print("✅ Values in valid range")
        
        # Check EVI values
        if 'EVI_mean' in df.columns:
            evi_vals = df['EVI_mean'].dropna()
            print("\n--- EVI Analysis ---")
            print(f"Mean: {evi_vals.mean():.4f}")
            print(f"Min:  {evi_vals.min():.4f}")
            print(f"Max:  {evi_vals.max():.4f}")
            
            if evi_vals.min() < -1 or evi_vals.max() > 1:
                issues.append("❌ EVI values outside valid range (-1 to 1)")
                print("❌ Values outside valid range!")
                print("   This indicates missing scaling factor (multiply by 0.0001)")
            elif evi_vals.min() < -0.2 or evi_vals.max() > 1:
                issues.append("⚠️  EVI values in unusual range")
                print("⚠️  Values in unusual range (but technically valid)")
            else:
                print("✅ Values in valid range")
        
        # Check VCI values
        if 'VCI_mean' in df.columns:
            vci_vals = df['VCI_mean'].dropna()
            print("\n--- VCI Analysis ---")
            print(f"Mean: {vci_vals.mean():.2f}")
            print(f"Min:  {vci_vals.min():.2f}")
            print(f"Max:  {vci_vals.max():.2f}")
            
            if vci_vals.min() < 0 or vci_vals.max() > 100:
                issues.append("❌ VCI values outside valid range (0 to 100)")
                print("❌ Values outside valid range!")
            else:
                print("✅ Values in valid range")
        
        print("\n" + "=" * 60)
        if issues:
            print("⚠️  ISSUES FOUND:")
            for issue in issues:
                print(f"  {issue}")
            return False
        else:
            print("✅ All values in valid ranges!")
            return True
            
    except Exception as e:
        print(f"❌ Error validating file: {e}")
        return False


def main():
    """Main validation routine"""
    print("\n" + "=" * 60)
    print("MODIS Vegetation Analysis - Data Validation Tool")
    print("=" * 60 + "\n")
    
    # Test 1: MODIS scaling
    print("Test 1: MODIS Data Scaling")
    validate_modis_scaling()
    
    print("\n\n")
    
    # Test 2: Check for statistics files
    print("Test 2: Statistics File Validation")
    print("-" * 60)
    
    # Look for statistics files
    output_dirs = list(Path("modis_outputs").glob("analysis_*/statistics"))
    
    if not output_dirs:
        print("⚠️  No statistics files found")
        print("   Run an analysis first, then rerun this validation")
    else:
        for stats_dir in output_dirs:
            csv_files = list(stats_dir.glob("monthly_summary_*.csv"))
            for csv_file in csv_files:
                validate_statistics_file(str(csv_file))
                print()


if __name__ == "__main__":
    main()